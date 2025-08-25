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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updateTimestamp();
    setInterval(updateTimestamp, 1000);
    setInterval(updateSessionTime, 1000);
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
    contentDiv.textContent = content;
    
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
