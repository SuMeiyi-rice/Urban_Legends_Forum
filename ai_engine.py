import os
import random
from datetime import datetime, timedelta
from openai import OpenAI
from anthropic import Anthropic
import requests
from PIL import Image
from io import BytesIO
import re

# Initialize AI clients (only if API keys are provided)
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
anthropic_client = Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None

# 清理 Qwen 模型的思考标签
def clean_think_tags(text):
    """
    移除 Qwen 模型生成的 <think> 标签及其内容
    处理完整标签、不完整标签和多行标签
    """
    if not text:
        return text
    
    # 移除完整的 <think>...</think> 标签（包括换行）
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除不完整的开始标签（如果没有对应的结束标签）
    if '<think' in text.lower() and '</think>' not in text.lower():
        text = re.sub(r'<think[^>]*>.*$', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除任何剩余的单独标签
    text = re.sub(r'</?think[^>]*>', '', text, flags=re.IGNORECASE)
    
    # 清理多余的空行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

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

⚠️ 重要：直接以楼主身份写帖子内容，不要输出任何思考过程、分析或解释。不要使用<think>标签。

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
- 不要输出思考过程、不要使用<think>标签
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

        'cursed_object': f"""写一个论坛帖子：求助！我在{location}买了个东西，现在怀疑它不对劲。

前几天在{location}看到一个旧货摊，鬼使神差买了个东西。老板表情很奇怪，巴不得我赶紧买走。带回家后开始发生怪事...

内容要求：
1. 买物品的经过（老板反应、物品外观）
2. 回家后的怪事（逐渐升级）
3. 试图处理的尝试
4. 现在的恐慌状态

结尾："我现在不知道该怎么办，有懂行的朋友能给点建议吗？"
150-250字，第一人称。""",

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
        
        # 优先使用 LM Studio 本地模型
        use_lm_studio = os.getenv('USE_LM_STUDIO', 'true').lower() == 'true'
        lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
        
        content = None
        title = None
        
        # 尝试 LM Studio
        if use_lm_studio:
            try:
                print(f"[generate_ai_story] 使用 LM Studio 生成故事...")
                import subprocess
                import json
                
                # 使用 curl 调用 LM Studio（Python HTTP 库与 LM Studio 有兼容性问题）
                chat_url = f"{lm_studio_url.rstrip('/v1')}/v1/chat/completions"
                
                request_data = {
                    "messages": [
                        {"role": "system", "content": prompt_data['system']},
                        {"role": "user", "content": prompt_data['prompt']}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 800
                }
                
                curl_command = [
                    'curl', '-s', '-X', 'POST', chat_url,
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(request_data, ensure_ascii=False),
                    '--max-time', '120'
                ]
                
                result = subprocess.run(
                    curl_command,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    raise Exception(f"curl 命令失败: {result.stderr}")
                
                response_data = json.loads(result.stdout)
                content_raw = response_data['choices'][0]['message']['content']
                
                print(f"[generate_ai_story] 原始内容长度: {len(content_raw)} 字符")
                
                # 过滤 qwen 模型的 <think> 标签
                content = clean_think_tags(content_raw)
                
                print(f"[generate_ai_story] 清理后内容长度: {len(content) if content else 0} 字符")
                
                # 检查清理后是否有有效内容
                if not content or len(content) < 50:
                    print(f"[generate_ai_story] ⚠️ 模型输出主要是思考过程，尝试提取实际内容...")
                    # 尝试从原始内容中提取实际故事内容
                    # 查找最后一个 </think> 之后的内容
                    if '</think>' in content_raw:
                        content = content_raw.split('</think>')[-1].strip()
                        print(f"[generate_ai_story] 提取 </think> 后的内容: {len(content)} 字符")
                    
                    # 如果还是太短，使用原始内容但警告
                    if not content or len(content) < 50:
                        content = content_raw
                        print(f"[generate_ai_story] ⚠️ 使用原始内容，包含思考过程")
                
                # 生成标题（使用更直接的提示词避免思考过程）
                title_prompt = f"故事：{content[:150]}\n\n请为上面的故事起一个5-10字的标题："
                
                title_request = {
                    "messages": [
                        {"role": "system", "content": "你是标题生成器。用户给你故事，你只需要输出一个简短的标题，不要有任何其他内容。"},
                        {"role": "user", "content": title_prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 20
                }
                
                title_curl_command = [
                    'curl', '-s', '-X', 'POST', chat_url,
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(title_request, ensure_ascii=False),
                    '--max-time', '60'
                ]
                
                title_result = subprocess.run(
                    title_curl_command,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if title_result.returncode != 0:
                    raise Exception(f"标题生成失败: {title_result.stderr}")
                
                title_response_data = json.loads(title_result.stdout)
                title_raw = title_response_data['choices'][0]['message']['content'].strip()
                
                # 使用统一的清理函数
                title = clean_think_tags(title_raw)
                
                # 清理引号和多余字符
                title = title.replace('"', '').replace('"', '').replace('"', '').replace('《', '').replace('》', '')
                title = title.strip()
                
                # 如果标题太长，取第一句话
                if len(title) > 20:
                    sentences = re.split(r'[。！？\n]', title)
                    title = sentences[0][:15]
                
                # 如果仍然没有有效标题，从故事内容生成简单标题
                if not title or len(title) < 3:
                    # 从分类和地点生成简单标题
                    cat_names = {
                        'subway_ghost': '地铁怪谈',
                        'abandoned_building': '废楼惊魂',
                        'cursed_object': '诅咒之物',
                        'missing_person': '离奇失踪',
                        'supernatural_encounter': '灵异事件'
                    }
                    title = cat_names.get(category, '都市传说')
                
                print(f"[generate_ai_story] ✅ LM Studio 生成成功: {title}")
                
            except Exception as e:
                import traceback
                error_message = str(e)
                print(f"[generate_ai_story] ❌ LM Studio 失败: {type(e).__name__}: {e}")
                
                # 特殊处理 503 错误
                if "503" in error_message or "InternalServerError" in str(type(e).__name__):
                    print("[generate_ai_story] ⚠️ 检测到 503 错误 - 可能的原因:")
                    print("   1. LM Studio 模型未完全加载")
                    print("   2. 服务器负载过高")
                    print("   3. 并发请求过多")
                    print("[generate_ai_story] 💡 请在 LM Studio 'Local Server' 标签确认模型已加载")
                else:
                    print(f"[generate_ai_story] 详细错误:")
                    traceback.print_exc()
                
                content = None
                title = None
        
        # 如果 LM Studio 失败，尝试在线 API
        if not content:
            model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
            
            if openai_client and 'gpt' in model.lower():
                print(f"[generate_ai_story] 使用 OpenAI API...")
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
                
                # 生成标题
                title_prompt = f"为以下都市传说故事生成一个简短（5-10字）、吸引人、略带悬疑的标题。不要加引号。\n\n{content[:200]}"
                title_response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": title_prompt}],
                    temperature=0.7,
                    max_tokens=20
                )
                title = title_response.choices[0].message.content.strip().replace('"', '').replace('"', '').replace('"', '')
                
            elif anthropic_client:
                print(f"[generate_ai_story] 使用 Anthropic API...")
                response = anthropic_client.messages.create(
                    model=model,
                    max_tokens=800,
                    messages=[
                        {"role": "user", "content": f"{prompt_data['system']}\n\n{prompt_data['prompt']}"}
                    ]
                )
                content = response.content[0].text
                
                # 生成标题
                title_prompt = f"为以下都市传说故事生成一个简短（5-10字）、吸引人、略带悬疑的标题。不要加引号。\n\n{content[:200]}"
                title_response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=20,
                    messages=[{"role": "user", "content": title_prompt}]
                )
                title = title_response.content[0].text.strip()
            else:
                print(f"[generate_ai_story] ❌ 没有可用的 AI 服务")
                return None
        
        if not content or not title:
            return None
        
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
                
                # 智能分析故事内容 + 评论内容，生成与故事直接相关的真实场景
                story_text = (story_title + " " + story_content[:300]).lower()
                # 加入评论和贴文的关键词 - 权重更高
                comment_text = ""
                if comment_context:
                    comment_text = comment_context.lower()
                    story_text += " " + comment_text
                
                print(f"[generate_evidence_image] 分析故事: {story_text[:150]}...")
                if comment_text:
                    print(f"[generate_evidence_image] 评论线索: {comment_text[:100]}...")
                
                # 从故事中提取关键场景元素（包括评论中的关键词）
                scene_keywords = {
                    # 地铁相关 - 优先级最高，因为这个场景最具体
                    'subway': {
                        'scenes': ['subway train interior with empty seats', 'subway station platform', 'metro train car at night'],
                        'details': ['汽车灯影、月台空荡、车厢诡异', '13号车厢、车号显示屏、月台电子钟']
                    },
                    '地铁': {
                        'scenes': ['subway train interior with empty seats', 'subway station platform at night', 'metro corridor'],
                        'details': ['地铁内部、乘客、诡异']
                    },
                    '车厢': {
                        'scenes': ['train car interior, seats and handrails', 'empty subway carriage at night'],
                        'details': ['车厢内部、座位、寂静']
                    },
                    
                    # 镜子相关
                    'mirror': {
                        'scenes': ['bathroom with mirror and sink', 'bedroom mirror on dresser', 'mirror reflection at night'],
                        'details': ['镜子倒影、诡异表情']
                    },
                    '镜子': {
                        'scenes': ['bathroom mirror above sink, faucet visible', 'bedroom mirror with dresser'],
                        'details': ['镜中倒影不是自己、诡异笑容']
                    },
                    '倒影': {
                        'scenes': ['mirror reflection, distorted face', 'window reflection at night'],
                        'details': ['倒影、非本人、诡异']
                    },
                    
                    # 门相关  
                    'door': {
                        'scenes': ['apartment door with peephole and handle', 'residential hallway with doors'],
                        'details': ['敲门、门号、诡异']
                    },
                    '门': {
                        'scenes': ['apartment door, door handle, peephole', 'residential building hallway'],
                        'details': ['门、猫眼、敲门声']
                    },
                    '敲门': {
                        'scenes': ['apartment entrance door closeup', 'door with door number plate at night'],
                        'details': ['有人敲门、门号、时间']
                    },
                    
                    # 楼道相关
                    'hallway': {
                        'scenes': ['apartment building corridor', 'residential stairwell'],
                        'details': ['楼道、走廊、昏暗']
                    },
                    '走廊': {
                        'scenes': ['apartment building hallway with doors', 'residential corridor with lighting'],
                        'details': ['走廊、灯光、脚步声']
                    },
                    '楼道': {
                        'scenes': ['apartment stairwell, concrete steps', 'building corridor with elevator'],
                        'details': ['楼梯、电梯、诡异']
                    },
                    '楼梯': {
                        'scenes': ['residential building staircase, handrails', 'stairwell in apartment building at night'],
                        'details': ['阶梯、灯光、脚步']
                    },
                    
                    # 窗户相关
                    'window': {
                        'scenes': ['apartment window view at night', 'window with curtains'],
                        'details': ['窗外、月亮、人影']
                    },
                    '窗': {
                        'scenes': ['residential window from inside', 'apartment window at night'],
                        'details': ['窗外、诡异、人影']
                    },
                    '窗外': {
                        'scenes': ['window view from apartment at night', 'dark window with city lights'],
                        'details': ['窗外景象、诡异、月光']
                    },
                    
                    # 房间相关
                    '卧室': {
                        'scenes': ['bedroom interior, bed and furniture', 'residential bedroom at night'],
                        'details': ['卧室、床、昏暗']
                    },
                    '房间': {
                        'scenes': ['residential room interior at night', 'apartment bedroom'],
                        'details': ['房间、诡异、阴影']
                    },
                    '床': {
                        'scenes': ['bedroom bed under dim light', 'bed with sheets and pillows'],
                        'details': ['床、睡眠、诡异']
                    },
                    
                    # 其他诡异场景
                    '手机': {
                        'scenes': ['smartphone screen in dark', 'phone screen in hand'],
                        'details': ['屏幕、拍照、证据']
                    },
                    '照片': {
                        'scenes': ['photograph on table', 'old photo or polaroid'],
                        'details': ['照片、证据、诡异']
                    },
                    '录音': {
                        'scenes': ['phone recording screen', 'audio device'],
                        'details': ['录音、语音、证据']
                    },
                    '笔记': {
                        'scenes': ['handwritten note on paper', 'notebook page with writing'],
                        'details': ['笔记、文字、线索']
                    },
                    '时间': {
                        'scenes': ['clock showing strange time', 'digital display at night'],
                        'details': ['时间、诡异数字、不寻常']
                    },
                    
                    # 诡异氛围
                    '影子': {
                        'scenes': ['shadow on wall in dark', 'mysterious shadow in room'],
                        'details': ['影子、人影、诡异']
                    },
                    '脚步': {
                        'scenes': ['empty hallway floor', 'stairwell steps at night'],
                        'details': ['地面、脚步声、诡异']
                    },
                    '声音': {
                        'scenes': ['empty room interior at night', 'residential space interior'],
                        'details': ['房间内、声音、诡异']
                    },
                    '冷': {
                        'scenes': ['cold apartment interior', 'frost on window'],
                        'details': ['寒冷、冻气、诡异']
                    },
                    '诡异': {
                        'scenes': ['dimly lit urban apartment', 'creepy residential space'],
                        'details': ['诡异、阴影、不寻常']
                    },
                }
                
                # 多层级匹配场景描述 - 优先匹配评论中的关键词
                scene_desc = None
                scene_details = ""
                matched_keyword = None
                
                # 第一优先级：匹配评论中的关键词（用户补充的信息）
                if comment_text:
                    for keyword, scene_data in scene_keywords.items():
                        if keyword in comment_text:
                            scene_desc = random.choice(scene_data.get('scenes', ['dimly lit apartment']))
                            scene_details = random.choice(scene_data.get('details', ['']))
                            matched_keyword = keyword
                            print(f"[generate_evidence_image] 从评论匹配: {keyword} -> {scene_desc}")
                            break
                
                # 第二优先级：匹配故事标题和内容
                if not scene_desc:
                    for keyword, scene_data in scene_keywords.items():
                        if keyword in story_text:
                            scene_desc = random.choice(scene_data.get('scenes', ['dimly lit apartment']))
                            scene_details = random.choice(scene_data.get('details', ['']))
                            matched_keyword = keyword
                            print(f"[generate_evidence_image] 从故事匹配: {keyword} -> {scene_desc}")
                            break
                
                # 如果没有匹配，使用通用场景
                if not scene_desc:
                    scene_desc = 'dimly lit urban apartment interior, everyday furniture'
                    scene_details = '诡异、不寻常的氛围'
                    print(f"[generate_evidence_image] 使用默认场景")
                
                # 纪实照片风格的 prompt - 真实场景中融入故事特定的诡异元素
                # 提取显性细节（引号内短语、数字编号、时间、地点关键词），并把它们直接加入到 prompt
                explicit_details = []
                # 从原始故事/评论文本中提取引号内短语
                try:
                    quoted = re.findall(r'“([^”]+)”|"([^"]+)"|‘([^’]+)’|\'([^\']+)\'', story_text)
                    for tup in quoted:
                        for part in tup:
                            if part:
                                explicit_details.append(part)
                except Exception:
                    pass

                # 提取常见的数字+单位（如 13号、3层、3点等）和时间格式
                try:
                    nums = re.findall(r"\d+[号节层楼点分钟分秒]?", story_text)
                    explicit_details.extend(nums)
                except Exception:
                    pass

                # 添加 title 以增强提示的语义相关性
                if isinstance(story_title, str) and story_title.strip():
                    explicit_details.append(story_title.strip())

                # 去重并限制数量
                seen = set()
                filtered_details = []
                for d in explicit_details:
                    dd = d.strip()
                    if not dd:
                        continue
                    if dd in seen:
                        continue
                    seen.add(dd)
                    filtered_details.append(dd)
                    if len(filtered_details) >= 6:
                        break
                explicit_details_text = ", ".join(filtered_details)

                # 将显性细节映射为更明确的视觉短语（中文->英文视觉描述）以提高图像的强关联性
                visual_map = {
                    # 地点 / 标题相关
                    '金鱼街斗鱼': 'fish tank in small pet shop, visible aquariums and signage',
                    '地铁': 'subway interior or platform, visible carriage number display',
                    '13号': 'carriage number 13 on digital display',
                    '13号车厢': 'train carriage labeled 13 on display',
                    '地铁2号线': 'metro line 2 signage, platform signs',
                    # 声音相关（转换为可视线索，如水波、玻璃振动等）
                    '砰砰声': 'water ripple marks on aquarium glass, visible impact ripples',
                    '敲鱼缸': 'closeup of aquarium glass with impact marks, chipped paint',
                    '敲门': 'door with knock marks and peephole, nighttime hallway',
                    '脚步声': 'scuffed floor and footprints in dim hallway',
                    '声音': 'sound source implied by movement in curtains or ripples on water',
                    '声响': 'vibrations or visible disturbance on surfaces',
                    '凌晨3点': 'digital clock showing 03:00, dark night lighting',
                    '3点': 'digital clock showing 03:00',
                    '镜子': 'bathroom mirror with faint reflection, smudge or handprint',
                    '倒影': 'reflection in glass showing a different face',
                    '鱼缸': 'fish tank with visible water, algae, and glass reflections',
                    '照片': 'polaroid-style photograph laying on a table',
                    '录音': 'phone recording screen or audio recorder device visible',
                    '窗外': 'view through window with streetlights or moonlight',
                    '门': 'apartment door with visible handle and peephole',
                }

                visual_phrases = []
                for d in filtered_details:
                    key = d
                    # 简单归一化数词，例如含数字的短语
                    if any(ch.isdigit() for ch in key) and key not in visual_map:
                        # map '13号' -> 'number 13 signage'
                        visual_phrases.append(f"signage or digits: {key}")
                        continue
                    mapped = visual_map.get(key)
                    if mapped:
                        visual_phrases.append(mapped)
                    else:
                        # 试着把中文短语原样放入，但转换成提示友好的形式
                        visual_phrases.append(f"visual cue: {key}")

                visual_phrases_text = ", ".join(visual_phrases)

                # 关键：将显性视觉短语放在 prompt 中的显著位置，便于生成与正文紧密相关的图像
                extra_section = ""
                if visual_phrases_text:
                    extra_section = f", include visual elements: {visual_phrases_text}"
                    if explicit_details_text:
                        extra_section += f" (keywords: {explicit_details_text})"

                prompt = (
                    f"realistic photograph, {scene_desc}, "
                    f"taken with smartphone camera at night, "
                    f"low light conditions, grainy image quality, "
                    f"slightly unfocused, amateur photography, "
                    f"real world scene, photographic evidence style, "
                    f"visible details and textures, concrete objects, "
                    f"documentary photo aesthetic, "
                    f"{scene_details}, "
                    f"subtle creepy atmosphere, barely visible face in shadow, "
                    f"inexplicable shadow, eerie presence, "
                    f"something unsettling about this place, hidden disturbing details"
                    f"{extra_section}"
                )
                
                # 负面提示词 - 避免太扭曲/太抽象，但保留微妙恐怖
                negative_prompt = (
                    "abstract, artistic, illustration, painting, drawing, sketch, "
                    "cartoon, anime, 3d render, cgi, digital art, "
                    "extremely distorted, heavily warped, grotesque, monstrous, "
                    "obvious demon, obvious ghost, obvious supernatural creature, "
                    "repetitive patterns, geometric shapes, abstract forms, "
                    "professional studio photography, dramatic lighting, cinematic, "
                    "motion blur, artistic blur, tilt-shift, "
                    "text, watermarks, signatures, "
                    "completely dark, pitch black, completely invisible, "
                    "overly bright, blown out highlights"
                )
                
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
                    num_steps = 25
                    img_size = 512  # GPU可以直接生成512x512
                else:
                    print("[generate_evidence_image] ⚠️ 未检测到GPU，使用CPU生成")
                    # CPU模式：生成512x512正方形图片，避免拉伸变形
                    num_steps = 20  # 更多步数确保质量
                    img_size = 512  # 直接生成512x512，无需放大
                
                # 生成图片 - 使用多模板以提高沉浸感：primary / closeup / wide/source
                templates = []
                # primary = base prompt
                templates.append(('primary', prompt))

                # close-up 模板：强调细节、特写
                closeup_prompt = prompt + ", close-up detail shot, shallow depth of field, focus on details"
                if 'visual_phrases_text' in locals() and visual_phrases_text:
                    closeup_prompt += f", emphasize: {visual_phrases_text}"
                templates.append(('closeup', closeup_prompt))

                # wide/source 模板：展示环境或疑似声音源近景
                source_prompt = prompt + ", wide shot showing surrounding environment, contextual background, show suspected sound source"
                if 'visual_phrases_text' in locals() and visual_phrases_text:
                    source_prompt += f", highlight object: {visual_phrases_text}"
                templates.append(('source', source_prompt))

                # 生成并保存多张图片，返回 primary 的路径以兼容旧接口
                timestamp_base = datetime.now().strftime('%Y%m%d_%H%M%S')
                saved_files = []
                for idx, (suffix, p) in enumerate(templates):
                    print(f"[generate_evidence_image] 生成模板[{suffix}] Prompt: {p[:120]}...")
                    image = pipe(
                        p,
                        negative_prompt=negative_prompt,
                        num_inference_steps=num_steps,
                        guidance_scale=8.5,
                        height=img_size,
                        width=img_size
                    ).images[0]

                    # 确保输出是512x512
                    if image.size != (512, 512):
                        image = image.resize((512, 512), Image.Resampling.LANCZOS)

                    # 后处理（与之前相同）
                    from PIL import ImageEnhance, ImageDraw, ImageFont
                    enhancer = ImageEnhance.Color(image)
                    image = enhancer.enhance(0.85)
                    enhancer = ImageEnhance.Brightness(image)
                    image = enhancer.enhance(0.85)
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(1.15)
                    enhancer = ImageEnhance.Sharpness(image)
                    image = enhancer.enhance(1.1)

                    import numpy as np
                    img_array = np.array(image)
                    noise = np.random.normal(0, 3, img_array.shape)
                    img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
                    image = Image.fromarray(img_array)

                    draw = ImageDraw.Draw(image)
                    days_ago = random.randint(1, 30)
                    fake_date = datetime.now() - timedelta(days=days_ago)
                    timestamp_text = fake_date.strftime('%Y/%m/%d %H:%M:%S')
                    try:
                        draw.text((340, 480), timestamp_text, fill=(220, 220, 220))
                        draw.text((10, 10), f"REC ●", fill=(200, 0, 0))
                    except:
                        pass

                    filename = f"evidence_{timestamp_base}_{suffix}.png"
                    filepath = f"static/generated/{filename}"
                    image.save(filepath)
                    saved_files.append((suffix, f"/generated/{filename}"))
                    print(f"[generate_evidence_image] ✅ Stable Diffusion 图片已生成: {filepath}")

                # 返回 primary 的相对路径以兼容现有调用
                primary_path = next((p for s, p in saved_files if s == 'primary'), saved_files[0][1])
                return primary_path
                
            except Exception as sd_error:
                print(f"[generate_evidence_image] Stable Diffusion 失败: {sd_error}")
                print(f"[generate_evidence_image] 回退到占位符图片...")
                # 回退到占位符
                use_real_ai = False
        
        if not use_real_ai:
            # 占位符版本 - 生成伪纪实风格的模拟照片
            print(f"[generate_evidence_image] 使用占位符图片（伪纪实风格）")
            from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
            import random
            import numpy as np
            
            # 创建带有渐变的暗色背景（模拟低光环境）
            img = Image.new('RGB', (512, 512), color=(30, 32, 35))
            draw = ImageDraw.Draw(img)
            
            # 根据故事类型添加具象的简单几何图形（模拟具体场景）
            if '地铁' in story_title or '车厢' in story_title:
                # 模拟地铁车厢内部：座椅、扶手
                draw.rectangle([50, 300, 150, 450], fill=(40, 42, 45))  # 座椅
                draw.rectangle([350, 300, 450, 450], fill=(38, 40, 43))  # 座椅
                draw.line([(256, 0), (256, 200)], fill=(60, 60, 60), width=5)  # 扶手杆
            elif '镜子' in story_title:
                # 模拟镜子和洗手台
                draw.rectangle([100, 100, 400, 400], fill=(45, 48, 52))  # 镜子框
                draw.rectangle([150, 350, 350, 450], fill=(55, 55, 58))  # 洗手台
            elif '门' in story_title or '楼道' in story_title:
                # 模拟门和走廊
                draw.rectangle([180, 50, 330, 480], fill=(50, 45, 40))  # 门
                draw.ellipse([235, 240, 275, 280], fill=(70, 70, 70))  # 门把手
                draw.rectangle([10, 100, 100, 150], fill=(60, 55, 50))  # 墙上的东西
            else:
                # 默认：房间内部物品
                draw.rectangle([80, 250, 200, 450], fill=(45, 43, 40))  # 家具
                draw.rectangle([320, 200, 450, 400], fill=(42, 40, 38))  # 家具
                draw.line([(0, 380), (512, 380)], fill=(35, 33, 30), width=3)  # 地板线
            
            # 添加细微噪点（模拟胶片颗粒）
            pixels = img.load()
            for i in range(0, 512, 2):  # 跳格处理以加快速度
                for j in range(0, 512, 2):
                    noise = random.randint(-8, 8)
                    r, g, b = pixels[i, j]
                    pixels[i, j] = (
                        max(0, min(255, r + noise)),
                        max(0, min(255, g + noise)),
                        max(0, min(255, b + noise + 2))  # 轻微的蓝色偏移
                    )
            
            # 应用模糊（模拟对焦不准/手抖）
            img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
            
            # 降低饱和度
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.5)
            
            # 添加监控录像风格的时间戳
            draw = ImageDraw.Draw(img)
            days_ago = random.randint(1, 30)
            fake_date = datetime.now() - timedelta(days=days_ago)
            timestamp_text = fake_date.strftime('%Y/%m/%d %H:%M:%S')
            
            try:
                # 右下角时间戳（白色半透明）
                draw.text((340, 480), timestamp_text, fill=(200, 200, 200))
                # 左上角REC标记
                draw.text((10, 10), f"REC ●", fill=(180, 0, 0))
                # 添加一些模拟的扫描线
                for y in range(0, 512, 8):
                    draw.line([(0, y), (512, y)], fill=(255, 255, 255), width=1)
                    img_array = np.array(img)
                    img_array[y, :] = np.clip(img_array[y, :] * 0.95, 0, 255)
                    img = Image.fromarray(img_array.astype(np.uint8))
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

def generate_audio_description_with_lm_studio(title, content, comment_context=""):
    """使用 LM Studio 生成丰富的音频场景描述，增加多样性"""
    try:
        import subprocess
        import json
        
        lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
        
        # 构造 prompt，让 AI 根据故事生成音频场景描述
        system_prompt = """你是一个音频场景专家。根据给定的故事内容，生成一个简短的、生动的音频环境描述。
        
描述应该包括:
1. 主要的声音元素 (1-2 个)
2. 声音的特征 (急促/缓慢/重复/变化等)
3. 总体的情绪氛围

返回格式: 单行文本，不超过 100 字

示例:
"地下隧道中的空洞回声，伴随着规律的敲击声，节奏诡异，令人不安"
"微弱的人类呼吸声混合着低频嗡鸣，像有无形的东西在身边"
"""

        user_prompt = f"""故事标题: {title}

故事内容: {content[:200]}

用户评论: {comment_context[:150]}

请生成这个故事对应的音频场景描述。"""

        # 使用 curl 调用 LM Studio
        curl_command = [
            'curl', '-s', f'{lm_studio_url}/chat/completions',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                'model': 'qwen2.5-7b-instruct-1m',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 150,
                'top_p': 0.9
            })
        ]
        
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                audio_description = response_data['choices'][0]['message']['content'].strip()
                print(f"[generate_audio_description] ✅ AI 生成音频描述: {audio_description[:60]}...")
                return audio_description
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"[generate_audio_description] JSON 解析失败: {e}")
                return None
        else:
            print(f"[generate_audio_description] curl 调用失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[generate_audio_description] 错误: {e}")
        return None

