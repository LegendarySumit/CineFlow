// ============================================
// CineFlow Project Management
// ============================================

let activeProject = null;
let allProjects = [];
let currentSessionId = null;
let currentMode = 'quick';
let isAnalyzing = false;
let sessionHistory = [];

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    initializeApp();
});

function initializeApp() {
    loadAllProjects();
    setupEventListeners();
    currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
    document.getElementById('session-id-display').textContent = `Session: #${currentSessionId.slice(-8)}`;
}

function setupEventListeners() {
    const crisisInput = document.getElementById('crisis-input');
    if (crisisInput) {
        crisisInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey && !isAnalyzing) {
                submitCrisis();
            }
        });
    }
}

// ============================================
// PROJECT MANAGEMENT
// ============================================

function openProjectSetupModal() {
    document.getElementById('project-setup-modal').classList.remove('hidden');
}

function closeProjectSetupModal() {
    document.getElementById('project-setup-modal').classList.add('hidden');
}

function handleProjectFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            createProject(data);
        } catch (err) {
            alert('Invalid JSON file: ' + err.message);
        }
    };
    reader.readAsText(file);
}

function handleProjectJsonPaste() {
    const jsonText = document.getElementById('project-json-input').value.trim();
    if (!jsonText) {
        alert('Please paste JSON data');
        return;
    }
    
    try {
        const data = JSON.parse(jsonText);
        console.log('Parsed JSON:', data);
        createProject(data);
    } catch (err) {
        console.error('JSON parse error:', err);
        alert('Invalid JSON: ' + err.message);
    }
}

function createProject(productionData) {
    const projectId = productionData.production_id || 'proj_' + Math.random().toString(36).substring(2, 9);
    
    fetch('/api/projects/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            project_id: projectId,
            production_data: productionData
        })
    })
    .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
    })
    .then(data => {
        if (data.status === 'success') {
            alert(`Project "${productionData.name}" created successfully!`);
            closeProjectSetupModal();
            document.getElementById('project-json-input').value = '';
            loadAllProjects();
        } else {
            const errors = data.errors ? data.errors.join(', ') : data.message;
            alert('Error: ' + errors);
        }
    })
    .catch(e => {
        console.error('Create project error:', e);
        alert('Failed to create project: ' + e.message);
    });
}

function loadAllProjects() {
    fetch('/api/projects/list')
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            allProjects = data.projects || [];
            renderProjectsList();
        })
        .catch(e => {
            console.error('Error loading projects:', e);
            document.getElementById('projects-list').innerHTML = '<p class="text-xs text-slate-500 px-2 py-3">Error loading projects</p>';
        });
}

function renderProjectsList() {
    const container = document.getElementById('projects-list');
    
    if (allProjects.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-500 px-2 py-3">No projects yet</p>';
        return;
    }
    
    container.innerHTML = allProjects.map(proj => `
        <div onclick="loadProjectUI('${proj.project_id}')" class="p-2 cursor-pointer rounded-xl border transition-all ${
            activeProject?.project_id === proj.project_id
                ? 'bg-violet-600/20 border-violet-500/50'
                : 'bg-[#1C1733]/50 border-violet-900/30 hover:border-violet-500/50'
        }">
            <p class="font-medium text-slate-200 text-xs">${proj.name}</p>
            <p class="text-[10px] text-slate-400">${proj.scenes_count} scenes • ₹${(proj.budget / 100000).toFixed(1)}L</p>
        </div>
    `).join('');
}

