// ============================================
// 都市传说档案馆 - 前端应用
// Mac OS 3 暗色系风格
// ============================================

const API_BASE = '/api';
let currentUser = null;
let token = localStorage.getItem('token');
let allStories = [];
let currentCategory = 'all';
let lastStoryCount = 0;
let lastNotificationCheck = 0;
let currentPage = 1;
let totalPages = 1;
let pagination = null;
// Notification client-side cache and pagination state
let notificationsCache = [];
let notifPerPage = 6;
let notifCurrentPage = 1;
// 在线用户数缓存（避免每次完全随机）
let cachedOnlineUsers = Math.floor(Math.random() * 13) + 3; // 初始3-15人


document.addEventListener('DOMContentLoaded', () => {
    console.log('✨ 都市传说档案馆已加载');
    if (token) verifyToken();
    loadStories();
    bindEvents();
    updateClock();
    setInterval(updateClock, 1000);
    
    // 新菜单栏事件
    bindHeaderEvents();
    
    // 每30秒检查新故事和通知
    setInterval(() => {
        loadStories(true);  // 静默刷新
        if (currentUser) checkNotifications();
    }, 30000);
    
    // 初始通知检查
    if (currentUser) checkNotifications();
});

function bindEvents() {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const toggleAuthBtn = document.getElementById('toggle-auth');
    const authForm = document.getElementById('auth-form');
    
    // 旧的登录/注册按钮已移除（在新菜单栏中处理）
    if (loginBtn) loginBtn.addEventListener('click', showLoginForm);
    if (registerBtn) registerBtn.addEventListener('click', showRegisterForm);
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
    if (toggleAuthBtn) toggleAuthBtn.addEventListener('click', toggleAuthForm);
    if (authForm) authForm.addEventListener('submit', handleAuthSubmit);
    
    document.querySelectorAll('.category-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.category-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            currentCategory = item.dataset.category;
            renderStories();
        });
    });
    
    const authModal = document.getElementById('auth-modal');
    const storyModal = document.getElementById('story-modal');
    
    if (authModal) {
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) closeAuthModal();
        });
    }
    
    if (storyModal) {
        storyModal.addEventListener('click', (e) => {
            if (e.target === storyModal) closeStoryModal();
        });
    }
    
    // 用户中心模态框点击外部关闭
    const userCenterModal = document.getElementById('user-center-modal');
    if (userCenterModal) {
        userCenterModal.addEventListener('click', (e) => {
            if (e.target === userCenterModal) {
                closeUserCenterModal();
            }
        });
    }
}

function closeUserCenterModal() {
    const modal = document.getElementById('user-center-modal');
    if (modal) {
        modal.style.display = 'none';
        // 停止 Lila 摄像头
        stopLilaCamera();
    }
}

// 头部菜单栏事件处理
function bindHeaderEvents() {
    // 搜索功能
    const searchInput = document.getElementById('search-posts');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const keyword = searchInput.value.trim();
                if (keyword) {
                    searchStories(keyword);
                }
            }
        });
    }
    
    // 用户中心
    const userMenu = document.getElementById('menu-user');
    if (userMenu) {
        userMenu.addEventListener('click', () => {
            if (currentUser) {
                showUserCenter();
            } else {
                showLoginForm();
            }
        });
    }
    
    // 通知中心
    const notificationsMenu = document.getElementById('menu-notifications');
    if (notificationsMenu) {
        notificationsMenu.addEventListener('click', () => {
            showNotificationCenter();
        });
    }
}

// 搜索故事
function searchStories(keyword) {
    if (!keyword) {
        renderStories();
        return;
    }
    
    const filtered = allStories.filter(story => 
        story.title.toLowerCase().includes(keyword.toLowerCase()) ||
        story.content.toLowerCase().includes(keyword.toLowerCase())
    );
    
    console.log(`🔍 搜索结果: 找到 ${filtered.length} 个故事`);
    renderStoriesFromList(filtered);
    showToast(`🔍 找到 ${filtered.length} 个相关故事`, 'info');
}

// 从指定列表渲染故事
function renderStoriesFromList(stories) {
    const container = document.getElementById('stories-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (stories.length === 0) {
        container.innerHTML = '<div class="loading-text">🔍 没有找到相关故事</div>';
        return;
    }
    
    container.innerHTML = stories.map(story => {
        return '<div class="story-item" onclick="showStoryDetail(' + story.id + ')">' +
            '<div class="story-title">👻 ' + escapeHtml(story.title) + '</div>' +
            '<div class="story-meta">' +
            '<span>👁️ ' + story.views + '</span>' +
            '<span>💬 ' + story.comments_count + '</span>' +
            '<span>📸 ' + story.evidence_count + '</span>' +
            '</div>' +
            '<div class="story-preview">' + escapeHtml(story.content.substring(0, 80)) + '</div>' +
            '<div class="story-footer">' +
            '<span>' + (story.ai_persona || '🤖 AI') + '</span>' +
            '<span>' + formatDate(story.created_at) + '</span>' +
            '</div>' +
            '</div>';
    }).join('');
}

// 显示用户中心
// 摄像头相关变量
let cameraStream = null;
let isCameraActive = false;
let animationFrameId = null;
let currentBrightness = 100;
let currentContrast = 130;
let filterEnabled = true;

// Who's Lila Camera Logic
let retroCameraStream = null;
let retroCameraAnimationId = null;
let lilaThreshold = 140;
let lilaPalette = 'lila';

const PROCESS_WIDTH = 160;
const PROCESS_HEIGHT = 120;

const lilaPalettes = {
    lila: {
        dark: [20, 5, 5],    // Deep dark red/black
        light: [255, 50, 50] // Who's Lila Red
    },
    bw: {
        dark: [10, 10, 10],
        light: [230, 230, 230]
    }
};

const bayerMatrix = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5]
];

function showUserCenter() {
    // 渲染并显示个人中心模态框
    const modal = document.getElementById('user-center-modal');
    const username = document.getElementById('uc-username');
    const incept = document.getElementById('uc-incept');
    const functionEl = document.getElementById('uc-function');
    const rankEl = document.getElementById('uc-rank');
    const categoriesEl = document.getElementById('uc-categories');
    const profileTypeEl = document.getElementById('uc-profile-type');

    if (currentUser) {
        if (username) username.textContent = currentUser.username.toUpperCase().split('').join(' . ');
        if (incept) {
            const date = new Date(currentUser.created_at || Date.now());
            incept.textContent = `${String(date.getMonth() + 1).padStart(2, '0')} / ${String(date.getDate()).padStart(2, '0')} / ${date.getFullYear()}`;
        }
        if (functionEl) functionEl.textContent = 'INVESTIGATOR';
        if (rankEl) rankEl.textContent = 'CURIOUS';
        
        // 获取用户最感兴趣的分类
        if (categoriesEl && token) {
            fetch(API_BASE + '/user-top-categories', {
                headers: { 'Authorization': 'Bearer ' + token }
            })
            .then(res => res.json())
            .then(data => {
                if (data.categories && data.categories.length > 0) {
                    categoriesEl.innerHTML = data.categories.map(cat => {
                        const categoryLabel = getCategoryLabel(cat.category);
                        return '<span class="retro-interest-tag">' + categoryLabel + '</span>';
                    }).join('');
                    updateProfileType(data.categories);
                } else {
                    categoriesEl.innerHTML = '<span class="retro-interest-tag retro-no-data-tag">NO DATA</span>';
                    updateProfileType([]);
                }
            })
            .catch(err => {
                console.error('Failed to load user categories:', err);
                categoriesEl.innerHTML = '<span class="retro-interest-tag retro-no-data-tag">ERROR</span>';
            });
        }
    } else {
        if (username) username.textContent = 'GUEST';
        if (incept) incept.textContent = '-- / -- / ----';
        if (functionEl) functionEl.textContent = 'VISITOR';
        if (rankEl) rankEl.textContent = 'UNKNOWN';
        
        // 访客状态
        if (categoriesEl) {
            categoriesEl.innerHTML = '<span class="retro-interest-tag retro-no-data-tag">NO DATA</span>';
        }
        updateProfileType([]);
    }

    if (modal) {
        modal.style.display = 'flex';
        // 初始化 Lila 摄像头控制
        initLilaCameraControls();
    }
}