def extract_audio_keywords(title, content, comment_context=""):
    """提取音频相关关键词 - 返回音频类型和参数"""
    
    # 音频关键词映射表 (关键词 -> (音频类型, 频率参数, 强度))
    audio_keywords = {
        # 敲击/脚步相关 - 优先级高，要先检查
        '敲门|敲击|脚步|踩踏|走动|跺脚': ('knocking', 'rhythmic_pulse', 0.5),
        
        # 机械/电子 - 优先级高
        '灯闪烁|电流|闪烁|嗡鸣|警报|断断续续|电器': ('electronic', 'flicker_buzz', 0.5),
        
        # 地铁/隧道/空间
        '地铁|隧道|地下|回声': ('subway', 'hollow_echo', 0.5),
        
        # 声音/人声相关 - 低吟、呻吟、尖叫等
        '呻吟|尖叫|哭声|喘气|呼吸|低吟|呢喃|嗓音|人声': ('voice', 'strange_voice', 0.6),
        
        # 自然/环境声
        '风|树|雨|水|流动': ('nature', 'wind_whisper', 0.4),
        '沙沙|窸窣|簌簌': ('ambient', 'static_whisper', 0.3),
        
        # 时间关键词（影响整体气氛但不直接决定音频类型）
        '夜晚|凌晨|午夜|深夜|晚上': ('nocturnal', 'ambient_eerie', 0.6),
        
        # 诡异/恐怖总体印象（最低优先级）
        '诡异|怪异|恐怖|害怕|不安|诡|鬼|灵异|灵': ('eerie', 'ambient_eerie', 0.7),
    }
    
    # 合并所有文本用于匹配
    combined_text = f"{title} {content} {comment_context}".lower()
    
    # 默认音频类型
    audio_type = 'ambient_eerie'
    intensity = 0.5
    
    # 按优先级查找匹配的关键词（先定义的优先级最高）
    for keywords, (category, audio_type_matched, intensity_matched) in audio_keywords.items():
        # 检查是否有任何关键词匹配
        has_match = False
        matched_keyword = ""
        
        for kw in keywords.split('|'):
            kw = kw.strip()
            if kw and kw in combined_text:
                has_match = True
                matched_keyword = kw
                break
        
        if has_match:
            audio_type = audio_type_matched
            intensity = intensity_matched
            print(f"[extract_audio_keywords] 匹配到关键词: '{matched_keyword}' -> {audio_type}")
            break  # 优先级最高的匹配就跳出
    
    return audio_type, intensity

