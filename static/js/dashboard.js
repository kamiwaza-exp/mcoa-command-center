// MCOA Dashboard JavaScript - Real-time WebSocket Communication

// Initialize WebSocket connection
const socket = io();

// State management
const state = {
    toolCounts: {},
    activeTools: new Set(),
    lastToolRuns: {}, // tool_name -> { section, parameters, result, duration, start_ts, end_ts }
    sessionStartTime: null,
    stats: {
        total_calls: 0,
        s2_calls: 0,
        s3_calls: 0,
        s4_calls: 0,
        avg_response_time: 0
    }
};

// DOM Elements
const elements = {
    chatMessages: document.getElementById('chat-messages'),
    queryInput: document.getElementById('query-input'),
    sendBtn: document.getElementById('send-btn'),
    clearBtn: document.getElementById('clear-btn'),
    testAllBtn: document.getElementById('test-all-btn'),
    executionDisplay: document.getElementById('execution-display'),
    timelineDisplay: document.getElementById('timeline-display'),
    toolDetails: document.getElementById('tool-details'),
    currentTime: document.getElementById('current-time'),
    runHistory: document.getElementById('run-history'),
    execModal: document.getElementById('exec-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    modalClose: document.getElementById('modal-close')
};

// Markdown rendering helper
function renderMarkdown(content) {
    // Configure marked options for safety
    marked.setOptions({
        breaks: true,  // Convert \n to <br>
        gfm: true,     // GitHub Flavored Markdown
        sanitize: false // We'll trust our own content
    });
    
    // Render markdown to HTML
    return marked.parse(content);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeFragoElements();  // Initialize FRAGO elements after DOM is ready
    updateTimestamp();
    setInterval(updateTimestamp, 1000);
    setInterval(updateSessionTime, 1000);
    
    // Initialize RF Monitor
    if (typeof initRFMonitor === 'function') {
        initRFMonitor();
    }
});

// Event Listeners
function initializeEventListeners() {
    // Send query on button click
    elements.sendBtn.addEventListener('click', sendQuery);
    
    // Send query on Enter key
    elements.queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendQuery();
        }
    });
    
    // Clear conversation
    elements.clearBtn.addEventListener('click', () => {
        if (confirm('Clear conversation history?')) {
            socket.emit('clear_conversation');
        }
    });
    
    // Test all tools
    elements.testAllBtn.addEventListener('click', () => {
        socket.emit('test_all_tools');
        addSystemMessage('Running all tool tests...');
    });
    
    // Quick action buttons
    document.querySelectorAll('.quick-btn[data-query]').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            elements.queryInput.value = query;
            sendQuery();
        });
    });
    
    // Tool item clicks: show latest execution in Active Tool Execution panel
    document.querySelectorAll('.tool-item').forEach(item => {
        item.addEventListener('click', () => {
            const toolName = item.getAttribute('data-tool');
            const rec = state.lastToolRuns[toolName];
            if (rec) {
                showExecutionRecord(toolName, rec);
            } else {
                elements.executionDisplay.innerHTML = `<div class="no-activity">No recorded execution for ${toolName}</div>`;
            }
        });
    });

    // Modal wiring
    if (elements.modalClose && elements.execModal) {
        elements.modalClose.addEventListener('click', hideModal);
        elements.execModal.addEventListener('click', (e) => {
            if (e.target === elements.execModal) hideModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') hideModal();
        });
    }
}

// Send Query
function sendQuery() {
    const query = elements.queryInput.value.trim();
    if (!query) return;
    
    // Add user message to chat
    addMessage('user', query);
    
    // Send to server
    socket.emit('send_query', { query: query });
    
    // Clear input
    elements.queryInput.value = '';
    elements.queryInput.focus();
}

// WebSocket Event Handlers
socket.on('connect', () => {
    console.log('Connected to MCOA server');
    addSystemMessage('Connected to MCOA Command Center');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    addSystemMessage('Connection lost. Attempting to reconnect...');
});

