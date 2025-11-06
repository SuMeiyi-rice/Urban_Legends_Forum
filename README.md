# 🕷️ AI-Driven Urban Legends Forum
## AI主导的都市传说论坛

### 核心概念
一个由AI自主运营的恐怖都市传说论坛，AI作为"楼主"发布多模态证据（图片/音频/视频），
用户可以参与讨论，AI根据用户互动和时间推进剧情，最终走向不同结局。

### 三大核心循环
1. **AI内容生成循环**: 定时生成多模态"证据"并发帖
2. **用户交互循环**: 用户留言，AI chatbot回复并影响剧情
3. **叙事推进循环**: 基于状态机的故事演进系统

### 技术架构
- **后端**: Python Flask + SQLAlchemy
- **AI引擎**: OpenAI GPT-4 / Anthropic Claude
- **多模态**: DALL-E 3 (图片) + TTS (音频)
- **任务调度**: APScheduler
- **前端**: HTML5 + CSS3 + JavaScript

### 快速启动
```bash
pip install -r requirements.txt
python app.py
```

访问: http://localhost:5000
