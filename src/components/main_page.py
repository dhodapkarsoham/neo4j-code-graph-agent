"""Main page HTML component for the Code Graph Agent."""

def get_main_page_html() -> str:
    """Generate the main HTML page."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Graph Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.5/dist/purify.min.js"></script>
    <style>
        .gradient-bg {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .glass-effect {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .custom-scrollbar::-webkit-scrollbar {{
            width: 6px;
        }}
        .custom-scrollbar::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 3px;
        }}
        .custom-scrollbar::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 3px;
        }}
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}
        .typing-indicator {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .fade-in {{
            animation: fadeIn 0.5s ease-in;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .slide-in {{
            animation: slideIn 0.3s ease-out;
        }}
        @keyframes slideIn {{
            from {{ transform: translateX(-100%); }}
            to {{ transform: translateX(0); }}
        }}
        .pulse-glow {{
            animation: pulseGlow 2s ease-in-out infinite alternate;
        }}
        @keyframes pulseGlow {{
            from {{ box-shadow: 0 0 5px rgba(59, 130, 246, 0.5); }}
            to {{ box-shadow: 0 0 20px rgba(59, 130, 246, 0.8); }}
        }}
        .text2cypher-ready {{
            background: linear-gradient(45deg, #10b981, #059669);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .query-input-container {{
            position: relative;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }}
        .query-input-container:focus-within {{
            border-color: #3b82f6;
            box-shadow: 0 4px 25px rgba(59, 130, 246, 0.2);
        }}
        .send-button {{
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .send-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
        }}
        .send-button:disabled {{
            background: #9ca3af;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        .tool-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            border: 1px solid #e5e7eb;
            transition: all 0.3s ease;
        }}
        .tool-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        .category-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .category-security {{ background: #fef2f2; color: #dc2626; }}
        .category-quality {{ background: #fffbeb; color: #d97706; }}
        .category-team {{ background: #eff6ff; color: #2563eb; }}
        .category-architecture {{ background: #f3e8ff; color: #7c3aed; }}
        .category-query {{ background: #f0fdf4; color: #16a34a; }}
        .category-custom {{ background: #f9fafb; color: #6b7280; }}
        .reasoning-step {{
            background: linear-gradient(135deg, rgba(252, 249, 246, 0.6) 0%, rgba(255, 255, 255, 0.8) 100%);
            border-left: 4px solid #0A6190;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }}
        .message-bubble {{
            max-width: 80%;
            padding: 16px 20px;
            border-radius: 18px;
            margin-bottom: 16px;
            position: relative;
            animation: fadeIn 0.3s ease-out;
        }}
        .user-message {{
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 6px;
        }}
        .assistant-message {{
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
            margin-right: auto;
            border-bottom-left-radius: 6px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        .timestamp {{
            font-size: 11px;
            opacity: 0.7;
            margin-top: 4px;
        }}
        .user-timestamp {{ text-align: right; }}
        .assistant-timestamp {{ text-align: left; }}
        .tab-button {{
            padding: 12px 24px;
            border: none;
            background: transparent;
            color: #6b7280;
            font-weight: 500;
            border-bottom: 2px solid transparent;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .tab-button.active {{
            color: #3b82f6;
            border-bottom-color: #3b82f6;
            background: rgba(59, 130, 246, 0.05);
        }}
        .tab-button:hover {{
            color: #3b82f6;
            background: rgba(59, 130, 246, 0.05);
        }}
        .status-indicator {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-connected {{ background: #10b981; }}
        .status-disconnected {{ background: #ef4444; }}
        .status-connecting {{ background: #f59e0b; animation: pulse 1.5s infinite; }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .quick-example {{
            background: rgba(59, 130, 246, 0.1);
            color: #3b82f6;
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 4px;
            display: inline-block;
        }}
        .quick-example:hover {{
            background: rgba(59, 130, 246, 0.2);
            transform: translateY(-1px);
        }}
        .text2cypher-feature {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }}
        .feature-icon {{
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .feature-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .feature-description {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Header -->
    <header class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="text-2xl font-bold">🔍 Code Graph Agent</div>
                    <div class="text-sm opacity-90">Intelligent Code Analysis</div>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="flex items-center">
                        <span id="connectionStatus" class="status-indicator status-disconnected"></span>
                        <span id="connectionText" class="text-sm">Disconnected</span>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <div class="container mx-auto px-6 py-8">
        <!-- Tabs -->
        <div class="flex border-b border-gray-200 mb-8">
            <button class="tab-button active" onclick="switchTab('chat')">💬 Chat Interface</button>
            <button class="tab-button" onclick="switchTab('tools')">🔧 Tools Management</button>
        </div>

        <!-- Chat Tab -->
        <div id="chatTab" class="tab-content">
            <div class="max-w-4xl mx-auto">
                <!-- Text2Cypher Feature Card -->
                <div class="text2cypher-feature">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Text2Cypher Ready</div>
                    <div class="feature-description">Ask questions in natural language and get Cypher queries generated automatically!</div>
                </div>

                <!-- Query Input -->
                <div class="query-input-container mb-8">
                    <div class="flex items-center p-4">
                        <div class="flex-1">
                            <textarea 
                                id="queryInput" 
                                placeholder="Ask me anything about your codebase... (e.g., 'What HIGH severity CVEs are affecting apoc.create.Create?')"
                                class="w-full border-none outline-none resize-none text-gray-800 placeholder-gray-500"
                                rows="3"
                                style="font-size: 16px; line-height: 1.5;"
                            ></textarea>
                        </div>
                        <div class="ml-4">
                            <button id="sendButton" class="send-button" onclick="sendQuery()">
                                Send
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Chat Messages -->
                <div id="chatMessages" class="space-y-4 mb-8"></div>

                <!-- Loading Indicator -->
                <div id="loadingIndicator" class="hidden text-center py-8">
                    <div class="typing-indicator mx-auto mb-4"></div>
                    <div class="text-gray-600">Processing your query...</div>
                </div>
            </div>
        </div>

        <!-- Tools Tab -->
        <div id="toolsTab" class="tab-content hidden">
            <div class="max-w-6xl mx-auto">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="toolsGrid">
                    <!-- Tools will be loaded here -->
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="/static/js/websocket.js"></script>
    <script src="/static/js/formatting.js"></script>
    <script src="/static/js/ui.js"></script>
    <script src="/static/js/reasoning.js"></script>
</body>
</html>
"""

def get_tools_management_html() -> str:
    """Generate the tools management HTML."""
    return """
    <div class="bg-white rounded-lg shadow-lg p-6">
        <h2 class="text-2xl font-bold mb-6 text-gray-800">🔧 Tools Management</h2>
        
        <!-- Text2Cypher Feature -->
        <div class="mb-8 p-4 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg">
            <div class="flex items-center space-x-3">
                <div class="text-2xl">🔍</div>
                <div>
                    <h3 class="font-semibold text-gray-800">Text2Cypher Tool</h3>
                    <p class="text-sm text-gray-600">Convert natural language to Cypher queries</p>
                </div>
                <div class="ml-auto">
                    <span class="text2cypher-ready">Active</span>
                </div>
            </div>
        </div>
        
        <!-- Available Tools -->
        <div id="toolsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Tools will be loaded here -->
        </div>
    </div>
    """