socket.on('tools_info', (data) => {
    console.log('Received tools info:', data);
});

socket.on('stats_update', (stats) => {
    updateStats(stats);
});

socket.on('query_status', (data) => {
    if (data.status === 'processing') {
        addSystemMessage('Processing query...');
    }
});

socket.on('query_response', (data) => {
    // Ensure we display string content; if an object slipped through, stringify it
    let content = data && data.response;
    if (content && typeof content === 'object') {
        try { content = JSON.stringify(content, null, 2); } catch (e) { content = String(content); }
    }
    addMessage('assistant', content || '');
    
    // Update response time if available
    if (data.response_time) {
        const timeStr = `Response time: ${data.response_time.toFixed(2)}s`;
        addSystemMessage(timeStr);
    }
});

socket.on('query_error', (data) => {
    let err = data && data.error;
    if (err && typeof err === 'object') {
        try { err = JSON.stringify(err, null, 2); } catch (e) { err = String(err); }
    }
    addMessage('error', `Error: ${err}`);
});

socket.on('tool_start', (data) => {
    console.log('Tool started:', data);
    
    // Mark tool as active
    const toolElement = document.querySelector(`[data-tool="${data.tool_name}"]`);
    if (toolElement) {
        toolElement.classList.add('active');
        state.activeTools.add(data.tool_name);
    }
    
    // Update execution display
    showToolExecution(data);

    // Record latest run start
    state.lastToolRuns[data.tool_name] = {
        section: data.section,
        parameters: data.parameters,
        start_ts: Date.now(),
    };
    
    // Add to timeline
    addToTimeline(data.tool_name, data.section, 'start');
});

socket.on('tool_complete', (data) => {
    console.log('Tool completed:', data);
    
    // Mark tool as completed
    const toolElement = document.querySelector(`[data-tool="${data.tool_name}"]`);
    if (toolElement) {
        toolElement.classList.remove('active');
        toolElement.classList.add('completed');
        setTimeout(() => {
            toolElement.classList.remove('completed');
        }, 500);
        
        // Update tool count
        updateToolCount(data.tool_name);
    }
    
    // Update execution display with result
    updateToolExecution(data);
    // Also refresh popout content with the final result
    enableExecutionPopout(data.tool_name, data.section, data.parameters, data.result, data.duration);

    // Update last run record
    if (!state.lastToolRuns[data.tool_name]) {
        state.lastToolRuns[data.tool_name] = {};
    }
    state.lastToolRuns[data.tool_name] = {
        ...(state.lastToolRuns[data.tool_name] || {}),
        section: data.section,
        parameters: data.parameters,
        result: data.result,
        duration: data.duration,
        end_ts: Date.now(),
    };
    
    // Add to timeline
    addToTimeline(data.tool_name, data.section, 'complete', data.duration);
    
    // Update tool details
    showToolDetails(data.tool_name, data);
});

socket.on('tool_error', (data) => {
    console.log('Tool error:', data);
    
    const toolElement = document.querySelector(`[data-tool="${data.tool_name}"]`);
    if (toolElement) {
        toolElement.classList.remove('active');
    }
    
    addMessage('error', `Tool error in ${data.tool_name}: ${data.error}`);
});

socket.on('guardrail_triggered', (data) => {
    console.log('Guardrail triggered:', data);
    
    // Flash guardrail indicator
    const guardrails = document.querySelectorAll('.guardrail-item');
    guardrails.forEach(g => {
        g.classList.add('triggered');
        setTimeout(() => g.classList.remove('triggered'), 2000);
    });
    
    addMessage('warning', `Security Block: ${data.violation}`);
});