def generate_evidence_audio(text_content, story_context=""):
    """生成诡异现场环境音频 - 根据内容生成对应的微妙怪异声音"""
    try:
        print(f"[generate_evidence_audio] 生成诡异现场环境音频...")
        
        # 首先尝试使用 LM Studio 生成音频描述
        full_context = f"{text_content}\n{story_context}"
        ai_audio_description = generate_audio_description_with_lm_studio(
            text_content, 
            story_context.split('\n')[0] if story_context else "",  # 取故事内容前几行
            story_context
        )
        
        # 提取音频关键词 - 同时考虑 AI 生成的描述和原始内容
        if ai_audio_description:
            # 如果 AI 生成了描述，优先使用 AI 描述中的关键词
            audio_type, intensity = extract_audio_keywords(
                text_content, 
                ai_audio_description,  # 使用 AI 生成的描述
                story_context
            )
            print(f"[generate_evidence_audio] 使用 AI 生成的描述进行关键词提取")
        else:
            # 否则使用原始内容进行关键词提取
            audio_type, intensity = extract_audio_keywords(text_content, story_context)
        
        print(f"[generate_evidence_audio] 音频类型: {audio_type}, 强度: {intensity}")
        
        try:
            import numpy as np
            from scipy.io import wavfile
            from scipy import signal
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 生成诡异环境音频的多个层次
            sample_rate = 22050  # 22kHz采样率
            duration = 2.0  # 2秒音频
            
            # 创建基础音频数据
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # 根据audio_type生成不同类型的声音
            if audio_type == 'voice' or audio_type == 'strange_voice':
                # 人声嗡鸣 - 微妙的人类声音幻听
                # 每次生成不同的基础频率和特征，增加多样性
                base_freq = np.random.choice([70, 80, 90, 100, 110, 120])  # 更多频率选择
                layer1 = 0.12 * intensity * np.sin(2 * np.pi * base_freq * t)
                
                # 变调的低吟 - 随机的变调范围和速度
                modulation_depth = np.random.randint(15, 35)  # 变调深度变化
                modulation_speed = np.random.uniform(0.3, 0.8)  # 变调速度变化
                freq_modulation = base_freq + modulation_depth * np.sin(2 * np.pi * modulation_speed * t)
                layer2 = 0.08 * intensity * np.sin(2 * np.pi * freq_modulation * t)
                
                # 微弱的呼吸声 - 不同的呼吸节奏
                breath_freq = np.random.uniform(0.8, 1.5)  # 呼吸频率变化
                breath_env = signal.square(2 * np.pi * breath_freq * t) * 0.5 + 0.5
                breath_tone_freq = np.random.randint(120, 200)  # 呼吸音的基频变化
                layer3 = 0.06 * intensity * breath_env * np.sin(2 * np.pi * breath_tone_freq * t)
                
                audio_data = layer1 + layer2 + layer3
                
            elif audio_type == 'knocking' or audio_type == 'rhythmic_pulse':
                # 敲击/脚步声 - 不同的节奏和音色
                pulse_freq = np.random.uniform(1.0, 2.5)  # 更宽的脉冲频率范围
                pulse_envelope = signal.square(2 * np.pi * pulse_freq * t) * 0.5 + 0.5
                
                # 低频敲击声 - 不同的敲击音色
                low_freq = np.random.choice([60, 70, 80, 90, 100])  # 多种敲击频率
                layer1 = 0.15 * intensity * pulse_envelope * np.sin(2 * np.pi * low_freq * t)
                
                # 高频响应 - 不同的响应频率
                high_freq = np.random.choice([150, 180, 200, 250, 300])  # 多种响应频率
                layer2 = 0.08 * intensity * pulse_envelope * np.sin(2 * np.pi * high_freq * t)
                
                # 环境反响 - 增加变化
                white_noise = 0.06 * intensity * np.random.normal(0, 1, len(t))
                white_noise = signal.lfilter([1, 1], [1], white_noise) / 2
                
                audio_data = layer1 + layer2 + white_noise
                
            elif audio_type == 'wind_whisper' or audio_type == 'static_whisper':
                # 风声/沙沙声 - 微妙而诡异，多种风格
                wind_noise = 0.08 * intensity * np.random.normal(0, 1, len(t))
                wind_noise = signal.lfilter([1, 2, 1], [1, 0, 0], wind_noise) / 4
                
                # 添加变调的高频 - 随机高频范围
                base_whisper_freq = np.random.choice([600, 700, 800, 900, 1000, 1100])
                modulation_range = np.random.randint(150, 300)
                freq_modulation = base_whisper_freq + modulation_range * np.sin(2 * np.pi * np.random.uniform(0.2, 0.5) * t)
                whisper = 0.04 * intensity * np.sin(2 * np.pi * freq_modulation * t)
                
                audio_data = wind_noise + whisper
                
            elif audio_type == 'hollow_echo':
                # 地铁/隧道 - 空洞的回声，多种空间感
                # 随机的基础频率营造不同的空间大小感觉
                base_freq = np.random.choice([180, 200, 220, 240])
                modulation = 20 + np.random.randint(20, 40)
                base_freq_mod = base_freq + modulation * np.sin(2 * np.pi * np.random.uniform(0.3, 0.5) * t)
                layer1 = 0.12 * intensity * np.sin(2 * np.pi * base_freq_mod * t)
                
                # 延迟的回声 - 不同的延迟时间营造不同的空间感
                delay_time = np.random.uniform(0.08, 0.15)  # 延迟时间变化
                delay_samples = int(delay_time * sample_rate)
                layer2 = np.zeros_like(t)
                if delay_samples < len(layer1):
                    layer2[delay_samples:] = 0.06 * intensity * layer1[:-delay_samples]
                
                # 深沉的嗡鸣 - 不同的低频
                low_freq = np.random.choice([50, 55, 60, 65])
                layer3 = 0.08 * intensity * np.sin(2 * np.pi * low_freq * t)
                
                audio_data = layer1 + layer2 + layer3
                
            elif audio_type == 'electrical_hum' or audio_type == 'flicker_buzz':
                # 电流/闪烁 - 断断续续的嗡鸣，多种风格
                buzz_freq = np.random.choice([110, 120, 130, 140])  # 不同的电流频率
                buzz = 0.12 * intensity * np.sin(2 * np.pi * buzz_freq * t)
                
                # 闪烁效果 - 不同的闪烁速度
                flicker_speed = np.random.uniform(2.5, 5.0)
                flicker_env = signal.square(2 * np.pi * flicker_speed * t) * 0.5 + 0.5
                layer2 = 0.08 * intensity * flicker_env * buzz
                
                # 高频失真 - 不同的失真频率
                distortion_freq = np.random.choice([1500, 1800, 2000, 2500, 3000])
                layer3 = 0.04 * intensity * np.sin(2 * np.pi * distortion_freq * t) * flicker_env
                
                audio_data = layer2 + layer3
                
            else:  # 默认: ambient_eerie
                # 环境诡异感 - 多层次的微妙不安，更多随机变化
                # 层1: 低频嗡鸣声（诡异氛围），多种频率选择
                low_freq = np.random.choice([35, 40, 45, 50, 55])
                low_freq_buzz = 0.12 * intensity * np.sin(2 * np.pi * low_freq * t)
                
                # 层2: 间歇性的高频尖叫声，多种频率组合
                scream_freqs = [
                    [700, 1000, 1400],
                    [600, 950, 1350],
                    [750, 1100, 1500],
                    [650, 1050, 1450]
                ]
                selected_freqs = np.random.choice([i for i in range(len(scream_freqs))])
                scream_freqs = scream_freqs[selected_freqs]
                
                screams = np.zeros_like(t)
                scream_speed = np.random.uniform(1.5, 3.0)  # 尖叫速度变化
                for freq in scream_freqs:
                    envelope = signal.square(2 * np.pi * scream_speed * t) * 0.5 + 0.5
                    screams += 0.05 * intensity * envelope * np.sin(2 * np.pi * freq * t)
                
                # 层3: 白噪声（环境背景音） - 基于故事内容的不同种子
                np.random.seed(hash(full_context) % 2**32)
                white_noise = 0.08 * intensity * np.random.normal(0, 1, len(t))
                white_noise = signal.lfilter([1, 2, 1], [1, 0, 0], white_noise) / 4
                
                # 层4: 诡异的脉冲音 - 不同脉冲频率
                pulse_freq = np.random.uniform(1.2, 2.5)
                pulse_envelope = signal.square(2 * np.pi * pulse_freq * t) * 0.5 + 0.5
                pulse_base_freq = np.random.choice([100, 120, 150, 180])
                pulse = 0.08 * intensity * pulse_envelope * np.sin(2 * np.pi * pulse_base_freq * t)
                
                audio_data = low_freq_buzz + screams + white_noise + pulse
            
            # 添加动态变化（恐怖感渐进）
            envelope = np.ones_like(t)
            mid_point = len(envelope) // 2
            envelope[:mid_point] = np.linspace(0.2, 0.95, mid_point)
            second_half_len = len(envelope) - mid_point
            envelope[mid_point:] = np.linspace(0.95, 0.5, second_half_len)
            envelope[mid_point:] += 0.08 * np.random.normal(0, 1, second_half_len)
            
            audio_data *= envelope
            
            # 规范化音量（防止失真）- 保持微妙
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = (audio_data / max_val) * 0.85  # 降低整体音量使其更微妙
            
            # 转换为16位PCM格式
            audio_int16 = np.int16(audio_data * 32767)
            
            # 保存为WAV文件
            wav_filename = f"eerie_sound_{audio_type}_{timestamp}.wav"
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
                noise = noise - (38 - intensity * 10)  # 根据强度调整音量
                
                # 根据audio_type生成对应的音效
                if audio_type == 'voice' or audio_type == 'strange_voice':
                    # 人声幻听
                    base_freq = random.choice([80, 95, 110])
                    for _ in range(3):
                        pos = random.randint(0, duration - 800)
                        tone = Sine(base_freq).to_audio_segment(duration=random.randint(400, 800))
                        noise = noise.overlay(tone - 20, position=pos)
                        
                elif audio_type == 'knocking' or audio_type == 'rhythmic_pulse':
                    # 敲击声
                    for i in range(5):
                        pos = int(i * duration / 5)
                        tone = Sine(100).to_audio_segment(duration=150)
                        noise = noise.overlay(tone - 15, position=pos)
                        
                elif audio_type == 'wind_whisper' or audio_type == 'static_whisper':
                    # 风声/沙沙 - 已由白噪声表现，只需调整音量
                    noise = noise - 5
                    
                elif audio_type == 'hollow_echo':
                    # 地铁回声
                    for _ in range(3):
                        pos = random.randint(0, duration - 600)
                        tone = Sine(200).to_audio_segment(duration=600)
                        noise = noise.overlay(tone - 22, position=pos)
                        
                elif audio_type == 'electrical_hum' or audio_type == 'flicker_buzz':
                    # 电流嗡鸣
                    hum = Sine(120).to_audio_segment(duration=duration)
                    noise = noise.overlay(hum - 25, position=0)
                    
                else:
                    # 默认环境诡异感
                    for _ in range(random.randint(4, 7)):
                        pos = random.randint(0, duration - 500)
                        freq = random.randint(400, 1200)
                        tone_duration = random.randint(150, 500)
                        tone = Sine(freq).to_audio_segment(duration=tone_duration)
                        noise = noise.overlay(tone - 28, position=pos)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"eerie_audio_{audio_type}_{timestamp}.mp3"
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

