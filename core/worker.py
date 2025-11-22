import os
import subprocess
import torch
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal
from controlnet_aux import OpenposeDetector
from core.pipeline_utils import PipelineLoader


class AIWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True

    def run(self):
        try:
            if not self.config.input_video_path or not os.path.exists(self.config.input_video_path):
                raise ValueError("无效的视频输入路径")

            # 目录准备
            base_dir = self.config.output_dir
            dirs = {
                "raw": os.path.join(base_dir, "frames_raw"),
                "pose": os.path.join(base_dir, "frames_pose"),
                "out": os.path.join(base_dir, "frames_out")
            }
            for d in dirs.values():
                os.makedirs(d, exist_ok=True)

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # === 1. 视频拆帧 ===
            fps = self.config.target_fps
            width = self.config.target_width

            self.progress_signal.emit(5, f"拆帧中 ({fps}fps)...")
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
                    img = Image.open(os.path.join(dirs["raw"], f_name))
                    pose = detector(img)
                    pose.save(os.path.join(dirs["pose"], f_name))

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
                prog = 50 + int((idx / total_frames) * 45)
                self.progress_signal.emit(prog, f"帧生成: {idx + 1}/{total_frames}")

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

    def stop(self):
        self.running = False