socket.on('conversation_cleared', () => {
    elements.chatMessages.innerHTML = '<div class="system-message">Conversation cleared. Ready for new queries.</div>';
    elements.executionDisplay.innerHTML = '<div class="no-activity">No active tool execution</div>';
    elements.timelineDisplay.innerHTML = '';
    elements.toolDetails.innerHTML = '<div class="no-data">No tool executions yet</div>';
    
    // Reset tool counts
    document.querySelectorAll('.tool-count').forEach(el => {
        el.textContent = '0';
    });
    
    state.toolCounts = {};
    state.lastToolRuns = {};

    // Clear run history
    if (elements.runHistory) {
        elements.runHistory.innerHTML = '<div class="no-data">No runs yet</div>';
    }
});

// Receive a run summary for historical selection
socket.on('run_summary', (summary) => {
    if (!elements.runHistory) return;
    // Create a card entry
    const card = document.createElement('div');
    card.className = 'run-card';
    card.dataset.runId = summary.run_id || '';

    const header = document.createElement('div');
    header.className = 'run-header';

    const title = document.createElement('div');
    title.className = 'run-title';
    title.textContent = (summary.query || 'Query').slice(0, 80);

    const meta = document.createElement('div');
    meta.className = 'run-meta';
    const duration = typeof summary.response_time === 'number' ? summary.response_time.toFixed(2) : '—';
    meta.textContent = `${duration}s`;

    header.appendChild(title);
    header.appendChild(meta);

    const toolsList = document.createElement('ul');
    toolsList.className = 'run-tools-list';
    const tools = Array.isArray(summary.tools) ? summary.tools : [];
    if (tools.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No tools invoked';
        toolsList.appendChild(li);
    } else {
        tools.forEach((t) => {
            const li = document.createElement('li');
            const sec = t.section ? ` [${t.section}]` : '';
            const dur = typeof t.duration === 'number' ? ` (${t.duration.toFixed(2)}s)` : '';
            li.textContent = `${t.tool_name || 'tool'}${sec}${dur}`;
            li.addEventListener('click', () => {
                // Show details for this tool in the Tool Details panel
                showToolDetails(t.tool_name || 'tool', {
                    tool_name: t.tool_name,
                    section: t.section,
                    duration: t.duration,
                    result: t.result,
                    parameters: t.parameters,
                });
            });
            toolsList.appendChild(li);
        });
    }

    // Response preview (click to push into chat)
    const preview = document.createElement('div');
    preview.className = 'run-preview';
    preview.style.marginTop = '0.25rem';
    preview.style.whiteSpace = 'pre-wrap';
    preview.style.color = 'var(--text-secondary)';
    preview.textContent = (summary.response_preview || '').slice(0, 200);
    preview.title = 'Click to paste response into chat';
    preview.addEventListener('click', () => {
        if (elements.queryInput) {
            elements.queryInput.value = summary.response_preview || '';
            elements.queryInput.focus();
        }
    });

    card.appendChild(header);
    card.appendChild(toolsList);
    card.appendChild(preview);

    // Insert newest on top
    if (elements.runHistory.children.length && !elements.runHistory.firstElementChild.classList.contains('no-data')) {
        elements.runHistory.insertBefore(card, elements.runHistory.firstChild);
    } else {
        elements.runHistory.innerHTML = '';
        elements.runHistory.appendChild(card);
    }
});

// UI Update Functions
function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    if (type === 'user') {
        header.textContent = '👤 USER';
    } else if (type === 'assistant') {
        header.textContent = '🎖️ MCOA';
    } else if (type === 'error') {
        header.textContent = '❌ ERROR';
        messageDiv.style.borderColor = '#e74c3c';
    } else if (type === 'warning') {
        header.textContent = '⚠️ WARNING';
        messageDiv.style.borderColor = '#f39c12';
    }
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Render markdown for assistant and system messages
    if (type === 'assistant' || type === 'system') {
        contentDiv.innerHTML = renderMarkdown(content);
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(header);
    messageDiv.appendChild(contentDiv);
    
    elements.chatMessages.appendChild(messageDiv);
    // Defer scroll to next frame to ensure layout has updated
    requestAnimationFrame(() => {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    });
}

