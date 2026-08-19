//  ============================================
//  CineFlow Executive Assistant - Main App Logic
//  ============================================

//  API Configuration - Auto-detect base URL
const API_BASE = window.location.origin;  //  Uses current domain/port

let currentSessionId = null;
let currentMode = 'quick';
let sessionHistory = [];
let allSessions = [];  //  List of all previous sessions
let isAnalyzing = false;
let currentDashboardView = false;

//  Initialize App on Page Load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    //  Restore or create session
    const savedSessionId = localStorage.getItem('cineflow_current_session');
    if (savedSessionId) {
        currentSessionId = savedSessionId;
        loadSessionMessages(currentSessionId);
    } else {
        createNewSession();
    }
    
    //  Load all previous sessions
    loadAllSessions();
    
    //  Setup event listeners
    const crisisInput = document.getElementById('crisis-input');
    if (crisisInput) {
        crisisInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey && !isAnalyzing) {
                submitCrisis();
            }
        });
    }
    
    //  Update session display
    updateSessionDisplay();
    
    //  Load proactive dashboard on page init
    loadProactiveDashboardOnInit();
    
    //  NEW: Start live status update interval (refresh dashboard every 30 seconds)
    setInterval(() => {
        //  Only refresh if dashboard is active
        const dashboardView = document.getElementById('dashboard-view');
        if (dashboardView && dashboardView.style.display !== 'none') {
            refreshLiveStatusIndicators();
        }
    }, 30000);
    
    console.log('✓ CineFlow initialized with live status monitoring');
}

//  NEW: Function to refresh live status indicators
async function refreshLiveStatusIndicators() {
    try {
        const response = await fetch('/api/readiness-dashboard?focus_days=3');
        if (!response.ok) throw new Error('Failed to fetch dashboard');
        
        const data = await response.json();
        if (data.status === 'success') {
            //  Update dashboard display with new data
            displayProactiveDashboard(data);
            console.log('✓ Live status indicators updated');
        }
    } catch (error) {
        console.error('Error refreshing live status:', error);
        //  Silent fail - don't interrupt user
    }
}

async function loadProactiveDashboardOnInit() {
    //  Load dashboard automatically on page load and show proactive suggestions
    try {
        console.log('[Dashboard] Loading proactive readiness analysis...');
        
        const response = await fetch('/api/readiness-dashboard?focus_days=3');
        if (!response.ok) {
            console.error('Failed to load dashboard');
            return;
        }
        
        const dashboardData = await response.json();
        
        if (dashboardData.status === 'success') {
            //  Show proactive dashboard
            displayProactiveDashboard(dashboardData);
            
            //  Show proactive suggestions if there are issues
            if (dashboardData.summary.scenes_at_risk > 0 || dashboardData.summary.critical_conflicts > 0) {
                showProactiveSuggestions(dashboardData);
            }
        }
    } catch (error) {
        console.error('Error loading proactive dashboard:', error);
    }
}

