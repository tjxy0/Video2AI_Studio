class GenerationConfig:
    """
    全局配置数据类
    """

    def __init__(self):
        # 输入输出
        self.input_video_path = ""
        self.output_dir = "output"

        # 预处理参数
        self.target_fps = 24
        self.target_width = 512
        self.enable_pose = True  # 是否启用骨骼提取

        # 模型路径
        self.model_path = ""
        self.yaml_path = "configs/v1-inference.yaml"

        # 生成参数
        self.prompt = "high quality, masterpiece, anime style, 1girl, vivid colors"
        self.negative_prompt = "low quality, bad anatomy, watermark, text, error, ugly, deformed"
        self.seed = 12345
        self.steps = 20
        self.cfg_scale = 7.5
        self.denoising_strength = 0.75  # 重绘幅度 (仅 enable_pose=False 时生效)

        # 性能开关
        self.use_xformers = False
        self.low_vram = False