function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.textContent = content;

    elements.chatMessages.appendChild(messageDiv);
    requestAnimationFrame(() => {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    });
}

function showToolExecution(data) {
    const html = `
        <div class="tool-execution">
            <div class="tool-execution-header">
                <span>🔧 ${data.tool_name}</span>
                <span>${data.section}</span>
            </div>
            <div class="tool-params">
                <strong>Parameters:</strong>
                ${JSON.stringify(data.parameters, null, 2)}
            </div>
            <div id="exec-${data.tool_name}" class="tool-result">
                <strong>Executing...</strong>
            </div>
        </div>
    `;
    
    elements.executionDisplay.innerHTML = html;
    enableExecutionPopout(data.tool_name, data.section, data.parameters, null, null);
}

// Render latest recorded execution for a tool into the Active Tool Execution panel
function showExecutionRecord(toolName, rec) {
    const paramsStr = safeJSONStringify(rec.parameters);
    const resultStr = safeJSONStringify(rec.result);
    const dur = typeof rec.duration === 'number' ? `${rec.duration.toFixed(3)}s` : '—';
    const html = `
        <div class="tool-execution">
            <div class="tool-execution-header">
                <span>🔧 ${toolName}</span>
                <span>${rec.section || ''}</span>
            </div>
            <div class="tool-params">
                <strong>Parameters:</strong>
                <pre>${paramsStr}</pre>
            </div>
            <div class="tool-result">
                <strong>Last Result (${dur}):</strong>
                <pre>${resultStr}</pre>
            </div>
        </div>
    `;
    elements.executionDisplay.innerHTML = html;
    enableExecutionPopout(toolName, rec.section, rec.parameters, rec.result, rec.duration);
}

function updateToolExecution(data) {
    const resultElement = document.getElementById(`exec-${data.tool_name}`);
    if (resultElement) {
        const resultStr = safeJSONStringify(data.result);
        resultElement.innerHTML = `
            <strong>Result (${data.duration.toFixed(3)}s):</strong>
            <pre>${resultStr}</pre>
        `;
    }
}

function addToTimeline(toolName, section, status, duration = null) {
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
    });
    
    const item = document.createElement('div');
    item.className = 'timeline-item';
    
    let sectionColor = '#3498db';
    if (section === 'S-2') sectionColor = '#9b59b6';
    else if (section === 'S-3') sectionColor = '#f39c12';
    
    item.innerHTML = `
        <span class="timeline-time">${time}</span>
        <span class="timeline-tool" style="color: ${sectionColor}">
            ${toolName} ${duration ? `(${duration.toFixed(2)}s)` : ''}
        </span>
        <div class="timeline-bar"></div>
    `;
    
    elements.timelineDisplay.insertBefore(item, elements.timelineDisplay.firstChild);
    
    // Keep only last 10 items
    while (elements.timelineDisplay.children.length > 10) {
        elements.timelineDisplay.removeChild(elements.timelineDisplay.lastChild);
    }
}

function updateToolCount(toolName) {
    if (!state.toolCounts[toolName]) {
        state.toolCounts[toolName] = 0;
    }
    state.toolCounts[toolName]++;
    
    const toolElement = document.querySelector(`[data-tool="${toolName}"]`);
    if (toolElement) {
        const countElement = toolElement.querySelector('.tool-count');
        if (countElement) {
            countElement.textContent = state.toolCounts[toolName];
        }
    }
}

function showToolDetails(toolName, data = null) {
    if (data) {
        const resultStr = safeJSONStringify(data.result);
        const html = `
            <div style="padding: 0.5rem;">
                <strong>${toolName}</strong>
                <div style="margin-top: 0.5rem; font-size: 0.75rem;">
                    <div>Duration: ${data.duration.toFixed(3)}s</div>
                    <div>Status: ${data.success ? '✅ Success' : '❌ Error'}</div>
                    <div style="margin-top: 0.5rem;">
                        <strong>Last Result:</strong>
                        <pre style="margin-top: 0.25rem; font-size: 0.7rem;">${resultStr}</pre>
                    </div>
                </div>
            </div>
        `;
        elements.toolDetails.innerHTML = html;
    }
}