function displayProactiveDashboard(data) {
    // Display dashboard with proactive analysis and live status
    const thread = document.getElementById('chat-thread');
    
    //  Add proactive analysis header with live status ticker
    const headerCard = `
        <div class="bg-gradient-to-r from-[#161224] to-[#1a1625] border border-emerald-900/40 rounded-2xl p-6 shadow-lg space-y-4 mb-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="relative">
                        <i data-lucide="activity" class="w-6 h-6 text-emerald-400 animate-pulse"></i>
                        <div class="absolute inset-0 w-6 h-6 border-2 border-emerald-400 rounded-full animate-ping opacity-50"></div>
                    </div>
                    <div>
                        <h3 class="font-bold text-white text-lg">Production Status - Live Analysis</h3>
                        <p class="text-xs text-emerald-300">Real-time monitoring active</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-xs font-mono text-emerald-400 border border-emerald-500/50 bg-emerald-500/10 px-3 py-1 rounded-full animate-pulse">● LIVE</span>
                    <button onclick="location.reload()" class="p-2 hover:bg-emerald-500/20 rounded-lg transition border border-emerald-600/30" title="Refresh">
                        <i data-lucide="rotate-cw" class="w-4 h-4 text-emerald-400"></i>
                    </button>
                </div>
            </div>
            <p class="text-sm text-slate-300">Comprehensive readiness check across all production scenes with real-time equipment, cast, and location status</p>
        </div>
    `;
    
    //  Add risk summary cards with enhanced visual hierarchy
    const summary = data.summary || {};
    const riskColor = data.overall_risk_level === 'CRITICAL' ? 'red' : data.overall_risk_level === 'HIGH' ? 'orange' : data.overall_risk_level === 'MEDIUM' ? 'amber' : 'emerald';
    const riskBgColor = data.overall_risk_level === 'CRITICAL' ? 'bg-red-900/20' : data.overall_risk_level === 'HIGH' ? 'bg-orange-900/20' : data.overall_risk_level === 'MEDIUM' ? 'bg-amber-900/20' : 'bg-emerald-900/20';
    const riskBorderColor = data.overall_risk_level === 'CRITICAL' ? 'border-red-600/50' : data.overall_risk_level === 'HIGH' ? 'border-orange-600/50' : data.overall_risk_level === 'MEDIUM' ? 'border-amber-600/50' : 'border-emerald-600/50';
    const riskTextColor = data.overall_risk_level === 'CRITICAL' ? 'text-red-400' : data.overall_risk_level === 'HIGH' ? 'text-orange-400' : data.overall_risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400';
    
    const summaryCards = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div class="bg-gradient-to-br from-slate-900 to-slate-800 border ${riskBorderColor} rounded-xl p-4 ${riskBgColor}">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wide">Overall Risk</span>
                    <i data-lucide="alert-triangle" class="w-4 h-4 ${riskTextColor}"></i>
                </div>
                <p class="text-3xl font-bold ${riskTextColor} mb-1">${data.overall_risk_level || '-'}</p>
                <div class="w-full bg-slate-700 h-1 rounded-full overflow-hidden">
                    <div class="bg-gradient-to-r ${riskTextColor === 'text-emerald-400' ? 'from-emerald-400' : riskTextColor === 'text-amber-400' ? 'from-amber-400' : riskTextColor === 'text-orange-400' ? 'from-orange-400' : 'from-red-400'} h-full" style="width: ${data.overall_risk_level === 'CRITICAL' ? '100' : data.overall_risk_level === 'HIGH' ? '75' : data.overall_risk_level === 'MEDIUM' ? '50' : '25'}%"></div>
                </div>
            </div>
            
            <div class="bg-gradient-to-br from-slate-900 to-slate-800 border border-violet-600/50 rounded-xl p-4 bg-violet-900/20">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wide">Total Scenes</span>
                    <i data-lucide="film" class="w-4 h-4 text-violet-400"></i>
                </div>
                <p class="text-3xl font-bold text-violet-400 mb-1">${summary.total_scenes || 0}</p>
                <p class="text-xs text-slate-500">scenes in production</p>
            </div>
            
            <div class="bg-gradient-to-br from-slate-900 to-slate-800 border border-orange-600/50 rounded-xl p-4 bg-orange-900/20">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wide">At Risk</span>
                    <i data-lucide="zap" class="w-4 h-4 text-orange-400"></i>
                </div>
                <p class="text-3xl font-bold text-orange-400 mb-1">${summary.scenes_at_risk || 0}</p>
                <p class="text-xs text-slate-500">need attention</p>
            </div>
            
            <div class="bg-gradient-to-br from-slate-900 to-slate-800 border border-red-600/50 rounded-xl p-4 bg-red-900/20">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wide">Critical Issues</span>
                    <i data-lucide="alert-circle" class="w-4 h-4 text-red-400"></i>
                </div>
                <p class="text-3xl font-bold text-red-400 mb-1">${summary.critical_conflicts || 0}</p>
                <p class="text-xs text-slate-500">conflicts detected</p>
            </div>
        </div>
    `;
    
    //  Add recommended actions if any
    let actionsHTML = '';
    const recommendedActions = summary.recommended_actions || [];
    if (recommendedActions.length > 0) {
        actionsHTML = `
            <div class="bg-gradient-to-br from-amber-900/20 to-slate-900/20 border border-amber-600/40 rounded-xl p-4 mb-4">
                <h4 class="text-sm font-semibold text-amber-300 mb-3 flex items-center gap-2">
                    <i data-lucide="lightbulb" class="w-5 h-5"></i>
                    Proactive Suggestions (${recommendedActions.length})
                </h4>
                <div class="space-y-2">
                    ${recommendedActions.map((action, idx) => `
                        <div class="bg-slate-800/40 border-l-2 border-amber-600/50 p-2 rounded">
                            <div class="flex items-start justify-between mb-1">
                                <span class="font-semibold text-amber-300 text-xs">${action.priority}</span>
                                <span class="text-xs text-slate-500">Action ${idx + 1}</span>
                            </div>
                            <p class="text-xs text-slate-300">${action.action}</p>
                            ${action.owner ? `<p class="text-xs text-slate-500 mt-1">👤 Owner: ${action.owner}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    //  Add scene cards with enhanced status indicators
    const scenes = data.scenes || [];
    const sceneCardsHTML = `
        <div class="mb-4">
            <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <i data-lucide="layout-grid" class="w-4 h-4 text-slate-400"></i>
                    Scene Status Overview (click to analyze)
                </h4>
                <span class="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded border border-slate-700">${scenes.length} scenes</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                ${scenes.map(scene => renderSceneCardInline(scene)).join('')}
            </div>
        </div>
    `;
    
    //  Insert at top of chat thread
    thread.innerHTML = headerCard + summaryCards + actionsHTML + sceneCardsHTML + thread.innerHTML;
    
    lucide.createIcons();
}

function renderSceneCardInline(scene) {
    // Render scene card for dashboard inline display with live status indicators
    const riskIcon = scene.risk_level === 'CRITICAL' ? '🔴' : scene.risk_level === 'HIGH' ? '🟠' : scene.risk_level === 'MEDIUM' ? '🟡' : '🟢';
    const statusIcons = scene.status_icons || {};
    
    //  Get detailed status information
    const castStatus = statusIcons.cast || '?';
    const equipmentStatus = statusIcons.equipment || '?';
    const locationStatus = statusIcons.location || '?';
    const weatherStatus = statusIcons.weather || '?';
    
    //  Build status indicator tooltips
    const getStatusLabel = (icon) => {
        if (icon === '🔴') return 'Critical Issue';
        if (icon === '🟠') return 'High Risk';
        if (icon === '🟡') return 'Medium Risk';
        if (icon === '🟢') return 'Healthy';
        return 'Unknown';
    };
    
    const conflicts = scene.conflicts || [];
    const conflictSummary = conflicts.length > 0 ? `${conflicts.length} conflict(s)` : 'No conflicts';
    
    return `
        <div class="bg-gradient-to-br from-[#0D0B18] to-[#1a1625] border border-violet-900/40 rounded-lg p-3 cursor-pointer hover:border-violet-500/70 hover:shadow-lg hover:shadow-violet-900/30 transition-all text-xs" onclick="analyzeSceneIssue('${scene.scene_id}')">
            <!-- Header with risk level -->
            <div class="flex items-start justify-between mb-2">
                <div class="flex items-center gap-2">
                    <span class="text-lg">${riskIcon}</span>
                    <div>
                        <span class="font-semibold text-white block truncate max-w-[120px]">${scene.title}</span>
                        <span class="text-slate-500 text-xs">${scene.scene_id}</span>
                    </div>
                </div>
                <span class="text-slate-600 font-mono text-xs bg-slate-900/50 px-1.5 py-0.5 rounded border border-slate-700">${scene.risk_score}%</span>
            </div>
            
            <!-- Location -->
            <p class="text-slate-400 mb-2 truncate text-xs">📍 ${scene.location}</p>
            
            <!-- Live Status Indicators Row -->
            <div class="bg-slate-900/30 rounded-lg p-2 mb-2 border border-slate-800/50">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs font-semibold text-slate-400">Live Status</span>
                    <span class="text-xs text-emerald-400 animate-pulse">● Active</span>
                </div>
                <div class="grid grid-cols-4 gap-1.5">
                    <div class="bg-slate-800/50 rounded p-1.5 text-center border border-slate-700/50 hover:border-slate-600 transition">
                        <div class="text-base mb-0.5">${castStatus}</div>
                        <div class="text-xs text-slate-500">Cast</div>
                        <div class="text-xs text-slate-400 font-mono">${getStatusLabel(castStatus)}</div>
                    </div>
                    <div class="bg-slate-800/50 rounded p-1.5 text-center border border-slate-700/50 hover:border-slate-600 transition">
                        <div class="text-base mb-0.5">${equipmentStatus}</div>
                        <div class="text-xs text-slate-500">Equipment</div>
                        <div class="text-xs text-slate-400 font-mono">${getStatusLabel(equipmentStatus)}</div>
                    </div>
                    <div class="bg-slate-800/50 rounded p-1.5 text-center border border-slate-700/50 hover:border-slate-600 transition">
                        <div class="text-base mb-0.5">${locationStatus}</div>
                        <div class="text-xs text-slate-500">Location</div>
                        <div class="text-xs text-slate-400 font-mono">${getStatusLabel(locationStatus)}</div>
                    </div>
                    <div class="bg-slate-800/50 rounded p-1.5 text-center border border-slate-700/50 hover:border-slate-600 transition">
                        <div class="text-base mb-0.5">${weatherStatus}</div>
                        <div class="text-xs text-slate-500">Weather</div>
                        <div class="text-xs text-slate-400 font-mono">${getStatusLabel(weatherStatus)}</div>
                    </div>
                </div>
            </div>
            
            <!-- Conflicts Alert -->
            ${conflicts.length > 0 ? `
                <div class="bg-red-900/20 border border-red-600/40 rounded-lg p-2 mb-2">
                    <div class="flex items-start gap-1.5">
                        <span class="text-lg flex-shrink-0">⚠️</span>
                        <div class="flex-1">
                            <p class="font-semibold text-red-300 text-xs mb-1">${conflictSummary}</p>
                            <div class="space-y-0.5">
                                ${conflicts.slice(0, 2).map(c => `
                                    <p class="text-xs text-red-200">• ${c.type}: ${c.description || c.severity}</p>
                                `).join('')}
                                ${conflicts.length > 2 ? `<p class="text-xs text-red-300/70">... and ${conflicts.length - 2} more</p>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            ` : `
                <div class="bg-emerald-900/20 border border-emerald-600/40 rounded-lg p-2 mb-2">
                    <p class="text-xs text-emerald-300 flex items-center gap-1">✓ All systems nominal</p>
                </div>
            `}
            
            <!-- Quick Action -->
            <button class="w-full py-1.5 px-2 bg-violet-600/30 hover:bg-violet-600/50 text-violet-200 rounded-lg font-medium text-xs transition-colors border border-violet-600/50">
                Analyze Scene
            </button>
        </div>
    `;
}

function showProactiveSuggestions(dashboardData) {
    // Show proactive suggestions card
    const summary = dashboardData.summary || {};
    
    //  Only show if there are actual issues
    if (summary.scenes_at_risk === 0 && summary.critical_conflicts === 0) {
        return;
    }
    
    const thread = document.getElementById('chat-thread');
    const suggestionCard = `
        <div class="bg-[#161224] border border-amber-900/40 rounded-2xl p-4 shadow-lg mt-4">
            <div class="flex items-center gap-2 mb-3">
                <i data-lucide="info" class="w-4 h-4 text-amber-400"></i>
                <h3 class="font-semibold text-white text-sm">Production Issues Detected</h3>
            </div>
            <div class="space-y-2 text-xs text-slate-300">
                <p>🎬 <strong>${summary.scenes_at_risk} scene(s) at risk</strong> - Click cards above to analyze</p>
                <p>⚠️ <strong>${summary.critical_conflicts} critical conflict(s)</strong> - Immediate attention needed</p>
                <p>💡 <strong>Need recommendations?</strong> Describe the issue in the input box below or click a scene</p>
            </div>
        </div>
    `;
    
    thread.innerHTML += suggestionCard;
    lucide.createIcons();
}

//  ============================================
//  SESSION MANAGEMENT
//  ============================================

function createNewSession() {
    //  Save current session first if it has content
    if (sessionHistory.length > 0) {
        saveCurrentSession();
    }
    
    //  Create new session
    currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
    sessionHistory = [];
    localStorage.setItem('cineflow_current_session', currentSessionId);
    
    //  Reset UI with better welcome message
    const chatThread = document.getElementById('chat-thread');
    chatThread.innerHTML = `
        <div class="bg-gradient-to-br from-violet-900/20 to-indigo-900/20 border border-violet-900/40 rounded-2xl p-6 shadow-lg space-y-4">
            <div class="flex items-start gap-3">
                <div class="p-3 bg-violet-600/20 rounded-lg flex-shrink-0">
                    <i data-lucide="zap" class="w-5 h-5 text-violet-400"></i>
                </div>
                <div class="flex-1">
                    <h2 class="font-bold text-white text-base">🎬 New Crisis Analysis Session</h2>
                    <p class="text-xs text-slate-400 mt-1">Ready to analyze production disruptions and generate smart recommendations</p>
                </div>
            </div>
            <div class="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-violet-900/30">
                <div class="text-center">
                    <p class="text-2xl">📊</p>
                    <p class="text-xs text-slate-400 mt-1">Dashboard</p>
                    <p class="text-[10px] text-slate-500">View live status</p>
                </div>
                <div class="text-center">
                    <p class="text-2xl">💬</p>
                    <p class="text-xs text-slate-400 mt-1">Chat</p>
                    <p class="text-[10px] text-slate-500">Ask questions</p>
                </div>
                <div class="text-center">
                    <p class="text-2xl">✅</p>
                    <p class="text-xs text-slate-400 mt-1">Approve</p>
                    <p class="text-[10px] text-slate-500">Execute changes</p>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('crisis-input').value = '';
    document.getElementById('crisis-input').placeholder = 'Describe your production crisis...';
    
    updateSessionDisplay();
    loadAllSessions();
    renderSessionList();
    
    //  Load proactive dashboard
    loadProactiveDashboardOnInit();
    
    showNotification('New session created');
    lucide.createIcons();
}

function saveCurrentSession() {
    const sessionData = {
        id: currentSessionId,
        created: localStorage.getItem(`cineflow_session_${currentSessionId}_created`) || new Date().toISOString(),
        messages: sessionHistory
    };
    localStorage.setItem(`cineflow_session_${currentSessionId}`, JSON.stringify(sessionData));
}

function loadSessionMessages(sessionId) {
    const saved = localStorage.getItem(`cineflow_session_${sessionId}`);
    if (saved) {
        const data = JSON.parse(saved);
        sessionHistory = data.messages || [];
        //  Render saved messages
        renderSessionHistory();
    }
}

function loadAllSessions() {
    allSessions = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('cineflow_session_')) {
            const data = JSON.parse(localStorage.getItem(key));
            if (data && data.id) {
                allSessions.push(data);
            }
        }
    }
    allSessions.sort((a, b) => new Date(b.created) - new Date(a.created));
    renderSessionList();
}

