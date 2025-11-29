import os
import sys
from omegaconf import OmegaConf  # 保持不变


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

        # === 路径修复: 确保 config_yaml 路径在打包和未打包环境下都正确 ===

        # 1. 确定基础路径
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(current_dir)

        # 2. 构造配置文件的绝对路径
        config_file_name = os.path.basename(config.yaml_path)
        config_yaml_path = os.path.join(base_path, 'configs', config_file_name)

        # 3. 最终检查和打印信息
        if not os.path.exists(config_yaml_path):
            print(f"警告: 未找到绝对路径配置 {config_yaml_path}，尝试使用相对路径。")
            config_yaml_path = config.yaml_path
        else:
            print(f"信息: 使用配置路径 {config_yaml_path}")
        # =================================================================

        # === NEW: 手动加载 YAML 配置并检查内容 ===
        try:
            # 加载 OmegaConf 对象
            original_config_omegaconf = OmegaConf.load(config_yaml_path)
        except Exception as e:
            # 如果加载过程中发生解析错误或 IO 错误
            raise ValueError(f"无法加载或解析 YAML 配置文件: {config_yaml_path}. 请检查文件内容或路径。原始错误: {e}")

        if original_config_omegaconf is None:
            # 如果文件被读取但内容为空或格式不正确导致返回 None
            raise ValueError(f"YAML 配置文件 {config_yaml_path} 内容为空或格式不正确。")

        # === 修复: 不再传递配置参数，而是让 diffusers 自动推断 ===
        # 原来的错误是因为 diffusers 内部尝试将 dict 当作文件路径处理
        # 现在我们完全移除 config 参数，让模型从模型文件中推断配置
        # ==========================================

        # === 分支 A: 启用骨骼 (OpenPose + ControlNet) ===
        if config.enable_pose:
            print("正在加载 ControlNet OpenPose 管道...")
            controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/sd-controlnet-openpose",
                torch_dtype=torch.float16
            )

            if config.model_path and config.model_path.endswith(".safetensors"):
                # 完全移除 config 参数
                pipe = StableDiffusionControlNetPipeline.from_single_file(
                    config.model_path,
                    controlnet=controlnet,
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
                # 完全移除 config 参数
                pipe = StableDiffusionImg2ImgPipeline.from_single_file(
                    config.model_path,
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



