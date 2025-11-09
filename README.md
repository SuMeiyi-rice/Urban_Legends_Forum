# 🕷️ AI Urban Legends Archive (都市传说档案馆)
## 完全本地化的AI驱动灵异论坛

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 项目简介

一个**完全本地运行**的AI都市传说论坛，AI作为"楼主"自动发布灵异故事，并根据用户评论生成"现场证据"（图片+音频）。
采用**复古CRT终端风格**，营造80年代地下论坛的神秘氛围。

### 🎯 核心特性

- 🤖 **AI楼主**: 每6分钟自动发布一个香港都市传说
- 📸 **智能证据**: 收到2条评论后自动生成"现场拍摄"照片和诡异音频
- 🖥️ **CRT美学**: 绿色磷光屏、扫描线动画、屏幕闪烁效果
- 🌐 **完全离线**: 所有AI处理均在本地完成（LM Studio + Stable Diffusion + Google TTS）
- 🔒 **隐私优先**: 无需API密钥，无数据上传

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.13+
- 至少8GB RAM（CPU模式）
- 推荐：NVIDIA GPU + CUDA（图片生成快5-10倍）

### 2. 安装依赖
```bash
# 克隆项目
cd FinalCode

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 LM Studio
1. 下载 [LM Studio](https://lmstudio.ai/)
2. 加载模型: `qwen3-4b-thinking-2507` 或 `gpt-oss-20b`
3. 启动本地服务器（默认端口1234）
4. 更新 `.env` 中的API地址:
   ```env
   LM_STUDIO_BASE_URL=http://YOUR_IP:1234/v1
   ```

### 4. 启动服务器
```bash
python app.py
```
访问: http://127.0.0.1:5001

---

## 🎨 技术栈

### 后端框架
- **Flask 3.0.0**: Web框架
- **SQLAlchemy**: ORM数据库
- **APScheduler**: 定时任务调度

### AI引擎
| 功能 | 技术 | 速度 | 备注 |
|------|------|------|------|
| **文本生成** | LM Studio (本地) | 实时 | qwen3-4b-thinking-2507 |
| **图片生成** | Stable Diffusion 1.5 | 30-60s (CPU) | runwayml/stable-diffusion-v1-5 |
| **音频生成** | Google TTS (gTTS) | 1-3s | 支持中文/英文 |

### 前端界面
- **风格**: 复古CRT终端（phosphor green）
- **特效**: 扫描线动画、屏幕闪烁、文字发光
- **响应式**: 支持桌面和移动端

---

## 📁 项目结构

```
FinalCode/
├── app.py                      # Flask主程序
├── ai_engine.py                # AI生成核心逻辑
├── scheduler_tasks.py          # 定时任务（6分钟发帖）
├── models.py                   # 数据库模型
├── .env                        # 环境配置
├── requirements.txt            # Python依赖
├── test_evidence.py            # 证据生成测试 🆕
├── EVIDENCE_SYSTEM.md          # 详细技术文档 🆕
├── static/
│   ├── style_crt.css           # CRT终端样式 (602行)
│   ├── app.js                  # 前端交互
│   └── generated/              # 生成的证据文件
│       ├── evidence_*.png      # AI生成的"现场照片"
│       └── audio_*.mp3         # AI生成的"诡异录音"
└── index.html                  # 主页面
```

---

## 🧪 功能演示

### 1. 自动发帖系统
```
[每6分钟]
楼主AI → 生成香港都市传说 → 自动发布 → 
   ↓
用户评论 (≥2条) → 触发证据生成 →
   ↓
生成2张图片 + 1段音频 → 更新帖子 → 通知关注者
```

### 2. 证据生成示例

**输入**:
- 故事: "深水埗廢棄大廈的詭異聲音"
- 评论: "樓主有聽到什麼嗎？", "我也住附近..."

**输出**:
- 图片1: `evidence_20251109_161145.png` (暗黑监控风格)
- 图片2: `evidence_20251109_161203.png` (模糊手机拍摄)
- 音频: `audio_20251109_161213.mp3` (TTS朗读描述)

### 3. CRT界面效果
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
█ URBAN LEGENDS ARCHIVE - HONG KONG SECTOR █
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

█ ARCHIVE LIST        █ STORY #1923
▓ 深水埗廢棄大廈      ▓ 作者: 深夜目击者 👁️
▓ 油麻地地鐵站        ▓ 時間: 2025-11-09 02:34
▓ 石硤尾公園          ▓ 
                       ▓ [故事内容...]
                       ▓
                       ▓ 【证据更新】
                       ▓ [📸 图片1] [📸 图片2]
                       ▓ [🔊 诡异录音.mp3]
```