function initLilaCameraControls() {
    const startBtn = document.getElementById('startBtn');
    const captureBtn = document.getElementById('captureBtn');
    const thresholdRange = document.getElementById('thresholdRange');
    
    if (startBtn) {
        // Clone to remove old listeners
        const newStartBtn = startBtn.cloneNode(true);
        startBtn.parentNode.replaceChild(newStartBtn, startBtn);
        
        newStartBtn.addEventListener('click', () => {
            if (!retroCameraStream) {
                startLilaCamera();
            } else {
                stopLilaCamera();
            }
        });
    }
    
    if (captureBtn) {
        const newCaptureBtn = captureBtn.cloneNode(true);
        captureBtn.parentNode.replaceChild(newCaptureBtn, captureBtn);
        
        newCaptureBtn.addEventListener('click', captureLilaImage);
    }
    
    if (thresholdRange) {
        thresholdRange.addEventListener('input', (e) => {
            lilaThreshold = parseInt(e.target.value);
        });
    }
    
    // Start clock
    setInterval(() => {
        const timestampEl = document.getElementById('lila-timestamp');
        if (timestampEl) {
            const now = new Date();
            timestampEl.innerText = now.toLocaleTimeString('en-US', { hour12: false });
        }
    }, 1000);
}

window.setPalette = (mode) => {
    lilaPalette = mode;
};

async function startLilaCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user" 
            },
            audio: false
        });
        
        retroCameraStream = stream;
        const video = document.getElementById('webcam');
        const startBtn = document.getElementById('startBtn');
        const captureBtn = document.getElementById('captureBtn');
        const loadingText = document.getElementById('loadingText');
        const outputCanvas = document.getElementById('outputCanvas');
        
        if (video) {
            video.srcObject = stream;
            await video.play();
        }
        
        if (startBtn) {
            startBtn.textContent = 'TERMINATE';
            startBtn.style.background = 'rgba(255, 50, 50, 0.4)';
        }
        
        if (captureBtn) captureBtn.disabled = false;
        if (loadingText) loadingText.style.display = 'none';
        
        // Setup Canvas Resolution
        if (outputCanvas) {
            outputCanvas.width = PROCESS_WIDTH;
            outputCanvas.height = PROCESS_HEIGHT;
        }
        
        // Start Processing Loop
        processLilaFrame();
        
    } catch (err) {
        console.error("Error accessing webcam:", err);
        const loadingText = document.getElementById('loadingText');
        if (loadingText) {
            loadingText.innerText = "ACCESS DENIED";
            loadingText.classList.remove('lila-flicker-text');
        }
    }
}

function stopLilaCamera() {
    if (retroCameraStream) {
        retroCameraStream.getTracks().forEach(track => track.stop());
        retroCameraStream = null;
    }
    
    if (retroCameraAnimationId) {
        cancelAnimationFrame(retroCameraAnimationId);
        retroCameraAnimationId = null;
    }
    
    const video = document.getElementById('webcam');
    const startBtn = document.getElementById('startBtn');
    const captureBtn = document.getElementById('captureBtn');
    const loadingText = document.getElementById('loadingText');
    const outputCanvas = document.getElementById('outputCanvas');
    
    if (video) {
        video.srcObject = null;
    }
    
    if (startBtn) {
        startBtn.textContent = 'INITIALIZE';
        startBtn.style.background = '';
    }
    
    if (captureBtn) {
        captureBtn.disabled = true;
        captureBtn.innerText = "CAPTURE";
        captureBtn.style.background = "rgba(80, 20, 20, 0.6)";
        captureBtn.style.color = "var(--lila-red)";
    }

    if (loadingText) {
        loadingText.style.display = 'flex';
        loadingText.innerText = "[ WAITING FOR SIGNAL ]";
        loadingText.classList.add('lila-flicker-text');
    }
    
    // Clear canvas
    if (outputCanvas) {
        const ctx = outputCanvas.getContext('2d');
        ctx.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
    }
}

function processLilaFrame() {
    if (!retroCameraStream) return;

    const video = document.getElementById('webcam');
    const outputCanvas = document.getElementById('outputCanvas');
    
    if (!video || !outputCanvas) return;
    
    const ctx = outputCanvas.getContext('2d');

    // Draw video to canvas (scaled down) - Mirrored
    ctx.save();
    ctx.scale(-1, 1);
    ctx.drawImage(video, -PROCESS_WIDTH, 0, PROCESS_WIDTH, PROCESS_HEIGHT);
    ctx.restore();

    // Get raw pixel data
    const imageData = ctx.getImageData(0, 0, PROCESS_WIDTH, PROCESS_HEIGHT);
    const data = imageData.data;

    // Apply Dithering Effect
    const pal = lilaPalettes[lilaPalette];
    
    // Tracking variables
    let sumX = 0;
    let sumY = 0;
    let pixelCount = 0;

    for (let y = 0; y < PROCESS_HEIGHT; y++) {
        for (let x = 0; x < PROCESS_WIDTH; x++) {
            const index = (y * PROCESS_WIDTH + x) * 4;
            
            // Convert to Grayscale (standard luminance formula)
            const r = data[index];
            const g = data[index + 1];
            const b = data[index + 2];
            const gray = 0.299 * r + 0.587 * g + 0.114 * b;

            // Get Bayer Threshold (0-15) mapped to 0-255 range partially
            const matrixValue = bayerMatrix[y % 4][x % 4];
            const ditherOffset = (matrixValue - 7.5) * 8; 

            // Decide pixel color
            if (gray + ditherOffset > lilaThreshold) {
                // Light Color
                data[index] = pal.light[0];
                data[index + 1] = pal.light[1];
                data[index + 2] = pal.light[2];
                
                // Accumulate for tracking
                sumX += x;
                sumY += y;
                pixelCount++;
            } else {
                // Dark Color
                data[index] = pal.dark[0];
                data[index + 1] = pal.dark[1];
                data[index + 2] = pal.dark[2];
            }
            // Alpha is always 255
            data[index + 3] = 255;
        }
    }

    // Update Head Position
    if (pixelCount > 50) {
        const targetX = sumX / pixelCount;
        const targetY = sumY / pixelCount;
        
        // Invert X coordinate to match mirrored display
        // If the user moves Left, the mirrored image moves Left (x decreases).
        // But if the tracking feels opposite, we invert the target X.
        const invertedTargetX = PROCESS_WIDTH - targetX;
        
        lilaHeadX += (invertedTargetX - lilaHeadX) * 0.15; // Smooth follow
        lilaHeadY += (targetY - lilaHeadY) * 0.15;
    }

    // Put processed pixels back
    ctx.putImageData(imageData, 0, 0);

    // Lila Eye Effect
    updateAndDrawEyes(ctx);

    retroCameraAnimationId = requestAnimationFrame(processLilaFrame);
}

