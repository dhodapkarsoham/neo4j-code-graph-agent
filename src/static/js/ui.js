// UI interaction handlers
class UI {
    constructor() {
        this.wsClient = new WebSocketClient();
        this.currentTab = 'chat';
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadTools();
    }

    setupWebSocket() {
        this.wsClient.connect();
        this.wsClient.onMessage((event) => {
            this.handleWebSocketMessage(JSON.parse(event.data));
        });
    }

    setupEventListeners() {
        // Query input handling
        const queryInput = document.getElementById('queryInput');
        const sendButton = document.getElementById('sendButton');

        if (queryInput) {
            queryInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendQuery();
                }
            });

            queryInput.addEventListener('input', () => {
                this.updateSendButton();
            });
        }

        if (sendButton) {
            sendButton.addEventListener('click', () => {
                this.sendQuery();
            });
        }
    }

    updateSendButton() {
        const queryInput = document.getElementById('queryInput');
        const sendButton = document.getElementById('sendButton');
        
        if (queryInput && sendButton) {
            const hasText = queryInput.value.trim().length > 0;
            sendButton.disabled = !hasText || this.isProcessing;
        }
    }

    sendQuery() {
        const queryInput = document.getElementById('queryInput');
        if (!queryInput || this.isProcessing) return;

        const query = queryInput.value.trim();
        if (!query) return;

        this.isProcessing = true;
        this.updateSendButton();

        // Add user message to chat
        this.addMessage('user', query);

        // Clear input
        queryInput.value = '';
        this.updateSendButton();

        // Show loading indicator
        this.showLoading();

        // Send via WebSocket
        this.wsClient.send({
            type: 'query',
            query: query
        });
    }

    handleWebSocketMessage(data) {
        console.log('Received WebSocket message:', data);

        switch (data.type) {
            case 'status':
                this.handleStatusMessage(data);
                break;
            case 'reasoning_step':
                this.handleReasoningStep(data);
                break;
            case 'tool_execution_result':
                this.handleToolExecutionResult(data);
                break;
            case 'final_response':
                this.handleFinalResponse(data);
                break;
            case 'error':
                this.handleError(data);
                break;
            case 'pong':
                // Connection test response
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleStatusMessage(data) {
        const statusIndicator = document.getElementById('connectionStatus');
        const statusText = document.getElementById('connectionText');
        
        if (statusIndicator && statusText) {
            if (data.status === 'connected') {
                statusIndicator.className = 'status-indicator status-connected';
                statusText.textContent = 'Connected';
            } else if (data.status === 'connecting') {
                statusIndicator.className = 'status-indicator status-connecting';
                statusText.textContent = 'Connecting...';
            } else {
                statusIndicator.className = 'status-indicator status-disconnected';
                statusText.textContent = 'Disconnected';
            }
        }
    }

    handleReasoningStep(data) {
        const reasoningHtml = ResponseFormatter.formatReasoning([data.step]);
        this.addReasoningStep(reasoningHtml);
    }

    handleToolExecutionResult(data) {
        // Store tool execution result for final response
        if (!this.currentToolResults) {
            this.currentToolResults = [];
        }
        this.currentToolResults.push(data);
    }

    handleFinalResponse(data) {
        this.hideLoading();
        this.isProcessing = false;
        this.updateSendButton();

        // Add assistant response
        const formattedResponse = ResponseFormatter.formatResponse(data.response);
        this.addMessage('assistant', formattedResponse, data.reasoning);

        // Clear current tool results
        this.currentToolResults = null;
    }

    handleError(data) {
        this.hideLoading();
        this.isProcessing = false;
        this.updateSendButton();

        this.addMessage('assistant', `❌ Error: ${data.message}`);
    }

    addMessage(role, content, reasoning = null) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-bubble ' + (role === 'user' ? 'user-message' : 'assistant-message');
        
        const timestamp = new Date().toLocaleTimeString();
        const timestampClass = role === 'user' ? 'user-timestamp' : 'assistant-timestamp';
        
        messageDiv.innerHTML = `
            <div>${content}</div>
            <div class="timestamp ${timestampClass}">${timestamp}</div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Add reasoning if available
        if (reasoning && Array.isArray(reasoning) && reasoning.length > 0) {
            const reasoningHtml = ResponseFormatter.formatReasoning(reasoning);
            this.addReasoningStep(reasoningHtml);
        }
    }

    addReasoningStep(reasoningHtml) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const reasoningDiv = document.createElement('div');
        reasoningDiv.className = 'reasoning-step fade-in';
        reasoningDiv.innerHTML = reasoningHtml;

        chatMessages.appendChild(reasoningDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('hidden');
        }
    }

    hideLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.add('hidden');
        }
    }

    switchTab(tabName) {
        this.currentTab = tabName;
        
        // Update tab buttons
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(btn => btn.classList.remove('active'));
        
        const activeButton = document.querySelector(`[onclick="switchTab('${tabName}')"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }

        // Update tab content
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => content.classList.add('hidden'));
        
        const activeContent = document.getElementById(tabName + 'Tab');
        if (activeContent) {
            activeContent.classList.remove('hidden');
        }

        // Load tools if switching to tools tab
        if (tabName === 'tools') {
            this.loadTools();
        }
    }

    async loadTools() {
        try {
            const response = await fetch('/api/tools');
            const data = await response.json();
            
            if (data.tools) {
                this.renderTools(data.tools);
            }
        } catch (error) {
            console.error('Error loading tools:', error);
        }
    }

    renderTools(tools) {
        const toolsGrid = document.getElementById('toolsGrid');
        if (!toolsGrid) return;

        toolsGrid.innerHTML = '';

        tools.forEach(tool => {
            const toolCard = document.createElement('div');
            toolCard.className = 'tool-card';
            
            const categoryClass = ResponseFormatter.getCategoryClass(tool.category);
            
            toolCard.innerHTML = `
                <div class="flex items-start justify-between mb-3">
                    <h3 class="font-semibold text-gray-800">${tool.name}</h3>
                    <span class="category-badge ${categoryClass}">${tool.category}</span>
                </div>
                <p class="text-sm text-gray-600 mb-4">${tool.description}</p>
                ${tool.parameters ? `
                    <div class="text-xs text-gray-500 mb-2">
                        <strong>Parameters:</strong> ${tool.parameters}
                    </div>
                ` : ''}
                <div class="flex justify-between items-center">
                    <span class="text-xs text-gray-400">${tool.result_count || 0} results</span>
                    ${tool.is_custom ? `
                        <button onclick="deleteTool('${tool.name}')" class="text-xs text-red-600 hover:text-red-800">
                            Delete
                        </button>
                    ` : ''}
                </div>
            `;

            toolsGrid.appendChild(toolCard);
        });
    }

    async deleteTool(toolName) {
        if (!confirm(`Are you sure you want to delete the tool "${toolName}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/tools/${toolName}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadTools(); // Reload tools
            } else {
                const error = await response.json();
                alert(`Error deleting tool: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error deleting tool:', error);
            alert('Error deleting tool');
        }
    }
}

// Global functions for HTML onclick handlers
function switchTab(tabName) {
    if (window.ui) {
        window.ui.switchTab(tabName);
    }
}

function sendQuery() {
    if (window.ui) {
        window.ui.sendQuery();
    }
}

function deleteTool(toolName) {
    if (window.ui) {
        window.ui.deleteTool(toolName);
    }
}

// Initialize UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ui = new UI();
});