// Utility: safe JSON stringify
function safeJSONStringify(obj) {
    if (obj == null) return '';
    try { return JSON.stringify(obj, null, 2); } catch (e) { return String(obj); }
}

// Hook the Active Tool Execution panel to open a modal with full content
function enableExecutionPopout(toolName, section, parameters, result, duration) {
    if (!elements.executionDisplay) return;
    const container = elements.executionDisplay.closest('.execution-panel');
    if (!container) return;
    container.style.cursor = 'zoom-in';
    container.onclick = () => openExecutionModal(toolName, section, parameters, result, duration);
}

function openExecutionModal(toolName, section, parameters, result, duration) {
    if (!elements.execModal) return;
    const paramsStr = safeJSONStringify(parameters);
    const resultStr = safeJSONStringify(result);
    const dur = typeof duration === 'number' ? `${duration.toFixed(3)}s` : '';
    elements.modalTitle.textContent = `🔧 ${toolName}${section ? ` — ${section}` : ''}`;
    elements.modalBody.innerHTML = `
        <div style="margin-bottom: 0.75rem;">${dur ? `<strong>Duration:</strong> ${dur}` : ''}</div>
        <div style="margin-bottom: 0.75rem;">
            <strong>Parameters</strong>
            <pre style="margin-top: 0.25rem;">${paramsStr}</pre>
        </div>
        <div>
            <strong>Result</strong>
            <pre style="margin-top: 0.25rem;">${resultStr || '(no result yet)'}</pre>
        </div>
    `;
    elements.execModal.classList.remove('hidden');
}

function hideModal() {
    if (elements.execModal) {
        elements.execModal.classList.add('hidden');
    }
}

function updateStats(stats) {
    state.stats = stats;
    
    document.getElementById('stat-total').textContent = stats.total_calls || 0;
    document.getElementById('stat-s2').textContent = stats.s2_calls || 0;
    document.getElementById('stat-s3').textContent = stats.s3_calls || 0;
    document.getElementById('stat-s4').textContent = stats.s4_calls || 0;
    document.getElementById('stat-avg').textContent = 
        stats.avg_response_time ? `${stats.avg_response_time.toFixed(2)}s` : '0.0s';
    
    if (stats.session_start && !state.sessionStartTime) {
        state.sessionStartTime = new Date(stats.session_start);
    }
}

function updateTimestamp() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
    });
    const dateStr = now.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
    });
    
    if (elements.currentTime) {
        elements.currentTime.textContent = `${dateStr} ${timeStr}`;
    }
}

function updateSessionTime() {
    if (state.sessionStartTime) {
        const now = new Date();
        const diff = Math.floor((now - state.sessionStartTime) / 1000);
        const minutes = Math.floor(diff / 60);
        const seconds = diff % 60;
        
        const timeStr = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        document.getElementById('stat-session').textContent = timeStr;
    }
}

// Auto-focus on input
elements.queryInput.focus();

// ============== FRAGO FUNCTIONALITY ==============

// FRAGO state management
const fragoState = {
    currentFrago: null,
    decisionPackage: null,
    requiredReports: [],
    generatedReports: {}
};

// FRAGO Modal Elements (initialized after DOM loads)
let fragoElements = {};