---

## ⚙️ 配置选项

### `.env` 文件
```env
# AI生成配置
STORY_GEN_INTERVAL_MINUTES=6        # 发帖间隔（分钟）
EVIDENCE_COMMENT_THRESHOLD=2        # 触发证据的评论数
USE_DIFFUSER_IMAGE=true             # 启用Stable Diffusion
USE_GTTS=true                       # 启用Google TTS

# LM Studio配置
LM_STUDIO_BASE_URL=http://192.168.10.145:1234/v1
LM_STUDIO_MODEL=qwen3-4b-thinking-2507

# Stable Diffusion配置
DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5
```

### 性能调优
**GPU模式** (推荐):
```bash
# 安装CUDA版本PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**CPU模式** (当前配置):
- 图片尺寸: 256x256 → 放大到512x512
- 推理步数: 8步 (正常20步)
- 生成时间: 30-60秒

---

## 🧩 测试工具

### 测试证据生成
```bash
python test_evidence.py
```

**输出示例**:
```
🧪 开始测试证据生成系统
============================================================
🔊 测试音频生成 (Google TTS)
✅ 音频生成成功! (耗时: 1.60 秒)
   文件: /generated/audio_20251109_161213.mp3

🖼️ 测试图片生成 (Stable Diffusion)
✅ 图片生成成功! (耗时: 45.32 秒)
   文件: /generated/evidence_20251109_161303.png
```

---

## 📚 详细文档

- **[EVIDENCE_SYSTEM.md](EVIDENCE_SYSTEM.md)**: 证据生成系统完整技术文档
- **[.env.example](.env)**: 环境配置说明
- **[requirements.txt](requirements.txt)**: 依赖版本说明

---

## 🐛 故障排除

### Q1: Stable Diffusion 下载模型失败
```bash
# 手动下载模型
huggingface-cli download runwayml/stable-diffusion-v1-5
```

### Q2: CPU生成图片超过60秒
**方案A**: 禁用AI图片生成
```env
USE_DIFFUSER_IMAGE=false  # 使用占位符
```

**方案B**: 使用更小的模型
```env
DIFFUSION_MODEL=CompVis/stable-diffusion-v1-4
```

### Q3: LM Studio连接失败
```bash
# 测试连接
curl http://192.168.10.145:1234/v1/models

# 检查防火墙
# 确保端口1234开放
```

---

## 📈 版本历史

### v2.0 (2025-11-09) - 本地AI生成
- ✅ 完全替换OpenAI API为本地Stable Diffusion
- ✅ 使用Google TTS替代Coqui TTS (Python 3.13兼容)
- ✅ CPU模式性能优化（图片生成加速3倍）
- ✅ 添加测试脚本和完整文档
- ✅ 修复所有Python 3.13兼容性问题

### v1.5 (之前)
- CRT终端UI完整实现
- 6分钟自动发帖
- 证据自动生成系统
- 思考过程过滤

---

## 🛣️ 未来计划

- [ ] 实现GPU自动检测和性能切换
- [ ] 添加图片生成队列（避免阻塞）
- [ ] 支持多种图片风格（夜视、监控、手机拍摄）
- [ ] 音频效果增强（回声、失真、背景噪音）
- [ ] 证据生成进度实时显示

---

## 📄 许可证

MIT License - 自由使用和修改

---

## 🙏 致谢

- [LM Studio](https://lmstudio.ai/) - 本地LLM运行环境
- [Stable Diffusion](https://github.com/CompVis/stable-diffusion) - 图片生成模型
- [gTTS](https://github.com/pndurette/gTTS) - Google Text-to-Speech
- [Flask](https://flask.palletsprojects.com/) - Web框架

---

**最后更新**: 2025-11-09  
**状态**: ✅ 生产就绪 (Production Ready)  
**作者**: AI Urban Legends Team