function captureLilaImage() {
    const captureBtn = document.getElementById('captureBtn');
    
    // Check if we are currently running the camera loop (Live Mode)
    if (retroCameraAnimationId) {
        // === CAPTURE MODE ===
        // Stop the processing loop to freeze the current frame
        cancelAnimationFrame(retroCameraAnimationId);
        retroCameraAnimationId = null;
        
        // Update UI to show "RETAKE" state
        if (captureBtn) {
            captureBtn.innerText = "RETAKE";
            captureBtn.style.background = "rgba(200, 50, 50, 0.8)"; // Brighter red for active state
            captureBtn.style.color = "#fff";
        }
        
    } else {
        // === RETAKE MODE ===
        // Resume the processing loop
        processLilaFrame();
        
        // Update UI back to "CAPTURE" state
        if (captureBtn) {
            captureBtn.innerText = "CAPTURE";
            captureBtn.style.background = "rgba(80, 20, 20, 0.6)"; // Back to normal
            captureBtn.style.color = "var(--lila-red)";
        }
    }
}

// 更新用户档案类型（根据兴趣分类）
function updateProfileType(categories) {
    const profileTypeEl = document.getElementById('uc-profile-type');
    if (!profileTypeEl) return;
    
    if (!categories || categories.length === 0) {
        profileTypeEl.textContent = 'ANALYZING...';
        return;
    }
    
    // 根据最感兴趣的分类定义用户类型
    const profileTypes = {
        'subway_ghost': 'URBAN EXPLORER',
        'abandoned_building': 'RUIN HUNTER',
        'cursed_object': 'ARTIFACT SEEKER',
        'missing_person': 'INVESTIGATOR',
        'time_anomaly': 'REALITY BENDER',
        'campus_horror': 'STUDENT WITNESS',
        'rental_mystery': 'TENANT SURVIVOR',
        'night_taxi': 'NIGHT WANDERER',
        'hospital_ward': 'MEDICAL ANOMALY',
        'elevator_incident': 'VERTICAL TRAVELER',
        'mirror_realm': 'REFLECTION WALKER',
        'apartment_mystery': 'APARTMENT OBSERVER'
    };
    
    const topCategory = categories[0].category;
    const profileType = profileTypes[topCategory] || 'UNKNOWN ENTITY';
    
    profileTypeEl.textContent = profileType;
}

// 获取分类标签
function getCategoryLabel(category) {
    const categoryLabels = {
        'subway_ghost': 'SUBWAY GHOST',
        'abandoned_building': 'ABANDONED BUILDING',
        'cursed_object': 'CURSED OBJECT',
        'missing_person': 'MISSING PERSON',
        'time_anomaly': 'TIME ANOMALY',
        'campus_horror': 'CAMPUS HORROR',
        'rental_mystery': 'RENTAL MYSTERY',
        'night_taxi': 'NIGHT TAXI',
        'hospital_ward': 'HOSPITAL WARD',
        'elevator_incident': 'ELEVATOR INCIDENT',
        'mirror_realm': 'MIRROR REALM',
        'apartment_mystery': 'APARTMENT MYSTERY'
    };
    return categoryLabels[category] || category.toUpperCase();
}

// 追踪用户点击的分类
async function trackCategoryClick(category) {
    if (!token || !category) return;
    
    try {
        await fetch(API_BASE + '/track-category-click', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ category: category })
        });
    } catch (error) {
        console.error('Failed to track category click:', error);
    }
}

// 通知中心逻辑在文件下方的异步实现处定义（避免重复）

async function loadStories(silent = false, page = 1) {
    try {
        const response = await fetch(`${API_BASE}/stories?page=${page}&per_page=8`);
        const data = await response.json();
        
        allStories = data.stories;
        pagination = data.pagination;
        currentPage = pagination.page;
        totalPages = pagination.pages;
        
        // 检测新故事
        if (!silent && lastStoryCount > 0 && pagination.total > lastStoryCount) {
            const diff = pagination.total - lastStoryCount;
            showToast(`🎃 有 ${diff} 个新故事发布了！`, 'info');
        }
        
        lastStoryCount = pagination.total;
        
        // 更新统计信息
        const countEl = document.getElementById('story-count');
        if (countEl) countEl.textContent = pagination.total;
        
        // 计算总评论数（所有故事的评论数之和）
        const totalComments = data.stories.reduce((sum, story) => sum + (story.comments_count || 0), 0);
        const commentCountEl = document.getElementById('comment-count');
        if (commentCountEl) {
            // 添加一些随机的基础评论数，使其看起来更真实（300-600之间）
            const baseComments = Math.floor(Math.random() * 300) + 300;
            commentCountEl.textContent = totalComments + baseComments;
        }
        
        // 模拟在线用户数（小幅波动，避免完全随机）
        const userCountEl = document.getElementById('user-count');
        if (userCountEl) {
            // 每次刷新时，在线用户数有±2的小幅波动
            const fluctuation = Math.floor(Math.random() * 5) - 2; // -2到+2
            cachedOnlineUsers = Math.max(3, Math.min(15, cachedOnlineUsers + fluctuation)); // 保持在3-15范围内
            userCountEl.textContent = cachedOnlineUsers;
        }
        
        // 更新最后更新时间
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) lastUpdateEl.textContent = '刚刚';
        
        renderStories();
        renderPagination();
    } catch (error) {
        console.error('加载故事失败:', error);
        if (!silent) showToast('加载故事失败', 'error');
    }
}

async function checkNotifications() {
    if (!token || !currentUser) return;
    
    try {
        const res = await fetch(API_BASE + '/notifications', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (res.ok) {
            const notifications = await res.json();
            const unread = notifications.filter(n => !n.is_read);

            // 更新菜单红点
            updateNotificationBadge(unread.length);

            if (unread.length > lastNotificationCheck) {
                // 有新通知 - 仅对新出现的显示弹窗（可点击跳转）
                const newCount = unread.length - lastNotificationCheck;
                const newOnes = unread.slice(0, newCount);
                newOnes.forEach(n => {
                    showNotificationPopup(n);
                });
            }

            lastNotificationCheck = unread.length;
        }
    } catch (error) {
        console.error('检查通知失败:', error);
    }
}

// 更新菜单栏红点
function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;
    if (count && count > 0) {
        badge.style.display = 'inline-block';
        badge.textContent = count > 99 ? '99+' : String(count);
    } else {
        badge.style.display = 'none';
    }
}

