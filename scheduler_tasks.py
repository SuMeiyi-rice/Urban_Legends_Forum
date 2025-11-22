from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

def scheduled_story_generation():
    """Scheduled task to generate new AI stories - generates 2 stories per run"""
    from app import app, db, Story
    from ai_engine import generate_ai_story, should_generate_new_story
    from story_engine import initialize_story_state
    
    with app.app_context():
        print(f"[{datetime.now()}] Running scheduled story generation...")
        
        # 每次生成2条帖子
        stories_to_generate = 2
        generated_count = 0
        
        for i in range(stories_to_generate):
            if should_generate_new_story():
                story_data = generate_ai_story()
                
                if story_data:
                    story = Story(
                        title=story_data['title'],
                        content=story_data['content'],
                        category=story_data['category'],
                        location=story_data['location'],
                        is_ai_generated=True,
                        ai_persona=story_data['ai_persona']
                    )
                    
                    db.session.add(story)
                    db.session.flush()
                    
                    initialize_story_state(story)
                    
                    db.session.commit()
                    
                    generated_count += 1
                    print(f"✅ Generated story {i+1}/{stories_to_generate}: {story.title}")
                else:
                    print(f"❌ Failed to generate story {i+1}/{stories_to_generate}")
            else:
                print(f"⏭️  Skipped story {i+1}/{stories_to_generate}: Max active stories reached")
                break
        
        print(f"📊 Generation summary: {generated_count}/{stories_to_generate} stories created")

def daily_story_refresh():
    """Refresh AI-generated stories twice daily."""
    from app import app, db
    from app import admin_reset_ai_stories

    with app.app_context():
        print(f"[{datetime.now()}] Refreshing AI-generated stories...")
        result = admin_reset_ai_stories()
        print(f"   Result: {result}")

def scheduled_state_progression():
    """Check and progress story states"""
    from app import app, db, Story
    from story_engine import check_state_transition, transition_story_state
    
    with app.app_context():
        print(f"[{datetime.now()}] Checking story state transitions...")
        
        active_stories = Story.query.filter(Story.current_state != 'ended').all()
        
        for story in active_stories:
            if check_state_transition(story):
                print(f"🔄 Transitioning story: {story.title}")
                transition_story_state(story, app.app_context)
                db.session.commit()
                print(f"✅ Story transitioned to: {story.current_state}")

def start_scheduler(app):
    """Initialize and start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # 【新功能】每天两次自动刷新帖子
    # 中午 11:59
    scheduler.add_job(
        func=daily_story_refresh,
        trigger='cron',
        hour=11,
        minute=59,
        id='noon_story_refresh',
        name='Noon story refresh at 11:59',
        replace_existing=True
    )
    
    # 晚上 23:59
    scheduler.add_job(
        func=daily_story_refresh,
        trigger='cron',
        hour=23,
        minute=59,
        id='night_story_refresh',
        name='Night story refresh at 23:59',
        replace_existing=True
    )
    
    # 【新功能】每20分钟生成2条新帖
    scheduler.add_job(
        func=scheduled_story_generation,
        trigger='interval',
        minutes=20,
        id='story_generation_20min',
        name='Generate 2 stories every 20 minutes',
        replace_existing=True
    )
    
    print("✅ Background scheduler started!")
    print(f"   - 📅 Noon story refresh: every day at 11:59")
    print(f"   - 📅 Night story refresh: every day at 23:59")
    print(f"   - 🔄 Story generation: 2 stories every 20 minutes")
    
    # 可选：环境变量覆盖（用于测试）
    story_interval_minutes = os.getenv('STORY_GEN_INTERVAL_MINUTES')
    story_interval_hours = os.getenv('STORY_GEN_INTERVAL_HOURS')
    
    if story_interval_minutes:
        # 使用分钟间隔（用于测试）
        interval_minutes = int(story_interval_minutes)
        scheduler.remove_job('story_generation_20min')
        scheduler.add_job(
            func=scheduled_story_generation,
            trigger='interval',
            minutes=interval_minutes,
            id='story_generation',
            name='Generate new AI urban legends',
            replace_existing=True
        )
        print(f"   - ⚠️  Override: story generation every {interval_minutes} minutes (from env)")
    elif story_interval_hours:
        # 使用小时间隔
        interval_hours = int(story_interval_hours)
        scheduler.remove_job('story_generation_20min')
        scheduler.add_job(
            func=scheduled_story_generation,
            trigger='interval',
            hours=interval_hours,
            id='story_generation',
            name='Generate new AI urban legends',
            replace_existing=True
        )
        print(f"   - ⚠️  Override: story generation every {interval_hours} hours (from env)")
    
    # Check story state progression every 30 minutes
    scheduler.add_job(
        func=scheduled_state_progression,
        trigger='interval',
        minutes=30,
        id='state_progression',
        name='Progress story states',
        replace_existing=True
    )
    print(f"   - 🔄 State progression: every 30 minutes")
    
    scheduler.start()
    
    return scheduler
