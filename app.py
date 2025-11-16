from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import jwt
import os
import json
import threading
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-horror')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ai_urban_legends.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, resources={r"/api/*": {"origins": "*"}})
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='👻')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='author', lazy=True)
    
class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='urban')
    location = db.Column(db.String(100))
    is_ai_generated = db.Column(db.Boolean, default=False)
    ai_persona = db.Column(db.String(100))
    current_state = db.Column(db.String(50), default='init')
    state_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='story', lazy=True, cascade='all, delete-orphan')
    evidence = db.relationship('Evidence', backref='story', lazy=True, cascade='all, delete-orphan')
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_ai_response = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Evidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    evidence_type = db.Column(db.String(20))
    file_path = db.Column(db.String(500))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'story_id', name='_user_story_uc'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    notification_type = db.Column(db.String(50), nullable=False) # e.g., 'new_reply', 'story_update'
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_default_stories():
    """初始化默认的三个故事（如果数据库为空）"""
    if Story.query.count() == 0:
        print("📝 创建默认故事...")
        
        default_stories = [
            {
                'title': '深夜地铁的第13节车厢',
                'content': '''昨晚加班到凌晨，赶最后一班地铁回家。车厢里只有零星几个人，我坐在靠门的位置刷手机。

列车停靠在"老街站"时，我无意间抬头看了一眼站台显示屏——上面显示这是"13号车厢"。
可是我明明记得这条线路只有12节车厢...

我环顾四周，发现其他乘客都低着头，一动不动。窗外的站台空无一人，但月台上的电子钟显示的时间是"25:73"。
车门缓缓关上，列车继续前行。我想站起来走到其他车厢，但双腿像灌了铅一样沉重。

最诡异的是，我发现窗户上倒映着我的脸，但表情却不是我现在的样子——镜中的我在笑，笑得很诡异...

各位，我该怎么办？现在列车还在行驶，但导航显示我的位置一直在"老街站"没有移动...''',
                'category': 'subway_ghost',
                'location': '地铁2号线',
                'is_ai_generated': True,
                'ai_persona': 'paranoid_reporter',
                'current_state': 'initial'
            },
            {
                'title': '出租屋镜子里的"室友"',
                'content': '''刚搬进这个老小区的单间已经三天了，房租便宜到离谱，房东说之前的租客"搬走了"。

第一天晚上洗漱时，我注意到浴室镜子有点模糊，就用毛巾擦了擦。擦完后，镜子里好像有什么东西一闪而过，但我以为是眼花。

第二天，我发现镜子上有一个手印，五根手指细长，明显不是我的。我把它擦掉了，心里有点发毛。

今天早上，我在镜子里看到了...一个模糊的人影站在我身后。我猛地转身，身后什么都没有。但当我再次看向镜子时，那个人影还在，而且...它在对我笑。

最可怕的是，我发现它的嘴型在说："别走，陪我玩玩..."

现在我不敢回头看镜子了，但又不敢离开浴室。它会跟出来吗？有人知道该怎么办吗？求助！''',
                'category': 'cursed_object',
                'location': '老城区单身公寓',
                'is_ai_generated': True,
                'ai_persona': 'scared_witness',
                'current_state': 'initial'
            },
            {
                'title': '凌晨三点的敲门声',
                'content': '''我住在7楼，这栋楼一共只有6层。

事情是这样的：上周开始，每天凌晨3:00整，我都会听到有人敲我家门。"咚、咚、咚"，三下，很有节奏。

第一次我以为是邻居搞错了，开门一看，走廊空荡荡的。门上的猫眼是坏的，从里面看出去一片漆黑。

第二次我装了监控，结果凌晨3点监控突然黑屏，只录到了敲门声，画面恢复时已经3:05了。

昨晚，我决定不睡觉，就坐在门口等着。2:59分，我听到楼梯间传来脚步声，很轻，但很清晰地在往上走...走...走到7楼。

我的门外传来了呼吸声。

我透过门缝往外看，看到了一双腿...但那双腿是悬空的，离地至少有20厘米。

"咚、咚、咚"——敲门声又响了。

我没敢开门，现在天亮了，但我发现门把手上有一个血手印...

各位，我该报警吗？还是搬家？有人遇到过类似的事情吗？''',
                'category': 'apartment_mystery',
                'location': '某住宅小区',
                'is_ai_generated': True,
                'ai_persona': 'investigator',
                'current_state': 'initial'
            }
        ]
        
        for story_data in default_stories:
            story = Story(**story_data)
            db.session.add(story)
        
        db.session.commit()
        print("✅ 默认故事创建完成")

