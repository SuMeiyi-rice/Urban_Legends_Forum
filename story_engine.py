import json
from datetime import datetime, timedelta
from ai_engine import generate_evidence_image, generate_evidence_audio

# Story state machine
STORY_STATES = {
    'init': {
        'description': '故事初始化',
        'next_states': ['unfolding'],
        'duration_hours': 6
    },
    'unfolding': {
        'description': '情节展开',
        'next_states': ['escalation', 'investigation'],
        'duration_hours': 12
    },
    'investigation': {
        'description': '深入调查',
        'next_states': ['revelation', 'danger'],
        'duration_hours': 18
    },
    'escalation': {
        'description': '事态升级',
        'next_states': ['danger', 'climax'],
        'duration_hours': 12
    },
    'danger': {
        'description': '危机时刻',
        'next_states': ['climax', 'twist'],
        'duration_hours': 24
    },
    'revelation': {
        'description': '真相揭露',
        'next_states': ['climax', 'twist'],
        'duration_hours': 18
    },
    'twist': {
        'description': '剧情反转',
        'next_states': ['climax', 'ending_horror', 'ending_mystery'],
        'duration_hours': 12
    },
    'climax': {
        'description': '故事高潮',
        'next_states': ['ending_horror', 'ending_mystery', 'ending_ambiguous'],
        'duration_hours': 6
    },
    'ending_horror': {
        'description': '恐怖结局',
        'next_states': ['ended'],
        'duration_hours': 0
    },
    'ending_mystery': {
        'description': '悬疑结局',
        'next_states': ['ended'],
        'duration_hours': 0
    },
    'ending_ambiguous': {
        'description': '开放结局',
        'next_states': ['ended'],
        'duration_hours': 0
    },
    'ended': {
        'description': '故事完结',
        'next_states': [],
        'duration_hours': 0
    }
}

def initialize_story_state(story):
    """Initialize state machine for a story"""
    state_data = {
        'current_state': 'init',
        'state_history': [
            {
                'state': 'init',
                'timestamp': datetime.utcnow().isoformat(),
                'trigger': 'story_created'
            }
        ],
        'next_transition_time': (datetime.utcnow() + timedelta(hours=STORY_STATES['init']['duration_hours'])).isoformat(),
        'user_interaction_count': 0,
        'evidence_generated': 0
    }
    
    story.state_data = json.dumps(state_data)
    story.current_state = 'init'
    
    return story

def check_state_transition(story):
    """Check if story should transition to next state"""
    if not story.state_data:
        return False
    
    state_data = json.loads(story.state_data)
    
    # Check if it's time to transition
    next_transition_time = datetime.fromisoformat(state_data['next_transition_time'])
    
    if datetime.utcnow() >= next_transition_time:
        return True
    
    # Check if user interaction threshold is met (can trigger early transition)
    if state_data['user_interaction_count'] >= 10:
        return True
    
    return False

def transition_story_state(story, app_context):
    """Transition story to next state"""
    from app import db, Evidence
    from ai_engine import generate_ai_story, generate_evidence_image, generate_evidence_audio
    
    if not story.state_data:
        initialize_story_state(story)
        db.session.commit()
        return
    
    state_data = json.loads(story.state_data)
    current_state = state_data['current_state']
    
    # Get possible next states
    possible_next_states = STORY_STATES[current_state]['next_states']
    
    if not possible_next_states:
        return  # Story has ended
    
    # Choose next state based on user interaction
    # More interactions = more investigation/revelation path
    # Fewer interactions = more escalation/danger path
    interaction_ratio = state_data['user_interaction_count'] / 10.0
    
    if interaction_ratio > 0.7 and 'investigation' in possible_next_states:
        next_state = 'investigation'
    elif interaction_ratio > 0.5 and 'revelation' in possible_next_states:
        next_state = 'revelation'
    elif interaction_ratio < 0.3 and 'escalation' in possible_next_states:
        next_state = 'escalation'
    elif interaction_ratio < 0.5 and 'danger' in possible_next_states:
        next_state = 'danger'
    else:
        # Random choice from available
        import random
        next_state = random.choice(possible_next_states)
    
    # Update state
    state_data['current_state'] = next_state
    state_data['state_history'].append({
        'state': next_state,
        'timestamp': datetime.utcnow().isoformat(),
        'trigger': 'time_based' if datetime.utcnow() >= datetime.fromisoformat(state_data['next_transition_time']) else 'interaction_based'
    })
    
    # Set next transition time
    duration = STORY_STATES[next_state]['duration_hours']
    if duration > 0:
        state_data['next_transition_time'] = (datetime.utcnow() + timedelta(hours=duration)).isoformat()
    
    # Reset interaction counter
    state_data['user_interaction_count'] = 0
    
    story.state_data = json.dumps(state_data)
    story.current_state = next_state
    
    # Generate new evidence based on state
    with app_context():
        generate_state_evidence(story, next_state)
    
    db.session.commit()

def generate_state_evidence(story, state):
    """Generate appropriate evidence for current state"""
    from app import db, Evidence, Comment
    
    # Generate evidence based on state
    evidence_types = {
        'init': ['text'],
        'unfolding': ['image', 'text'],
        'investigation': ['image', 'audio'],
        'escalation': ['image', 'audio', 'text'],
        'danger': ['image', 'audio'],
        'revelation': ['text', 'image'],
        'twist': ['image', 'audio'],
        'climax': ['image', 'audio', 'text']
    }
    
    types_to_generate = evidence_types.get(state, ['text'])
    
    for evidence_type in types_to_generate:
        if evidence_type == 'image':
            image_path = generate_evidence_image(story.title, story.content)
            if image_path:
                evidence = Evidence(
                    story_id=story.id,
                    evidence_type='image',
                    file_path=image_path,
                    description=f'在{story.location}发现的可疑照片'
                )
                db.session.add(evidence)
        
        elif evidence_type == 'audio':
            audio_path = generate_evidence_audio(story.content)
            if audio_path:
                evidence = Evidence(
                    story_id=story.id,
                    evidence_type='audio',
                    file_path=audio_path,
                    description=f'{story.ai_persona}的录音记录'
                )
                db.session.add(evidence)
        
        elif evidence_type == 'text':
            # Generate text update via AI
            update_texts = {
                'init': f'【更新】{story.ai_persona}首次发布了这个故事...',
                'unfolding': f'【更新】事态正在发展，{story.location}出现了新的情况...',
                'investigation': f'【更新】经过调查，我发现了一些令人不安的细节...',
                'escalation': f'【更新】情况比我想象的要严重，它又出现了...',
                'danger': f'【更新】我可能惹上麻烦了，有人在跟踪我...',
                'revelation': f'【更新】真相终于浮出水面，但我宁愿自己从未知道...',
                'twist': f'【更新】等等，事情根本不是我想的那样...',
                'climax': f'【最终更新】这是我最后一次发帖了...'
            }
            
            update_text = update_texts.get(state, '【更新】情况有了新的进展...')
            
            comment = Comment(
                content=update_text,
                story_id=story.id,
                author_id=None,
                is_ai_response=True
            )
            db.session.add(comment)
    
    # Update evidence count
    if story.state_data:
        state_data = json.loads(story.state_data)
        state_data['evidence_generated'] += len(types_to_generate)
        story.state_data = json.dumps(state_data)

def record_user_interaction(story):
    """Record user interaction with story"""
    if not story.state_data:
        initialize_story_state(story)
    
    state_data = json.loads(story.state_data)
    state_data['user_interaction_count'] += 1
    story.state_data = json.dumps(state_data)
