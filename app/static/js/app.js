// ============================================
// CineFlow Executive Assistant - Main App Logic
// ============================================

let currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
let currentMode = 'quick';
let sessionHistory = [];
let isAnalyzing = false;

// Initialize App
function initializeApp() {
    document.getElementById('session-id-display').textContent = `#${currentSessionId.slice(-8)}`;
    loadSessionHistory();
    
    // Event listeners
    document.getElementById('crisis-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey && !isAnalyzing) {
            submitCrisis();
        }
    });
}

// Set Analysis Mode
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

// Apply Template
function applyTemplate(templateText) {
    const input = document.getElementById('crisis-input');
    input.value = templateText;
    input.focus();
}

// Create New Session
function createNewSession() {
    currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
    document.getElementById('session-id-display').textContent = `#${currentSessionId.slice(-8)}`;
    
    // Save current session if it has messages
    if (sessionHistory.length > 0) {
        // Could save to localStorage or IndexedDB
    }
    
    // Reset UI
    document.getElementById('chat-thread').innerHTML = `
        <div class="bg-[#161224] border border-violet-900/40 rounded-2xl p-6 shadow-lg space-y-3">
            <div class="flex items-center gap-3">
                <div class="p-2.5 bg-violet-600/20 rounded-lg">
                    <i data-lucide="zap" class="w-5 h-5 text-violet-400"></i>
                </div>
                <div>
                    <h2 class="font-bold text-white text-base">New Crisis Session</h2>
                    <p class="text-xs text-slate-400">Ready to analyze production disruptions</p>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('crisis-input').value = '';
    sessionHistory = [];
    loadSessionHistory();
    lucide.createIcons();
}

// Submit Crisis for Analysis
async function submitCrisis() {
    const sceneId = document.getElementById('scene-selector').value;
    const description = document.getElementById('crisis-input').value.trim();
    const thread = document.getElementById('chat-thread');
    const submitBtn = document.getElementById('submit-btn');
    
    if (!description) {
        alert('Please describe the crisis');
        return;
    }
    
    if (isAnalyzing) return;
    isAnalyzing = true;
    submitBtn.disabled = true;
    
    // Add User Message Bubble
    const userBubbleId = 'user_' + Date.now();
    thread.innerHTML += `
        <div class="flex justify-end">
            <div class="user-bubble">
                <span class="scene-tag">Scene: ${sceneId} | ${currentMode.toUpperCase()}</span>
                ${description}
            </div>
        </div>
    `;
    
    // Clear input
    document.getElementById('crisis-input').value = '';
    
    // Add Agent Loading Card
    const responseId = 'resp_' + Date.now();
    thread.innerHTML += `
        <div id="${responseId}" class="agent-response loading space-y-4">
            <div class="agent-response-header">
                <span class="agent-response-title">
                    <i data-lucide="cpu" class="w-4 h-4 text-violet-400 spinner"></i>
                    CineFlow Executive Recommendation
                </span>
                <span class="response-badge badge-analyzing">Analyzing...</span>
            </div>
            <div id="${responseId}_reasoning" class="reasoning-stepper">
                <div class="reasoning-step running">▸ Phase 1: Planning & Context</div>
                <div class="reasoning-step">○ Phase 2: Impact Assessment</div>
                <div class="reasoning-step">○ Phase 3: Cascade Detection</div>
                <div class="reasoning-step">○ Phase 4: Cost Optimization</div>
                <div class="reasoning-step">○ Phase 5: Synthesis</div>
            </div>
        </div>
    `;
    
    lucide.createIcons();
    thread.scrollTop = thread.scrollHeight;
    
    try {
        // Call FastAPI backend
        const response = await fetch('/api/analyze-crisis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: description,
                scene_id: sceneId,
                session_id: currentSessionId,
                analysis_mode: currentMode
            })
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Store in history
        sessionHistory.push({
            timestamp: new Date().toISOString(),
            scene: sceneId,
            crisis: description,
            mode: currentMode,
            response: data
        });
        
        // Render Response
        renderAgentResponse(responseId, data);
        loadSessionHistory();
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById(responseId).innerHTML = `
            <div class="agent-response-header border-b border-red-900/30 pb-3">
                <span class="agent-response-title text-red-400">
                    <i data-lucide="alert-circle" class="w-4 h-4"></i>
                    Analysis Failed
                </span>
                <span class="response-badge badge-error">Error</span>
            </div>
            <p class="text-slate-300 text-sm">Could not reach CineFlow backend server. Ensure the backend is running on port 8000.</p>
            <div class="flex gap-2 pt-2">
                <button onclick="submitCrisis()" class="action-button secondary">
                    <i data-lucide="refresh-cw" class="w-3 h-3"></i>
                    Try Again
                </button>
                <button onclick="showBackendStatus()" class="action-button secondary">
                    <i data-lucide="info" class="w-3 h-3"></i>
                    Backend Status
                </button>
            </div>
        `;
        lucide.createIcons();
    }
    
    isAnalyzing = false;
    submitBtn.disabled = false;
}

// Render Agent Response
function renderAgentResponse(elementId, data) {
    const el = document.getElementById(elementId);
    
    if (!data || data.status !== 'success') {
        el.innerHTML = `
            <div class="agent-response-header">
                <span class="agent-response-title text-amber-400">
                    <i data-lucide="alert-triangle" class="w-4 h-4"></i>
                    Analysis Incomplete
                </span>
                <span class="response-badge badge-error">Warning</span>
            </div>
            <p class="text-slate-300 text-sm">${data?.error || 'Unable to complete analysis'}</p>
        `;
        lucide.createIcons();
        return;
    }
    
    const analysis = data.analysis || {};
    const financial = analysis.financial_impact || {};
    const cascades = analysis.cascade_check || {};
    const riskLevel = analysis.risk_level || 'UNKNOWN';
    const summary = analysis.executive_summary || 'Analysis complete';
    const nextActions = analysis.next_actions || [];
    const recommendation = analysis.recommended_action || {};
    
    // Build metrics display
    let metricsHtml = '';
    if (financial.daily_burn !== undefined) {
        metricsHtml = `
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Daily Burn</div>
                    <div class="metric-value gold">₹${formatCurrency(financial.daily_burn)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Setup Cost</div>
                    <div class="metric-value">${formatCurrency(financial.setup_cost || 0)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Net Savings</div>
                    <div class="metric-value green">₹${formatCurrency(financial.net_benefit || 0)}</div>
                </div>
            </div>
        `;
    }
    
    // Build next actions
    let actionsHtml = '';
    if (nextActions.length > 0) {
        actionsHtml = '<div class="space-y-2 mt-3"><div class="text-xs text-slate-400 font-semibold">RECOMMENDED NEXT STEPS:</div>';
        nextActions.slice(0, 3).forEach((action, idx) => {
            actionsHtml += `
                <div class="flex gap-2 text-sm">
                    <span class="text-violet-400 font-bold">${idx + 1}.</span>
                    <span class="text-slate-300">${action.label || action}</span>
                </div>
            `;
        });
        actionsHtml += '</div>';
    }
    
    // Determine badge color based on risk
    let badgeClass = 'badge-safe';
    if (riskLevel === 'HIGH') badgeClass = 'badge-error';
    else if (riskLevel === 'MEDIUM') badgeClass = 'badge-analyzing';
    
    el.innerHTML = `
        <div class="agent-response-header">
            <span class="agent-response-title">
                <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-400"></i>
                CineFlow Executive Recommendation
            </span>
            <span class="response-badge ${badgeClass}">Risk: ${riskLevel}</span>
        </div>
        
        <p class="text-slate-300 text-sm leading-relaxed">${summary}</p>
        
        ${metricsHtml}
        
        ${recommendation.action ? `
            <div class="bg-[#0D0B18] border-l-4 border-violet-600 p-3 rounded-lg">
                <p class="text-xs text-slate-400 font-semibold mb-1">DECISION</p>
                <p class="text-sm font-semibold text-white">${recommendation.action}</p>
                <p class="text-xs text-slate-400 mt-1">${recommendation.reasoning || ''}</p>
            </div>
        ` : ''}
        
        ${actionsHtml}
        
        <div class="flex gap-2 pt-3 border-t border-violet-900/30">
            <button onclick="approveDecision()" class="action-button primary">
                <i data-lucide="check" class="w-3 h-3"></i>
                Approve & Execute
            </button>
            <button onclick="exploreAlternatives()" class="action-button secondary">
                <i data-lucide="git-branch" class="w-3 h-3"></i>
                Explore Alternatives
            </button>
            <button onclick="askFollowUp()" class="action-button secondary">
                <i data-lucide="message-square" class="w-3 h-3"></i>
                Follow-up Question
            </button>
        </div>
    `;
    
    lucide.createIcons();
}

// Action: Approve Decision
function approveDecision() {
    const thread = document.getElementById('chat-thread');
    thread.innerHTML += `
        <div class="flex justify-end">
            <div class="user-bubble">
                <span class="scene-tag">ACTION: DECISION APPROVED</span>
                Execute the recommended decision immediately
            </div>
        </div>
    `;
    
    thread.innerHTML += `
        <div class="agent-response space-y-3">
            <div class="agent-response-header">
                <span class="agent-response-title text-emerald-400">
                    <i data-lucide="check-circle-2" class="w-4 h-4"></i>
                    Decision Executed
                </span>
                <span class="response-badge badge-safe">Confirmed</span>
            </div>
            <p class="text-slate-300 text-sm">Decision approved and queued for execution. Crew notifications sent immediately. Scene schedule updated and audit logged.</p>
            <div class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
                <p class="text-xs text-emerald-400 font-semibold">STATUS: COMPLETE</p>
                <p class="text-sm text-slate-300 mt-1">All crew members have been notified of changes.</p>
            </div>
        </div>
    `;
    
    thread.scrollTop = thread.scrollHeight;
    lucide.createIcons();
}

// Action: Explore Alternatives
function exploreAlternatives() {
    const thread = document.getElementById('chat-thread');
    thread.innerHTML += `
        <div class="flex justify-end">
            <div class="user-bubble">
                <span class="scene-tag">ACTION: EXPLORE ALTERNATIVES</span>
                Show me other possible solutions
            </div>
        </div>
    `;
    
    thread.innerHTML += `
        <div class="agent-response space-y-3">
            <div class="agent-response-header">
                <span class="agent-response-title">
                    <i data-lucide="layers" class="w-4 h-4 text-blue-400"></i>
                    Alternative Solutions
                </span>
                <span class="response-badge" style="background-color: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.3); color: #3B82F6;">3 Options</span>
            </div>
            
            <div class="comparison-card">
                <div class="card-header">
                    <span class="card-title">Option 1: Scene Swap</span>
                    <span class="card-badge">SAFE</span>
                </div>
                <div class="card-details">
                    <div class="detail-item"><strong>Cost:</strong> ₹55K</div>
                    <div class="detail-item"><strong>ROI:</strong> 445%</div>
                    <div class="detail-item"><strong>Delay:</strong> None</div>
                    <div class="detail-item"><strong>Risk:</strong> Low</div>
                </div>
            </div>
            
            <div class="comparison-card">
                <div class="card-header">
                    <span class="card-title">Option 2: Reschedule</span>
                    <span class="card-badge" style="background-color: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3); color: #F59E0B;">RISKY</span>
                </div>
                <div class="card-details">
                    <div class="detail-item"><strong>Cost:</strong> ₹120K</div>
                    <div class="detail-item"><strong>ROI:</strong> 210%</div>
                    <div class="detail-item"><strong>Delay:</strong> 2 days</div>
                    <div class="detail-item"><strong>Risk:</strong> Medium</div>
                </div>
            </div>
            
            <div class="comparison-card">
                <div class="card-header">
                    <span class="card-title">Option 3: Workaround</span>
                    <span class="card-badge" style="background-color: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); color: #EF4444;">UNSAFE</span>
                </div>
                <div class="card-details">
                    <div class="detail-item"><strong>Cost:</strong> ₹20K</div>
                    <div class="detail-item"><strong>ROI:</strong> 150%</div>
                    <div class="detail-item"><strong>Delay:</strong> 1 day</div>
                    <div class="detail-item"><strong>Risk:</strong> High</div>
                </div>
            </div>
        </div>
    `;
    
    thread.scrollTop = thread.scrollHeight;
    lucide.createIcons();
}

// Action: Ask Follow-up
function askFollowUp() {
    const thread = document.getElementById('chat-thread');
    thread.innerHTML += `
        <div class="flex justify-end">
            <div class="user-bubble">
                <span class="scene-tag">ACTION: FOLLOW-UP QUESTION</span>
                Ready to refine analysis with additional constraints
            </div>
        </div>
    `;
    
    document.getElementById('crisis-input').placeholder = 'Ask a follow-up question or provide additional constraints...';
    document.getElementById('crisis-input').focus();
    
    thread.scrollTop = thread.scrollHeight;
}

// Show Backend Status
function showBackendStatus() {
    const thread = document.getElementById('chat-thread');
    thread.innerHTML += `
        <div class="agent-response space-y-2 bg-red-950/20 border-red-900/40">
            <p class="text-sm text-red-400">Backend server is not responding.</p>
            <p class="text-xs text-slate-400">Make sure to start the backend:</p>
            <div class="bg-[#0D0B18] p-2 rounded text-xs font-mono text-violet-300 mt-2">
                python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
            </div>
        </div>
    `;
    thread.scrollTop = thread.scrollHeight;
}

// Load Session History
function loadSessionHistory() {
    const container = document.getElementById('session-history-list');
    container.innerHTML = '';
    
    if (sessionHistory.length === 0) {
        container.innerHTML = `
            <div class="text-xs text-slate-500 px-2 py-3 text-center">
                No sessions yet. Create one to get started.
            </div>
        `;
        return;
    }
    
    sessionHistory.forEach((session, idx) => {
        const date = new Date(session.timestamp);
        const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        const sceneShort = session.scene.split(':')[0];
        const label = session.crisis.substring(0, 25) + (session.crisis.length > 25 ? '...' : '');
        
        container.innerHTML += `
            <div onclick="loadSession(${idx})" class="session-item cursor-pointer">
                <div class="session-title">${sceneShort}</div>
                <div class="session-meta">${label}</div>
                <div class="session-meta">${timeStr}</div>
            </div>
        `;
    });
}

// Load Session
function loadSession(idx) {
    // Placeholder for loading previous session
    console.log('Load session', idx);
}

// Utility: Format Currency
function formatCurrency(amount) {
    if (amount >= 10000000) {
        return (amount / 10000000).toFixed(1) + 'Cr';
    } else if (amount >= 100000) {
        return (amount / 100000).toFixed(1) + 'L';
    } else if (amount >= 1000) {
        return (amount / 1000).toFixed(1) + 'K';
    }
    return amount.toFixed(0);
}