function loadProjectUI(projectId) {
    fetch(`/api/projects/load/${projectId}`, { method: 'POST' })
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            if (!data || data.status !== 'success') {
                alert('Failed to load project: ' + (data?.message || 'Unknown error'));
                return;
            }
            
            activeProject = data.metadata || data;
            
            // Update UI
            document.getElementById('project-name').textContent = data.metadata?.name || data.name || 'Unknown';
            document.getElementById('project-meta').textContent = `${data.metadata?.scenes_count || 0} scenes • Budget: ₹${(data.metadata?.budget || 0) / 100000}L`;
            document.getElementById('active-project-display').classList.remove('hidden');
            document.getElementById('budget-display').classList.remove('hidden');
            document.getElementById('budget-amount').textContent = `₹${((data.metadata?.budget || 0) / 100000).toFixed(1)}L`;
            document.getElementById('input-dock').classList.remove('hidden');
            
            // Populate scene selector
            const sceneSelector = document.getElementById('scene-selector');
            sceneSelector.innerHTML = '<option value="">Select a scene...</option>' + 
                (data.scenes || []).map(s => `<option value="${s.scene_id}">${s.scene_id}: ${s.title}</option>`).join('');
            
            // Update projects list visual
            renderProjectsList();
            
            // Create new session for this project
            currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 9);
            sessionHistory = [];
            document.getElementById('session-id-display').textContent = `Session: #${currentSessionId.slice(-8)}`;
            renderSessionList();
        })
        .catch(e => alert('Error loading project: ' + e.message));
}

function renderSessionList() {
    const container = document.getElementById('session-history-list');
    
    if (!activeProject) {
        container.innerHTML = '<p class="text-xs text-slate-500 px-2 py-3">Load a project first</p>';
        return;
    }
    
    if (sessionHistory.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-500 px-2 py-3">No analyses yet</p>';
        return;
    }
    
    container.innerHTML = sessionHistory.map((session, idx) => `
        <div class="p-2 bg-[#1C1733]/50 rounded-xl border border-violet-900/30 text-xs">
            <p class="font-medium text-slate-200">${session.scene}</p>
            <p class="text-[10px] text-slate-400 truncate">${session.crisis}</p>
        </div>
    `).join('');
}

// ============================================
// ANALYSIS MODE
// ============================================

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

// ============================================
// CRISIS ANALYSIS
// ============================================

