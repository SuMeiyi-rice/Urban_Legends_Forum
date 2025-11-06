from app import app, db, Story, Comment, Evidence
from datetime import datetime, timedelta
from story_engine import initialize_story_state

def create_initial_data():
    with app.app_context():
        # Check if data already exists
        if Story.query.count() > 0:
            print("✅ 数据库已有数据，跳过初始化。")
            return

        print("👻 正在创建初始都市传说数据...")

        # 1. 创建一个活跃的、可回复的帖子
        active_story = Story(
            title="【紧急求助】我在旺角金鱼街买的鱼，有点不对劲...",
            content="""
上周我在旺角金鱼街一家不起眼的小店里买了一条黑色的斗鱼。老板当时眼神很奇怪，一直说这条鱼“有灵性”，让我好好待它。

回家后，怪事就开始了。

首先，我明明只喂了鱼粮，但鱼缸里总会出现一些红色的、像血丝一样的东西。其次，每天半夜三点，我都会准时听到鱼缸传来“哒、哒、哒”的敲击声，就像有人在用指甲敲玻璃。

最恐怖的是昨晚，我起夜看到鱼缸里根本不是我的鱼，而是一张模糊的人脸！我吓得当场尖叫，再开灯看时，鱼又变回了原样。

我现在不敢靠近那个鱼缸了，总感觉它在盯着我。我该怎么办？把它扔掉？还是送回那家店？那家店我还找得到吗...
            """,
            category='cursed_object',
            location='旺角金鱼街',
            is_ai_generated=True,
            ai_persona='👻 新手养鱼人',
            current_state='unfolding',
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        initialize_story_state(active_story)
        db.session.add(active_story)
        db.session.flush() # to get active_story.id

        # 添加一些初始评论
        comment1 = Comment(story_id=active_story.id, author_id=None, is_ai_response=True, content="【楼主更新】谢谢大家的关心，我决定今晚再去那家店看看。希望能找到老板问个清楚。")
        db.session.add(comment1)

        # 2. 创建一个已封存的“僵尸帖”
        zombie_story = Story(
            title="【档案封存】关于油麻地戏院最后一排的座位",
            content="""
(此帖已被系统封存，内容仅供查阅)

这是十几年前的一个帖子了。当时有位网友说，他一个人在油麻地戏院看午夜场电影，明明买的是中间的票，却不知不觉坐到了最后一排最角落的位置。

他说，电影放映中他感觉旁边有人，但转头看又什么都没有。更诡异的是，他听到旁边的人在学电影里的台词，一字不差，但声音是冰冷的、没有感情的。

他当时没敢动，直到电影散场才飞奔出去。后来他再也没去过那家戏院。

这个帖子当时引起了很大的轰动，很多人回复说自己也有类似的经历。但不久后，原楼主就再也没有上过线，这个账号也永远停在了最后一次登录。
            """,
            category='subway_ghost', # Using this category for cinema ghost
            location='油麻地戏院',
            is_ai_generated=True,
            ai_persona='🔒 系统档案员',
            current_state='ended',
            created_at=datetime(2010, 5, 20),
            updated_at=datetime(2010, 6, 1),
            views=108345
        )
        zombie_story.state_data = '{"current_state": "ended", "state_history": [{"state": "ended", "trigger": "system_archive"}]}'
        db.session.add(zombie_story)

        # 3. 创建另一个已完结的悬疑故事
        mystery_story = Story(
            title="【已完结】我好像登上了不存在的红色小巴",
            content="""
这个故事已经完结，多谢各位的追踪。

事情发生在上个月，我从旺角搭红色小巴回大埔，但那辆小巴很奇怪，车上的乘客全都面无表情，一言不发。司机全程没说话，车里的广播一直在播一些听不清的杂音。

最恐怖的是，车窗外的街景越来越陌生，完全不是我熟悉的路。我当时很害怕，偷偷给朋友发了定位，但他回复说我的位置显示在海上。

最后，车在一个我完全不认识的码头停了下来，所有乘客都机械地起身下车，走向一艘漆黑的渡轮。我趁司机不注意，从另一边车门逃了出来，一路狂奔才回到了市区。

后来根据大家的线索，我们发现那可能和几十年前的一宗海上事故有关。虽然没有确切答案，但我想我永远不会再搭深夜的红色小巴了。
            """,
            category='time_anomaly',
            location='旺角至大埔',
            is_ai_generated=True,
            ai_persona='🙏 幸存者',
            current_state='ending_mystery',
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow() - timedelta(days=10),
            views=54088
        )
        mystery_story.state_data = '{"current_state": "ending_mystery", "state_history": [{"state": "ending_mystery", "trigger": "user_conclusion"}]}'
        db.session.add(mystery_story)

        db.session.commit()
        print("✅ 初始数据创建成功！")

if __name__ == '__main__':
    create_initial_data()