// Initialize FRAGO elements and event listeners
function initializeFragoElements() {
    fragoElements = {
        fetchBtn: document.getElementById('fetch-frago-btn'),
        fragoModal: document.getElementById('frago-modal'),
        fragoText: document.getElementById('frago-text'),
        processBtn: document.getElementById('process-frago-btn'),
        cancelBtn: document.getElementById('cancel-frago-btn'),
        fragoModalClose: document.getElementById('frago-modal-close'),
        
        decisionModal: document.getElementById('decision-modal'),
        decisionStatus: document.getElementById('go-no-go'),
        analysisContent: document.getElementById('analysis-content'),
        reportsList: document.getElementById('reports-list'),
        generateAllBtn: document.getElementById('generate-all-reports-btn'),
        closeDecisionBtn: document.getElementById('close-decision-btn'),
        decisionModalClose: document.getElementById('decision-modal-close'),
        
        reportModal: document.getElementById('report-modal'),
        reportContent: document.getElementById('report-content'),
        downloadReportBtn: document.getElementById('download-report-btn'),
        submitReportBtn: document.getElementById('submit-report-btn'),
        closeReportBtn: document.getElementById('close-report-btn'),
        reportModalClose: document.getElementById('report-modal-close')
    };
    
    // Initialize FRAGO event listeners
    if (fragoElements.fetchBtn) {
        // Fetch FRAGO button
        fragoElements.fetchBtn.addEventListener('click', async () => {
            await fetchFrago();
        });
    }
    
    // Process FRAGO button
    fragoElements.processBtn?.addEventListener('click', () => {
        if (fragoState.currentFrago) {
            processFrago();
        }
    });
    
    // Cancel/Close buttons
    fragoElements.cancelBtn?.addEventListener('click', () => hideFragoModal());
    fragoElements.fragoModalClose?.addEventListener('click', () => hideFragoModal());
    fragoElements.closeDecisionBtn?.addEventListener('click', () => hideDecisionModal());
    fragoElements.decisionModalClose?.addEventListener('click', () => hideDecisionModal());
    fragoElements.closeReportBtn?.addEventListener('click', () => hideReportModal());
    fragoElements.reportModalClose?.addEventListener('click', () => hideReportModal());
    
    // Generate all reports button
    fragoElements.generateAllBtn?.addEventListener('click', () => {
        generateAllReports();
    });
    
    // Submit report button
    fragoElements.submitReportBtn?.addEventListener('click', () => {
        submitCurrentReport();
    });
    
    // Download report button
    fragoElements.downloadReportBtn?.addEventListener('click', () => {
        downloadCurrentReport();
    });
}

// Fetch FRAGO from server
async function fetchFrago() {
    try {
        addSystemMessage('Fetching FRAGO...');
        const response = await fetch('/api/frago/fetch');
        const frago = await response.json();
        
        fragoState.currentFrago = frago;
        displayFrago(frago);
    } catch (error) {
        console.error('Error fetching FRAGO:', error);
        addMessage('error', 'Failed to fetch FRAGO: ' + error.message);
    }
}

// Display FRAGO in modal
function displayFrago(frago) {
    if (fragoElements.fragoText) {
        fragoElements.fragoText.textContent = frago.text;
        document.getElementById('frago-modal-title').textContent = `📋 FRAGO ${frago.frago_id}`;
    }
    showFragoModal();
}

// Process FRAGO through backend
function processFrago() {
    if (!fragoState.currentFrago) return;
    
    hideFragoModal();
    addMessage('system', `Processing FRAGO ${fragoState.currentFrago.frago_id}...`);
    
    // Send to backend for processing
    socket.emit('process_frago', {
        frago: fragoState.currentFrago.text
    });
}

// Handle FRAGO processing status
socket.on('frago_status', (data) => {
    addSystemMessage(`FRAGO Processing: ${data.message}`);
});

// Handle FRAGO decision package
socket.on('frago_decision_package', (data) => {
    console.log('Received decision package:', data);
    fragoState.decisionPackage = data;
    fragoState.requiredReports = data.required_reports || [];
    
    displayDecisionPackage(data);
});