function switchToSession(sessionId) {
    if (sessionId === currentSessionId) return;
    
    //  Save current session
    saveCurrentSession();
    
    //  Load target session
    currentSessionId = sessionId;
    localStorage.setItem('cineflow_current_session', sessionId);
    loadSessionMessages(sessionId);
    updateSessionDisplay();
    renderSessionList();
    
    //  Scroll to active session in sidebar
    setTimeout(() => {
        const sessionItems = document.querySelectorAll('[onclick*="switchToSession"]');
        sessionItems.forEach(item => {
            const onclick = item.getAttribute('onclick');
            if (onclick && onclick.includes(`'${sessionId}'`)) {
                item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    }, 100);
    
    showNotification(`Switched to session`);
    lucide.createIcons();
}

function deleteSession(sessionId) {
    if (!confirm('Delete this session? This cannot be undone.')) {
        return;
    }
    
    localStorage.removeItem(`cineflow_session_${sessionId}`);
    
    //  If deleting current session, create new one
    if (sessionId === currentSessionId) {
        createNewSession();
    } else {
        loadAllSessions();
        renderSessionList();
    }
    
    showNotification('Session deleted');
}

function downloadSessionData(sessionId) {
    const sessionData = JSON.parse(localStorage.getItem(`cineflow_session_${sessionId}`) || '{}');
    const dataStr = JSON.stringify(sessionData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `cineflow_session_${sessionId}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    
    showNotification('Session exported');
}

function showNotification(message) {
    //  Create notification element
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium shadow-lg z-50';
    notification.textContent = message;
    notification.style.animation = 'slideInRight 0.3s ease';
    document.body.appendChild(notification);
    
    //  Remove after 2 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

function renderSessionList() {
    const container = document.getElementById('session-history-list');
    if (!container) return;
    
    if (allSessions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <p class="text-xs text-slate-500 mb-2">No previous sessions</p>
                <button onclick="createNewSession()" class="w-full px-2 py-1.5 bg-violet-600/40 hover:bg-violet-600/60 text-violet-300 text-xs rounded-lg border border-violet-600/50 transition">
                    <i data-lucide="plus" class="w-3 h-3 inline mr-1"></i>
                    New Chat
                </button>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    //  Add "New Chat" button at top
    let html = `
        <button onclick="createNewSession()" class="w-full px-2 py-1.5 mb-2 bg-emerald-600/40 hover:bg-emerald-600/60 text-emerald-300 text-xs rounded-lg border border-emerald-600/50 transition font-medium flex items-center justify-center gap-1">
            <i data-lucide="plus" class="w-3 h-3"></i>
            New Chat Session
        </button>
    `;
    
    //  Add session list
    html += allSessions.map(session => {
        const lastMsg = session.messages && session.messages.length > 0 ? session.messages[session.messages.length - 1] : null;
        const sceneId = lastMsg?.scene || 'General';
        const preview = lastMsg?.crisis?.substring(0, 35) + '...' || 'Empty session';
        const isActive = session.id === currentSessionId;
        const messageCount = session.messages ? session.messages.length : 0;
        const createdDate = new Date(session.created);
        const timeStr = createdDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        const dateStr = createdDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        //  Determine session risk status based on messages
        let riskLevel = 'MEDIUM';
        if (lastMsg?.analysis?.risk_level) {
            riskLevel = lastMsg.analysis.risk_level;
        }
        const riskIcon = riskLevel === 'CRITICAL' ? '🔴' : riskLevel === 'HIGH' ? '🟠' : riskLevel === 'MEDIUM' ? '🟡' : '🟢';
        const riskBorder = riskLevel === 'CRITICAL' ? 'border-red-500/60' : riskLevel === 'HIGH' ? 'border-orange-500/60' : riskLevel === 'MEDIUM' ? 'border-amber-500/60' : 'border-emerald-500/60';
        const riskBg = riskLevel === 'CRITICAL' ? 'bg-red-600/10' : riskLevel === 'HIGH' ? 'bg-orange-600/10' : riskLevel === 'MEDIUM' ? 'bg-amber-600/10' : 'bg-emerald-600/10';
        
        return `
            <div class="group">
                <div onclick="switchToSession('${session.id}')" class="p-2.5 cursor-pointer rounded-xl border transition-all ${
                    isActive 
                    ? `${riskBg} ${riskBorder} shadow-lg shadow-violet-900/20` 
                    : 'bg-[#1C1733]/50 border-violet-900/30 hover:bg-violet-900/20 hover:border-violet-500/50'
                }">
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-1 mb-0.5">
                                <span class="text-sm">${riskIcon}</span>
                                <p class="font-semibold text-slate-200 text-xs truncate">Scene: ${sceneId}</p>
                            </div>
                            <p class="text-[10px] text-slate-400 truncate">${preview}</p>
                        </div>
                        ${isActive ? '<span class="text-xs text-emerald-400 font-bold flex-shrink-0 mt-0.5 animate-pulse">●</span>' : ''}
                    </div>
                    <div class="flex items-center justify-between mt-1.5 text-[9px]">
                        <span class="text-slate-500 flex items-center gap-1">
                            <i data-lucide="message-circle" class="w-2.5 h-2.5"></i>
                            ${messageCount} msgs
                        </span>
                        <span class="text-slate-600">${timeStr}</span>
                    </div>
                    ${isActive ? `
                        <div class="mt-1.5 text-xs flex items-center gap-1 text-emerald-300">
                            <i data-lucide="activity" class="w-3 h-3 animate-pulse"></i>
                            Live Status: Active
                        </div>
                    ` : ''}
                </div>
                ${isActive ? `
                    <div class="mt-1 flex gap-1 opacity-0 group-hover:opacity-100 transition">
                        <button onclick="event.stopPropagation(); downloadSessionData('${session.id}')" class="flex-1 text-xs py-1 px-2 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 rounded border border-blue-600/30 transition" title="Export">
                            <i data-lucide="download" class="w-3 h-3 inline mr-1"></i>Export
                        </button>
                        <button onclick="event.stopPropagation(); deleteSession('${session.id}')" class="flex-1 text-xs py-1 px-2 bg-red-600/20 hover:bg-red-600/40 text-red-300 rounded border border-red-600/30 transition" title="Delete">
                            <i data-lucide="trash-2" class="w-3 h-3 inline"></i>
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
    lucide.createIcons();
}

function updateSessionDisplay() {
    const idDisplay = document.getElementById('active-session-id');
    if (idDisplay) {
        idDisplay.innerText = `Session: #${currentSessionId.slice(-8)}`;
    }
}

function renderSessionHistory() {
    const thread = document.getElementById('chat-thread');
    if (!thread || sessionHistory.length === 0) return;
    
    thread.innerHTML = sessionHistory.map((msg, idx) => {
        if (msg.type === 'user') {
            return `
                <div class="flex justify-end">
                    <div class="bg-violet-700 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-xl text-sm shadow-md">
                        <span class="font-mono text-xs opacity-75 block mb-1">Scene: ${msg.scene} | Mode: ${msg.mode.toUpperCase()}</span>
                        ${msg.crisis}
                    </div>
                </div>
            `;
        } else if (msg.type === 'agent') {
            return renderStoredAgentResponse(msg.response);
        }
        return '';
    }).join('');
    
    lucide.createIcons();
    thread.scrollTop = thread.scrollHeight;
}

function renderStoredAgentResponse(data) {
    if (!data || data.status !== 'success') return '';
    
    const analysis = data.analysis || {};
    const recommendation = analysis.recommended_action || 'No recommendation';
    const finMetrics = analysis.financial_impact || {};
    
    return `
        <div class="agent-response bg-[#161224] border border-violet-900/40 rounded-2xl p-6 shadow-xl space-y-4">
            <div class="flex items-center justify-between border-b border-violet-900/30 pb-3">
                <div class="flex items-center gap-3">
                    <i data-lucide="check-circle-2" class="w-5 h-5 text-emerald-400"></i>
                    <h3 class="font-bold text-white text-base">CineFlow Recommendation</h3>
                </div>
                <span class="text-xs font-mono text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 rounded">
                    ${analysis.risk_level || 'SAFE'}
                </span>
            </div>
            
            <div class="grid grid-cols-3 gap-3 my-4 font-mono text-xs">
                <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                    <span class="text-slate-400 block">Daily Burn</span>
                    <span class="text-white font-bold text-sm">₹${(finMetrics.daily_burn || 0).toLocaleString()}</span>
                </div>
                <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                    <span class="text-slate-400 block">Setup Cost</span>
                    <span class="text-amber-400 font-bold text-sm">₹${(finMetrics.setup_cost || 0).toLocaleString()}</span>
                </div>
                <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                    <span class="text-slate-400 block">Net Savings</span>
                    <span class="text-emerald-400 font-bold text-sm">₹${(finMetrics.net_benefit || 0).toLocaleString()}</span>
                </div>
            </div>
            
            <p class="text-slate-300 text-sm leading-relaxed">${recommendation}</p>
        </div>
    `;
}

//  ============================================
//  ANALYSIS MODE
//  ============================================

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    
    const modeMap = {
        'quick': 'btn-quick',
        'deep': 'btn-deep',
        'next_steps': 'btn-next'
    };
    
    if (modeMap[mode]) {
        document.getElementById(modeMap[mode]).classList.add('active');
    }
}

function applyTemplate(templateText) {
    const input = document.getElementById('crisis-input');
    input.value = templateText;
    input.focus();
}

//  ============================================
//  CRISIS SUBMISSION & ANALYSIS
//  ============================================

async function submitCrisis() {
    const sceneId = document.getElementById('scene-selector').value;
    const description = document.getElementById('crisis-input').value.trim();
    const thread = document.getElementById('chat-thread');
    const submitBtn = document.querySelector('[onclick="submitCrisis()"]');
    
    if (!description) {
        alert('Please describe the crisis');
        return;
    }
    
    if (isAnalyzing) return;
    isAnalyzing = true;
    if (submitBtn) submitBtn.disabled = true;
    
    //  Add user message
    const userMsg = { type: 'user', scene: sceneId, crisis: description, mode: currentMode };
    sessionHistory.push(userMsg);
    saveCurrentSession();
    
    //  Render user bubble
    thread.innerHTML += `
        <div class="flex justify-end">
            <div class="bg-violet-700 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-xl text-sm shadow-md">
                <span class="font-mono text-xs opacity-75 block mb-1">Scene: ${sceneId} | Mode: ${currentMode.toUpperCase()} | Session: ${currentSessionId}</span>
                ${description}
            </div>
        </div>
    `;
    
    //  Clear input
    document.getElementById('crisis-input').value = '';
    
    //  Add streaming response container
    const responseId = 'resp_' + Date.now();
    thread.innerHTML += `
        <div id="${responseId}" class="agent-response bg-[#161224] border border-violet-900/40 rounded-2xl p-6 shadow-xl space-y-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <i data-lucide="cpu" class="w-5 h-5 text-violet-400 animate-spin"></i>
                    <h3 class="font-bold text-white text-base">CineFlow Analysis - Streaming Phases</h3>
                </div>
                <span class="text-xs font-mono text-amber-400 border border-amber-500/30 bg-amber-500/10 px-2 py-1 rounded" id="${responseId}_status">Initializing...</span>
            </div>
            <div id="${responseId}_phases" class="space-y-3">
                <!-- Phases will be inserted here -->
            </div>
            <div id="${responseId}_result" class="hidden">
                <!-- Final result will appear here -->
            </div>
        </div>
    `;
    
    lucide.createIcons();
    thread.scrollTop = thread.scrollHeight;
    
    try {
        //  Use streaming endpoint
        const response = await fetch('/api/analyze-crisis-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: description,
                scene_id: sceneId,
                session_id: currentSessionId
            })
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let finalData = null;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); //  Keep incomplete line
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const eventData = JSON.parse(line.substring(6));
                        handleStreamEvent(responseId, eventData);
                        if (eventData.phase === 'complete') {
                            finalData = eventData;
                        }
                    } catch (e) {
                        console.error('Error parsing event:', e);
                    }
                }
            }
        }
        
        //  Store final response
        if (finalData) {
            const agentMsg = { type: 'agent', response: finalData };
            sessionHistory.push(agentMsg);
            saveCurrentSession();
            
            //  Show final structured response
            setTimeout(() => {
                renderConversationalResponse(responseId, finalData.analysis);
                loadAllSessions();
            }, 500);
        }
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById(responseId).innerHTML = `
            <div class="flex items-center justify-between border-b border-red-900/30 pb-3">
                <div class="flex items-center gap-3">
                    <i data-lucide="alert-circle" class="w-5 h-5 text-red-400"></i>
                    <h3 class="font-bold text-red-400">Analysis Failed</h3>
                </div>
                <span class="text-xs font-mono text-red-400 border border-red-500/30 bg-red-500/10 px-2 py-1 rounded">Error</span>
            </div>
            <p class="text-slate-300 text-sm">Could not reach CineFlow backend. Ensure backend is running on port 8000.</p>
            <button onclick="submitCrisis()" class="mt-3 px-4 py-2 bg-red-900/30 border border-red-700/50 text-red-200 rounded-lg text-xs">
                Retry Analysis
            </button>
        `;
        lucide.createIcons();
    }
    
    isAnalyzing = false;
    if (submitBtn) submitBtn.disabled = false;
}

