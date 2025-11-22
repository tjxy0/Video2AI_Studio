import subprocess
import torch
import webbrowser

class EnvironmentChecker:
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

    @staticmethod
    def get_cuda_info():
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
        return "N/A"

    @staticmethod
    def open_install_guide(tool_name):
        urls = {
            "ffmpeg": "https://ffmpeg.org/download.html",
            "pytorch": "https://pytorch.org/get-started/locally/"
        }
        webbrowser.open(urls.get(tool_name, "https://www.google.com"))