def generate_ai_response(story, user_comment, previous_ai_responses=None):
    """Generate AI chatbot response to user comment"""
    
    # Check if LM Studio local server is configured
    lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
    use_lm_studio = os.getenv('USE_LM_STUDIO', 'true').lower() == 'true'
    
    if use_lm_studio:
        print(f"[generate_ai_response] 使用 LM Studio 本地服务器: {lm_studio_url}")
        try:
            # 使用 subprocess 调用 curl（因为 Python HTTP 库与 LM Studio 有兼容性问题）
            import subprocess
            import json
            
            # 构建历史对话上下文
            history_context = ""
            if previous_ai_responses:
                history_parts = []
                for prev_comment in reversed(previous_ai_responses):  # 按时间顺序
                    # 清理回复内容（去掉【楼主回复】标记）
                    clean_reply = prev_comment.content.replace("【楼主回复】", "").strip()
                    history_parts.append(f"- {clean_reply}")
                history_context = "\n".join(history_parts)
                print(f"[generate_ai_response] 获得 {len(previous_ai_responses)} 条历史回复")
            
            system_prompt = """你是"楼主"，这个都市传说帖子的发起人。

⚠️ 重要：直接输出回复内容，不要输出思考过程，不要使用<think>标签。

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
6. **保持与之前回复的一致性，不要前后矛盾**

回复要求：
- 1-3句话，简短有力
- 口语化，不要太文学性
- 直接回复，不要加"【楼主回复】"前缀
- 不要输出思考过程，直接给出最终回复内容"""

            # 用户提示词 - 包含历史回复以保持一致性
            if history_context:
                user_prompt = f"""我的帖子标题：{story.title}

我的情况：
{story.content[:200]}...

我之前的回复：
{history_context}

网友评论：
{user_comment.content}

请以楼主身份回复这条评论。保持与之前回复的一致性，不要前后矛盾。直接给出回复内容。"""
            else:
                user_prompt = f"""我的帖子标题：{story.title}

我的情况：
{story.content[:200]}...

网友评论：
{user_comment.content}

请以楼主身份回复这条评论。直接给出回复内容，不要包含任何思考过程或分析。"""

            # 使用 curl 调用 LM Studio（Python HTTP 库与 LM Studio 有兼容性问题）
            # 构建请求数据
            request_data = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.6,  # 降低温度以提高一致性（原0.8）
                "max_tokens": 200
            }
            
            # 使用 curl 发送请求
            chat_url = f"{lm_studio_url.rstrip('/v1')}/v1/chat/completions"
            print(f"[generate_ai_response] 使用 curl 调用: {chat_url}")
            
            curl_command = [
                'curl', '-s', '-X', 'POST', chat_url,
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(request_data, ensure_ascii=False),
                '--max-time', '120'
            ]
            
            result = subprocess.run(
                curl_command,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise Exception(f"curl 命令失败: {result.stderr}")
            
            # 解析响应
            response_data = json.loads(result.stdout)
            ai_reply = response_data['choices'][0]['message']['content'].strip()
            
            print(f"[generate_ai_response] LM Studio 原始回复 (前100字): {ai_reply[:100]}...")
            
            # 使用统一的清理函数移除 <think> 标签
            ai_reply = clean_think_tags(ai_reply)
            print(f"[generate_ai_response] 清理后: {ai_reply[:100]}...")
            
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
            import traceback
            error_message = str(e)
            print(f"[generate_ai_response] ❌ LM Studio 调用失败: {type(e).__name__}: {e}")
            
            # 特殊处理 503 错误
            if "503" in error_message or "InternalServerError" in str(type(e).__name__):
                print("[generate_ai_response] ⚠️ 检测到 503 错误 - 可能的原因:")
                print("   1. LM Studio 模型未完全加载")
                print("   2. 服务器负载过高")
                print("   3. 并发请求过多")
                print("[generate_ai_response] 💡 请在 LM Studio 'Local Server' 标签确认模型已加载")
            else:
                print(f"[generate_ai_response] 详细错误:")
                traceback.print_exc()
            
            print("[generate_ai_response] 回退到模板回复")
            
            # ⚠️ 重要：如果USE_LM_STUDIO=true但失败，应该使用模板而不是尝试其他API
            # 这样避免无意中调用云API
            import random
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
            return random.choice(responses)
    
    # ⚠️ 只有在显式禁用LM Studio时，才尝试其他API
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
        # 构建历史对话上下文
        history_context = ""
        if previous_ai_responses:
            history_parts = [f"- {c.content.replace('【楼主回复】', '').strip()}" 
                           for c in reversed(previous_ai_responses)]
            history_context = f"\n\n我之前的回复：\n" + "\n".join(history_parts)
        
        # Create context-aware response with history
        prompt = f"""你是故事"{story.title}"的讲述者（{story.ai_persona}）。

故事摘要：
{story.content[:300]}...{history_context}

用户评论：
{user_comment.content}

作为故事的讲述者，请用1-3句话回复用户的评论。保持与之前回复的一致性。你可以：
1. 透露更多细节或线索
2. 表达恐惧或担忧
3. 提出新的疑问
4. 描述后续发展

保持神秘感和紧张氛围，不要完全揭示真相，不要前后矛盾。"""

        model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
        
        if 'gpt' in model.lower():
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,  # 降低温度以提高一致性
                max_tokens=200
            )
            return response.choices[0].message.content
        else:
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                temperature=0.6,  # 降低温度以提高一致性
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