// Display decision package
function displayDecisionPackage(package) {
    // Set GO/NO-GO decision
    const goNoGo = fragoElements.decisionStatus;
    if (goNoGo) {
        goNoGo.className = 'go-no-go-indicator';
        goNoGo.textContent = package.decision || 'PENDING';
        
        if (package.decision === 'GO') {
            goNoGo.classList.add('go');
        } else if (package.decision === 'NO-GO') {
            goNoGo.classList.add('no-go');
        } else {
            goNoGo.classList.add('go-caveats');
        }
    }
    
    // Display analysis
    if (fragoElements.analysisContent) {
        fragoElements.analysisContent.innerHTML = renderMarkdown(package.analysis || 'No analysis available');
    }
    
    // Display required reports
    if (fragoElements.reportsList) {
        fragoElements.reportsList.innerHTML = '';
        const reports = package.required_reports || [];
        
        if (reports.length === 0) {
            fragoElements.reportsList.innerHTML = '<p>No reports required</p>';
        } else {
            reports.forEach(reportType => {
                const reportCard = createReportCard(reportType);
                fragoElements.reportsList.appendChild(reportCard);
            });
        }
    }
    
    showDecisionModal();
}

// Create report card element
function createReportCard(reportType) {
    const card = document.createElement('div');
    card.className = 'report-card';
    card.dataset.reportType = reportType;
    
    const icon = reportType === 'LOGSTAT' ? '📦' : 
                 reportType === 'PERSTAT' ? '👥' : 
                 reportType === 'SPOT' ? '🎯' : '📄';
    
    card.innerHTML = `
        <div class="report-card-header">
            <span class="report-icon">${icon}</span>
            <span class="report-type">${reportType}</span>
        </div>
        <div class="report-card-status" id="status-${reportType}">
            <span class="status-text">Not Generated</span>
        </div>
        <div class="report-card-actions">
            <button class="btn-generate" onclick="generateReport('${reportType}')">Generate</button>
            <button class="btn-view hidden" onclick="viewReport('${reportType}')">View</button>
            <button class="btn-submit hidden" onclick="submitReport('${reportType}')">Submit</button>
        </div>
    `;
    
    return card;
}

// Generate specific report
function generateReport(reportType) {
    addSystemMessage(`Generating ${reportType}...`);
    
    // Update card status
    const statusEl = document.getElementById(`status-${reportType}`);
    if (statusEl) {
        statusEl.innerHTML = '<span class="status-text generating">Generating...</span>';
    }
    
    // Send generation request
    socket.emit('generate_report', {
        report_type: reportType,
        data: {
            unit: '3rd PLT',
            issue: fragoState.decisionPackage?.analysis?.includes('fuel') ? 'fuel shortfall' : 'operational requirement',
            location: 'grid 38S MC 45678 12345'
        }
    });
}

// Generate all required reports
function generateAllReports() {
    fragoState.requiredReports.forEach(reportType => {
        generateReport(reportType);
    });
}

// Handle report generation complete
socket.on('report_generated', (data) => {
    console.log('Report generated:', data);
    fragoState.generatedReports[data.report_type] = {
        content: data.content,
        pdf_path: data.pdf_path
    };
    
    // Update card status
    const statusEl = document.getElementById(`status-${data.report_type}`);
    if (statusEl) {
        statusEl.innerHTML = '<span class="status-text generated">Generated ✓</span>';
    }
    
    // Show view and submit buttons
    const card = document.querySelector(`[data-report-type="${data.report_type}"]`);
    if (card) {
        card.querySelector('.btn-generate')?.classList.add('hidden');
        card.querySelector('.btn-view')?.classList.remove('hidden');
        card.querySelector('.btn-submit')?.classList.remove('hidden');
    }
    
    addSystemMessage(`${data.report_type} generated successfully`);
});

// View report
function viewReport(reportType) {
    const reportData = fragoState.generatedReports[reportType];
    if (reportData) {
        document.getElementById('report-modal-title').textContent = `📄 ${reportType}`;
        fragoElements.reportContent.innerHTML = renderMarkdown(reportData.content);
        fragoElements.submitReportBtn.dataset.reportType = reportType;
        fragoElements.downloadReportBtn.dataset.reportType = reportType;
        fragoElements.downloadReportBtn.dataset.pdfPath = reportData.pdf_path || '';
        showReportModal();
    }
}