with app.app_context():
    db.create_all()
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/generated', exist_ok=True)
    init_default_stories()

def generate_token(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        data = jwt.decode(token.replace('Bearer ', ''), app.config['SECRET_KEY'], algorithms=['HS256'])
        return data['user_id']
    except:
        return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/<path:path>')
def serve_other(path):
    return send_from_directory('static', path)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(user)
    db.session.commit()
    
    token = generate_token(user.id)
    
    return jsonify({
        'token': token,
        'user': {'id': user.id, 'username': user.username, 'avatar': user.avatar}
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_token(user.id)
    
    return jsonify({
        'token': token,
        'user': {'id': user.id, 'username': user.username, 'avatar': user.avatar}
    })

@app.route('/api/stories', methods=['GET'])
def get_stories():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 8, type=int)  # 每页8个故事
    
    # 查询总数
    total = Story.query.count()
    
    # 分页查询
    pagination = Story.query.order_by(Story.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    stories = pagination.items
    
    return jsonify({
        'stories': [{
            'id': s.id,
            'title': s.title,
            'content': s.content[:200] + '...' if len(s.content) > 200 else s.content,
            'category': s.category,
            'location': s.location,
            'is_ai_generated': s.is_ai_generated,
            'ai_persona': s.ai_persona,
            'current_state': s.current_state,
            'created_at': s.created_at.isoformat(),
            'views': s.views,
            'comments_count': len(s.comments),
            'evidence_count': len(s.evidence)
        } for s in stories],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_page': pagination.prev_num if pagination.has_prev else None,
            'next_page': pagination.next_num if pagination.has_next else None
        }
    })

@app.route('/api/stories/<int:story_id>', methods=['GET'])
def get_story(story_id):
    story = Story.query.get_or_404(story_id)
    story.views += 1
    db.session.commit()
    
    return jsonify({
        'id': story.id,
        'title': story.title,
        'content': story.content,
        'category': story.category,
        'location': story.location,
        'is_ai_generated': story.is_ai_generated,
        'ai_persona': story.ai_persona,
        'current_state': story.current_state,
        'created_at': story.created_at.isoformat(),
        'views': story.views,
        'evidence': [{
            'id': e.id,
            'type': e.evidence_type,
            'file_path': e.file_path,
            'description': e.description,
            'created_at': e.created_at.isoformat()
        } for e in story.evidence],
        'comments': [{
            'id': c.id,
            'content': c.content,
            'is_ai_response': c.is_ai_response,
            'author': {
                'id': c.author.id if c.author else None,
                'username': c.author.username if c.author else 'AI',
                'avatar': c.author.avatar if c.author else '🤖'
            },
            'created_at': c.created_at.isoformat()
        } for c in story.comments]
    })

@app.route('/api/stories/<int:story_id>/comments', methods=['POST'])
def add_comment(story_id):
    token = request.headers.get('Authorization')
    user_id = verify_token(token) if token else None
    
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    story = Story.query.get_or_404(story_id)
    
    comment = Comment(
        content=data.get('content'),
        story_id=story_id,
        author_id=user_id,
        is_ai_response=False
    )
    
    db.session.add(comment)
    
    # Record user interaction for state machine
    from story_engine import record_user_interaction
    record_user_interaction(story)
    
    db.session.commit()
    
    # Create notification for user's own comment (for AI response)
    create_notifications_for_followers(story, comment)

    # 启动后台线程，5秒后生成AI回复（测试用）
    print(f"[add_comment] 启动后台线程，5秒后生成AI回复...")
    threading.Thread(
        target=delayed_ai_response,
        args=(story_id, comment.id, 5),  # 5秒延迟（测试）
        daemon=True
    ).start()
    
    # 检查是否达到证据生成阈值（只统计用户评论，不包括AI回复）
    user_comment_count = Comment.query.filter_by(story_id=story_id, is_ai_response=False).count()
    evidence_threshold = int(os.getenv('EVIDENCE_COMMENT_THRESHOLD', 2))
    
    print(f"[add_comment] 当前用户评论数: {user_comment_count}, 证据阈值: {evidence_threshold}")
    
    # 每达到阈值的倍数就生成新证据（例如：2,4,6,8...条评论时）
    if user_comment_count >= evidence_threshold and user_comment_count % evidence_threshold == 0:
        print(f"[add_comment] ✅ 用户评论数达到阈值倍数 ({user_comment_count})，启动证据生成...")
        threading.Thread(
            target=generate_evidence_for_story,
            args=(story_id, comment.id),  # 传递触发评论的ID
            daemon=True
        ).start()
    else:
        print(f"[add_comment] 未达到证据生成条件 (用户评论数: {user_comment_count}, 需要: {evidence_threshold}的倍数)")
    
    return jsonify({
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': {
                'id': comment.author.id,
                'username': comment.author.username,
                'avatar': comment.author.avatar
            },
            'created_at': comment.created_at.isoformat()
        },
        'ai_response_pending': True,
        'message': 'AI楼主正在思考回复，请稍候...'
    }), 201