// 可点击的通知弹窗（会在点击时跳转并标记为已读）
function showNotificationPopup(n) {
    const id = 'notif-popup-' + Date.now();
    const el = document.createElement('div');
    el.id = id;
    el.className = 'notification-popup';
    el.style.position = 'fixed';
    el.style.top = '20px';
    el.style.right = '20px';
    el.style.background = 'linear-gradient(180deg, #6699ff, #3366ff)';
    el.style.color = '#fff';
    el.style.padding = '10px 14px';
    el.style.border = '2px outset #999';
    el.style.fontSize = '12px';
    el.style.zIndex = 2500;
    el.style.boxShadow = '2px 2px 8px rgba(0,0,0,0.35)';
    el.style.borderRadius = '4px';
    el.innerHTML = '<div style="font-weight:bold; margin-bottom:4px;">通知</div><div style="max-width:300px;">' + escapeHtml(n.content) + '</div>';

    el.addEventListener('click', () => {
        openNotificationTarget(n.story_id, n.comment_id, n.id);
        // remove immediately
        el.remove();
    });

    document.body.appendChild(el);

    // 自动移除（稍长些时间让用户点击）
    setTimeout(() => {
        const e = document.getElementById(id);
        if (e) e.remove();
    }, 8000);
}

// 打开通知目标：展示帖文、滚动到评论并高亮，标记通知已读
async function openNotificationTarget(storyId, commentId, notificationId) {
    try {
        await showStoryDetail(storyId);

        // 等待短暂时间确保 DOM 渲染完成
        await new Promise(r => setTimeout(r, 180));

        if (commentId) {
            const el = document.getElementById('comment-' + commentId);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.classList.add('comment-highlight');
                setTimeout(() => el.classList.remove('comment-highlight'), 1800);
            }
        }

        // 标记为已读（单条）并更新 badge
        await markNotificationsRead([notificationId]);
    } catch (err) {
        console.error('打开通知目标失败:', err);
    }
}

// 向后端标记通知为已读；传入通知 id 列表
async function markNotificationsRead(ids) {
    if (!ids || ids.length === 0) return;
    try {
        const res = await fetch(API_BASE + '/notifications/read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ ids: ids })
        });
        if (res.ok) {
            // 刷新通知计数
            const data = await res.json();
            // 拉取最新未读数并显示
            checkNotifications();
        }
    } catch (err) {
        console.error('标记通知已读失败:', err);
    }
}

// 显示通知中心 – 列出最近通知并支持点击跳转/标记已读
async function showNotificationCenter() {
    if (!token || !currentUser) {
        showToast('请先登录以查看通知', 'warning');
        return;
    }

    try {
        const res = await fetch(API_BASE + '/notifications', { headers: { 'Authorization': 'Bearer ' + token } });
        if (!res.ok) return showToast('无法加载通知', 'error');
        const notifications = await res.json();

        // cache notifications for client-side filtering/pagination
        notificationsCache = notifications || [];
        notifCurrentPage = 1;

        // render UI controls and list
        const list = document.getElementById('notification-list');
        const paginationEl = document.getElementById('notification-pagination');
        list.innerHTML = '';
        if (!notificationsCache || notificationsCache.length === 0) {
            list.innerHTML = '<div style="color:#ccc;">暂无通知</div>';
            if (paginationEl) paginationEl.innerHTML = '';
        } else {
            renderNotificationListPage();
            renderNotificationPagination();
        }

        const center = document.getElementById('notification-center');
        if (center) {
            // position the center under the menubar notifications icon
            try {
                const icon = document.getElementById('menu-notifications');
                if (icon) {
                    // make visible off-screen to measure width if needed
                    center.style.display = 'block';
                    center.style.visibility = 'hidden';

                    // measure center width
                    const cw = center.offsetWidth || 360;
                    const rect = icon.getBoundingClientRect();
                    // prefer aligning center horizontally with the icon center
                    let left = Math.round(rect.left + rect.width / 2 - cw / 2);
                    const padding = 8;
                    // clamp to viewport
                    if (left < padding) left = padding;
                    if (left + cw + padding > window.innerWidth) left = Math.max(padding, window.innerWidth - cw - padding);

                    const top = Math.round(rect.bottom + 6);
                    center.style.left = left + 'px';
                    center.style.top = top + 'px';
                    center.style.visibility = 'visible';
                } else {
                    // fallback: show at top-right
                    center.style.display = 'block';
                    center.style.left = '';
                    center.style.top = '70px';
                }
            } catch (err) {
                console.error('定位通知中心失败:', err);
                center.style.display = 'block';
            }
        }

        // wire click-outside-to-close for notification center
        if (!window._notifCenterOutsideHandlerAdded) {
            window._notifCenterOutsideHandler = (e) => {
                const centerEl = document.getElementById('notification-center');
                const icon = document.getElementById('menu-notifications');
                if (!centerEl || centerEl.style.display !== 'block') return;
                // do nothing when clicking inside center or on the notifications menu icon
                if (centerEl.contains(e.target) || (icon && icon.contains(e.target))) return;
                centerEl.style.display = 'none';
            };
            window.addEventListener('click', window._notifCenterOutsideHandler);
            window._notifCenterOutsideHandlerAdded = true;
        }

        // wire custom filter dropdown and mark-all button
        const filterBtn = document.getElementById('notification-filter-button');
        const filterMenu = document.getElementById('notification-filter-menu');
        if (filterBtn && filterMenu) {
            // toggle menu
            filterBtn.onclick = (e) => {
                e.stopPropagation();
                filterMenu.style.display = (filterMenu.style.display === 'block') ? 'none' : 'block';
            };

            // option clicks
            filterMenu.querySelectorAll('.notif-filter-option').forEach(opt => {
                opt.onclick = (ev) => {
                    ev.stopPropagation();
                    const v = opt.dataset.value;
                    filterBtn.dataset.value = v;
                    // update label text
                    filterBtn.firstChild && (filterBtn.firstChild.textContent = opt.textContent);
                    // fallback: update innerText (button contains text and arrow span)
                    filterBtn.innerHTML = opt.textContent + ' <span style="opacity:0.8; font-size:12px;">▾</span>';
                    filterMenu.style.display = 'none';
                    notifCurrentPage = 1;
                    renderNotificationListPage();
                    renderNotificationPagination();
                };
            });

            // click outside to close
            if (!window._notifFilterOutsideHandlerAdded) {
                window.addEventListener('click', () => {
                    const m = document.getElementById('notification-filter-menu');
                    if (m) m.style.display = 'none';
                });
                window._notifFilterOutsideHandlerAdded = true;
            }
        }

        const markAllBtn = document.getElementById('notification-markall');
        if (markAllBtn) markAllBtn.onclick = async () => {
            await markAllNotificationsRead();
            // refresh view
            const res2 = await fetch(API_BASE + '/notifications', { headers: { 'Authorization': 'Bearer ' + token } });
            if (res2.ok) {
                notificationsCache = await res2.json();
                notifCurrentPage = 1;
                renderNotificationListPage();
                renderNotificationPagination();
            }
        };

    } catch (err) {
        console.error('打开通知中心失败:', err);
        showToast('打开通知中心失败', 'error');
    }
}