// Submit report
function submitReport(reportType) {
    const reportData = fragoState.generatedReports[reportType];
    socket.emit('submit_report', {
        report_type: reportType,
        pdf_path: reportData?.pdf_path || '',
        destination: reportType === 'LOGSTAT' ? 'Battalion S-4' : 
                     reportType === 'PERSTAT' ? 'Battalion S-1' :
                     reportType === 'SPOT' ? 'Battalion S-2' : 'Battalion HQ'
    });
}

// Submit current report (from modal)
function submitCurrentReport() {
    const reportType = fragoElements.submitReportBtn.dataset.reportType;
    if (reportType) {
        submitReport(reportType);
        hideReportModal();
    }
}

// Download current report PDF
function downloadCurrentReport() {
    const reportType = fragoElements.downloadReportBtn.dataset.reportType;
    const pdfPath = fragoElements.downloadReportBtn.dataset.pdfPath;
    
    if (pdfPath) {
        // Extract just the filename from the path
        const filename = pdfPath.split('/').pop();
        
        // Create download link
        const downloadUrl = `/api/reports/download/${filename}`;
        
        // Create temporary anchor element to trigger download
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        addSystemMessage(`Downloading ${reportType} PDF...`);
    } else {
        addMessage('warning', `No PDF available for ${reportType}. The report may not have been generated with PDF output.`);
    }
}

// Handle report submission confirmation
socket.on('report_submitted', (data) => {
    console.log('Report submitted:', data);
    
    // Update card status with Discord indicator
    const statusEl = document.getElementById(`status-${data.report_type}`);
    if (statusEl) {
        const discordIndicator = data.discord_sent ? ' 📤' : '';
        statusEl.innerHTML = `<span class="status-text submitted">Submitted ✓ ${data.confirmation}${discordIndicator}</span>`;
    }
    
    // Show success message with Discord status
    const discordMsg = data.discord_sent ? ' Report posted to Discord channel.' : '';
    addMessage('success', data.message + discordMsg);
});

// Handle FRAGO errors
socket.on('frago_error', (data) => {
    addMessage('error', `FRAGO Error: ${data.message}`);
});

// Modal show/hide functions
function showFragoModal() {
    fragoElements.fragoModal?.classList.remove('hidden');
}

function hideFragoModal() {
    fragoElements.fragoModal?.classList.add('hidden');
}

function showDecisionModal() {
    fragoElements.decisionModal?.classList.remove('hidden');
}

function hideDecisionModal() {
    fragoElements.decisionModal?.classList.add('hidden');
}

function showReportModal() {
    fragoElements.reportModal?.classList.remove('hidden');
}

function hideReportModal() {
    fragoElements.reportModal?.classList.add('hidden');
}

// Add success message type
function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    if (type === 'success') {
        header.textContent = '✅ SUCCESS';
        messageDiv.style.borderColor = '#27ae60';
    } else if (type === 'system') {
        header.textContent = '⚙️ SYSTEM';
        messageDiv.style.borderColor = '#3498db';
    } else if (type === 'user') {
        header.textContent = '👤 USER';
    } else if (type === 'assistant') {
        header.textContent = '🎖️ MCOA';
    } else if (type === 'error') {
        header.textContent = '❌ ERROR';
        messageDiv.style.borderColor = '#e74c3c';
    } else if (type === 'warning') {
        header.textContent = '⚠️ WARNING';
        messageDiv.style.borderColor = '#f39c12';
    }
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Render markdown for assistant and system messages
    if (type === 'assistant' || type === 'system') {
        contentDiv.innerHTML = renderMarkdown(content);
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(header);
    messageDiv.appendChild(contentDiv);
    
    elements.chatMessages.appendChild(messageDiv);
    requestAnimationFrame(() => {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    });
}