@app.route('/api/stories/<int:story_id>/follow', methods=['POST', 'GET'])
def follow_story(story_id):
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    story = Story.query.get_or_404(story_id)
    follow = Follow.query.filter_by(user_id=user_id, story_id=story_id).first()

    if request.method == 'GET':
        return jsonify({'followed': bool(follow)})

    if follow:
        db.session.delete(follow)
        db.session.commit()
        return jsonify({'status': 'unfollowed'})
    else:
        new_follow = Follow(user_id=user_id, story_id=story_id)
        db.session.add(new_follow)
        db.session.commit()
        return jsonify({'status': 'followed'})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'content': n.content,
        'story_id': n.story_id,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat()
    } for n in notifications])

@app.route('/api/notifications/read', methods=['POST'])
def read_notifications():
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    notification_ids = data.get('ids', [])

    Notification.query.filter(
        Notification.user_id == user_id,
        Notification.id.in_(notification_ids)
    ).update({'is_read': True}, synchronize_session=False)
    
    db.session.commit()
    return jsonify({'status': 'success'})

def create_notifications_for_followers(story, comment, ai_response=False):
    with app.app_context():
        followers = Follow.query.filter_by(story_id=story.id).all()
        for follow in followers:
            # Don't notify the user who made the comment
            if not ai_response and follow.user_id == comment.author_id:
                continue

            notification = Notification(
                user_id=follow.user_id,
                story_id=story.id,
                comment_id=comment.id,
                notification_type='new_reply' if not ai_response else 'story_update',
                content=f'你关注的故事 "{story.title}" 有了新回复。' if not ai_response else f'你关注的故事 "{story.title}" 有了新进展。'
            )
            db.session.add(notification)
        db.session.commit()