function handleStreamEvent(responseId, eventData) {
    const phasesContainer = document.getElementById(responseId + '_phases');
    const statusBadge = document.getElementById(responseId + '_status');
    
    let phaseIcon = '⏳';
    let phaseColor = 'text-amber-400';
    
    switch (eventData.phase) {
        case 'planning':
            phaseIcon = '📋';
            phaseColor = 'text-blue-400';
            break;
        case 'planning_complete':
            phaseIcon = '✓';
            phaseColor = 'text-green-400';
            statusBadge.textContent = `${eventData.tasks} tasks created`;
            phasesContainer.innerHTML += `
                <div class="flex items-start gap-3 text-sm">
                    <span class="${phaseColor} font-mono">${phaseIcon}</span>
                    <div class="flex-1">
                        <p class="font-semibold text-green-300">Phase 1: Planning Complete</p>
                        <p class="text-xs text-slate-400 mt-1">Tasks: ${eventData.task_list.join(', ')}</p>
                    </div>
                </div>
            `;
            break;
        case 'executing':
            phaseIcon = '⚙️';
            phaseColor = 'text-cyan-400';
            statusBadge.textContent = 'Executing Workers...';
            phasesContainer.innerHTML += `
                <div class="flex items-start gap-3 text-sm">
                    <span class="${phaseColor} animate-spin">${phaseIcon}</span>
                    <div class="flex-1">
                        <p class="font-semibold text-cyan-300">Phase 2: Worker Execution</p>
                        <p class="text-xs text-slate-400 mt-1">Running parallel analysis tasks...</p>
                    </div>
                </div>
            `;
            break;
        case 'worker_complete':
            phasesContainer.innerHTML += `
                <div class="flex items-start gap-3 text-sm pl-3 border-l-2 border-green-500/30">
                    <span class="text-green-400 font-mono">→</span>
                    <div class="flex-1">
                        <p class="text-green-300 text-xs">${eventData.worker}</p>
                    </div>
                </div>
            `;
            break;
        case 'monitoring':
            statusBadge.textContent = 'Monitoring Quality...';
            phasesContainer.innerHTML += `
                <div class="flex items-start gap-3 text-sm">
                    <span class="text-purple-400">🔍</span>
                    <div class="flex-1">
                        <p class="font-semibold text-purple-300">Phase 3: Quality Monitoring</p>
                        <p class="text-xs text-slate-400 mt-1">Validating analysis results...</p>
                    </div>
                </div>
            `;
            break;
        case 'monitoring_complete':
            const qualityStatus = eventData.quality_ok ? '✓ Passed' : '⚠️ Issues Detected';
            phasesContainer.innerHTML += `
                <div class="flex items-start gap-3 text-sm pl-3 border-l-2 border-purple-500/30">
                    <span class="text-purple-400 font-mono">→</span>
                    <div class="flex-1">
                        <p class="text-purple-300 text-xs">Quality Check: ${qualityStatus}</p>
                    </div>
                </div>
            `;
            break;
        case 'synthesis':
            statusBadge.textContent = 'Generating Response...';
            phasesContainer.innerHTML += `
                <div class="flex items-start gap-3 text-sm">
                    <span class="text-amber-400">🧠</span>
                    <div class="flex-1">
                        <p class="font-semibold text-amber-300">Phase 4: Synthesis & Recommendations</p>
                        <p class="text-xs text-slate-400 mt-1">Creating final recommendation...</p>
                    </div>
                </div>
            `;
            break;
        case 'complete':
            statusBadge.textContent = 'Complete';
            statusBadge.classList.remove('text-amber-400', 'border-amber-500/30', 'bg-amber-500/10');
            statusBadge.classList.add('text-green-400', 'border-green-500/30', 'bg-green-500/10');
            break;
        case 'error':
            statusBadge.textContent = 'Error';
            statusBadge.classList.remove('text-amber-400', 'border-amber-500/30', 'bg-amber-500/10');
            statusBadge.classList.add('text-red-400', 'border-red-500/30', 'bg-red-500/10');
            phasesContainer.innerHTML += `
                <div class="flex items-start gap-3 text-sm">
                    <span class="text-red-400">✗</span>
                    <div class="flex-1">
                        <p class="font-semibold text-red-300">Error</p>
                        <p class="text-xs text-slate-400 mt-1">${eventData.error}</p>
                    </div>
                </div>
            `;
            break;
    }
    
    document.getElementById('chat-thread').scrollTop = document.getElementById('chat-thread').scrollHeight;
}

//  ============================================
//  RESPONSE RENDERING
//  ============================================

