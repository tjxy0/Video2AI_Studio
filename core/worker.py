import os
import subprocess
import shutil  # 新增：用于清理目录
from PyQt6.QtCore import QThread, pyqtSignal


# 注意：移除了顶部的 torch, PIL, controlnet_aux 导入
# 改为在 run() 方法中延迟导入，确保 GUI 启动时不崩溃

class AIWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True

    def run(self):
        # 确保 temp 目录变量在 try 块外部定义，以便在 finally 块中访问
        temp_dir = None
        base_dir = self.config.output_dir

        try:
            # === 延迟导入区 ===
            import torch
            from PIL import Image
            from controlnet_aux import OpenposeDetector
            from core.pipeline_utils import PipelineLoader
            # =================

            if not self.config.input_video_path or not os.path.exists(self.config.input_video_path):
                raise ValueError("无效的视频输入路径")

            # 确保主输出目录存在
            os.makedirs(base_dir, exist_ok=True)

            # 临时目录 (用于存放中间帧：raw, pose)
            temp_dir = os.path.join(base_dir, self.config.temp_dir_name)

            # 最终输出帧目录
            final_out_dir_name = "frames_out"
            out_dir = os.path.join(base_dir, final_out_dir_name)

            dirs = {
                # 原始帧和姿态帧放在临时目录
                "raw": os.path.join(temp_dir, "frames_raw"),
                "pose": os.path.join(temp_dir, "frames_pose"),
                # 最终生成帧放在主目录
                "out": out_dir
            }

            # 清理并创建必要的目录
            if os.path.exists(temp_dir):
                self.progress_signal.emit(1, "清理旧临时文件...")
                shutil.rmtree(temp_dir)  # 每次运行前清理旧的临时目录

            os.makedirs(temp_dir, exist_ok=True)
            for d in dirs.values():
                # 确保所有子目录都创建
                os.makedirs(d, exist_ok=True)

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # === 1. 视频拆帧 ===
            fps = self.config.target_fps
            width = self.config.target_width

            self.progress_signal.emit(5, f"拆帧中 ({fps}fps) -> 临时目录...")
            subprocess.run([
                "ffmpeg", "-y", "-i", self.config.input_video_path,
                "-vf", f"fps={fps},scale={width}:-1",
                "-q:v", "2",
                os.path.join(dirs["raw"], "frame_%04d.jpg")
            ], check=True, startupinfo=startupinfo)

            frame_files = sorted([f for f in os.listdir(dirs["raw"]) if f.endswith(".jpg")])
            total_frames = len(frame_files)

            # === 2. 姿态估计 (可选) ===
            if self.config.enable_pose:
                self.progress_signal.emit(15, "OpenPose 检测中...")
                detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

                for idx, f_name in enumerate(frame_files):
                    if not self.running: return

                    # --- 内存优化：处理完即释放 ---
                    img = Image.open(os.path.join(dirs["raw"], f_name))
                    pose = detector(img)
                    pose.save(os.path.join(dirs["pose"], f_name))
                    del img, pose  # 释放当前帧的内存

                    prog = 20 + int((idx / total_frames) * 20)
                    self.progress_signal.emit(prog, f"提取骨骼: {idx + 1}/{total_frames}")

                del detector
                torch.cuda.empty_cache()
            else:
                self.progress_signal.emit(20, "跳过骨骼提取 (Img2Img 模式)")

            # === 3. 风格化生成 ===
            self.progress_signal.emit(40, "加载生成模型...")
            pipe = PipelineLoader.load_pipeline(self.config)

            self.progress_signal.emit(50, "生成中...")
            for idx, f_name in enumerate(frame_files):
                if not self.running: return

                raw_img = Image.open(os.path.join(dirs["raw"], f_name))
                generator = torch.Generator(device="cuda").manual_seed(self.config.seed)

                # === 核心生成逻辑分支 ===
                if self.config.enable_pose:
                    # A: 使用骨骼控制网
                    pose_img = Image.open(os.path.join(dirs["pose"], f_name))
                    image = pipe(
                        prompt=self.config.prompt,
                        negative_prompt=self.config.negative_prompt,
                        image=pose_img,  # ControlNet 输入骨骼
                        num_inference_steps=self.config.steps,
                        generator=generator,
                        guidance_scale=self.config.cfg_scale
                    ).images[0]
                    del pose_img  # 释放骨骼图内存
                else:
                    # B: 使用图生图
                    image = pipe(
                        prompt=self.config.prompt,
                        negative_prompt=self.config.negative_prompt,
                        image=raw_img,  # Img2Img 输入原图
                        strength=self.config.denoising_strength,  # 重绘幅度
                        num_inference_steps=self.config.steps,
                        generator=generator,
                        guidance_scale=self.config.cfg_scale
                    ).images[0]

                image.save(os.path.join(dirs["out"], f_name))

                # --- 内存优化：释放当前帧和生成结果的内存 ---
                del raw_img, image
                torch.cuda.empty_cache()  # 每次释放 VRAM

                prog = 50 + int((idx / total_frames) * 45)
                self.progress_signal.emit(prog, f"帧生成: {idx + 1}/{total_frames}")

            del pipe  # 任务完成后卸载模型
            torch.cuda.empty_cache()

            # === 4. 视频合成 ===
            self.progress_signal.emit(95, "合成视频...")
            subprocess.run([
                "ffmpeg", "-y", "-r", str(fps),
                "-i", os.path.join(dirs["out"], "frame_%04d.jpg"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                os.path.join(base_dir, "final_output.mp4")
            ], check=True, startupinfo=startupinfo)

            self.progress_signal.emit(100, "完成！")
            self.finished_signal.emit()

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))

        finally:
            # === 5. 清理临时文件 (每次清理) ===
            if temp_dir and os.path.exists(temp_dir):
                self.progress_signal.emit(100, "清理临时文件...")
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"清理临时目录失败: {e}")
            # ==================================

    def stop(self):
        self.running = False