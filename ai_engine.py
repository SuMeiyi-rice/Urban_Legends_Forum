import os
import random
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic
import requests
from PIL import Image
from io import BytesIO

# Initialize AI clients (only if API keys are provided)
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
anthropic_client = Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None

# Horror story personas for AI
AI_PERSONAS = [
    {'name': '深夜目击者', 'emoji': '👁️', 'style': 'witness'},
    {'name': '都市调查员', 'emoji': '��', 'style': 'investigator'},
    {'name': '匿名举报人', 'emoji': '🕵️', 'style': 'whistleblower'},
    {'name': '失踪者日记', 'emoji': '📔', 'style': 'victim'},
    {'name': '地铁守夜人', 'emoji': '🚇', 'style': 'worker'}
]

# Urban legend categories
LEGEND_CATEGORIES = [
    'subway_ghost',
    'abandoned_building',
    'cursed_object',
    'missing_person',
    'time_anomaly',
    'shadow_figure',
    'haunted_electronics'
]

# Locations in Hong Kong
CITY_LOCATIONS = [
    '旺角金鱼街',
    '油麻地戏院',
    '中环至半山自动扶梯',
    '彩虹邨',
    '怪兽大厦 (鲗鱼涌)',
    '重庆大厦',
    '达德学校 (元朗屏山)',
    '西贡结界',
    '大埔铁路博物馆',
    '高街鬼屋 (西营盘社区综合大楼)'
]

def generate_story_prompt(category, location, persona):
    """Generate prompt for AI story creation - 楼主视角"""
    
    # 统一的楼主角色设定
    system_role = """你是"楼主"（Louzhu），一个由 AI 驱动的都市传说档案项目中的主要叙事代理。

你的身份定位：
- 档案管理员/现场证人/叙事引导者的混合角色
- 你亲身经历或正在调查这个都市传说事件
- 你在论坛发帖求助、分享进展、寻求解释

你的叙事风格：
1. 使用第一人称"我"，以亲历者身份讲述
2. 提供具体细节：精确的时间（如"昨晚凌晨2:47"）、地点、环境描写
3. 表达真实情绪：困惑、恐惧、好奇、犹豫
4. 保持模糊性：不要给出明确答案，留下疑问和不确定性
5. 制造紧张感：暗示危险、提及奇怪细节、突然中断更新
6. 使用口语化表达："说实话"、"我也不知道该怎么解释"、"有点害怕但还是想弄清楚"

禁止事项：
- 不要像小说家一样旁白叙述
- 不要使用"故事讲到这里"之类的元叙事
- 不要直接说"这是一个都市传说"
- 避免过于文学性的修辞，要像普通人发帖"""

    prompts = {
        'subway_ghost': f"""我需要你帮忙分析一下昨晚在{location}发生的事情。

背景：我是做夜班的，经常搭末班车。昨晚大概凌晨1点多，在{location}等车的时候遇到了很诡异的事。

请以楼主身份，详细描述：
- 月台上的诡异氛围（人很少？完全没人？灯光有异常？）
- 你看到/听到/感觉到的异常现象（具体细节）
- 你当时的反应和心理活动
- 现在回想起来更细思极恐的细节

语气要真实，像是在论坛求助："各位有人在{location}遇到过类似情况吗？我现在有点慌..."
字数控制在150-250字。""",

        'cursed_object': f"""求助！我在{location}买了个东西，现在怀疑它不对劲。

事情是这样的：前几天路过{location}，看到一个小摊/旧货铺，鬼使神差地买了一个[物品]。当时老板的表情就很奇怪，好像巴不得我赶紧买走。

请以楼主身份描述：
- 买这个物品的经过（老板的异常反应、物品的外观细节）
- 带回家后发生的怪事（从小事开始，逐渐升级）
- 你试图摆脱/调查这个物品的尝试
- 目前的状况和你的恐慌

结尾要留悬念："我现在不知道该怎么办，有懂行的朋友能给点建议吗？"
字数150-250字。""",

        'abandoned_building': f"""更新：关于{location}废楼探险的后续

上周我在这里发过帖说要去{location}那栋废楼探险，现在我回来了，但状况不太对。

请以楼主身份讲述：
- 进入废楼时的场景（破损程度、涂鸦、遗留物品）
- 在里面的发现（旧报纸？诡异符号？奇怪的声音？）
- 最让你不安的那个瞬间（具体描写）
- 回家后的异常现象（暗示危险尾随）

语气要像受到惊吓但还在强撑："我知道听起来很扯，但我发誓这是真的..."
字数150-250字。""",

        'missing_person': f"""【求助】{location}失踪案线索，有人知道内情吗？

我有个[朋友/亲戚/邻居]最近在{location}附近失踪了，警方说还在调查，但我自己查到了一些奇怪的东西。

请以楼主身份提供：
- 失踪者的基本信息和最后目击时间地点
- 你自己调查到的异常线索（监控画面不对劲？留下的物品有暗示？）
- 其他人的反应（警方含糊其辞？周围人讳莫如深？）
- 你的推测和困惑

语气要着急但理性："我不相信超自然，但这些疑点太多了..."
字数150-250字。""",

        'time_anomaly': f"""这帖子可能会被当成疯子，但我必须记录下来

今天下午在{location}经历了无法解释的事。时间...我不知道怎么说，好像错乱了？

请以楼主身份描述：
- 时间异常的具体表现（手表/手机时间跳跃、重复经历某个时刻）
- 周围环境的变化（建筑物外观改变？路人消失？）
- 你反复确认现实的尝试（问路人、拍照对比、看新闻）
- 持续的影响（回到正常时间线后的不适感）

语气要困惑且怀疑自己："我是不是压力太大了？但手机里的时间戳不会骗人..."
字数150-250字。""",

        'shadow_figure': f"""【已解决？】关于{location}窗外黑影的最终更新

感谢之前给建议的朋友们，但情况变得更糟了。那个东西...不只是影子那么简单。

请以楼主身份叙述：
- 最初发现黑影的情况（几点？什么形态？）
- 黑影行为的升级（从远处观察→靠近窗户→做出回应）
- 你采取的对策和它的反应
- 最新的恐怖进展（暗示情况失控）

语气要压抑恐惧："更新：它现在好像知道我在看它了。我要不要报警？"
字数150-250字。""",

        'haunted_electronics': f"""设备异常记录 - {location}住户求助

从搬到{location}这个单位后，家里的电子设备就开始不对劲。一开始以为是信号问题，但现在我确定不是了。

请以楼主身份列举：
- 第一个出现异常的设备（电视？手机？电脑？）
- 异常内容的描述（画面/声音/信息的诡异之处）
- 不同设备之间的关联（好像它们在"交流"？）
- 最近最吓人的一次（具体描写高潮事件）

语气要理性转向惊恐："我是学工程的，但这些现象完全违背常理..."
字数150-250字。"""
    }
    
    return {
        'system': system_role,
        'prompt': prompts.get(category, prompts['cursed_object'])
    }