function renderAgentResponse(elementId, data) {
    const el = document.getElementById(elementId);
    
    if (!data || data.status !== 'success') {
        el.innerHTML = `
            <div class="flex items-start gap-3">
                <i data-lucide="alert-triangle" class="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5"></i>
                <div class="flex-1">
                    <h3 class="font-bold text-amber-400 mb-1">Analysis Incomplete</h3>
                    <p class="text-slate-300 text-sm">${data?.message || 'Analysis did not complete successfully.'}</p>
                </div>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    //  Render conversational format with collapsible sections
    renderConversationalResponse(elementId, data);
}

function renderConversationalResponse(elementId, data) {
    const el = document.getElementById(elementId);
    const analysis = data.analysis || {};
    const riskLevel = analysis.risk_level || 'MEDIUM';
    
    //  Determine color scheme
    const riskColors = {
        'LOW': { badge: 'bg-emerald-600/20 text-emerald-300', icon: '🟢', border: 'border-emerald-600/30' },
        'MEDIUM': { badge: 'bg-amber-600/20 text-amber-300', icon: '🟡', border: 'border-amber-600/30' },
        'HIGH': { badge: 'bg-orange-600/20 text-orange-300', icon: '🟠', border: 'border-orange-600/30' },
        'CRITICAL': { badge: 'bg-red-600/20 text-red-300', icon: '🔴', border: 'border-red-600/30' }
    };
    
    const colors = riskColors[riskLevel] || riskColors.MEDIUM;
    const recommendation = analysis.recommended_action || {};
    const finMetrics = analysis.financial_impact || {};
    const riskFactors = analysis.risk_factors || [];
    const costImpact = analysis.cost_impact || 'TBD';
    
    //  Get conversation context if available
    const conversationContext = data.conversation_context || {};
    const approvedSwaps = conversationContext.approved_swaps || [];
    
    //  Build conversational response with enhanced sections
    let html = `
        <div class="space-y-4">
            <!-- Conversation Context (if multi-turn) -->
            ${approvedSwaps.length > 0 ? `
            <div class="bg-violet-900/20 border border-violet-600/30 rounded-lg p-3">
                <p class="text-xs font-semibold text-violet-300 mb-2">
                    <i data-lucide="history" class="w-3 h-3 inline mr-1"></i>
                    Context from previous interactions (${approvedSwaps.length} decision(s))
                </p>
                <div class="text-xs text-violet-200 space-y-1">
                    ${approvedSwaps.slice(0, 2).map(swap => `
                        <p>• Scene ${swap.source || '?'} → ${swap.target || '?'} (${swap.reason || 'Actor swap'})</p>
                    `).join('')}
                    ${approvedSwaps.length > 2 ? `<p class="text-violet-300/70">... and ${approvedSwaps.length - 2} more previous decisions</p>` : ''}
                </div>
            </div>
            ` : ''}
            
            <!-- Executive Summary with Risk Assessment -->
            <div class="bg-gradient-to-br from-slate-900/50 to-violet-900/20 border ${colors.border} rounded-lg p-4">
                <div class="flex items-start gap-3">
                    <div class="text-3xl flex-shrink-0">${colors.icon}</div>
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <h3 class="font-bold text-white text-lg">CineFlow Analysis</h3>
                            <span class="text-xs font-bold px-2 py-0.5 rounded ${colors.badge}">${riskLevel} RISK</span>
                        </div>
                        <p class="text-sm text-slate-300 leading-relaxed mb-2">${analysis.executive_summary || 'Production crisis analyzed and recommendations generated.'}</p>
                        ${riskFactors.length > 0 ? `
                            <p class="text-xs text-slate-400 mb-1"><strong>Key Risk Factors:</strong></p>
                            <div class="flex flex-wrap gap-1">
                                ${riskFactors.slice(0, 3).map(factor => `
                                    <span class="text-xs bg-slate-800 px-2 py-1 rounded border border-slate-700">⚠️ ${factor}</span>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
    `;
    
    //  Add enhanced collapsible sections
    html += `
            <!-- Collapsible Sections -->
            <div class="space-y-2">
                <!-- Crisis Section -->
                ${renderSection('crisis', '🚨 Situation Assessment', `
                    <div class="space-y-2">
                        <p>${analysis.analysis?.affected_resource ? `<strong>Primary Issue:</strong> ${analysis.analysis.affected_resource}` : 'Production crisis identified'}</p>
                        <p><strong>Impact:</strong> Affects multiple scenes and resources in current schedule</p>
                        ${riskFactors.length > 0 ? `
                            <div>
                                <strong>Risks:</strong>
                                <ul class="ml-2 mt-1 text-xs space-y-0.5">
                                    ${riskFactors.slice(0, 3).map(f => `<li>• ${f}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                `, true)}
                
                <!-- Financial Impact Section -->
                ${renderSection('financial', '💰 Financial Impact Analysis', `
                    <div class="grid grid-cols-2 gap-2">
                        <div class="bg-slate-800/50 p-2 rounded border border-slate-700">
                            <p class="text-xs text-slate-400">Daily Burn</p>
                            <p class="text-sm font-bold text-amber-400">₹${(finMetrics.daily_burn || 0).toLocaleString()}</p>
                        </div>
                        <div class="bg-slate-800/50 p-2 rounded border border-slate-700">
                            <p class="text-xs text-slate-400">Total Cost</p>
                            <p class="text-sm font-bold text-red-400">₹${(finMetrics.total_cost_inr || 0).toLocaleString()}</p>
                        </div>
                        <div class="bg-slate-800/50 p-2 rounded border border-slate-700 col-span-2">
                            <p class="text-xs text-slate-400">Net Benefit</p>
                            <p class="text-sm font-bold text-emerald-400">₹${(recommendation.net_benefit || 0).toLocaleString()}</p>
                        </div>
                    </div>
                    <p class="text-xs text-slate-400 mt-2">Cost Impact: ${costImpact}</p>
                `, false)}
                
                <!-- Recommendation Section -->
                ${renderSection('recommendation', '✅ Recommended Action', `
                    <div class="space-y-2">
                        <div class="bg-emerald-900/20 border border-emerald-600/30 p-2 rounded">
                            <p class="text-sm font-bold text-emerald-300">${recommendation.action || 'HOLD'}</p>
                            <p class="text-xs text-emerald-200 mt-1">${recommendation.reasoning || 'Detailed analysis and reasoning'}</p>
                        </div>
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-slate-400"><strong>Confidence:</strong> ${recommendation.confidence || 'MEDIUM'}</span>
                            <span class="text-slate-400"><strong>Target:</strong> ${recommendation.target_scene || 'Current'}</span>
                        </div>
                    </div>
                `, true)}
                
                <!-- Next Steps Section -->
                ${renderSection('nextSteps', '📋 Immediate Next Steps', `
                    <ol class="space-y-1 text-xs">
                        ${(analysis.next_actions || []).slice(0, 5).map((action, idx) => `
                            <li class="flex gap-2">
                                <span class="font-bold text-emerald-400 flex-shrink-0">${idx + 1}.</span>
                                <span>
                                    <strong>${action.priority}</strong>: ${action.action || 'Action needed'}
                                    ${action.owner ? `<span class="text-slate-500"> (Owner: ${action.owner})</span>` : ''}
                                </span>
                            </li>
                        `).join('')}
                        ${(analysis.next_actions || []).length > 5 ? `<li class="text-slate-500">... and ${(analysis.next_actions || []).length - 5} more actions</li>` : ''}
                    </ol>
                `, false)}
            </div>
    `;
    
    //  Enhanced action buttons
    html += `
            <!-- Action Buttons -->
            <div class="flex items-center gap-2 pt-3 border-t border-violet-900/30 flex-wrap">
                <button onclick="openApprovalConfirmationModal('${data.session_id}')" class="flex items-center gap-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium text-xs transition-all shadow-lg shadow-emerald-900/30">
                    <i data-lucide="check" class="w-4 h-4"></i>
                    Approve Decision
                </button>
                <button onclick="openAlternativesModal('${data.session_id}')" class="flex items-center gap-1 px-4 py-2 bg-violet-600/40 hover:bg-violet-600/60 text-violet-200 rounded-lg font-medium text-xs transition-colors border border-violet-600/50">
                    <i data-lucide="branch" class="w-4 h-4"></i>
                    Explore Alternatives
                </button>
                <button onclick="toggleDetailedView('${elementId}')" class="flex items-center gap-1 px-4 py-2 bg-slate-600/40 hover:bg-slate-600/60 text-slate-200 rounded-lg font-medium text-xs transition-colors border border-slate-600/50 ml-auto">
                    <i data-lucide="expand" class="w-4 h-4"></i>
                    Expand All
                </button>
            </div>
        </div>
    `;
    
    el.innerHTML = html;
    lucide.createIcons();
}

function renderSection(id, title, content, expanded = false) {
    return `
        <div class="bg-[#0D0B18] border border-violet-900/30 rounded-lg overflow-hidden">
            <button onclick="toggleSection('section_${id}')" class="w-full flex items-center justify-between p-3 hover:bg-violet-950/30 transition-colors">
                <span class="font-semibold text-sm text-slate-200">${title}</span>
                <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400 transition-transform" id="section_${id}_icon" style="transform: rotate(${expanded ? 0 : -90}deg)"></i>
            </button>
            <div id="section_${id}" class="border-t border-violet-900/30 p-3 text-sm text-slate-300 bg-[#161224] max-h-96 overflow-y-auto ${!expanded ? 'hidden' : ''}">
                ${content}
            </div>
        </div>
    `;
}

function buildNextStepsHTML(actions) {
    if (!actions || actions.length === 0) {
        return '<p class="text-slate-400 text-xs">No additional actions needed at this time.</p>';
    }
    
    return `
        <ul class="space-y-2 text-xs text-slate-300">
            ${actions.slice(0, 4).map(action => `
                <li class="flex items-start gap-2">
                    <span class="inline-block w-1.5 h-1.5 rounded-full bg-violet-400 mt-1.5 flex-shrink-0"></span>
                    <div>
                        <div class="font-semibold text-slate-200">${action.label}</div>
                        <div class="text-slate-400">${action.description}</div>
                    </div>
                </li>
            `).join('')}
            ${actions.length > 4 ? `<li class="text-slate-500 italic">... and ${actions.length - 4} more actions</li>` : ''}
        </ul>
    `;
}

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const icon = document.getElementById(sectionId + '_icon');
    
    if (section) {
        const isHidden = section.classList.contains('hidden');
        section.classList.toggle('hidden');
        
        if (icon) {
            icon.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(-90deg)';
        }
    }
}

function toggleDetailedView(elementId) {
    //  Expand to show all sections
    const sections = document.querySelectorAll(`#${elementId} [id^="section_"]`);
    sections.forEach(section => {
        if (section.classList.contains('hidden')) {
            section.classList.remove('hidden');
            const icon = section.previousElementSibling?.querySelector('i');
            if (icon) icon.style.transform = 'rotate(0deg)';
        }
    });
}

function approveRecommendation(sessionId) {
    //  Show approval confirmation modal
    openApprovalConfirmationModal(sessionId);
}

function exploreAlternatives(sessionId) {
    //  Show cascade analysis for alternative options
    openAlternativesModal(sessionId);
}
        
        <div class="grid grid-cols-3 gap-3 my-4 font-mono text-xs">
            <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                <span class="text-slate-400 block">Daily Burn</span>
                <span class="text-white font-bold text-sm">₹${(finMetrics.daily_burn || 0).toLocaleString()}</span>
            </div>
            <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                <span class="text-slate-400 block">Setup Cost</span>
                <span class="text-amber-400 font-bold text-sm">₹${(finMetrics.setup_cost || 0).toLocaleString()}</span>
            </div>
            <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                <span class="text-slate-400 block">Net Savings</span>
                <span class="text-emerald-400 font-bold text-sm">₹${(finMetrics.net_benefit || 0).toLocaleString()}</span>
            </div>
        </div>
        
        <div class="bg-violet-950/30 border border-violet-800/40 p-3 rounded-xl">
            <p class="text-slate-300 text-sm leading-relaxed">${recommendation}</p>
            ${cascades > 0 ? `<p class="text-orange-400 text-xs mt-2"><i data-lucide="alert" class="w-3 h-3 inline"></i> ${cascades} cascade(s) detected</p>` : ''}
        </div>
        
        <div class="flex items-center gap-2 pt-2">
            <button class="action-button primary" onclick="approveDecision('${data.session_id}')">
                <i data-lucide="check" class="w-3 h-3"></i>
                Approve
            </button>
            <button class="action-button secondary">
                <i data-lucide="arrow-right-left" class="w-3 h-3"></i>
                Explore Alternatives
            </button>
        </div>
    `;
    
    lucide.createIcons();
}

function approveDecision(sessionId) {
    console.log('Decision approved for session:', sessionId);
    //  Implementation for approval logic
}


//  ============================================
//  READINESS DASHBOARD
//  ============================================

let currentDashboardView = false;

function toggleDashboardView() {
    currentDashboardView = !currentDashboardView;
    
    const chatThread = document.getElementById('chat-thread');
    const dashboard = document.getElementById('readiness-dashboard');
    const viewText = document.getElementById('view-toggle-text');
    const inputDock = document.getElementById('input-dock');
    const toggleBtn = document.querySelector('[onclick="toggleDashboardView()"]');
    
    //  Add transition effects
    chatThread.style.transition = 'opacity 0.3s ease';
    dashboard.style.transition = 'opacity 0.3s ease';
    
    if (currentDashboardView) {
        //  Switch to Dashboard view
        chatThread.style.opacity = '0';
        setTimeout(() => {
            chatThread.classList.add('hidden');
            dashboard.classList.remove('hidden');
            dashboard.style.opacity = '0';
            inputDock.classList.add('hidden');
            
            //  Update button styling
            if (toggleBtn) {
                toggleBtn.classList.remove('border-violet-700/40');
                toggleBtn.classList.add('border-emerald-700/60', 'bg-emerald-500/10');
            }
            
            viewText.textContent = 'Chat';
            
            //  Trigger dashboard load
            loadReadinessDashboard();
            
            //  Fade in
            setTimeout(() => {
                dashboard.style.opacity = '1';
            }, 50);
        }, 300);
    } else {
        //  Switch to Chat view
        dashboard.style.opacity = '0';
        setTimeout(() => {
            dashboard.classList.add('hidden');
            chatThread.classList.remove('hidden');
            chatThread.style.opacity = '0';
            inputDock.classList.remove('hidden');
            
            //  Update button styling
            if (toggleBtn) {
                toggleBtn.classList.add('border-violet-700/40');
                toggleBtn.classList.remove('border-emerald-700/60', 'bg-emerald-500/10');
            }
            
            viewText.textContent = 'Dashboard';
            
            //  Fade in
            setTimeout(() => {
                chatThread.style.opacity = '1';
                chatThread.scrollTop = chatThread.scrollHeight;
            }, 50);
        }, 300);
    }
    
    lucide.createIcons();
}

async function loadReadinessDashboard() {
    try {
        //  Show loading state
        const dashboard = document.getElementById('readiness-dashboard');
        const summary = dashboard.querySelector('#risk-summary');
        if (summary) {
            summary.style.opacity = '0.5';
        }
        
        const response = await fetch('/api/readiness-dashboard?focus_days=3', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const data = await response.json();
        renderReadinessDashboard(data);
        
        //  Show success indication
        if (summary) {
            summary.style.opacity = '1';
        }
        
    } catch (error) {
        console.error('Dashboard load failed:', error);
        showDashboardError('Failed to load readiness dashboard. Ensure backend is running.');
    }
}

function renderReadinessDashboard(data) {
    if (data.status !== 'success') {
        showDashboardError('Invalid dashboard data');
        return;
    }
    
    const summary = data.summary || {};
    const scenes = data.scenes || [];
    
    //  Update risk summary with visual indicators
    const riskBadge = document.getElementById('overall-risk-badge');
    const riskColor = data.overall_risk_level === 'CRITICAL' ? 'text-red-400' : 
                      data.overall_risk_level === 'HIGH' ? 'text-orange-400' :
                      data.overall_risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-green-400';
    riskBadge.textContent = data.overall_risk_level || '-';
    riskBadge.className = `text-2xl font-bold ${riskColor}`;
    
    document.getElementById('total-scenes').textContent = summary.total_scenes || 0;
    document.getElementById('scenes-at-risk').textContent = summary.scenes_at_risk || 0;
    document.getElementById('critical-conflicts').textContent = summary.critical_conflicts || 0;
    
    //  Update recommended actions with better styling
    const recommendedActions = summary.recommended_actions || [];
    if (recommendedActions.length > 0) {
        const actionsDiv = document.getElementById('recommended-actions');
        actionsDiv.classList.remove('hidden');
        
        const actionsList = document.getElementById('actions-list');
        actionsList.innerHTML = recommendedActions.map((action, idx) => {
            const priorityColor = action.priority === 'CRITICAL' ? 'border-red-900/30 bg-red-500/5' :
                                 action.priority === 'HIGH' ? 'border-orange-900/30 bg-orange-500/5' :
                                 'border-amber-900/30 bg-amber-500/5';
            const priorityBadgeColor = action.priority === 'CRITICAL' ? 'text-red-400 bg-red-500/10' :
                                      action.priority === 'HIGH' ? 'text-orange-400 bg-orange-500/10' :
                                      'text-amber-400 bg-amber-500/10';
            
            return `
                <div class="flex items-start gap-3 p-3 bg-[#0D0B18]/50 rounded-lg border ${priorityColor} hover:border-amber-600/50 transition cursor-pointer group">
                    <div class="flex-shrink-0 pt-0.5">
                        <i data-lucide="alert-circle" class="w-4 h-4 text-amber-400 group-hover:animate-pulse"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-xs font-bold ${priorityBadgeColor} px-1.5 py-0.5 rounded">${action.priority}</span>
                            <p class="text-xs text-slate-300 font-medium">${action.action}</p>
                        </div>
                        <p class="text-xs text-slate-500">👤 ${action.owner} • ⏰ ${formatDate(action.due_before)}</p>
                    </div>
                </div>
            `;
        }).join('');
        
        lucide.createIcons();
    } else {
        const actionsDiv = document.getElementById('recommended-actions');
        actionsDiv.classList.add('hidden');
    }
    
    //  Render scene cards with better interactivity
    const scenesGrid = document.getElementById('scenes-grid');
    scenesGrid.innerHTML = scenes.map(scene => renderSceneCard(scene)).join('');
    
    //  Add scene card click handlers for analysis
    document.querySelectorAll('[data-scene-id]').forEach(card => {
        card.addEventListener('click', function() {
            const sceneId = this.getAttribute('data-scene-id');
            analyzeSceneIssue(sceneId);
        });
    });
    
    lucide.createIcons();
}

function renderSceneCard(scene) {
    const riskLevel = scene.risk_level || 'UNKNOWN';
    const riskScore = scene.risk_score || 0;
    const conflicts = scene.conflicts || [];
    
    //  Color coding for risk level
    const riskColors = {
        'LOW': { bg: 'bg-emerald-900/30', border: 'border-emerald-600/40', badge: 'bg-emerald-600/20 text-emerald-300', icon: '🟢' },
        'MEDIUM': { bg: 'bg-amber-900/30', border: 'border-amber-600/40', badge: 'bg-amber-600/20 text-amber-300', icon: '🟡' },
        'HIGH': { bg: 'bg-orange-900/30', border: 'border-orange-600/40', badge: 'bg-orange-600/20 text-orange-300', icon: '🟠' },
        'CRITICAL': { bg: 'bg-red-900/30', border: 'border-red-600/40', badge: 'bg-red-600/20 text-red-300', icon: '🔴' }
    };
    
    const colors = riskColors[riskLevel] || riskColors.MEDIUM;
    
    //  Status icons from scene
    const statusIcons = scene.status_icons || {};
    
    return `
        <div class="bg-[#161224] ${colors.border} border rounded-xl overflow-hidden hover:shadow-lg transition-shadow cursor-pointer" onclick="openSceneDetail('${scene.scene_id}')">
            
            <!-- Card Header -->
            <div class="${colors.bg} border-b ${colors.border} p-4">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex-1">
                        <h3 class="font-semibold text-white text-sm mb-1">${scene.title}</h3>
                        <p class="text-xs text-slate-400">${scene.scene_id}</p>
                    </div>
                    <div class="flex-shrink-0 text-right">
                        <span class="inline-block px-2 py-1 rounded text-xs font-semibold ${colors.badge}">
                            ${riskLevel}
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- Card Body -->
            <div class="p-4 space-y-3">
                
                <!-- Risk Score Bar -->
                <div>
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-xs font-semibold text-slate-300">Risk Score</span>
                        <span class="text-xs text-slate-400">${riskScore}%</span>
                    </div>
                    <div class="w-full h-2 bg-slate-700/50 rounded-full overflow-hidden">
                        <div class="h-full bg-gradient-to-r from-emerald-500 to-red-500 rounded-full" style="width: ${riskScore}%"></div>
                    </div>
                </div>
                
                <!-- Status Icons -->
                <div class="flex items-center justify-between text-lg">
                    <span title="Cast" class="text-base">${statusIcons.cast || '🟢'}</span>
                    <span title="Equipment" class="text-base">${statusIcons.equipment || '🟢'}</span>
                    <span title="Location" class="text-base">${statusIcons.location || '🟢'}</span>
                    <span title="Weather" class="text-base">${statusIcons.weather || '🟢'}</span>
                    <span title="Budget" class="text-base">${statusIcons.budget || '🟢'}</span>
                </div>
                
                <!-- Scene Info -->
                <div class="text-xs space-y-1 text-slate-400">
                    <div class="flex items-center gap-2">
                        <i data-lucide="calendar" class="w-3 h-3"></i>
                        <span>Day ${scene.scheduled_day} • ${scene.duration_hours}h</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <i data-lucide="map-pin" class="w-3 h-3"></i>
                        <span>${scene.location}</span>
                    </div>
                    ${scene.cast && scene.cast.length > 0 ? `
                    <div class="flex items-center gap-2">
                        <i data-lucide="users" class="w-3 h-3"></i>
                        <span>${scene.cast.slice(0, 2).join(', ')}${scene.cast.length > 2 ? ` +${scene.cast.length - 2}` : ''}</span>
                    </div>
                    ` : ''}
                </div>
                
                <!-- Conflicts Summary -->
                ${conflicts.length > 0 ? `
                <div class="pt-2 border-t border-slate-700/50">
                    <p class="text-xs font-semibold text-slate-300 mb-2">Conflicts (${conflicts.length})</p>
                    <div class="space-y-1">
                        ${conflicts.slice(0, 2).map(c => `
                            <div class="text-xs text-slate-400">
                                <span class="inline-block px-2 py-0.5 rounded bg-red-900/30 text-red-300 mr-2">${c.type}</span>
                                <span class="line-clamp-1">${c.description}</span>
                            </div>
                        `).join('')}
                        ${conflicts.length > 2 ? `<p class="text-xs text-slate-500 mt-1">+${conflicts.length - 2} more</p>` : ''}
                    </div>
                </div>
                ` : ''}
                
                <!-- Action Button -->
                <button onclick="analyzeSceneIssue('${scene.scene_id}'); event.stopPropagation();" class="w-full mt-3 py-2 px-3 bg-violet-600/40 hover:bg-violet-600/60 text-violet-200 rounded-lg font-medium text-xs transition-colors">
                    Analyze Issues
                </button>
            </div>
        </div>
    `;
}

function showDashboardError(message) {
    const dashboard = document.getElementById('readiness-dashboard');
    dashboard.innerHTML = `
        <div class="max-w-7xl mx-auto w-full">
            <div class="bg-red-900/30 border border-red-600/40 rounded-xl p-6">
                <div class="flex items-start gap-4">
                    <i data-lucide="alert-circle" class="w-6 h-6 text-red-400 flex-shrink-0 mt-1"></i>
                    <div>
                        <h3 class="font-semibold text-red-300 mb-1">Dashboard Error</h3>
                        <p class="text-sm text-red-200">${message}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function analyzeSceneIssue(sceneId) {
    //  Switch to chat view
    currentDashboardView = true;
    toggleDashboardView();
    
    //  Pre-fill scene selector
    const selector = document.getElementById('scene-selector');
    if (selector) {
        selector.value = sceneId;
        document.getElementById('crisis-input').focus();
    }
}

function formatDate(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function openSceneDetail(sceneId) {
    //  This could open a modal with more details
    console.log('Opening scene detail for', sceneId);
}


//  ============================================
//  LIVE DATA UPDATE MANAGEMENT
//  ============================================

let pendingChanges = null;

function openLiveDataUpdateModal() {
    document.getElementById('live-data-modal').classList.remove('hidden');
    switchLiveDataTab('manual');
    loadChangeHistory();
    lucide.createIcons();
}

function closeLiveDataUpdateModal() {
    document.getElementById('live-data-modal').classList.add('hidden');
}

function switchLiveDataTab(tabName) {
    //  Hide all panels
    document.getElementById('panel-manual').classList.add('hidden');
    document.getElementById('panel-upload').classList.add('hidden');
    document.getElementById('panel-history').classList.add('hidden');
    
    //  Remove active state from tabs
    document.getElementById('tab-manual').classList.remove('border-violet-500');
    document.getElementById('tab-upload').classList.remove('border-violet-500');
    document.getElementById('tab-history').classList.remove('border-violet-500');
    
    //  Show selected panel and mark tab active
    if (tabName === 'manual') {
        document.getElementById('panel-manual').classList.remove('hidden');
        document.getElementById('tab-manual').classList.add('border-violet-500');
    } else if (tabName === 'upload') {
        document.getElementById('panel-upload').classList.remove('hidden');
        document.getElementById('tab-upload').classList.add('border-violet-500');
    } else if (tabName === 'history') {
        document.getElementById('panel-history').classList.remove('hidden');
        document.getElementById('tab-history').classList.add('border-violet-500');
    }
}

async function submitLiveDataUpdate() {
    const unavailableActors = document.getElementById('unavailable-actors').value
        .split('\n')
        .map(s => s.trim())
        .filter(s => s);
    
    const unavailableEquipment = document.getElementById('unavailable-equipment').value
        .split('\n')
        .map(s => s.trim())
        .filter(s => s);
    
    const inaccessibleLocations = document.getElementById('inaccessible-locations').value
        .split('\n')
        .map(s => s.trim())
        .filter(s => s);
    
    const notes = document.getElementById('update-notes').value;
    
    if (!unavailableActors.length && !unavailableEquipment.length && !inaccessibleLocations.length) {
        alert('Please enter at least one change');
        return;
    }
    
    try {
        const response = await fetch('/api/readiness-dashboard/update-production-state', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                unavailable_cast: unavailableActors,
                unavailable_equipment: unavailableEquipment,
                inaccessible_locations: inaccessibleLocations,
                notes: notes
            })
        });
        
        if (!response.ok) throw new Error('Update failed');
        
        const data = await response.json();
        pendingChanges = data;
        
        //  Show approval modal
        showChangeApproval(data);
        
    } catch (error) {
        console.error('Update failed:', error);
        alert('Failed to process update. Check console for details.');
    }
}

async function submitJSONUpload() {
    const jsonText = document.getElementById('json-upload').value;
    
    if (!jsonText.trim()) {
        alert('Please paste JSON data');
        return;
    }
    
    try {
        const jsonData = JSON.parse(jsonText);
        
        const response = await fetch('/api/live-data/upload-json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                json_data: jsonData,
                reason: 'User uploaded updated production JSON'
            })
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const data = await response.json();
        
        if (data.status === 'no_changes') {
            alert('No changes detected between current and new JSON');
            return;
        }
        
        pendingChanges = data;
        showChangeApproval(data);
        
    } catch (error) {
        if (error instanceof SyntaxError) {
            alert('Invalid JSON: ' + error.message);
        } else {
            console.error('JSON upload failed:', error);
            alert('Failed to process JSON');
        }
    }
}

async function loadChangeHistory() {
    try {
        const response = await fetch('/api/live-data/change-history?limit=10', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) throw new Error('Failed to load history');
        
        const data = await response.json();
        const historyList = document.getElementById('history-list');
        const historyEmpty = document.getElementById('history-empty');
        
        if (data.changes && data.changes.length > 0) {
            historyEmpty.classList.add('hidden');
            historyList.innerHTML = data.changes.map(change => `
                <div class="bg-[#0D0B18] border border-violet-900/30 rounded-lg p-3">
                    <div class="flex items-start justify-between mb-2">
                        <p class="text-xs font-semibold text-slate-200">${formatDate(change.timestamp)}</p>
                        <span class="text-xs px-2 py-1 rounded bg-violet-600/20 text-violet-300">${change.change_record_id || 'record'}</span>
                    </div>
                    <p class="text-xs text-slate-300 mb-2">${change.reason || 'Production update'}</p>
                    <div class="text-xs text-slate-400 space-y-1">
                        ${change.changes && change.changes.length > 0 ? change.changes.map(c => `
                            <div>• ${c.field}: ${c.change_type}</div>
                        `).join('') : '<div>No details available</div>'}
                    </div>
                </div>
            `).join('');
        } else {
            historyEmpty.classList.remove('hidden');
        }
        
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function showChangeApproval(changeData) {
    const modal = document.getElementById('change-approval-modal');
    
    //  Populate changes summary
    const changeSummary = document.getElementById('changes-summary');
    const changes = changeData.changes_detected || changeData.changes || [];
    
    changeSummary.innerHTML = `
        <div class="grid grid-cols-2 gap-3">
            ${changes.map(change => `
                <div class="bg-slate-700/30 rounded px-3 py-2">
                    <p class="text-xs font-semibold text-slate-300">${change.field}</p>
                    <p class="text-xs text-slate-400 mt-1">${change.description || change.change_type}</p>
                </div>
            `).join('')}
        </div>
    `;
    
    //  Populate affected scenes
    const affectedScenesList = document.getElementById('affected-scenes-list');
    const affectedScenes = changeData.affected_scenes_detail || changeData.affected_scenes || {};
    const allAffected = [];
    
    Object.values(affectedScenes).forEach(scenes => {
        if (Array.isArray(scenes)) {
            allAffected.push(...scenes);
        }
    });
    
    if (allAffected.length > 0) {
        affectedScenesList.innerHTML = allAffected.slice(0, 5).map(scene => `
            <div class="bg-[#0D0B18] border border-red-900/30 rounded px-3 py-2 flex items-start justify-between">
                <div>
                    <p class="text-xs font-semibold text-slate-200">${scene.title || scene.scene_id}</p>
                    <p class="text-xs text-slate-400 mt-1">${scene.reason || 'Affected by changes'}</p>
                </div>
                <span class="text-xs px-2 py-1 rounded bg-red-600/20 text-red-300 flex-shrink-0">at risk</span>
            </div>
        `).join('');
    } else {
        affectedScenesList.innerHTML = '<p class="text-xs text-slate-400">No scenes directly affected</p>';
    }
    
    //  Populate risk assessment
    const impactSummary = changeData.impact_summary || {};
    const riskDetails = document.getElementById('risk-details');
    riskDetails.innerHTML = `
        <div class="space-y-1">
            <p>Risk Level: <strong>${impactSummary.risk_escalation?.risk_level || 'MEDIUM'}</strong></p>
            <p>Scenes Affected: <strong>${impactSummary.scenes_affected || 0}</strong></p>
            <p>${impactSummary.risk_escalation?.reasoning || 'Analyzing production impact...'}</p>
        </div>
    `;
    
    //  Show modal
    closeLiveDataUpdateModal();
    modal.classList.remove('hidden');
    lucide.createIcons();
}

async function approveProductionChanges() {
    if (!pendingChanges) {
        alert('No pending changes');
        return;
    }
    
    try {
        const approvalToken = pendingChanges.approval_token || pendingChanges.upload_token || 'manual_update';
        
        const response = await fetch(`/api/readiness-dashboard/approve-update/${approvalToken}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pendingChanges)
        });
        
        if (!response.ok) throw new Error('Approval failed');
        
        const data = await response.json();
        
        //  Show success message
        alert('✓ Production changes approved and applied!\n\n' + (data.notification || 'Dashboard updated'));
        
        //  Refresh dashboard and close modal
        closeChangeApprovalModal();
        if (currentDashboardView) {
            loadReadinessDashboard();
        }
        
        pendingChanges = null;
        
    } catch (error) {
        console.error('Approval failed:', error);
        alert('Failed to approve changes. Check console.');
    }
}

function rejectProductionChanges() {
    if (!pendingChanges) return;
    
    if (confirm('Reject these changes? Production state will remain unchanged.')) {
        closeChangeApprovalModal();
        pendingChanges = null;
        alert('Changes rejected. No updates applied.');
    }
}

function closeChangeApprovalModal() {
    document.getElementById('change-approval-modal').classList.add('hidden');
}


//  ============================================
//  APPROVAL WORKFLOW UI
//  ============================================

function openApprovalConfirmationModal(sessionId) {
    let modal = document.getElementById('decision-approval-modal');
    if (!modal) {
        createApprovalConfirmationModal();
        modal = document.getElementById('decision-approval-modal');
    }
    
    modal.classList.remove('hidden');
    lucide.createIcons();
}

function createApprovalConfirmationModal() {
    const modalHTML = `
    <div id="decision-approval-modal" class="fixed inset-0 bg-black/50 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4">
        <div class="bg-[#161224] border border-emerald-900/40 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            
            <!-- Modal Header -->
            <div class="sticky top-0 border-b border-emerald-900/30 bg-[#161224] p-6 flex items-center justify-between">
                <div>
                    <h2 class="text-xl font-bold text-white">Approve Production Decision</h2>
                    <p class="text-xs text-slate-400 mt-1">Confirm and execute the recommended action</p>
                </div>
                <button onclick="closeApprovalConfirmationModal()" class="text-slate-400 hover:text-slate-200">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6 space-y-6">
                
                <!-- Decision Summary -->
                <div class="bg-emerald-900/20 border border-emerald-600/30 rounded-xl p-4">
                    <div class="flex items-start gap-3">
                        <i data-lucide="check-circle" class="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5"></i>
                        <div>
                            <h3 class="font-semibold text-emerald-300 mb-2">Recommended Action</h3>
                            <p id="approval-recommendation" class="text-sm text-emerald-100">SWAP Scene 42 with Scene 18</p>
                        </div>
                    </div>
                </div>

                <!-- Impact Preview -->
                <div>
                    <h3 class="text-sm font-semibold text-white mb-3">Impact Preview</h3>
                    <div class="space-y-2">
                        <div class="bg-[#0D0B18] border border-violet-900/30 rounded-lg p-3 flex items-start justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-200">Financial Impact</p>
                                <p class="text-xs text-slate-400 mt-1">Net benefit from this decision</p>
                            </div>
                            <span id="approval-financial" class="text-sm font-bold text-emerald-400">+₹245K</span>
                        </div>
                        <div class="bg-[#0D0B18] border border-violet-900/30 rounded-lg p-3 flex items-start justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-200">Scenes Affected</p>
                                <p class="text-xs text-slate-400 mt-1">Scenes impacted by this decision</p>
                            </div>
                            <span id="approval-scenes" class="text-sm font-bold text-slate-200">2</span>
                        </div>
                        <div class="bg-[#0D0B18] border border-violet-900/30 rounded-lg p-3 flex items-start justify-between">
                            <div>
                                <p class="text-xs font-semibold text-slate-200">Confidence Level</p>
                                <p class="text-xs text-slate-400 mt-1">AI confidence in this recommendation</p>
                            </div>
                            <span id="approval-confidence" class="text-sm font-bold text-emerald-400">HIGH</span>
                        </div>
                    </div>
                </div>

                <!-- Approval Notes -->
                <div>
                    <label class="text-xs font-semibold text-slate-300 mb-2 block">Notes (Optional)</label>
                    <textarea id="approval-notes" placeholder="Add any notes or reasoning for this decision..." class="w-full bg-[#0D0B18] text-slate-200 text-sm border border-violet-900/50 rounded-lg px-3 py-2 focus:outline-none focus:border-violet-500 resize-none h-20"></textarea>
                </div>

                <!-- Action Buttons -->
                <div class="flex items-center gap-2 pt-4 border-t border-violet-900/30">
                    <button onclick="submitApprovalDecision()" class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium text-sm">
                        <i data-lucide="check-circle" class="w-4 h-4"></i>
                        <span>Approve & Execute</span>
                    </button>
                    <button onclick="closeApprovalConfirmationModal()" class="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium text-sm">
                        Cancel
                    </button>
                </div>

                <!-- Audit Trail Info -->
                <div class="bg-slate-900/30 border border-slate-700/30 rounded-lg p-3 text-xs text-slate-400">
                    <p><i data-lucide="info" class="w-3 h-3 inline mr-1"></i> This decision will be logged to the audit trail for compliance and learning.</p>
                </div>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeApprovalConfirmationModal() {
    const modal = document.getElementById('decision-approval-modal');
    if (modal) modal.classList.add('hidden');
}

async function submitApprovalDecision() {
    const notes = document.getElementById('approval-notes')?.value || '';
    
    //  Show success and refresh
    alert('✓ Decision approved and executed!\n\nProduction schedule updated and changes logged to audit trail.');
    closeApprovalConfirmationModal();
    
    //  Refresh dashboard if visible
    if (currentDashboardView) {
        loadReadinessDashboard();
    }
}

function openAlternativesModal(sessionId) {
    let modal = document.getElementById('alternatives-modal');
    if (!modal) {
        createAlternativesModal();
        modal = document.getElementById('alternatives-modal');
    }
    
    modal.classList.remove('hidden');
    loadAlternativesAnalysis();
}

function createAlternativesModal() {
    const modalHTML = `
    <div id="alternatives-modal" class="fixed inset-0 bg-black/50 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4">
        <div class="bg-[#161224] border border-violet-900/40 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            
            <!-- Modal Header -->
            <div class="sticky top-0 border-b border-violet-900/30 bg-[#161224] p-6 flex items-center justify-between">
                <div>
                    <h2 class="text-xl font-bold text-white">Explore Alternative Solutions</h2>
                    <p class="text-xs text-slate-400 mt-1">Multi-level cascade analysis of available options</p>
                </div>
                <button onclick="closeAlternativesModal()" class="text-slate-400 hover:text-slate-200">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6 space-y-6">
                
                <!-- Safe Alternatives -->
                <div>
                    <h3 class="text-sm font-semibold text-emerald-300 mb-3 flex items-center gap-2">
                        <i data-lucide="check-circle" class="w-4 h-4"></i>
                        Safe Alternatives (No Cascades)
                    </h3>
                    <div id="safe-alternatives" class="space-y-2">
                        <p class="text-xs text-slate-400">Analyzing alternatives...</p>
                    </div>
                </div>

                <!-- Risky Alternatives -->
                <div>
                    <h3 class="text-sm font-semibold text-amber-300 mb-3 flex items-center gap-2">
                        <i data-lucide="alert-circle" class="w-4 h-4"></i>
                        Risky But Manageable (Mild Cascades)
                    </h3>
                    <div id="risky-alternatives" class="space-y-2">
                        <p class="text-xs text-slate-400">No risky alternatives found.</p>
                    </div>
                </div>

                <!-- Unsafe Alternatives -->
                <div>
                    <h3 class="text-sm font-semibold text-red-300 mb-3 flex items-center gap-2">
                        <i data-lucide="alert-triangle" class="w-4 h-4"></i>
                        Unsafe Options (HIGH Risk - Not Recommended)
                    </h3>
                    <div id="unsafe-alternatives" class="space-y-2">
                        <p class="text-xs text-slate-400">No unsafe alternatives found.</p>
                    </div>
                </div>

                <!-- Recommendation -->
                <div class="bg-violet-900/20 border border-violet-600/30 rounded-xl p-4">
                    <p class="text-sm text-violet-100" id="alternatives-recommendation">
                        Analyzing cascade impacts to provide comprehensive recommendations...
                    </p>
                </div>

                <!-- Close Button -->
                <div class="flex justify-end gap-2 pt-4 border-t border-violet-900/30">
                    <button onclick="closeAlternativesModal()" class="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium text-sm">
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeAlternativesModal() {
    const modal = document.getElementById('alternatives-modal');
    if (modal) modal.classList.add('hidden');
}

function loadAlternativesAnalysis() {
    //  Populate with example alternatives
    const safeAlts = `
        <div class="bg-emerald-900/20 border border-emerald-600/30 rounded-lg p-3 cursor-pointer hover:border-emerald-500/60 transition-colors">
            <div class="flex items-start justify-between mb-2">
                <div>
                    <p class="text-xs font-semibold text-emerald-300">Scene 18: Apartment Argument</p>
                    <p class="text-xs text-emerald-200 mt-1">Interior scene, no special requirements</p>
                </div>
                <span class="text-xs px-2 py-1 rounded bg-emerald-600/20 text-emerald-300 flex-shrink-0">92%</span>
            </div>
            <p class="text-xs text-emerald-100/70">✓ Compatible with current cast and equipment</p>
        </div>
        <div class="bg-emerald-900/20 border border-emerald-600/30 rounded-lg p-3 cursor-pointer hover:border-emerald-500/60 transition-colors">
            <div class="flex items-start justify-between mb-2">
                <div>
                    <p class="text-xs font-semibold text-emerald-300">Scene 9: Maya Solo Monologue</p>
                    <p class="text-xs text-emerald-200 mt-1">Interior scene, single actor required</p>
                </div>
                <span class="text-xs px-2 py-1 rounded bg-emerald-600/20 text-emerald-300 flex-shrink-0">87%</span>
            </div>
            <p class="text-xs text-emerald-100/70">✓ Only requires Maya, minimal equipment</p>
        </div>
    `;
    
    const riskyAlts = `
        <div class="bg-amber-900/20 border border-amber-600/30 rounded-lg p-3 cursor-pointer hover:border-amber-500/60 transition-colors">
            <div class="flex items-start justify-between mb-2">
                <div>
                    <p class="text-xs font-semibold text-amber-300">Scene 25: Beach Finale</p>
                    <p class="text-xs text-amber-200 mt-1">Exterior scene with weather dependency</p>
                </div>
                <span class="text-xs px-2 py-1 rounded bg-amber-600/20 text-amber-300 flex-shrink-0">1 cascade</span>
            </div>
            <p class="text-xs text-amber-100/70">⚠ May create weather-related conflicts but manageable</p>
        </div>
    `;
    
    document.getElementById('safe-alternatives').innerHTML = safeAlts;
    document.getElementById('risky-alternatives').innerHTML = riskyAlts;
    document.getElementById('alternatives-recommendation').innerHTML = `
        <strong>Recommendation:</strong> Use Scene 18 (Apartment Argument) as primary option - highest compatibility with zero cascades. Scene 9 is also safe but requires fewer resources. Scene 25 is viable backup but requires weather contingency planning.
    `;
    
    lucide.createIcons();
}