def delayed_ai_response(story_id, comment_id, delay_seconds=60):
    """延迟生成AI回复"""
    print(f"[delayed_ai_response] 开始等待 {delay_seconds} 秒... story_id={story_id}, comment_id={comment_id}")
    time.sleep(delay_seconds)
    
    print(f"[delayed_ai_response] 开始生成AI回复...")
    with app.app_context():
        story = Story.query.get(story_id)
        comment = Comment.query.get(comment_id)
        
        if not story or not comment:
            print(f"[delayed_ai_response] ERROR: Story or Comment not found!")
            return
        
        print(f"[delayed_ai_response] 调用 generate_ai_response...")
        from ai_engine import generate_ai_response
        
        # 获取该故事的历史AI回复
        previous_ai_responses = Comment.query.filter_by(
            story_id=story_id,
            is_ai_response=True
        ).order_by(Comment.created_at.desc()).limit(3).all()
        
        ai_response = generate_ai_response(story, comment, previous_ai_responses)
        print(f"[delayed_ai_response] AI回复生成完成: {ai_response[:50]}..." if ai_response else "[delayed_ai_response] AI回复为空!")
        
        if ai_response:
            ai_comment = Comment(
                content=ai_response,
                story_id=story_id,
                author_id=None,
                is_ai_response=True
            )
            db.session.add(ai_comment)
            db.session.commit()
            
            # 创建通知给评论者
            notification = Notification(
                user_id=comment.author_id,
                story_id=story_id,
                comment_id=ai_comment.id,
                notification_type='ai_reply',
                content=f'AI楼主回复了你在 "{story.title}" 中的评论。'
            )
            db.session.add(notification)
            
            # 通知所有关注者
            create_notifications_for_followers(story, ai_comment, ai_response=True)
            
            db.session.commit()

