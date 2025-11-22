import sys
import os
import shutil
import subprocess
import time
import cv2
from pathlib import Path

# GUI Imports
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QFrame

# Fluent Widgets (按照报告推荐使用)
from qfluentwidgets import (
    FluentWindow, SubtitleLabel, PrimaryPushButton, ProgressBar,
    InfoBar, InfoBarPosition, CardWidget, IconWidget,
    BodyLabel, PushSettingCard, RangeSettingCard,
    SwitchSettingCard, LineEdit, TextEdit, ScrollArea,
    FluentIcon as FIF, setTheme, Theme
)

# AI & Processing Imports
import torch
from PIL import Image
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler


# -----------------------------------------------------------------------------
# 核心逻辑层 (Model & Worker)
# -----------------------------------------------------------------------------

class EnvironmentChecker:
    """
    对应报告 7.1 节：环境完整性保障
    负责检测 CUDA 和 FFmpeg 状态
    """

    @staticmethod
    def check_ffmpeg():
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def check_cuda():
        return torch.cuda.is_available()


class GenerationConfig:
    """
    配置数据类
    """

    def __init__(self):
        self.input_video_path = ""
        self.model_path = ""  # .safetensors 路径
        self.output_dir = "output"
        self.prompt = "high quality, masterpiece, anime style, 1girl, vivid colors"
        self.negative_prompt = "low quality, bad anatomy, watermark, text, error"
        self.seed = 12345
        self.steps = 20
        self.cfg_scale = 7.5
        self.use_xformers = False
        self.low_vram = False


class AIWorker(QThread):
    """
    对应报告 2.2 节 & 8.2 节：数据流转管线与线程模型
    """
    progress_signal = pyqtSignal(int, str)  # 进度(0-100), 状态文本
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, config: GenerationConfig):
        super().__init__()
        self.config = config
        self.running = True

    def run(self):
        try:
            if not self.config.input_video_path or not os.path.exists(self.config.input_video_path):
                raise ValueError("无效的视频输入路径")

            # 准备目录
            temp_raw = os.path.join(self.config.output_dir, "frames_raw")
            temp_pose = os.path.join(self.config.output_dir, "frames_pose")
            temp_out = os.path.join(self.config.output_dir, "frames_out")

            for d in [temp_raw, temp_pose, temp_out]:
                os.makedirs(d, exist_ok=True)

            # -------------------------------------------------------
            # 阶段 1: 视频重采样与拆帧 (FFmpeg)
            # 对应报告 4.2 节: "fps=24,scale=512:-1"
            # -------------------------------------------------------
            self.progress_signal.emit(5, "正在进行 FFmpeg 时域重采样 (24fps)...")

            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", self.config.input_video_path,
                "-vf", "fps=24,scale=512:-1",  # 核心滤镜：锁定24帧，宽512，高自适应
                "-q:v", "2",  # 高质量 JPG
                os.path.join(temp_raw, "frame_%04d.jpg")
            ]

            # Windows下隐藏控制台窗口
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(ffmpeg_cmd, check=True, startupinfo=startupinfo)

            frame_files = sorted([f for f in os.listdir(temp_raw) if f.endswith(".jpg")])
            total_frames = len(frame_files)
            if total_frames == 0:
                raise RuntimeError("FFmpeg 未能提取任何帧")

            # -------------------------------------------------------
            # 阶段 2: 语义骨骼提取 (OpenPose)
            # 对应报告 5.1 节: ControlNet Aux 集成
            # -------------------------------------------------------
            self.progress_signal.emit(15, "正在加载 OpenPose 检测器...")

            # 延迟导入以加快 GUI 启动速度
            from controlnet_aux import OpenposeDetector

            # 自动下载/加载模型
            detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

            self.progress_signal.emit(20, "开始提取骨骼关键点...")

            for idx, f_name in enumerate(frame_files):
                if not self.running: return

                img_path = os.path.join(temp_raw, f_name)
                img = Image.open(img_path)

                # 推理并保存骨骼图
                pose = detector(img)
                pose.save(os.path.join(temp_pose, f_name))

                # 更新进度 (20% - 40%)
                prog = 20 + int((idx / total_frames) * 20)
                self.progress_signal.emit(prog, f"提取骨骼: {idx + 1}/{total_frames}")

            # 释放显存，防止 OOM
            del detector
            torch.cuda.empty_cache()

            # -------------------------------------------------------
            # 阶段 3: Stable Diffusion 生成
            # 对应报告 6.1 & 6.2 节: 确定性控制
            # -------------------------------------------------------
            self.progress_signal.emit(40, "正在加载 Stable Diffusion 模型...")

            # 加载 ControlNet
            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/sd-controlnet-openpose",
                torch_dtype=torch.float16
            )

            # 加载基础模型 (支持 safetensors 单文件)
            # 注意：实际使用需要对应配置 yaml，这里为了演示简化了 config 加载
            if self.config.model_path.endswith(".safetensors"):
                pipe = StableDiffusionControlNetPipeline.from_single_file(
                    self.config.model_path,
                    controlnet=controlnet,
                    torch_dtype=torch.float16,
                    use_safetensors=True,
                    load_safety_checker=False
                )
            else:
                # 默认回退到在线模型作为演示
                pipe = StableDiffusionControlNetPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    controlnet=controlnet,
                    torch_dtype=torch.float16
                )

            # 调度器配置
            pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

            # 显存优化 (报告 6.3 节)
            if self.config.use_xformers:
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    print("xFormers 不可用，跳过")

            if self.config.low_vram:
                pipe.enable_model_cpu_offload()
            else:
                pipe.to("cuda")

            self.progress_signal.emit(50, "开始批量生成风格化帧...")

            for idx, f_name in enumerate(frame_files):
                if not self.running: return

                pose_path = os.path.join(temp_pose, f_name)
                pose_img = Image.open(pose_path)

                # -------------------------------------------------------
                # 核心：确定性噪声初始化 (报告 6.2 节)
                # 每次循环都重新创建 Generator 并设置相同的 Seed
                # -------------------------------------------------------
                generator = torch.Generator(device="cuda").manual_seed(self.config.seed)

                image = pipe(
                    self.config.prompt,
                    negative_prompt=self.config.negative_prompt,
                    image=pose_img,
                    num_inference_steps=self.config.steps,
                    generator=generator,  # 传入重置后的生成器
                    guidance_scale=self.config.cfg_scale
                ).images[0]

                save_path = os.path.join(temp_out, f_name)
                image.save(save_path)

                # 更新进度 (50% - 95%)
                prog = 50 + int((idx / total_frames) * 45)
                self.progress_signal.emit(prog, f"生成中: {idx + 1}/{total_frames}")

            # -------------------------------------------------------
            # 阶段 4: 合成视频 (可选，这里简单调用 FFmpeg 合成)
            # -------------------------------------------------------
            self.progress_signal.emit(95, "正在合成最终视频...")
            output_video = os.path.join(self.config.output_dir, "final_output.mp4")

            ffmpeg_build_cmd = [
                "ffmpeg", "-y",
                "-r", "24",
                "-i", os.path.join(temp_out, "frame_%04d.jpg"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_video
            ]
            subprocess.run(ffmpeg_build_cmd, check=True, startupinfo=startupinfo)

            self.progress_signal.emit(100, "完成！")
            self.finished_signal.emit()

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))

    def stop(self):
        self.running = False