function getFilteredNotifications() {
    const filterBtn = document.getElementById('notification-filter-button');
    const mode = (filterBtn && filterBtn.dataset && filterBtn.dataset.value) ? filterBtn.dataset.value : 'all';
    if (!notificationsCache || notificationsCache.length === 0) return [];
    
    // 按通知分类过滤（全部/评论/证据）
    if (mode === 'all') return notificationsCache.slice();
    
    // 按 notification_category 过滤
    return notificationsCache.filter(n => {
        const category = n.notification_category || 'comment';
        return category === mode;
    });
}

function renderNotificationListPage() {
    const list = document.getElementById('notification-list');
    if (!list) return;
    const filtered = getFilteredNotifications();
    if (!filtered || filtered.length === 0) {
        list.innerHTML = '<div style="color:#ccc;">暂无通知</div>';
        return;
    }

    const pages = Math.max(1, Math.ceil(filtered.length / notifPerPage));
    if (notifCurrentPage > pages) notifCurrentPage = pages;
    const start = (notifCurrentPage - 1) * notifPerPage;
    const pageItems = filtered.slice(start, start + notifPerPage);

    list.innerHTML = '';
    pageItems.forEach(n => {
        const item = document.createElement('div');
        item.style.padding = '8px';
        item.style.border = '1px solid rgba(255,255,255,0.04)';
        item.style.background = n.is_read ? 'transparent' : 'linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01))';
        item.style.cursor = 'pointer';

        // 获取通知分类标签
        const category = n.notification_category || 'comment';
        let categoryLabel = '📝 评论';
        let categoryColor = '#88ccff';
        if (category === 'evidence') {
            categoryLabel = '🎬 证据';
            categoryColor = '#ffaa66';
        }

        const contentHtml = '<div style="display:flex; justify-content:space-between; align-items:start; gap:8px;">' +
            '<div style="flex:1;">' +
            '<div style="font-size:12px; color:#fff;">' + escapeHtml(n.content) + '</div>' +
            '<div style="font-size:10px; color:#ccc; margin-top:6px;">' + formatDate(n.created_at) + '</div>' +
            '</div>' +
            '<div style="font-size:9px; background:' + categoryColor + '20; color:' + categoryColor + '; padding:2px 6px; border-radius:3px; white-space:nowrap;">' + categoryLabel + '</div>' +
            '</div>';
        item.innerHTML = contentHtml;

        item.addEventListener('click', async () => {
            await openNotificationTarget(n.story_id, n.comment_id, n.id);
            // mark locally as read
            n.is_read = true;
            item.style.background = 'transparent';
        });

        list.appendChild(item);
    });
}

function renderNotificationPagination() {
    const paginationEl = document.getElementById('notification-pagination');
    if (!paginationEl) return;
    const filtered = getFilteredNotifications();
    const total = filtered.length;
    const pages = Math.max(1, Math.ceil(total / notifPerPage));

    if (pages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }

    // Clear existing content
    paginationEl.innerHTML = '';

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'macos3-button';
    prevBtn.textContent = '◀';
    if (notifCurrentPage <= 1) {
        prevBtn.disabled = true;
        prevBtn.style.opacity = '0.5';
    } else {
        prevBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            changeNotifPage(notifCurrentPage - 1);
        });
    }

    // Page info
    const pageInfo = document.createElement('span');
    pageInfo.style.color = '#fff';
    pageInfo.style.margin = '0 8px';
    pageInfo.textContent = '第 ' + notifCurrentPage + ' / ' + pages + ' 页';

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'macos3-button';
    nextBtn.textContent = '▶';
    if (notifCurrentPage >= pages) {
        nextBtn.disabled = true;
        nextBtn.style.opacity = '0.5';
    } else {
        nextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            changeNotifPage(notifCurrentPage + 1);
        });
    }

    paginationEl.appendChild(prevBtn);
    paginationEl.appendChild(pageInfo);
    paginationEl.appendChild(nextBtn);
}

// global helper for pagination buttons
function changeNotifPage(p) {
    notifCurrentPage = p;
    renderNotificationListPage();
    renderNotificationPagination();
}

async function markAllNotificationsRead() {
    if (!notificationsCache || notificationsCache.length === 0) return;
    const unread = notificationsCache.filter(n => !n.is_read).map(n => n.id);
    if (unread.length === 0) return;
    await markNotificationsRead(unread);
    // mark local cache
    notificationsCache.forEach(n => { n.is_read = true; });
    updateNotificationBadge(0);
}

function renderStories() {
    const container = document.getElementById('stories-container');
    if (!container) return;
    
    const filtered = currentCategory === 'all' ? allStories : allStories.filter(s => s.category === currentCategory);
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="loading-text">暂无档案</div>';
        return;
    }
    
    container.innerHTML = filtered.map(story => {
        return '<div class="story-item" onclick="showStoryDetail(' + story.id + ')">' +
            '<div class="story-title">👻 ' + escapeHtml(story.title) + '</div>' +
            '<div class="story-meta">' +
            '<span>👁️ ' + story.views + '</span>' +
            '<span>💬 ' + story.comments_count + '</span>' +
            '<span>📸 ' + story.evidence_count + '</span>' +
            '</div>' +
            '<div class="story-preview">' + escapeHtml(story.content.substring(0, 80)) + '</div>' +
            '<div class="story-footer">' +
            '<span>' + (story.ai_persona || '🤖 AI') + '</span>' +
            '<span>' + formatDate(story.created_at) + '</span>' +
            '</div>' +
            '</div>';
    }).join('');
}