async function submitCrisis() {
    if (!activeProject) {
        alert('Please load a project first');
        return;
    }
    
    const sceneId = document.getElementById('scene-selector').value;
    const description = document.getElementById('crisis-input').value.trim();
    
    if (!sceneId) {
        alert('Please select a scene');
        return;
    }
    
    if (!description) {
        alert('Please describe the crisis');
        return;
    }
    
    if (isAnalyzing) return;
    isAnalyzing = true;
    
    const thread = document.getElementById('chat-thread');
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    
    // Add user message
    thread.innerHTML += `
        <div class="flex justify-end">
            <div class="bg-violet-700 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-xl text-sm shadow-md">
                <span class="font-mono text-xs opacity-75 block mb-1">Scene: ${sceneId} | Mode: ${currentMode.toUpperCase()}</span>
                ${description}
            </div>
        </div>
    `;
    
    // Add loading response
    const responseId = 'resp_' + Date.now();
    thread.innerHTML += `
        <div id="${responseId}" class="agent-response bg-[#161224] border border-violet-900/40 rounded-2xl p-6 shadow-xl space-y-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <i data-lucide="cpu" class="w-5 h-5 text-violet-400 animate-spin"></i>
                    <h3 class="font-bold text-white text-base">Analysis in Progress</h3>
                </div>
                <span class="text-xs font-mono text-amber-400 border border-amber-500/30 bg-amber-500/10 px-2 py-1 rounded">Running</span>
            </div>
            <div id="${responseId}_progress" class="text-xs font-mono bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30 text-violet-300 space-y-2">
                <div>[⏳] Phase 1: Planning production schedule impact...</div>
            </div>
        </div>
    `;
    
    document.getElementById('crisis-input').value = '';
    lucide.createIcons();
    thread.scrollTop = thread.scrollHeight;
    
    try {
        const response = await fetch('/api/analyze-crisis', {
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
        
        const data = await response.json();
        renderAgentResponse(responseId, data);
        
        // Store in session history only after successful analysis
        sessionHistory.push({ scene: sceneId, crisis: description, mode: currentMode });
        renderSessionList();
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById(responseId).innerHTML = `
            <div class="flex items-center justify-between border-b border-red-900/30 pb-3">
                <div class="flex items-center gap-3">
                    <i data-lucide="alert-circle" class="w-5 h-5 text-red-400"></i>
                    <h3 class="font-bold text-red-400">Analysis Failed</h3>
                </div>
            </div>
            <p class="text-slate-300 text-sm">Could not reach backend. Ensure it's running on port 8000.</p>
            <button onclick="submitCrisis()" class="mt-3 px-4 py-2 bg-red-900/30 border border-red-700/50 text-red-200 rounded-lg text-xs">
                Retry
            </button>
        `;
        lucide.createIcons();
    }
    
    isAnalyzing = false;
    submitBtn.disabled = false;
}

function renderAgentResponse(elementId, data) {
    const el = document.getElementById(elementId);
    
    if (!data || data.status !== 'success') {
        el.innerHTML = `<p class="text-slate-300">Analysis failed: ${data?.message || 'Unknown error'}</p>`;
        return;
    }
    
    const analysis = data.analysis || {};
    
    // Extract recommendation - handle both string and object formats
    let recText = 'Review and implement the recommended action';
    const recData = analysis.recommended_action;
    if (typeof recData === 'string') {
        recText = recData;
    } else if (recData && typeof recData === 'object') {
        if (recData.reasoning) {
            recText = recData.reasoning;
        } else if (recData.action) {
            recText = `${recData.action}${recData.target_scene ? ` to ${recData.target_scene}` : ''}`;
        }
    }
    
    // Use executive summary as primary narrative, fallback to recommendation text
    const narrative = data.executive_summary || recText;
    const fin = analysis.financial_impact || {};
    const risk = analysis.risk_level || 'MEDIUM';
    
    const riskColors = {
        'LOW': 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
        'MEDIUM': 'text-amber-400 bg-amber-500/10 border-amber-500/30',
        'HIGH': 'text-orange-400 bg-orange-500/10 border-orange-500/30',
        'CRITICAL': 'text-red-400 bg-red-500/10 border-red-500/30'
    };
    
    // Format financial metrics if available
    const finDisplay = fin.daily_burn || fin.setup_cost || fin.net_benefit ? `
        <div class="grid grid-cols-3 gap-3 my-4 font-mono text-xs">
            <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                <span class="text-slate-400 block">Daily Burn</span>
                <span class="text-white font-bold text-sm">₹${(fin.daily_burn || 0).toLocaleString()}</span>
            </div>
            <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                <span class="text-slate-400 block">Setup Cost</span>
                <span class="text-amber-400 font-bold text-sm">₹${(fin.setup_cost || 0).toLocaleString()}</span>
            </div>
            <div class="bg-[#0D0B18] p-3 rounded-xl border border-violet-900/30">
                <span class="text-slate-400 block">Net Savings</span>
                <span class="text-emerald-400 font-bold text-sm">₹${(fin.net_benefit || 0).toLocaleString()}</span>
            </div>
        </div>
    ` : '';
    
    el.innerHTML = `
        <div class="flex items-center justify-between border-b border-violet-900/30 pb-3">
            <div class="flex items-center gap-3">
                <i data-lucide="check-circle-2" class="w-5 h-5 text-emerald-400"></i>
                <h3 class="font-bold text-white text-base">Executive Recommendation</h3>
            </div>
            <span class="text-xs font-mono ${riskColors[risk] || riskColors.MEDIUM} px-2 py-1 rounded border">${risk}</span>
        </div>
        
        <p class="text-slate-300 text-sm leading-relaxed mt-4 mb-4">${narrative}</p>
        
        ${finDisplay}
        
        <div class="flex items-center gap-2 pt-2">
            <button class="action-button primary" onclick="approveDecision()">/button>
            <button class="action-button secondary">
                <i data-lucide="arrow-right-left" class="w-3 h-3"></i>
                Alternatives
            </button>
        </div>
    `;
    lucide.createIcons();
}

function approveDecision() {
    alert('Decision approved! (Implementation coming soon)');
}