# -----------------------------------------------------------------------------
# 界面层 (View) - 基于 PyQt-Fluent-Widgets
# -----------------------------------------------------------------------------

class HomeInterface(QWidget):
    """
    主工作台：文件拖入与任务控制
    """

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.setObjectName("homeInterface")

        self.vBoxLayout = QVBoxLayout(self)

        # 1. 标题
        self.titleLabel = SubtitleLabel("视频风格化工作台", self)

        # 2. 拖拽区域 (使用 CardWidget 模拟)
        self.dropArea = CardWidget(self)
        self.dropArea.setAcceptDrops(True)
        self.dropArea.setFixedSize(600, 200)
        self.dropAreaLayout = QVBoxLayout(self.dropArea)

        self.iconWidget = IconWidget(FIF.VIDEO, self.dropArea)
        self.iconWidget.setFixedSize(48, 48)
        self.hintLabel = BodyLabel("将视频文件拖拽至此，或点击选择", self.dropArea)

        self.dropAreaLayout.addWidget(self.iconWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.dropAreaLayout.addWidget(self.hintLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        # 启用拖拽事件
        self.dropArea.dragEnterEvent = self.dragEnterEvent
        self.dropArea.dropEvent = self.dropEvent
        self.dropArea.mousePressEvent = self.selectFile

        # 3. 进度条
        self.progressBar = ProgressBar(self)
        self.progressBar.setFixedWidth(600)
        self.progressBar.setValue(0)
        self.statusLabel = BodyLabel("准备就绪", self)

        # 4. 开始按钮
        self.startBtn = PrimaryPushButton("开始生成处理", self)
        self.startBtn.setFixedWidth(200)
        self.startBtn.clicked.connect(self.start_processing)

        # 布局添加
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.dropArea, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(30)
        self.vBoxLayout.addWidget(self.statusLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addWidget(self.progressBar, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.startBtn, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addStretch(1)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        if files:
            self.load_video(files[0])

    def selectFile(self, e):
        fname, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "Video Files (*.mp4 *.avi *.mov)")
        if fname:
            self.load_video(fname)

    def load_video(self, path):
        self.config.input_video_path = path
        self.hintLabel.setText(f"已加载: {os.path.basename(path)}")
        self.iconWidget.setIcon(FIF.COMPLETED)

    def start_processing(self):
        if not self.config.input_video_path:
            InfoBar.warning(
                title='未选择视频',
                content="请先拖入或选择一个视频文件。",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 锁定 UI
        self.startBtn.setEnabled(False)
        self.startBtn.setText("处理中...")

        # 启动 Worker
        self.worker = AIWorker(self.config)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def update_progress(self, value, text):
        self.progressBar.setValue(value)
        self.statusLabel.setText(text)

    def on_finished(self):
        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始生成处理")
        self.progressBar.setValue(100)
        InfoBar.success(
            title='任务完成',
            content="视频生成已完成，请查看 output 文件夹。",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            parent=self
        )

    def on_error(self, err_msg):
        self.startBtn.setEnabled(True)
        self.startBtn.setText("开始生成处理")
        self.progressBar.setValue(0)
        self.statusLabel.setText("发生错误")
        InfoBar.error(
            title='处理失败',
            content=err_msg,
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            parent=self
        )


class SettingInterface(ScrollArea):
    """
    设置中心：调整参数
    """

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.setObjectName("settingInterface")

        # 标题
        self.expandLayout.addWidget(SubtitleLabel("生成参数设置", self))

        # 模型选择
        self.modelCard = PushSettingCard(
            "选择文件",
            FIF.folder,
            "Stable Diffusion 模型 (.safetensors)",
            self.config.model_path if self.config.model_path else "尚未选择，默认将下载通用模型",
            self.scrollWidget
        )
        self.modelCard.clicked.connect(self.select_model)
        self.expandLayout.addWidget(self.modelCard)

        # 提示词
        self.promptEdit = TextEdit(self.scrollWidget)
        self.promptEdit.setPlaceholderText("正向提示词 (Prompt)")
        self.promptEdit.setText(self.config.prompt)
        self.promptEdit.textChanged.connect(lambda: setattr(self.config, 'prompt', self.promptEdit.toPlainText()))
        self.expandLayout.addWidget(self.promptEdit)

        # 步数设置 (RangeSettingCard)
        self.stepsCard = RangeSettingCard(
            self.config.steps, 60,
            FIF.SPEED_HIGH,
            "迭代步数 (Steps)",
            "ControlNet 通常需要 20-30 步",
            self.scrollWidget
        )
        self.stepsCard.setValue(self.config.steps)
        self.stepsCard.valueChanged.connect(lambda v: setattr(self.config, 'steps', v))
        self.expandLayout.addWidget(self.stepsCard)

        # CFG Scale
        self.cfgCard = RangeSettingCard(
            int(self.config.cfg_scale * 10), 200,
            FIF.PALETTE,
            "提示词相关性 (CFG Scale)",
            "数值越高越遵循提示词，建议 7.0-9.0",
            self.scrollWidget
        )
        self.cfgCard.setValue(int(self.config.cfg_scale * 10))
        # 注意：这里简化处理，GUI显示整数，实际存储浮点
        self.cfgCard.valueChanged.connect(lambda v: setattr(self.config, 'cfg_scale', v / 10.0))
        self.expandLayout.addWidget(self.cfgCard)

        # 随机种子
        self.seedCard = LineEdit(self.scrollWidget)
        self.seedCard.setPlaceholderText("随机种子 (Seed)")
        self.seedCard.setText(str(self.config.seed))
        self.seedCard.textChanged.connect(self.update_seed)
        self.expandLayout.addWidget(self.seedCard)

        # 性能开关
        self.xformersCard = SwitchSettingCard(
            FIF.FLASH,
            "启用 xFormers",
            "降低显存占用并加速推理 (需要环境支持)",
            self.config.use_xformers,
            self.scrollWidget
        )
        self.xformersCard.checkedChanged.connect(lambda v: setattr(self.config, 'use_xformers', v))
        self.expandLayout.addWidget(self.xformersCard)

        self.expandLayout.addStretch(1)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

    def select_model(self):
        fname, _ = QFileDialog.getOpenFileName(self, "选择模型", "", "Safetensors (*.safetensors);;All Files (*)")
        if fname:
            self.config.model_path = fname
            self.modelCard.setContent(fname)

    def update_seed(self, text):
        if text.isdigit():
            self.config.seed = int(text)


class MainWindow(FluentWindow):
    """
    主窗口容器
    """

    def __init__(self):
        super().__init__()
        self.config = GenerationConfig()

        # 初始化窗口属性
        self.setWindowTitle("Video2AI Studio")
        self.resize(900, 700)
        self.setWindowIcon(QIcon("assets/icon.png"))  # 假设有图标

        # 运行环境自检 (报告 7.1 节)
        self.run_env_check()

        # 创建子界面
        self.homeInterface = HomeInterface(self.config, self)
        self.settingInterface = SettingInterface(self.config, self)

        # 添加导航项
        self.addSubInterface(self.homeInterface, FIF.HOME, "工作台")
        self.addSubInterface(self.settingInterface, FIF.SETTING, "设置")

    def run_env_check(self):
        """
        启动时检查 FFmpeg 和 CUDA
        """
        if not EnvironmentChecker.check_ffmpeg():
            InfoBar.error(
                title='环境缺失',
                content='未检测到 FFmpeg，视频处理功能将无法使用。请安装 FFmpeg 并配置环境变量。',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=-1,
                parent=self
            )

        if not EnvironmentChecker.check_cuda():
            InfoBar.warning(
                title='GPU 不可用',
                content='未检测到 NVIDIA GPU 或 CUDA 环境。推理速度将极慢。',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self
            )


if __name__ == "__main__":
    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)

    # 设置主题
    setTheme(Theme.DARK)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())