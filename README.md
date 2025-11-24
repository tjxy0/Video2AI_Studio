# **Video2AI Studio：视频风格化工作台**

## **🌟 项目简介**

Video2AI Studio 是一个基于 **Stable Diffusion** 和 **ControlNet (OpenPose)** 技术的桌面应用，旨在提供一个高效、易用的工作台，帮助用户将普通视频一键转换为各种艺术风格（如动漫、油画）的视频。

本应用采用了 PyQt-Fluent-Widgets 框架构建了现代化 UI，并针对 AI 流程进行了多项性能优化，包括显存优化和临时文件自动清理。

## **✨ 主要功能与特性**

* **分步式工作流 (Wizard)**：通过 "欢迎页 \-\> 步骤 1 (预处理) \-\> 步骤 2 (参数设置) \-\> 步骤 3 (任务控制)" 的引导式流程，确保用户轻松完成所有配置。  
* **AI 核心功能**：  
  * **ControlNet 骨骼提取**：支持 OpenPose 骨骼提取，实现视频角色动作的精确控制和重绘。  
  * **Img2Img 风格迁移**：支持纯粹的图生图模式，用于视频风格的平滑迁移。  
* **性能优化**：  
  * **低显存模式 (Low VRAM)**：支持模型自动 CPU 卸载 (enable\_model\_cpu\_offload)，适合 4GB \- 6GB 显卡。  
  * **xFormers 优化**：支持启用 xFormers，显著减少显存占用并加速推理。  
  * **内存管理**：在帧处理、姿态提取和生成等关键环节中，通过显存缓存清理 (torch.cuda.empty\_cache()) 机制，有效降低内存峰值占用。  
* **高效文件管理**：  
  * **自定义输出**：用户可以自由选择最终合成视频的输出目录。  
  * **临时文件清理**：处理过程中产生的原始帧、骨骼图等中间文件将存储在 output/temp\_frames 临时文件夹中，并在任务结束后**自动彻底清理**。  
* **环境自检**：启动时自动检测 CUDA (GPU)、FFmpeg 等关键依赖状态。

## **🛠️ 环境要求**

* **操作系统**：Windows 10/11, Linux (推荐 Windows)  
* **Python 环境**：Python 3.10  
* **显卡**：NVIDIA GPU (最低 4GB VRAM，推荐 8GB 或更高)  
* **依赖**：  
  * CUDA Toolkit (12.8 ，取决于您的 PyTorch 版本)  
  * FFmpeg (必须安装并添加到系统环境变量中)

## **📦 安装与启动**

### **1\. 克隆项目**

``` bash
git clone https://github.com/tjxy0/Video2AI_Studio.git 
cd Video2AI\_Studio
```

### **2\. 创建并激活虚拟环境 (推荐)**
``` bash
python \-m venv venv  
# Windows  
.\\venv\\Scripts\\activate  
# macOS/Linux  
source venv/bin/activate
```
### **3\. 安装依赖**

请确保您的 PyTorch/CUDA 版本与 GPU 兼容,本项目使用的CUDA版本为12.8。项目依赖在 requirements.txt 中：
``` bash
pip install \-r requirements.txt  
# 注意：PyTorch/xformers 的 GPU 版本需要使用特定命令安装，  
pip3 install torch torchvision xformers --index-url https://download.pytorch.org/whl/cu128
```

### **4\. 启动应用**
``` bash
python main.py
```
## **🚀 使用工作流**

应用启动后，您将进入分步式工作流。请按照以下步骤操作：

### **欢迎页**

点击 **"开始工作流"** 进入配置流程。

### **步骤 1: 视频与预处理设置**

1. **选择视频**：拖入或点击选择源视频文件。  
2. **设置预处理**：配置 目标帧率 (FPS) 和 目标宽度 (PX)。  
3. **骨骼提取**：选择是否 启用骨骼提取 (ControlNet 模式) 或禁用 (Img2Img 模式)。  
4. 点击 **"下一步"**。

### **步骤 2: 生成参数设置**

1. **选择基础模型**：点击选择 .safetensors 格式的 Stable Diffusion Checkpoint 模型。  
2. **配置提示词**：输入 正向提示词 (Prompt) 和 负面提示词 (Negative Prompt)。  
3. **调整核心参数**：设置 迭代步数、CFG Scale 和 随机种子 (Seed)。  
   * **注意**：如果您在步骤 1 关闭了骨骼提取，请配置 重绘幅度 (denoising\_strength)。  
4. 点击 **"下一步"**。

### **步骤 3: 输出设置与任务控制**

1. **选择最终输出目录**：点击 **"选择目录"** 设定最终视频 final\_output.mp4 的保存位置。  
2. **启动任务**：点击 **"开始生成处理"** 启动 AI 工作线程。进度和状态将实时显示。  
3. **中止任务**：在处理过程中，您可以随时点击 **"停止任务"** 来中止。

## **💡 性能提示**

1. **Low VRAM 模式**：如果您的显存小于 8GB，请在 **“设置”** 页面启用 **“低显存模式”**。  
2. **临时文件**：所有中间文件（原始帧、姿态图）都会被自动清理，无需手动干预。

## **许可协议**

本项目采用 [Apache 许可证 2.0](http://www.apache.org/licenses/LICENSE-2.0)。