function renderPagination() {
    const container = document.getElementById('pagination-container');
    if (!container || !pagination) return;
    
    if (pagination.pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<div class="pagination">';
    
    // 上一页按钮
    if (pagination.has_prev) {
        html += `<button class="macos3-button" onclick="changePage(${pagination.prev_page})">◀ 上一页</button>`;
    } else {
        html += `<button class="macos3-button" disabled style="opacity: 0.5;">◀ 上一页</button>`;
    }
    
    // 页码信息
    html += `<span style="margin: 0 15px; color: #6b0080; font-weight: bold;">第 ${pagination.page} / ${pagination.pages} 页</span>`;
    
    // 下一页按钮
    if (pagination.has_next) {
        html += `<button class="macos3-button" onclick="changePage(${pagination.next_page})">下一页 ▶</button>`;
    } else {
        html += `<button class="macos3-button" disabled style="opacity: 0.5;">下一页 ▶</button>`;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function changePage(page) {
    currentPage = page;
    loadStories(false, page);
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function showStoryDetail(storyId) {
    try {
        // 保存当前故事ID到全局变量
        window.currentStoryId = storyId;
        
        const response = await fetch(API_BASE + '/stories/' + storyId);
        const story = await response.json();
        
        // 追踪用户点击的分类
        if (currentUser && story.category && token) {
            trackCategoryClick(story.category);
        }
        
        // 调试信息
        console.log('📖 故事详情加载:', story.title);
        console.log('📸 证据数量:', story.evidence ? story.evidence.length : 0);
        if (story.evidence && story.evidence.length > 0) {
            console.log('📸 证据列表:', story.evidence);
        }
        
        const titleEl = document.getElementById('story-title');
        if (titleEl) titleEl.textContent = story.title;
        
        let html = '<div style="border-bottom: 2px dashed #6b0080; padding-bottom: 10px; margin-bottom: 10px;">' +
            '<div style="font-weight: bold; color: #6b0080;">作者: ' + (story.ai_persona || 'AI楼主') + ' 👻</div>' +
            '<div style="font-size: 10px; color: #666; margin: 5px 0;">' + formatDate(story.created_at) + ' | 浏览: ' + story.views + '</div>';
        
        // 显示封贴说明
        if (story.current_state === 'locked' || (story.title && story.title.includes('【已封贴】'))) {
            html += '<div style="border-top: 1px solid #999; border-bottom: 1px solid #999; padding: 8px 0; margin: 10px 0; text-align: center; color: #666; font-size: 10px;">' +
                '本贴已超过1年无人回复，已封锁禁止回复' +
                '</div>';
        }
        
        html += '<div id="story-original-content" style="white-space: pre-wrap; line-height: 1.6; word-break: break-all; font-size: 11px;">' + escapeHtml(story.content) + '</div>' +
            '</div>';
        
        if (story.evidence && story.evidence.length > 0) {
            console.log('✅ 开始渲染证据区域...');
            html += '<div class="evidence-section"><div class="evidence-title">📸 证据</div><div class="evidence-grid">';
            story.evidence.forEach(e => {
                html += '<div class="evidence-item">';
                // Check both 'type' and 'evidence_type' fields, default to 'image' if not specified
                const evidenceType = e.type || e.evidence_type || 'image';
                if (evidenceType === 'image') {
                    html += '<img src="' + e.file_path + '" style="width:100%; aspect-ratio: 1/1; object-fit: contain; background-color: #000; border: 1px solid #666;">';
                } else if (evidenceType === 'audio') {
                    html += '<audio controls style="width:100%; height:30px;"><source src="' + e.file_path + '"></audio>';
                }
                html += '<div class="evidence-desc">' + escapeHtml(e.description) + '</div></div>';
            });
            html += '</div></div>';
        }
        
        html += '<div class="comment-section"><h3 style="color: #6b0080; border-bottom: 2px dashed #6b0080; padding-bottom: 8px;">💬 评论</h3>';
        
        if (story.comments && story.comments.length > 0) {
            // 构建评论树结构
            const commentMap = {};
            const topLevelComments = [];
            
            // 第一遍：创建所有评论的映射
            story.comments.forEach(c => {
                commentMap[c.id] = {...c, replies: []};
            });
            
            // 第二遍：构建树结构
            story.comments.forEach(c => {
                if (c.parent_id && commentMap[c.parent_id]) {
                    commentMap[c.parent_id].replies.push(commentMap[c.id]);
                } else {
                    topLevelComments.push(commentMap[c.id]);
                }
            });
            
            // 渲染评论树
            const renderComment = (comment, isReply = false) => {
                const indent = isReply ? 'margin-left: 20px; border-left: 2px solid #ccc; padding-left: 10px;' : '';
                let commentHtml = '<div id="comment-' + comment.id + '" class="comment-item" style="' + indent + '">' +
                    '<div class="comment-author">' + escapeHtml(comment.author.username) + ' ' + comment.author.avatar + '</div>' +
                    '<div class="comment-text">' + escapeHtml(comment.content) + '</div>' +
                    '<div class="comment-time">' + formatDate(comment.created_at);
                
                // 添加回复按钮（如果未封贴且用户已登录）
                const isLocked = story.current_state === 'locked' || (story.title && story.title.includes('【已封贴】'));
                if (!isLocked && currentUser) {
                    commentHtml += ' <a href="#" onclick="showReplyBox(' + comment.id + ', \'' + escapeHtml(comment.author.username) + '\'); return false;" style="color: #6b0080; font-size: 10px; margin-left: 10px;">回复</a>';
                }
                
                commentHtml += '</div>' +
                    '<div id="reply-box-' + comment.id + '" style="display: none; margin-top: 8px;"></div>' +
                    '</div>';
                
                // 渲染子回复
                if (comment.replies && comment.replies.length > 0) {
                    comment.replies.forEach(reply => {
                        commentHtml += renderComment(reply, true);
                    });
                }
                
                return commentHtml;
            };
            
            topLevelComments.forEach(c => {
                html += renderComment(c);
            });
        }
        
        // 检查是否封贴
        const isLocked = story.current_state === 'locked' || (story.title && story.title.includes('【已封贴】'));
        
        if (isLocked) {
            html += '<div style="text-align: center; color: #999; padding: 20px; margin-top: 12px; border-top: 1px dotted #999;">' +
                '<div style="font-size: 12px;">🔒 本帖已封锁，无法继续评论</div>' +
                '</div>';
        } else if (currentUser) {
            html += '<div style="margin-top: 12px; padding-top: 12px; border-top: 1px dotted #999;">' +
                '<form onsubmit="submitComment(event, ' + storyId + ')">' +
                '<textarea id="comment-text" placeholder="你的看法..." style="width:100%; height:60px; padding:8px; border:2px inset #999; font-size:11px; resize:none; font-family: MS Sans Serif, Arial;"></textarea>' +
                '<button type="submit" class="macos3-button" style="margin-top:8px; width:100%;">发 表</button>' +
                '</form></div>';
        } else {
            html += '<p style="text-align:center; color:#666; margin-top:12px;"><a href="#" onclick="showLoginForm(); return false;" style="color:#6b0080;">登录</a> 后发表评论</p>';
        }
        
        html += '</div>';
        const contentEl = document.getElementById('story-content');
        if (contentEl) {
            contentEl.innerHTML = html;
            console.log('✅ 故事内容已渲染到模态框');
        }
        
        const storyModal = document.getElementById('story-modal');
        if (storyModal) {
            storyModal.style.display = 'flex';
            console.log('✅ 故事模态框已打开');
            // 滚动到顶部
            contentEl.scrollTop = 0;
        }
    } catch (error) {
        console.error('加载故事详情失败:', error);
        showToast('加载失败', 'error');
    }
}

function showReplyBox(commentId, authorName) {
    // 隐藏其他回复框
    document.querySelectorAll('[id^="reply-box-"]').forEach(box => {
        if (box.id !== 'reply-box-' + commentId) {
            box.style.display = 'none';
        }
    });
    
    const replyBox = document.getElementById('reply-box-' + commentId);
    if (!replyBox) return;
    
    // 切换显示/隐藏
    if (replyBox.style.display === 'none' || !replyBox.innerHTML) {
        replyBox.innerHTML = '<form onsubmit="submitReply(event, ' + commentId + ')" style="margin-top: 8px;">' +
            '<div style="color: #666; font-size: 10px; margin-bottom: 4px;">回复 @' + escapeHtml(authorName) + ':</div>' +
            '<textarea id="reply-text-' + commentId + '" placeholder="输入回复..." style="width:100%; height:50px; padding:6px; border:2px inset #999; font-size:10px; resize:none; font-family: MS Sans Serif, Arial;"></textarea>' +
            '<div style="margin-top: 6px;">' +
            '<button type="submit" class="macos3-button" style="font-size: 10px; padding: 4px 12px;">发送</button> ' +
            '<button type="button" onclick="hideReplyBox(' + commentId + ')" class="macos3-button" style="font-size: 10px; padding: 4px 12px;">取消</button>' +
            '</div></form>';
        replyBox.style.display = 'block';
        document.getElementById('reply-text-' + commentId).focus();
    } else {
        replyBox.style.display = 'none';
    }
}

function hideReplyBox(commentId) {
    const replyBox = document.getElementById('reply-box-' + commentId);
    if (replyBox) {
        replyBox.style.display = 'none';
    }
}

async function submitReply(event, parentCommentId) {
    event.preventDefault();
    if (!currentUser) {
        showToast('请先登录', 'warning');
        return;
    }
    
    const replyText = document.getElementById('reply-text-' + parentCommentId);
    const content = replyText ? replyText.value.trim() : '';
    
    if (!content) {
        showToast('不能为空', 'warning');
        return;
    }
    
    // 从URL或当前打开的故事中获取storyId
    const storyModal = document.getElementById('story-modal');
    const storyTitle = document.getElementById('story-title');
    if (!storyModal || storyModal.style.display === 'none') {
        showToast('错误：无法获取故事ID', 'error');
        return;
    }
    
    // 从comment元素中获取storyId（通过API重新获取）
    const commentElement = document.getElementById('comment-' + parentCommentId);
    if (!commentElement) {
        showToast('错误：评论不存在', 'error');
        return;
    }
    
    // 从当前打开的故事详情中获取storyId
    const storyId = window.currentStoryId;
    if (!storyId) {
        showToast('错误：无法获取故事ID', 'error');
        return;
    }
    
    try {
        const res = await fetch(API_BASE + '/stories/' + storyId + '/comments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ 
                content: content,
                parent_id: parentCommentId
            })
        });
        
        if (res.ok) {
            showToast('已回复', 'success');
            setTimeout(() => showStoryDetail(storyId), 1500);
        } else {
            const err = await res.json();
            showToast(err.error || '回复失败', 'error');
        }
    } catch (error) {
        console.error('发表回复失败:', error);
        showToast('错误', 'error');
    }
}

async function submitComment(event, storyId) {
    event.preventDefault();
    if (!currentUser) {
        showToast('请先登录', 'warning');
        return;
    }
    
    const commentText = document.getElementById('comment-text');
    const content = commentText ? commentText.value.trim() : '';
    
    if (!content) {
        showToast('不能为空', 'warning');
        return;
    }
    
    try {
        const res = await fetch(API_BASE + '/stories/' + storyId + '/comments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ content: content })
        });
        
        if (res.ok) {
            showToast('已发表', 'success');
            setTimeout(() => showStoryDetail(storyId), 1500);
        } else {
            const err = await res.json();
            showToast(err.error || '发表失败', 'error');
        }
    } catch (error) {
        console.error('发表评论失败:', error);
        showToast('错误', 'error');
    }
}