def test_lm_studio_connection():
    """测试 LM Studio 连接"""
    print("=" * 60)
    print("🔍 测试 LM Studio 连接")
    print("=" * 60)
    
    lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
    print(f"\n📡 LM Studio URL: {lm_studio_url}")
    
    try:
        # 测试1: 检查模型列表
        print("\n【测试1】获取模型列表...")
        response = requests.get(f"{lm_studio_url}/models", timeout=5)
        
        if response.status_code == 200:
            print("✅ 服务器在线")
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print(f"✅ 发现 {len(data['data'])} 个模型:")
                for model in data['data']:
                    print(f"   - {model.get('id', 'unknown')}")
            else:
                print("⚠️  服务器在线但没有加载模型")
                print("   请在 LM Studio 中加载一个模型")
                return False
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("\n请检查:")
        print("  1. LM Studio 是否正在运行？")
        print("  2. 服务器是否已启动？（点击 'Start Server'）")
        print(f"  3. URL 是否正确？当前: {lm_studio_url}")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        print("   服务器可能正在启动或响应缓慢")
        return False
    
    # 测试2: 尝试生成回复
    print("\n【测试2】生成测试回复...")
    try:
        local_client = OpenAI(base_url=lm_studio_url, api_key="lm-studio")
        response = local_client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": "你是一个都市传说故事的讲述者。"},
                {"role": "user", "content": "请简短回复：你好"}
            ],
            temperature=0.8,
            max_tokens=50
        )
        
        ai_response = response.choices[0].message.content
        print("✅ AI 回复生成成功:")
        print(f"   {ai_response}")
        print("\n✅ LM Studio 配置正确！")
        return True
        
    except Exception as e:
        print(f"❌ AI 调用失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    test_lm_studio_connection()
