from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

def scheduled_story_generation():
    """Scheduled task to generate new AI stories"""
    from app import app, db, Story
    from ai_engine import generate_ai_story, should_generate_new_story
    from story_engine import initialize_story_state
    
    with app.app_context():
        print(f"[{datetime.now()}] Running scheduled story generation...")
        
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
                
                print(f"✅ Generated new story: {story.title}")
            else:
                print("❌ Failed to generate story")
        else:
            print("⏭️  Skipped: Max active stories reached")

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
    
    # Generate new stories every 6 hours
    story_interval = int(os.getenv('STORY_GEN_INTERVAL_HOURS', 6))
    scheduler.add_job(
        func=scheduled_story_generation,
        trigger='interval',
        hours=story_interval,
        id='story_generation',
        name='Generate new AI urban legends',
        replace_existing=True
    )
    
    # Check story state progression every 30 minutes
    scheduler.add_job(
        func=scheduled_state_progression,
        trigger='interval',
        minutes=30,
        id='state_progression',
        name='Progress story states',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Background scheduler started!")
    print(f"   - Story generation: every {story_interval} hours")
    print(f"   - State progression: every 30 minutes")
    
    return scheduler