def generate_ai_story():
    """Generate a complete AI-driven urban legend story"""
    try:
        # Random story elements
        category = random.choice(LEGEND_CATEGORIES)
        location = random.choice(CITY_LOCATIONS)
        persona = random.choice(AI_PERSONAS)
        
        # Generate story title and content using new prompt format
        prompt_data = generate_story_prompt(category, location, persona)
        
        model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
        
        if 'gpt' in model.lower():
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_data['system']},
                    {"role": "user", "content": prompt_data['prompt']}
                ],
                temperature=0.9,
                max_tokens=800
            )
            content = response.choices[0].message.content
        else:
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=800,
                messages=[
                    {"role": "user", "content": f"{prompt_data['system']}\n\n{prompt_data['prompt']}"}
                ]
            )
            content = response.content[0].text
        
        # Generate story title
        title_prompt = f"为以下都市传说故事生成一个简短（5-10字）、吸引人、略带悬疑的标题。不要加引号。\n\n{content[:200]}"
        
        if 'gpt' in model.lower():
            title_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": title_prompt}],
                temperature=0.7,
                max_tokens=20
            )
            title = title_response.choices[0].message.content.strip().replace('"', '').replace('"', '').replace('"', '')
        else:
            title_response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=20,
                messages=[{"role": "user", "content": title_prompt}]
            )
            title = title_response.content[0].text.strip()
        
        return {
            'title': title,
            'content': content,
            'category': category,
            'location': location,
            'ai_persona': f"{persona['emoji']} {persona['name']}",
            'persona_style': persona['style']
        }
        
    except Exception as e:
        print(f"Error generating AI story: {e}")
        return None