function showLoginForm() {
    const titleEl = document.getElementById('modal-title');
    const emailGroup = document.getElementById('email-group');
    const toggleBtn = document.getElementById('toggle-auth');
    const authForm = document.getElementById('auth-form');
    
    if (titleEl) titleEl.textContent = '登 录';
    if (emailGroup) emailGroup.style.display = 'none';
    if (toggleBtn) toggleBtn.dataset.mode = 'register';
    if (authForm) authForm.reset();
    
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
}

function showRegisterForm() {
    const titleEl = document.getElementById('modal-title');
    const emailGroup = document.getElementById('email-group');
    const toggleBtn = document.getElementById('toggle-auth');
    const authForm = document.getElementById('auth-form');
    
    if (titleEl) titleEl.textContent = '注 册';
    if (emailGroup) emailGroup.style.display = 'block';
    if (toggleBtn) toggleBtn.dataset.mode = 'login';
    if (authForm) authForm.reset();
    
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
}

function toggleAuthForm() {
    const toggleBtn = document.getElementById('toggle-auth');
    if (!toggleBtn) return;
    
    if (toggleBtn.dataset.mode === 'register') {
        showRegisterForm();
    } else {
        showLoginForm();
    }
}

async function handleAuthSubmit(event) {
    event.preventDefault();
    
    const usernameEl = document.getElementById('username');
    const passwordEl = document.getElementById('password');
    const emailEl = document.getElementById('email');
    const emailGroup = document.getElementById('email-group');
    
    const username = usernameEl ? usernameEl.value.trim() : '';
    const password = passwordEl ? passwordEl.value.trim() : '';
    const isReg = emailGroup && emailGroup.style.display !== 'none';
    
    if (!username || !password) {
        showToast('用户名和密码必填', 'warning');
        return;
    }
    
    const data = { username: username, password: password };
    if (isReg) {
        const email = emailEl ? emailEl.value.trim() : '';
        if (!email) {
            showToast('邮箱必填', 'warning');
            return;
        }
        data.email = email;
    }
    
    try {
        const endpoint = isReg ? 'register' : 'login';
        const res = await fetch(API_BASE + '/' + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            const result = await res.json();
            token = result.token;
            currentUser = result.user;
            localStorage.setItem('token', token);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            updateAuthUI();
            closeAuthModal();
            showToast((isReg ? '注册' : '登录') + '成功', 'success');
            
            // 登录成功后立即检查通知
            checkNotifications();
        } else {
            const err = await res.json();
            showToast(err.error || '错误', 'error');
        }
    } catch (error) {
        console.error('认证失败:', error);
        showToast('错误', 'error');
    }
}

function updateAuthUI() {
    const guestView = document.getElementById('guest-view');
    const userView = document.getElementById('user-view');
    
    if (currentUser) {
        if (guestView) guestView.style.display = 'none';
        if (userView) userView.style.display = 'block';
        
        const avatarEl = document.getElementById('user-avatar');
        const nameEl = document.getElementById('user-name');
        
        if (avatarEl) avatarEl.textContent = currentUser.avatar || '👻';
        if (nameEl) nameEl.textContent = currentUser.username;
    } else {
        if (guestView) guestView.style.display = 'block';
        if (userView) userView.style.display = 'none';
    }
}

function logout() {
    currentUser = null;
    token = null;
    localStorage.removeItem('token');
    localStorage.removeItem('currentUser');
    updateAuthUI();
    showToast('已登出', 'success');
}

async function verifyToken() {
    if (!token) return;
    
    try {
        const res = await fetch(API_BASE + '/notifications', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (res.ok) {
            const userStr = localStorage.getItem('currentUser');
            if (userStr) {
                currentUser = JSON.parse(userStr);
                updateAuthUI();
            }
        } else {
            localStorage.removeItem('token');
            token = null;
        }
    } catch (error) {
        console.error('验证失败:', error);
    }
}

function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
}

