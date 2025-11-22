import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler


class PipelineLoader:
    """
    封装复杂的模型加载逻辑 (报告 6.1)
    处理 .safetensors 单文件加载与 ControlNet 注入
    """

    @staticmethod
    def load_pipeline(config):
        # 1. 加载 ControlNet (OpenPose)
        # 使用 fp16 精度以节省显存 (报告 6.3)
        controlnet = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-openpose",
            torch_dtype=torch.float16
        )

        # 2. 加载 Stable Diffusion
        # 区分单文件加载 (.safetensors) 和文件夹加载
        if config.model_path and config.model_path.endswith(".safetensors"):
            # 必须指定 original_config_file 才能离线加载单文件 (报告 6.1)
            pipe = StableDiffusionControlNetPipeline.from_single_file(
                config.model_path,
                controlnet=controlnet,
                original_config_file=config.yaml_path,
                torch_dtype=torch.float16,
                use_safetensors=True,
                load_safety_checker=False
            )
        else:
            # 默认回退到在线模型 (如果用户未选择)
            print("未指定本地模型，使用 HuggingFace 在线模型...")
            pipe = StableDiffusionControlNetPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                controlnet=controlnet,
                torch_dtype=torch.float16
            )

        # 3. 替换调度器 (Scheduler)
        # UniPC 可以在 20 步内生成高质量图像，提升视频处理速度
        pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

        # 4. 显存与性能优化 (报告 6.3)
        if config.use_xformers:
            try:
                pipe.enable_xformers_memory_efficient_attention()
            except Exception as e:
                print(f"xFormers 启用失败: {e}")

        if config.low_vram:
            # CPU Offload: 仅在推理时将模型层移入 GPU
            pipe.enable_model_cpu_offload()
        else:
            pipe.to("cuda")

        return pipe