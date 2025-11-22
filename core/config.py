class GenerationConfig:
    """
    全局配置数据类，用于在 GUI 和 Worker 之间传递参数
    """

    def __init__(self):
        # 输入输出
        self.input_video_path = ""
        self.output_dir = "output"

        # 模型路径
        self.model_path = ""  # .safetensors 路径
        self.yaml_path = "configs/v1-inference.yaml"  # 配置文件路径

        # 生成参数
        self.prompt = "high quality, masterpiece, anime style, 1girl, vivid colors"
        self.negative_prompt = "low quality, bad anatomy, watermark, text, error, ugly, deformed"
        self.seed = 12345
        self.steps = 20
        self.cfg_scale = 7.5

        # 硬件优化开关
        self.use_xformers = False
        self.low_vram = False