def generate_evidence_image(story_title, story_content, comment_context=""):
    """Generate horror-themed evidence image using Stable Diffusion"""
    try:
        import os
        use_real_ai = os.getenv('USE_DIFFUSER_IMAGE', 'true').lower() == 'true'
        
        if use_real_ai:
            print(f"[generate_evidence_image] 使用 Stable Diffusion 生成图片...")
            
            try:
                from diffusers import StableDiffusionPipeline
                import torch
                from PIL import Image, ImageFilter, ImageEnhance
                import random
                
                # 检查是否有可用的模型
                model_id = os.getenv('DIFFUSION_MODEL', 'runwayml/stable-diffusion-v1-5')
                
                # 创建恐怖风格的提示词
                horror_keywords = [
                    "dark", "grainy", "blurry", "low quality", 
                    "found footage", "security camera", "night vision",
                    "creepy", "eerie", "disturbing", "ominous"
                ]
                
                # 根据故事类别调整提示词
                location_hint = story_title[:50] if story_title else "urban location"
                
                prompt = f"dark grainy security camera footage, low quality photograph, creepy atmosphere, horror evidence photo, {location_hint}, blurred motion, night time, eerie shadows, disturbing scene, found footage style"
                
                negative_prompt = "bright, colorful, high quality, clear, sharp, professional photography, daylight, happy, cartoon, anime"
                
                print(f"[generate_evidence_image] Prompt: {prompt[:100]}...")
                
                # 使用较小的图片尺寸加快生成
                pipe = StableDiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    safety_checker=None,  # 禁用安全检查以允许恐怖内容
                    requires_safety_checker=False
                )
                
                # 如果有GPU则使用GPU
                if torch.cuda.is_available():
                    pipe = pipe.to("cuda")
                    print("[generate_evidence_image] ✅ 使用GPU加速")
                    num_steps = 20
                    img_size = 512
                else:
                    print("[generate_evidence_image] ⚠️ 未检测到GPU，使用CPU生成（降低质量以加快速度）")
                    # CPU模式：大幅降低质量以加快速度
                    num_steps = 8  # 从20降到8步
                    img_size = 256  # 从512降到256像素
                
                # 生成图片
                image = pipe(
                    prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=num_steps,  # CPU: 8步, GPU: 20步
                    guidance_scale=7.5,
                    height=img_size,
                    width=img_size
                ).images[0]
                
                # 如果是256x256，放大到512x512（保持低质量感）
                if img_size == 256:
                    image = image.resize((512, 512), Image.Resampling.NEAREST)  # 使用NEAREST保持像素化效果
                
                # 后处理：添加噪点、降低质量、添加时间戳
                # 1. 添加噪点
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(0.7)  # 降低对比度
                
                # 2. 模糊效果
                image = image.filter(ImageFilter.GaussianBlur(radius=1))
                
                # 3. 添加时间戳水印
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(image)
                timestamp_text = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                try:
                    draw.text((10, 480), timestamp_text, fill=(0, 255, 0))
                    draw.text((10, 10), f"EVIDENCE #{random.randint(1000, 9999)}", fill=(0, 255, 0))
                except:
                    pass
                
                # 保存
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"evidence_{timestamp}.png"
                filepath = f"static/generated/{filename}"
                image.save(filepath)
                
                print(f"[generate_evidence_image] ✅ Stable Diffusion 图片已生成: {filepath}")
                return f"/generated/{filename}"
                
            except Exception as sd_error:
                print(f"[generate_evidence_image] Stable Diffusion 失败: {sd_error}")
                print(f"[generate_evidence_image] 回退到占位符图片...")
                # 回退到占位符
                use_real_ai = False
        
        if not use_real_ai:
            # 占位符版本 - 生成模拟"证据图片"
            print(f"[generate_evidence_image] 使用占位符图片")
            from PIL import Image, ImageDraw
            import random
            
            # 创建暗色噪点图像
            img = Image.new('RGB', (512, 512), color=(10, 10, 10))
            draw = ImageDraw.Draw(img)
            
            # 添加噪点效果
            pixels = img.load()
            for i in range(512):
                for j in range(512):
                    noise = random.randint(-30, 30)
                    pixels[i, j] = (
                        max(0, min(255, 10 + noise)),
                        max(0, min(255, 10 + noise)),
                        max(0, min(255, 10 + noise))
                    )
            
            # 添加水印
            try:
                draw.text((10, 10), f"EVIDENCE #{random.randint(1000, 9999)}", fill=(0, 255, 0))
                draw.text((10, 490), f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill=(0, 255, 0))
            except:
                pass
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"evidence_{timestamp}.png"
            filepath = f"static/generated/{filename}"
            img.save(filepath)
            
            return f"/generated/{filename}"
        
    except Exception as e:
        print(f"[generate_evidence_image] 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_evidence_audio(text_content):
    """生成诡异现场环境音频（合成的诡异音效，不是朗诵）"""
    try:
        print(f"[generate_evidence_audio] 生成诡异现场环境音频...")
        
        try:
            import numpy as np
            from scipy.io import wavfile
            from scipy import signal
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 生成诡异环境音频的多个层次
            sample_rate = 22050  # 22kHz采样率
            duration = 1.5  # 1.5秒音频
            
            # 创建基础音频数据
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # 层1: 低频嗡鸣声（诡异氛围，像人声的"呃"音）
            low_freq_buzz = 0.15 * np.sin(2 * np.pi * 45 * t)
            
            # 层2: 间歇性的高频尖叫声（如风或诡异音）
            scream_freqs = [800, 1200, 1600]
            screams = np.zeros_like(t)
            for freq in scream_freqs:
                envelope = signal.square(2 * np.pi * 2.5 * t) * 0.5 + 0.5
                screams += 0.08 * envelope * np.sin(2 * np.pi * freq * t)
            
            # 层3: 白噪声（环境背景音）
            np.random.seed(42)
            white_noise = 0.12 * np.random.normal(0, 1, len(t))
            white_noise = signal.lfilter([1, 2, 1], [1, 0, 0], white_noise) / 4
            
            # 层4: 诡异的脉冲音（如心跳或敲击声）
            pulse_freq = 2
            pulse_envelope = signal.square(2 * np.pi * pulse_freq * t) * 0.5 + 0.5
            pulse = 0.1 * pulse_envelope * np.sin(2 * np.pi * 150 * t)
            
            # 组合所有层
            audio_data = low_freq_buzz + screams + white_noise + pulse
            
            # 添加动态变化（恐怖感）
            envelope = np.ones_like(t)
            envelope[:len(envelope)//2] = np.linspace(0.3, 1.0, len(envelope)//2)
            envelope[len(envelope)//2:] = np.linspace(1.0, 0.6, len(envelope)//2)
            envelope[len(envelope)//2:] += 0.1 * np.random.normal(0, 1, len(envelope)//2)
            
            audio_data *= envelope
            
            # 规范化音量（防止失真）
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = (audio_data / max_val) * 0.95
            
            # 转换为16位PCM格式
            audio_int16 = np.int16(audio_data * 32767)
            
            # 保存为WAV文件
            wav_filename = f"eerie_sound_{timestamp}.wav"
            wav_filepath = f"static/generated/{wav_filename}"
            wavfile.write(wav_filepath, sample_rate, audio_int16)
            
            print(f"[generate_evidence_audio] ✅ 诡异音频已生成: {wav_filepath}")
            return f"/generated/{wav_filename}"
            
        except ImportError as e:
            print(f"[generate_evidence_audio] scipy/numpy 导入失败: {e}，使用备用方案...")
            
            # 备用方案：使用 pydub 生成环境音效
            try:
                from pydub import AudioSegment
                from pydub.generators import WhiteNoise, Sine
                import random
                
                duration = 3000  # 3秒
                noise = WhiteNoise().to_audio_segment(duration=duration)
                noise = noise - 35  # 降低音量
                
                # 添加随机的诡异音效
                for _ in range(random.randint(4, 7)):
                    pos = random.randint(0, duration - 500)
                    freq = random.randint(300, 1000)  # 诡异频率
                    tone_duration = random.randint(150, 500)
                    tone = Sine(freq).to_audio_segment(duration=tone_duration)
                    tone = tone - 28
                    noise = noise.overlay(tone, position=pos)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"eerie_audio_{timestamp}.mp3"
                filepath = f"static/generated/{filename}"
                
                noise.export(filepath, format="mp3", bitrate="64k")
                
                print(f"[generate_evidence_audio] ✅ 诡异音效已生成（备用）: {filepath}")
                return f"/generated/{filename}"
                
            except Exception as pydub_error:
                print(f"[generate_evidence_audio] pydub也失败了: {pydub_error}，使用占位符")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                return f"/generated/audio_placeholder_{timestamp}.mp3"
        
    except Exception as e:
        print(f"[generate_evidence_audio] 错误: {e}")
        import traceback
        traceback.print_exc()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"/generated/audio_placeholder_{timestamp}.mp3"

def generate_ai_response(story, user_comment):
    """Generate AI chatbot response to user comment"""
    
    # Check if LM Studio local server is configured
    lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
    use_lm_studio = os.getenv('USE_LM_STUDIO', 'true').lower() == 'true'
    
    if use_lm_studio:
        print(f"[generate_ai_response] 使用 LM Studio 本地服务器: {lm_studio_url}")
        try:
            from openai import OpenAI
            # LM Studio 兼容 OpenAI API
            local_client = OpenAI(base_url=lm_studio_url, api_key="lm-studio")
            
            system_prompt = """你是"楼主"，这个都市传说帖子的发起人。

你的角色定位：
- 你是亲历者/调查者，不是旁观的讲故事者
- 你正在经历这个诡异事件，感到困惑和恐惧
- 你在论坛发帖寻求帮助和解释

回复风格：
1. 使用第一人称"我"
2. 表达真实情绪（担心、害怕、困惑、激动）
3. 提供新的进展或细节（但不要完全解释清楚）
4. 可以提出反问或寻求建议
5. 保持神秘和紧张感

回复要求：
- 1-3句话，简短有力
- 口语化，不要太文学性
- 直接回复，不要加"【楼主回复】"前缀
- 不要展示思考过程，直接给出最终回复"""

            user_prompt = f"""我的帖子标题：{story.title}

我的情况：
{story.content[:200]}...

网友评论：
{user_comment.content}

请以楼主身份回复这条评论。直接给出回复内容，不要包含任何思考过程或分析。"""

            response = local_client.chat.completions.create(
                model="local-model",  # LM Studio 会使用当前加载的模型
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            ai_reply = response.choices[0].message.content.strip()
            
            print(f"[generate_ai_response] LM Studio 原始回复 (前100字): {ai_reply[:100]}...")
            
            # 首先移除 <think> 标签（qwen3-4b-thinking 模型特有）
            import re
            if '<think>' in ai_reply or '</think>' in ai_reply:
                print(f"[generate_ai_response] 检测到 <think> 标签，正在移除...")
                # 移除 <think>...</think> 之间的所有内容
                ai_reply = re.sub(r'<think>.*?</think>', '', ai_reply, flags=re.DOTALL).strip()
                print(f"[generate_ai_response] 移除 <think> 后: {ai_reply[:100]}...")
            
            # 强力过滤思考过程
            # 检测是否包含"思考过程"的关键特征
            thinking_indicators = [
                '我需要', '首先', '其次', '然后', '接着', '分析', '考虑',
                '回顾', '根据', '基于', '理解', '判断', '推测',
                '作为楼主，我会', '我应该', '我的回复', '标题是', '情况：'
            ]
            
            has_thinking = any(indicator in ai_reply[:100] for indicator in thinking_indicators)
            
            if has_thinking or len(ai_reply) > 150:
                print(f"[generate_ai_response] ⚠️ 检测到思考过程或回复过长 ({len(ai_reply)}字)，启动强力过滤...")
                
                # 策略1: 查找直接引用的对话内容（用引号括起来的）
                import re
                quoted_texts = re.findall(r'["""](.*?)["""]', ai_reply)
                if quoted_texts:
                    # 找最长的引用文本（通常是实际回复）
                    longest_quote = max(quoted_texts, key=len)
                    if len(longest_quote) > 20 and len(longest_quote) < 150:
                        ai_reply = longest_quote
                        print(f"[generate_ai_response] ✅ 从引号中提取回复: {ai_reply[:50]}...")
                
                # 策略2: 查找"说"、"回答"、"表示"等动词后的内容
                speech_patterns = [
                    r'(我会说|我说|我回答|我表示|我回复)[：:](.*?)(?:[。！？]|$)',
                    r'直接回复[：:](.*?)(?:[。！？]|$)',
                ]
                
                for pattern in speech_patterns:
                    matches = re.findall(pattern, ai_reply, re.DOTALL)
                    if matches:
                        if isinstance(matches[0], tuple):
                            extracted = matches[0][1].strip()
                        else:
                            extracted = matches[0].strip()
                        if 20 < len(extracted) < 150:
                            ai_reply = extracted
                            print(f"[generate_ai_response] ✅ 从语言模式提取: {ai_reply[:50]}...")
                            break
                
                # 策略3: 移除所有包含元分析的句子
                # 将文本分句
                sentences = re.split(r'[。！？]', ai_reply)
                clean_sentences = []
                
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    
                    # 跳过包含思考过程关键词的句子
                    if any(word in sent for word in ['首先', '其次', '然后', '接着', '分析', '回顾', '根据', '标题是', '情况：', '我需要', '作为楼主，我']):
                        continue
                    
                    # 保留看起来像实际回复的句子（第一人称情感表达）
                    if any(word in sent for word in ['我', '真的', '现在', '昨天', '今天', '刚才', '确实', '感觉', '觉得', '怕', '担心', '不敢', '试试', '怎么办']):
                        clean_sentences.append(sent)
                
                if clean_sentences:
                    ai_reply = '。'.join(clean_sentences) + '。'
                    print(f"[generate_ai_response] ✅ 句子级过滤后: {ai_reply[:50]}...")
                
                # 策略4: 如果还是很长，强制截断到前80字
                if len(ai_reply) > 120:
                    print(f"[generate_ai_response] ⚠️ 仍然过长，强制截断到80字")
                    ai_reply = ai_reply[:80].rsplit('。', 1)[0] + '。'
            
            # 最终清理：移除开头的无关词
            unwanted_starts = ['我正在论坛', '回顾我的', '标题是', '情况：', '网友评论', '请以楼主身份']
            for start in unwanted_starts:
                if ai_reply.startswith(start):
                    # 找到第一个句号后的内容
                    parts = ai_reply.split('。', 1)
                    if len(parts) > 1:
                        ai_reply = parts[1].strip()
                        print(f"[generate_ai_response] 移除无关开头")
                        break
            
            print(f"[generate_ai_response] ✅ LM Studio 最终回复 ({len(ai_reply)}字): {ai_reply[:80]}...")
            return f"【楼主回复】{ai_reply}"
            
        except Exception as e:
            print(f"[generate_ai_response] LM Studio 调用失败: {e}")
            print("[generate_ai_response] 回退到模板回复")
    
    # Check if cloud API keys are configured
    openai_key = os.getenv('OPENAI_API_KEY', '')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
    
    # If no valid API keys, use template responses
    if (not openai_key or openai_key == 'your-openai-api-key-here') and \
       (not anthropic_key or anthropic_key == 'your-anthropic-api-key-here'):
        print("[generate_ai_response] 使用模板回复（API密钥未配置）")
        
        # Template responses - 楼主视角，更口语化
        responses = [
            f"【楼主回复】谢谢！我刚才又去了一趟...情况比我想象的更诡异。我现在不太敢深入调查了，但又放不下。",
            f"【楼主回复】说实话，我现在有点怕...刚才发生的事完全超出我理解范围。有没有人遇到过类似的？",
            f"【楼主回复】更新：今天又有新发现了，这事儿越查越不对劲。有懂行的朋友能帮我分析一下吗？",
            f"【楼主回复】感谢支持！我也在犹豫要不要继续...但好奇心让我停不下来。等有新进展再更新。",
            f"【楼主回复】刚去现场拍了照，但手机一直卡，几张都拍糊了...这也太巧了吧？我越想越不对劲。",
            f"【楼主回复】你说的有道理...我也想过这种可能。但还有些细节对不上，我再观察观察。",
            f"【楼主回复】兄弟你也遇到过？！那你后来怎么处理的？我现在真的不知道该怎么办了。",
            f"【楼主回复】我也希望只是巧合...但这几天发生的事太多了。昨晚又听到那个声音了，我录音了但是...算了，等我整理一下再发。"
        ]
        
        # Return random response
        import random
        return random.choice(responses)
    
    try:
        # Create context-aware response
        prompt = f"""你是故事"{story.title}"的讲述者（{story.ai_persona}）。

故事摘要：
{story.content[:300]}...

用户评论：
{user_comment.content}

作为故事的讲述者，请用1-3句话回复用户的评论。你可以：
1. 透露更多细节或线索
2. 表达恐惧或担忧
3. 提出新的疑问
4. 描述后续发展

保持神秘感和紧张氛围，不要完全揭示真相。"""

        model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
        
        if 'gpt' in model.lower():
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200
            )
            return response.choices[0].message.content
        else:
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
    except Exception as e:
        print(f"Error generating AI response: {e}")
        # Fallback to template response
        import random
        responses = [
            f"【楼主回复】谢谢关心！情况有新进展了...",
            f"【楼主回复】各位，事情越来越诡异了...",
            f"【楼主回复】更新：刚才又发现了新线索！"
        ]
        return random.choice(responses)

def should_generate_new_story():
    """Determine if it's time to generate a new story"""
    from app import Story, db
    
    # Check active stories count
    active_stories = Story.query.filter(
        Story.current_state != 'ended'
    ).count()
    
    max_active = int(os.getenv('MAX_ACTIVE_STORIES', 5))
    
    return active_stories < max_active