function closeStoryModal() {
    const modal = document.getElementById('story-modal');
    if (modal) modal.style.display = 'none';
}

function formatDate(d) {
    return new Date(d).toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(t) {
    const div = document.createElement('div');
    div.textContent = t;
    return div.innerHTML;
}

function showToast(msg, type) {
    type = type || 'info';
    const id = 'toast-' + Date.now();
    
    const bgMap = {
        'success': 'linear-gradient(180deg, #66cc66, #44aa44)',
        'error': 'linear-gradient(180deg, #ff6666, #cc3333)',
        'warning': 'linear-gradient(180deg, #ffcc66, #ff9933)',
        'info': 'linear-gradient(180deg, #6699ff, #3366ff)'
    };
    
    const bg = bgMap[type] || bgMap['info'];
    
    document.body.insertAdjacentHTML('beforeend',
        '<div id="' + id + '" style="position: fixed; top: 20px; right: 20px; background: ' + bg + '; color: white; padding: 10px 14px; border: 2px outset #999; font-size: 11px; z-index: 2000; box-shadow: 2px 2px 6px rgba(0,0,0,0.3); border-radius: 2px;">' +
        escapeHtml(msg) +
        '</div>'
    );
    
    setTimeout(() => {
        const el = document.getElementById(id);
        if (el) el.remove();
    }, 3000);
}

function updateClock() {
    const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    const items = document.querySelectorAll('.menu-item');
    if (items.length > 0) items[0].textContent = now;
}

// ============================================
// Lila Eye & Mouth Effect Logic
// ============================================
let lilaEyes = [];
let lilaMouths = [];
const MAX_EYES = 12;
const MAX_MOUTHS = 2;
let lilaHeadX = PROCESS_WIDTH / 2;
let lilaHeadY = PROCESS_HEIGHT / 2;

function updateAndDrawEyes(ctx) {
    // === EYES ===
    // Spawn logic - Increased rate and count
    if (lilaEyes.length < MAX_EYES && Math.random() < 0.15) {
        // Try to spawn multiple eyes at once
        const spawnCount = Math.floor(Math.random() * 2) + 1;
        
        for(let k=0; k<spawnCount; k++) {
            if (lilaEyes.length >= MAX_EYES) break;
            
            // Spawn relative to head position
            // Range: +/- 40 pixels from center
            const offsetX = (Math.random() - 0.5) * 80;
            const offsetY = (Math.random() - 0.5) * 60 - 15; // Slightly higher bias (eyes area)

            lilaEyes.push({
                relX: offsetX,
                relY: offsetY,
                type: Math.random() > 0.7 ? 'large' : 'small',
                life: 60 + Math.random() * 60,
                blinkOffset: Math.random() * 1000
            });
        }
    }

    // Draw Eyes
    for (let i = lilaEyes.length - 1; i >= 0; i--) {
        let eye = lilaEyes[i];
        eye.life--;
        
        if (eye.life <= 0) {
            lilaEyes.splice(i, 1);
            continue;
        }

        // Blink
        const now = Date.now();
        const blink = Math.sin((now + eye.blinkOffset) / 200) > 0.9;

        if (!blink) {
            // Calculate absolute position based on current head position
            const drawX = lilaHeadX + eye.relX;
            const drawY = lilaHeadY + eye.relY;
            drawPixelEye(ctx, drawX, drawY, eye.type);
        }
    }

    // === MOUTHS ===
    // Spawn logic - Lower rate
    if (lilaMouths.length < MAX_MOUTHS && Math.random() < 0.05) {
        // Spawn relative to head position (Lower half)
        // Shifted slightly left (-5) to center better
        const offsetX = (Math.random() - 0.5) * 20 - 5; 
        const offsetY = 35 + Math.random() * 20;    // Below center (mouth area) - Lowered

        lilaMouths.push({
            relX: offsetX,
            relY: offsetY,
            life: 80 + Math.random() * 60
        });
    }

    // Draw Mouths
    for (let i = lilaMouths.length - 1; i >= 0; i--) {
        let mouth = lilaMouths[i];
        mouth.life--;
        
        if (mouth.life <= 0) {
            lilaMouths.splice(i, 1);
            continue;
        }

        const drawX = lilaHeadX + mouth.relX;
        const drawY = lilaHeadY + mouth.relY;
        drawPixelMouth(ctx, drawX, drawY);
    }
}

function drawPixelMouth(ctx, cx, cy) {
    const C_WHITE = '#e0e0e0';
    const C_BLACK = '#110505';
    
    // 2 = Black (Outline), 1 = White (Teeth), 0 = Transparent
    const map = [
        [2,0,0,0,0,0,0,0,0,0,0,0,0,0,2],
        [2,2,0,0,0,0,0,0,0,0,0,0,0,2,2],
        [2,1,2,2,2,2,2,2,2,2,2,2,2,1,2],
        [0,2,1,1,2,1,1,2,1,1,2,1,1,2,0],
        [0,2,1,1,2,1,1,2,1,1,2,1,1,2,0],
        [0,0,2,1,1,2,2,2,2,2,1,1,2,0,0],
        [0,0,0,2,2,1,1,1,1,1,2,2,0,0,0],
        [0,0,0,0,0,2,2,2,2,2,0,0,0,0,0]
    ];

    const h = map.length;
    const w = map[0].length;
    const startX = Math.floor(cx - w/2);
    const startY = Math.floor(cy - h/2);

    for(let y=0; y<h; y++) {
        for(let x=0; x<w; x++) {
            const val = map[y][x];
            if(val === 0) continue;
            ctx.fillStyle = val === 1 ? C_WHITE : C_BLACK;
            ctx.fillRect(startX + x, startY + y, 1, 1);
        }
    }
}

function drawPixelEye(ctx, cx, cy, type) {
    const C_WHITE = '#e0e0e0';
    const C_RED = '#ff3333';
    const C_BLACK = '#110505';
    
    let map = [];
    
    if (type === 'small') {
        map = [
            [0,0,1,1,1,0,0],
            [0,1,2,3,2,1,0],
            [1,2,3,3,3,2,1],
            [0,1,2,3,2,1,0],
            [0,0,1,1,1,0,0]
        ];
    } else {
        map = [
            [0,0,0,1,1,1,1,1,0,0,0],
            [0,1,1,2,2,2,2,2,1,1,0],
            [1,1,2,2,3,3,3,2,2,1,1],
            [1,2,2,3,3,3,3,3,2,2,1],
            [1,1,2,2,3,3,3,2,2,1,1],
            [0,1,1,2,2,2,2,2,1,1,0],
            [0,0,0,1,1,1,1,1,0,0,0]
        ];
    }

    const h = map.length;
    const w = map[0].length;
    const startX = Math.floor(cx - w/2);
    const startY = Math.floor(cy - h/2);

    for(let y=0; y<h; y++) {
        for(let x=0; x<w; x++) {
            const val = map[y][x];
            if(val === 0) continue;
            ctx.fillStyle = val === 1 ? C_WHITE : (val === 2 ? C_RED : C_BLACK);
            ctx.fillRect(startX + x, startY + y, 1, 1);
        }
    }
}
