const API_BASE = '/api';
let currentUser = null;
let authToken = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadStories();
    loadArchives(); // Load archives on startup
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('login-btn').addEventListener('click', () => showAuthModal('login'));
    document.getElementById('register-btn').addEventListener('click', () => showAuthModal('register'));
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Close modals
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').style.display = 'none';
        });
    });
    
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
    
    // Add event listener for notification bell
    document.getElementById('notification-bell').addEventListener('click', toggleNotificationPanel);
}

function checkAuth() {
    authToken = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');
    
    if (authToken && userData) {
        currentUser = JSON.parse(userData);
        updateAuthUI();
    }
}

function updateAuthUI() {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const userInfo = document.getElementById('user-info');
    
    if (currentUser) {
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        userInfo.style.display = 'inline-flex';
        document.getElementById('user-avatar').textContent = currentUser.avatar;
        document.getElementById('username').textContent = currentUser.username;
        document.getElementById('notification-bell').style.display = 'block';
        loadNotifications();
    } else {
        loginBtn.style.display = 'inline-block';
        registerBtn.style.display = 'inline-block';
        userInfo.style.display = 'none';
        document.getElementById('notification-bell').style.display = 'none';
    }
}

async function loadNotifications() {
    if (!authToken) return;

    const panel = document.getElementById('notification-panel');
    const countBadge = document.getElementById('notification-count');

    try {
        const response = await fetch(`${API_BASE}/notifications`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const notifications = await response.json();

        const unreadCount = notifications.filter(n => !n.is_read).length;
        if (unreadCount > 0) {
            countBadge.textContent = unreadCount;
            countBadge.style.display = 'block';
        } else {
            countBadge.style.display = 'none';
        }

        if (notifications.length === 0) {
            panel.innerHTML = '<div class="notification-item">没有新通知</div>';
            return;
        }

        panel.innerHTML = notifications.map(n => `
            <div class="notification-item ${!n.is_read ? 'unread' : ''}" data-notification-id="${n.id}" data-story-id="${n.story_id}">
                <p>${n.content}</p>
                <small>${new Date(n.created_at).toLocaleString('zh-CN')}</small>
            </div>
        `).join('');
        
        // Add event listeners to notification items
        document.querySelectorAll('.notification-item').forEach(item => {
            const notifId = item.dataset.notificationId;
            const storyId = item.dataset.storyId;
            if (notifId && storyId) {
                item.addEventListener('click', function() {
                    readNotification(parseInt(notifId), parseInt(storyId));
                });
            }
        });

    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function toggleNotificationPanel() {
    const panel = document.getElementById('notification-panel');
    if (panel.style.display === 'block') {
        panel.style.display = 'none';
    } else {
        panel.style.display = 'block';
        loadNotifications();
    }
}

async function readNotification(notificationId, storyId) {
    await fetch(`${API_BASE}/notifications/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ ids: [notificationId] })
    });

    document.getElementById('notification-panel').style.display = 'none';
    viewStory(storyId);
    loadNotifications();
}

function showAuthModal(mode) {
    const modal = document.getElementById('auth-modal');
    const formContainer = document.getElementById('auth-form');
    
    const isLogin = mode === 'login';
    
    formContainer.innerHTML = `
        <h2>${isLogin ? '登录' : '注册'}</h2>
        <div class="auth-form">
            <input type="text" id="auth-username" placeholder="用户名" required>
            ${!isLogin ? '<input type="email" id="auth-email" placeholder="邮箱" required>' : ''}
            <input type="password" id="auth-password" placeholder="密码" required>
            <button id="auth-submit-btn" data-mode="${isLogin ? 'login' : 'register'}">
                ${isLogin ? '登录' : '注册'}
            </button>
        </div>
    `;
    
    // Add event listener for the auth button
    const authBtn = formContainer.querySelector('#auth-submit-btn');
    authBtn.addEventListener('click', function() {
        if (isLogin) {
            login();
        } else {
            register();
        }
    });
    
    modal.style.display = 'block';
}

async function login() {
    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userData', JSON.stringify(currentUser));
            updateAuthUI();
            document.getElementById('auth-modal').style.display = 'none';
            loadStories();
            loadArchives();
        } else {
            alert('登录失败：用户名或密码错误');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('登录失败，请重试');
    }
}

async function register() {
    const username = document.getElementById('auth-username').value;
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userData', JSON.stringify(currentUser));
            updateAuthUI();
            document.getElementById('auth-modal').style.display = 'none';
            loadStories();
            loadArchives();
        } else {
            alert('注册失败：用户名可能已存在');
        }
    } catch (error) {
        console.error('Register error:', error);
        alert('注册失败，请重试');
    }
}

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    authToken = null;
    currentUser = null;
    updateAuthUI();
    loadStories();
    loadArchives();
}

async function loadStories() {
    const grid = document.getElementById('story-grid');
    grid.innerHTML = '<div class="loading">正在加载恐怖档案...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/stories`);
        const stories = await response.json();
        
        const activeStories = stories.filter(s => s.current_state !== 'ended' && s.current_state !== 'ending_mystery' && s.current_state !== 'ending_horror' && s.current_state !== 'ending_ambiguous');

        if (activeStories.length === 0) {
            grid.innerHTML = '<div class="loading">暂无活跃故事... AI正在创作中...</div>';
            return;
        }
        
        grid.innerHTML = activeStories.map(story => `
            <div class="story-card" data-story-id="${story.id}">
                <div class="story-header">
                    <span class="ai-persona">${story.ai_persona || '📝 匿名'}</span>
                    <span class="story-state">${getStateDisplay(story.current_state)}</span>
                </div>
                <div class="story-title">${story.title}</div>
                <div class="story-content">${story.content}</div>
                <div class="story-meta">
                    <span>📍 ${story.location || '未知地点'}</span>
                    <span>👁️ ${story.views} | 💬 ${story.comments_count} | 📎 ${story.evidence_count}</span>
                </div>
            </div>
        `).join('');
        
        // Add event listeners to all story cards
        document.querySelectorAll('.story-card').forEach(card => {
            card.addEventListener('click', function() {
                const storyId = parseInt(this.dataset.storyId);
                viewStory(storyId);
            });
        });
        
    } catch (error) {
        console.error('Error loading stories:', error);
        grid.innerHTML = '<div class="loading">加载失败，请刷新页面</div>';
    }
}

function getStateDisplay(state) {
    const stateMap = {
        'init': '初现',
        'unfolding': '展开',
        'investigation': '调查中',
        'escalation': '升级',
        'danger': '危险',
        'revelation': '真相',
        'twist': '反转',
        'climax': '高潮',
        'ending_horror': '恐怖结局',
        'ending_mystery': '悬疑结局',
        'ending_ambiguous': '未知结局',
        'ended': '已完结'
    };
    return stateMap[state] || state;
}

async function viewStory(storyId) {
    const modal = document.getElementById('story-modal');
    const detailContainer = document.getElementById('story-detail');
    
    detailContainer.innerHTML = '<div class="loading">加载中...</div>';
    modal.style.display = 'block';
    
    console.log('Opening story:', storyId);
    console.log('Current user:', currentUser);
    console.log('Auth token:', authToken ? 'exists' : 'missing');
    
    try {
        const response = await fetch(`${API_BASE}/stories/${storyId}`);
        const story = await response.json();
        
        // Check follow status
        let followStatus = { followed: false };
        if (authToken) {
            const followCheckResponse = await fetch(`${API_BASE}/stories/${storyId}/follow`, { method: 'GET', headers: { 'Authorization': `Bearer ${authToken}` } });
            if(followCheckResponse.ok) followStatus = await followCheckResponse.json();
        }
        
        console.log('Follow status:', followStatus);

        detailContainer.innerHTML = `
            <div class="story-header">
                <div class="story-header-left">
                    <span class="ai-persona">${story.ai_persona || '📝 匿名'}</span>
                    <span class="story-state">${getStateDisplay(story.current_state)}</span>
                </div>
                ${currentUser ? `<button class="follow-btn ${followStatus.followed ? 'followed' : ''}" data-story-id="${story.id}">${followStatus.followed ? '✓ 已关注' : '+ 关注'}</button>` : '<span style="color: #666; font-size: 0.9em;">请登录后关注</span>'}
            </div>
            
            <h2 class="story-title">${story.title}</h2>
            
            <div class="story-meta">
                <span>📍 ${story.location || '未知地点'}</span>
                <span>📅 ${new Date(story.created_at).toLocaleString('zh-CN')}</span>
                <span>👁️ ${story.views} 次查看</span>
            </div>
            
            <div class="story-content" style="margin-top: 30px; white-space: pre-wrap;">
                ${story.content}
            </div>
            
            ${story.evidence && story.evidence.length > 0 ? `
                <div class="evidence-section">
                    <h3 style="color: var(--blood-red); margin-bottom: 20px;">🔍 证据档案</h3>
                    ${story.evidence.map(e => `
                        <div class="evidence-item">
                            ${e.type === 'image' ? `<img src="${e.file_path}" alt="Evidence">` : ''}
                            ${e.type === 'audio' ? `<audio controls src="${e.file_path}" style="width: 100%;"></audio>` : ''}
                            <p style="margin-top: 10px; font-size: 0.9em;">${e.description}</p>
                            <small style="color: #666;">${new Date(e.created_at).toLocaleString('zh-CN')}</small>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            <div class="comments-section">
                <h3 style="color: var(--blood-red); margin-bottom: 20px;">💬 讨论区</h3>
                
                ${currentUser ? `
                    <div class="comment-form">
                        <textarea id="comment-text" placeholder="发表你的看法...（AI会回复你）"></textarea>
                        <button id="submit-comment-btn" data-story-id="${story.id}">提交评论</button>
                    </div>
                ` : '<p style="color: #666;">请先登录后参与讨论</p>'}
                
                <div id="comments-list">
                    ${story.comments && story.comments.length > 0 ? 
                        story.comments.map(c => `
                            <div class="comment ${c.is_ai_response ? 'ai-response' : ''}">
                                <div class="comment-author ${c.is_ai_response ? 'ai' : ''}">
                                    ${c.author.avatar} ${c.author.username}
                                    ${c.is_ai_response ? ' [AI回复]' : ''}
                                </div>
                                <div>${c.content}</div>
                                <small style="color: #666;">${new Date(c.created_at).toLocaleString('zh-CN')}</small>
                            </div>
                        `).join('') 
                        : '<p style="color: #666; margin-top: 20px;">还没有评论...</p>'
                    }
                </div>
            </div>
        `;
        
        // Add event listeners after content is loaded
        const followBtn = detailContainer.querySelector('.follow-btn');
        if (followBtn) {
            followBtn.addEventListener('click', function() {
                followStory(story.id, this);
            });
        }
        
        const submitBtn = detailContainer.querySelector('#submit-comment-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', function() {
                submitComment(story.id);
            });
        }
        
    } catch (error) {
        console.error('Error loading story:', error);
        detailContainer.innerHTML = '<div class="loading">加载失败</div>';
    }
    
    // Highlight active archive item
    document.querySelectorAll('.archive-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeArchiveItems = document.querySelectorAll('.archive-item');
    activeArchiveItems.forEach(item => {
        if (item.dataset.storyId == storyId) {
            item.classList.add('active');
        }
    });
}

async function submitComment(storyId) {
    if (!authToken) {
        alert('请先登录');
        return;
    }
    
    const textarea = document.getElementById('comment-text');
    const content = textarea.value.trim();
    
    if (!content) {
        alert('请输入评论内容');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/stories/${storyId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ content })
        });
        
        if (response.ok) {
            const data = await response.json();
            textarea.value = '';
            // Show pending message
            if (data.ai_response_pending) {
                showToast('✅ 评论已发布', 'AI楼主正在思考回复中，请稍候...', storyId);
            }
            // Reload story to show new comment
            setTimeout(() => viewStory(storyId), 1000);
        } else {
            alert('评论失败，请重试');
        }
    } catch (error) {
        console.error('Error submitting comment:', error);
        alert('评论失败，请重试');
    }
}

async function loadArchives() {
    const archiveList = document.getElementById('archive-list');
    try {
        const response = await fetch(`${API_BASE}/stories`);
        const stories = await response.json();
        
        archiveList.innerHTML = stories.map(story => `
            <div class="archive-item" data-story-id="${story.id}">
                <div class="archive-title">${story.title}</div>
                <div class="archive-status ${story.current_state}">${getStateDisplay(story.current_state)}</div>
            </div>
        `).join('');
        
        // Add event listeners to all archive items
        document.querySelectorAll('.archive-item').forEach(item => {
            item.addEventListener('click', function() {
                const storyId = parseInt(this.dataset.storyId);
                viewStory(storyId);
            });
        });
        
    } catch (error) {
        console.error('Error loading archives:', error);
        archiveList.innerHTML = '<p>档案加载失败</p>';
    }
}

// Modify viewStory to highlight active archive
async function viewStory(storyId) {
    const modal = document.getElementById('story-modal');
    const detailContainer = document.getElementById('story-detail');
    
    detailContainer.innerHTML = '<div class="loading">加载中...</div>';
    modal.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/stories/${storyId}`);
        const story = await response.json();
        
        detailContainer.innerHTML = `
            <div class="story-header">
                <span class="ai-persona">${story.ai_persona || '📝 匿名'}</span>
                <span class="story-state">${getStateDisplay(story.current_state)}</span>
            </div>
            
            <h2 class="story-title">${story.title}</h2>
            
            <div class="story-meta">
                <span>📍 ${story.location || '未知地点'}</span>
                <span>📅 ${new Date(story.created_at).toLocaleString('zh-CN')}</span>
                <span>👁️ ${story.views} 次查看</span>
            </div>
            
            <div class="story-content" style="margin-top: 30px; white-space: pre-wrap;">
                ${story.content}
            </div>
            
            ${story.evidence && story.evidence.length > 0 ? `
                <div class="evidence-section">
                    <h3 style="color: var(--blood-red); margin-bottom: 20px;">🔍 证据档案</h3>
                    ${story.evidence.map(e => `
                        <div class="evidence-item">
                            ${e.type === 'image' ? `<img src="${e.file_path}" alt="Evidence">` : ''}
                            ${e.type === 'audio' ? `<audio controls src="${e.file_path}" style="width: 100%;"></audio>` : ''}
                            <p style="margin-top: 10px; font-size: 0.9em;">${e.description}</p>
                            <small style="color: #666;">${new Date(e.created_at).toLocaleString('zh-CN')}</small>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            <div class="comments-section">
                <h3 style="color: var(--blood-red); margin-bottom: 20px;">💬 讨论区</h3>
                
                ${currentUser ? `
                    <div class="comment-form">
                        <textarea id="comment-text" placeholder="发表你的看法...（AI会回复你）"></textarea>
                        <button onclick="submitComment(${story.id})">提交评论</button>
                    </div>
                ` : '<p style="color: #666;">请先登录后参与讨论</p>'}
                
                <div id="comments-list">
                    ${story.comments && story.comments.length > 0 ? 
                        story.comments.map(c => `
                            <div class="comment ${c.is_ai_response ? 'ai-response' : ''}">
                                <div class="comment-author ${c.is_ai_response ? 'ai' : ''}">
                                    ${c.author.avatar} ${c.author.username}
                                    ${c.is_ai_response ? ' [AI回复]' : ''}
                                </div>
                                <div>${c.content}</div>
                                <small style="color: #666;">${new Date(c.created_at).toLocaleString('zh-CN')}</small>
                            </div>
                        `).join('') 
                        : '<p style="color: #666; margin-top: 20px;">还没有评论...</p>'
                    }
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading story:', error);
        detailContainer.innerHTML = '<div class="loading">加载失败</div>';
    }
    
    // Highlight active archive item
    document.querySelectorAll('.archive-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeArchiveItem = document.querySelector(`.archive-item[onclick="viewStory(${storyId})"]`);
    if (activeArchiveItem) {
        activeArchiveItem.classList.add('active');
    }
}

//关注功能
async function followStory(storyId, btn) {
    if (!authToken) {
        alert('请先登录');
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/stories/${storyId}/follow`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        if (data.status === 'followed') {
            btn.textContent = '已关注';
            btn.classList.add('followed');
        } else {
            btn.textContent = '关注';
            btn.classList.remove('followed');
        }
    } catch (error) {
        console.error('Follow error:', error);
    }
}

// Auto-refresh stories and archives every 5 minutes
setInterval(() => {
    loadStories();
    loadArchives();
}, 5 * 60 * 1000);

// Track last notification check
let lastNotificationCount = 0;

// Show toast notification
function showToast(title, content, storyId) {
    const toast = document.getElementById('toast-notification');
    toast.innerHTML = `
        <div class="toast-title">${title}</div>
        <div class="toast-content">${content}</div>
    `;
    toast.classList.add('show');
    
    // Remove any existing click listeners
    const newToast = toast.cloneNode(true);
    toast.parentNode.replaceChild(newToast, toast);
    
    // Add click event listener
    newToast.addEventListener('click', function() {
        viewStory(storyId);
        newToast.classList.remove('show');
    });
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        newToast.classList.remove('show');
    }, 5000);
}

// Check for new notifications (more frequently)
async function checkNewNotifications() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE}/notifications`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const notifications = await response.json();
        
        const unreadNotifications = notifications.filter(n => !n.is_read);
        
        // If we have new unread notifications
        if (unreadNotifications.length > lastNotificationCount) {
            const newNotification = unreadNotifications[0];
            showToast('🔔 新消息', newNotification.content, newNotification.story_id);
            loadNotifications(); // Update notification bell
        }
        
        lastNotificationCount = unreadNotifications.length;
    } catch (error) {
        console.error('Error checking notifications:', error);
    }
}

// Auto-refresh notifications every minute
setInterval(loadNotifications, 1 * 60 * 1000);

// Check for new notifications every 10 seconds
setInterval(checkNewNotifications, 10 * 1000);
