class PipelineLoader:
    """
    根据配置动态加载 ControlNet 管线或 Img2Img 管线
    """

    @staticmethod
    def load_pipeline(config):
        # 延迟导入 AI 库，防止启动时的 DLL 错误
        import torch
        from diffusers import (
            StableDiffusionControlNetPipeline,
            StableDiffusionImg2ImgPipeline,
            ControlNetModel,
            UniPCMultistepScheduler
        )
        from diffusers.utils import is_xformers_available

        # === 分支 A: 启用骨骼 (OpenPose + ControlNet) ===
        if config.enable_pose:
            print("正在加载 ControlNet OpenPose 管道...")
            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/sd-controlnet-openpose",
                torch_dtype=torch.float16
            )

            if config.model_path and config.model_path.endswith(".safetensors"):
                pipe = StableDiffusionControlNetPipeline.from_single_file(
                    config.model_path,
                    controlnet=controlnet,
                    original_config_file=config.yaml_path,
                    torch_dtype=torch.float16,
                    use_safetensors=True,
                    load_safety_checker=False
                )
            else:
                pipe = StableDiffusionControlNetPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    controlnet=controlnet,
                    torch_dtype=torch.float16
                )

        # === 分支 B: 禁用骨骼 (纯 Img2Img) ===
        else:
            print("正在加载 Img2Img 图生图管道 (无骨骼)...")
            if config.model_path and config.model_path.endswith(".safetensors"):
                pipe = StableDiffusionImg2ImgPipeline.from_single_file(
                    config.model_path,
                    original_config_file=config.yaml_path,
                    torch_dtype=torch.float16,
                    use_safetensors=True,
                    load_safety_checker=False
                )
            else:
                pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=torch.float16
                )

        # 通用配置
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

        # === 优化 xFormers 加载逻辑 ===
        if config.use_xformers:
            if is_xformers_available():
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                    print(">> xFormers 优化已启用")
                except Exception as e:
                    print(f">> xFormers 启用失败: {e}")
            else:
                print(">> 警告: 配置启用了 xFormers，但未检测到该库。已自动回退到标准模式。")

        if config.low_vram:
            pipe.enable_model_cpu_offload()
            print(">> Low VRAM 模式已启用 (CPU Offload)")
        else:
            pipe.to("cuda")

        return pipe