def generate_evidence_for_story(story_id, trigger_comment_id=None):
    """为故事生成证据（图片和音频）- 根据故事内容智能调整证据类型
    
    有声音关键词的故事：
    - 首次及以后每次生成1个音频
    - 当音频总数达到3或3的倍数时，额外生成1张图片
    
    无声音关键词的故事：
    - 每次生成1张图片
    """
    print(f"[generate_evidence_for_story] 开始为故事 ID={story_id} 生成证据...")
    
    with app.app_context():
        story = Story.query.get(story_id)
        if not story:
            print(f"[generate_evidence_for_story] ERROR: Story not found!")
            return
        
        from ai_engine import generate_evidence_image, generate_evidence_audio
        
        # 检测故事中是否提到声音相关内容
        sound_keywords = [
            '声音', '声响', '敲', '敲门', '敲击', '敲打', '砰', '咚', '嘎吱', '尖叫',
            '哭声', '笑声', '呼吸', '脚步', '脚步声', '呼救', '求救', '呼喊', '说话',
            '耳鸣', '异响', '诡异声', '怪声', '鬼哭', '风声', '水流', '滴答', '咔',
            '铃声', '铃', '警报', '打鼾', '打呼', '录音', '录音笔', '录音机', 
            'sound', 'noise', 'scream', 'voice', 'whisper', 'knock'
        ]
        
        # 将故事标题和内容转换为小写来检查关键词
        full_text = (story.title + " " + story.content + " " + 
                    (Comment.query.filter_by(story_id=story_id, is_ai_response=False)
                     .with_entities(Comment.content).all()
                     and " ".join([c[0] for c in Comment.query.filter_by(story_id=story_id, is_ai_response=False)
                                   .with_entities(Comment.content).all()]) or "")).lower()
        
        # 检测是否包含声音关键词
        has_sound_keyword = any(keyword in full_text for keyword in sound_keywords)
        
        print(f"[generate_evidence_for_story] 声音关键词检测: {'有' if has_sound_keyword else '无'}")
        
        # 获取当前证据统计
        total_evidence_count = Evidence.query.filter_by(story_id=story_id).count()
        audio_evidence_count = Evidence.query.filter_by(story_id=story_id, evidence_type='audio').count()
        image_evidence_count = Evidence.query.filter_by(story_id=story_id, evidence_type='image').count()
        
        print(f"[generate_evidence_for_story] 当前证据: 总计{total_evidence_count}个 (音频{audio_evidence_count}个, 图片{image_evidence_count}个)")
        
        # 优先使用触发生成的最新评论，其次是其他评论
        comment_context = ""
        if trigger_comment_id:
            trigger_comment = Comment.query.get(trigger_comment_id)
            if trigger_comment and not trigger_comment.is_ai_response:
                comment_context = trigger_comment.content + " "
                print(f"[generate_evidence_for_story] 使用触发评论: {trigger_comment.content[:50]}...")
        
        # 添加其他用户评论作为补充上下文
        other_comments = [c.content for c in story.comments if not c.is_ai_response and c.id != trigger_comment_id]
        comment_context += " ".join(other_comments[:4])
        
        # ===== 策略1：有声音关键词的故事 =====
        if has_sound_keyword:
            print(f"[generate_evidence_for_story] 🔊 检测到声音元素 - 生成音频证据")
            
            # 生成1个音频证据
            print(f"[generate_evidence_for_story] 生成音频证据...")
            audio_path = generate_evidence_audio(
                f"{story.title}\n{story.content[:200]}\n{comment_context[:100]}"
            )
            
            if audio_path:
                evidence = Evidence(
                    story_id=story_id,
                    evidence_type='audio',
                    file_path=audio_path,
                    description=f"现场录音 - 诡异声响证据"
                )
                db.session.add(evidence)
                db.session.commit()  # 立即提交以更新计数
                print(f"[generate_evidence_for_story] ✅ 音频证据已生成: {audio_path}")
                
                # 更新计数
                audio_evidence_count = Evidence.query.filter_by(story_id=story_id, evidence_type='audio').count()
                print(f"[generate_evidence_for_story] 当前音频证据总数: {audio_evidence_count}")
                
                # 检查是否需要生成图片（当音频数达到3或3的倍数时）
                if audio_evidence_count > 0 and audio_evidence_count % 3 == 0:
                    print(f"[generate_evidence_for_story] 🔊 音频证据达到{audio_evidence_count}个（3的倍数），生成图片辅助...")
                    
                    image_path = generate_evidence_image(
                        story.title,
                        story.content,
                        comment_context
                    )
                    
                    if image_path:
                        evidence = Evidence(
                            story_id=story_id,
                            evidence_type='image',
                            file_path=image_path,
                            description=f"现场拍摄 - 第{audio_evidence_count//3}组补充证据"
                        )
                        db.session.add(evidence)
                        db.session.commit()
                        print(f"[generate_evidence_for_story] ✅ 图片证据已生成: {image_path}")
                        
                        # 更新故事内容
                        story.content += f"\n\n【证据组合更新 #{audio_evidence_count//3}】\n我录了{audio_evidence_count}段音频，拍了张现场照片。这组证据能说明问题吗？"
                    else:
                        # 只更新故事，不生成图片
                        story.content += f"\n\n【音频证据更新】\n我已经录了{audio_evidence_count}段音频了。声音真的很诡异..."
                else:
                    # 仅生成音频，不生成图片
                    story.content += f"\n\n【音频证据更新】\n我又录了一段音频，这是第{audio_evidence_count}段了..."
            
            story.updated_at = datetime.utcnow()
            db.session.commit()
        
        # ===== 策略2：无声音关键词的故事 =====
        else:
            print(f"[generate_evidence_for_story] 📸 仅视觉元素 - 生成图片证据")
            
            # 生成1张图片证据
            print(f"[generate_evidence_for_story] 生成图片证据...")
            image_path = generate_evidence_image(
                story.title,
                story.content,
                comment_context
            )
            
            if image_path:
                evidence = Evidence(
                    story_id=story_id,
                    evidence_type='image',
                    file_path=image_path,
                    description="现场拍摄 - 基于网友反馈"
                )
                db.session.add(evidence)
                print(f"[generate_evidence_for_story] ✅ 图片证据已生成: {image_path}")
                
                # 更新故事内容
                story.content += "\n\n【证据更新】\n根据大家的反馈，我又仔细观察了一遍。拍了这张照片，你们看看有没有发现什么异常..."
            
            story.updated_at = datetime.utcnow()
            db.session.commit()
        
        # 通知所有关注者
        followers = Follow.query.filter_by(story_id=story_id).all()
        for follow in followers:
            notification = Notification(
                user_id=follow.user_id,
                story_id=story_id,
                notification_type='evidence_update',
                content=f'你关注的故事 "{story.title}" 更新了新的证据！'
            )
            db.session.add(notification)
        
        db.session.commit()
        print(f"[generate_evidence_for_story] ✅ 证据生成完成！")

if __name__ == '__main__':
    # Start background scheduler for AI story generation
    from scheduler_tasks import start_scheduler
    scheduler = start_scheduler(app)
    
    try:
        app.run(debug=True, port=5001)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
