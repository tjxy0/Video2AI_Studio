import os
import subprocess
import torch
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

# 延迟导入 controlnet_aux 以避免 GUI 启动卡顿
from controlnet_aux import OpenposeDetector

from core.pipeline_utils import PipelineLoader


class AIWorker(QThread):
    """
    对应报告 2.2 节：Model-View-Worker 模式
    负责核心管线的异步执行，防止界面冻结
    """
    progress_signal = pyqtSignal(int, str)  # 进度(0-100), 状态文本
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

            # 准备临时目录
            base_dir = self.config.output_dir
            dirs = {
                "raw": os.path.join(base_dir, "frames_raw"),
                "pose": os.path.join(base_dir, "frames_pose"),
                "out": os.path.join(base_dir, "frames_out")
            }
            for d in dirs.values():
                os.makedirs(d, exist_ok=True)

            # Windows 下隐藏 FFmpeg 控制台窗口
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # =======================================================
            # 步骤 1: 视频拆帧 (FFmpeg) - 报告 4.2
            # =======================================================
            self.progress_signal.emit(5, "正在进行时域重采样 (24fps)...")

            ffmpeg_extract_cmd = [
                "ffmpeg", "-y",
                "-i", self.config.input_video_path,
                "-vf", "fps=24,scale=512:-1",  # 锁定 24 帧与 512 宽
                "-q:v", "2",  # 高质量 JPG
                os.path.join(dirs["raw"], "frame_%04d.jpg")
            ]

            subprocess.run(ffmpeg_extract_cmd, check=True, startupinfo=startupinfo)

            frame_files = sorted([f for f in os.listdir(dirs["raw"]) if f.endswith(".jpg")])
            total_frames = len(frame_files)
            if total_frames == 0:
                raise RuntimeError("FFmpeg 未能提取任何帧")

            # =======================================================
            # 步骤 2: 姿态估计 (OpenPose) - 报告 5.1
            # =======================================================
            self.progress_signal.emit(15, "正在加载 OpenPose 检测器...")

            # 自动下载/加载 OpenPose 预处理器
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

            self.progress_signal.emit(20, "开始提取骨骼关键点...")

            for idx, f_name in enumerate(frame_files):
                if not self.running: return

                img_path = os.path.join(dirs["raw"], f_name)
                img = Image.open(img_path)

                # 推理并保存
                pose = detector(img)
                pose.save(os.path.join(dirs["pose"], f_name))

                # 更新进度 (20% -> 40%)
                prog = 20 + int((idx / total_frames) * 20)
                self.progress_signal.emit(prog, f"提取骨骼: {idx + 1}/{total_frames}")

            # 显存清理
            del detector
            torch.cuda.empty_cache()

            # =======================================================
            # 步骤 3: 风格化生成 (Stable Diffusion) - 报告 6.2
            # =======================================================
            self.progress_signal.emit(40, "正在加载 Stable Diffusion 模型...")

            pipe = PipelineLoader.load_pipeline(self.config)

            self.progress_signal.emit(50, "开始批量生成...")

            for idx, f_name in enumerate(frame_files):
                if not self.running: return

                pose_path = os.path.join(dirs["pose"], f_name)
                pose_img = Image.open(pose_path)

                # ---------------------------------------------------
                # 关键核心：确定性噪声初始化
                # 必须在每次循环内部重置 Generator，确保背景闪烁最小化
                # ---------------------------------------------------
                generator = torch.Generator(device="cuda").manual_seed(self.config.seed)

                image = pipe(
                    prompt=self.config.prompt,
                    negative_prompt=self.config.negative_prompt,
                    image=pose_img,
                    num_inference_steps=self.config.steps,
                    generator=generator,  # 传入重置后的生成器
                    guidance_scale=self.config.cfg_scale
                ).images[0]

                image.save(os.path.join(dirs["out"], f_name))

                # 更新进度 (50% -> 95%)
                prog = 50 + int((idx / total_frames) * 45)
                self.progress_signal.emit(prog, f"生成中: {idx + 1}/{total_frames}")

            # =======================================================
            # 步骤 4: 视频合成 (FFmpeg)
            # =======================================================
            self.progress_signal.emit(95, "正在合成最终视频...")
            output_video_path = os.path.join(base_dir, "final_output.mp4")

            ffmpeg_build_cmd = [
                "ffmpeg", "-y",
                "-r", "24",
                "-i", os.path.join(dirs["out"], "frame_%04d.jpg"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_video_path
            ]
            subprocess.run(ffmpeg_build_cmd, check=True, startupinfo=startupinfo)

            self.progress_signal.emit(100, "处理完成！")
            self.finished_signal.emit()

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))

    def stop(self):
        self.running = False