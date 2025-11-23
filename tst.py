def check_cuda():
    """检测 CUDA 是否可用 (延迟加载 torch 以防止 DLL 错误导致崩溃)"""
    try:
        import torch
        return torch.cuda.is_available()
    except (ImportError, OSError):
        return False


@staticmethod
def check_xformers():
    """检测 xformers 库是否安装"""
    try:
        import xformers
        return True
    except (ImportError, OSError):
        return False


print(check_cuda())
print(check_xformers())
