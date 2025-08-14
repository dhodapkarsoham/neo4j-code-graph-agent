"""FastAPI web UI for Code Graph Agent."""

import json
import logging
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.agent import agent
from src.mcp_tools import tool_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Suppress noisy neo4j driver logs
logging.getLogger('neo4j').setLevel(logging.ERROR)

app = FastAPI(title="Code Graph Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    """Serve the main UI."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta http-equiv="Pragma" content="no-cache" />
        <meta http-equiv="Expires" content="0" />
    <title>Code Graph Agent</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        .neo4j-primary { background: linear-gradient(135deg, #014063 0%, #014063 100%); }
        .neo4j-secondary { background: linear-gradient(135deg, #4C99A4 0%, #4C99A4 100%); }
        .tab-active { background: linear-gradient(135deg, #0A6190 0%, #0A6190 100%); color: white; }
        .tab-inactive { background: #F2EAD4; color: #4A4A4A; }
        .tool-card { background: #FCF9F6; border: 1px solid #90CB62; }
        .category-badge { background: linear-gradient(135deg, #00A3E0 0%, #0072C6 100%); }
        .security-badge { background: linear-gradient(135deg, #FF6F61 0%, #D64541 100%); }
        .architecture-badge { background: linear-gradient(135deg, #8A2BE2 0%, #6A0DAD 100%); }
        .team-badge { background: linear-gradient(135deg, #FFD700 0%, #FFC107 100%); }
        .quality-badge { background: linear-gradient(135deg, #20B2AA 0%, #008B8B 100%); }
        .custom-badge { background: linear-gradient(135deg, #808080 0%, #696969 100%); }
        .glass-effect { backdrop-filter: blur(10px); background: rgba(255, 255, 255, 0.9); }
            .stop-btn:hover { background-color: #D43300 !important; }
            /* Rich text styling for prettier responses */
            .rich-text { color: #1f2937; line-height: 1.7; }
            .rich-text h1, .rich-text h2, .rich-text h3, .rich-text h4 { color: #0f172a; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
            .rich-text h1 { font-size: 1.5rem; }
            .rich-text h2 { font-size: 1.375rem; }
            .rich-text h3 { font-size: 1.25rem; }
            .rich-text p { margin: 0.5rem 0; }
            .rich-text ul { list-style: disc; margin-left: 1.25rem; padding-left: 0.5rem; }
            .rich-text ol { list-style: decimal; margin-left: 1.25rem; padding-left: 0.5rem; }
            .rich-text li { margin: 0.25rem 0; }
            .rich-text blockquote { border-left: 4px solid #93c5fd; padding-left: 0.75rem; color: #374151; background: #f8fafc; border-radius: 0.25rem; }
            .rich-text code { background: #f3f4f6; padding: 0.1rem 0.3rem; border-radius: 0.25rem; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
            .rich-text pre { background: #0b2533; color: #e5e7eb; padding: 0.75rem; border-radius: 0.5rem; overflow-x: auto; }
            .rich-text table { width: 100%; border-collapse: collapse; margin: 0.75rem 0; }
            .rich-text th, .rich-text td { border: 1px solid #e5e7eb; padding: 0.5rem 0.75rem; text-align: left; }
            .rich-text th { background: #f3f4f6; font-weight: 600; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen" style="font-family: 'Public Sans', sans-serif;">
    <div id="root"></div>

    <script type="text/babel" data-presets="env,react">
        const { useState, useEffect } = React;

        function App() {
            const [activeTab, setActiveTab] = useState('query');
            const [query, setQuery] = useState('');
            const [messages, setMessages] = useState([]);
            const [collapsedGroups, setCollapsedGroups] = useState({});
            const [loading, setLoading] = useState(false);
            const [tools, setTools] = useState([]);
            const [showCreateTool, setShowCreateTool] = useState(false);
            const [isStreaming, setIsStreaming] = useState(false);
            const [newTool, setNewTool] = useState({
                name: '',
                description: '',
                category: 'Custom',
                query: ''
            });
            const [selectedTool, setSelectedTool] = useState(null);
            const [showToolDetails, setShowToolDetails] = useState(false);
            const [editingTool, setEditingTool] = useState({
                name: '',
                description: '',
                query: ''
            });

            useEffect(() => {
                loadTools();
            }, []);

            const loadTools = async () => {
                try {
                    const response = await fetch('/api/tools');
                    const data = await response.json();
                    setTools(data);
                } catch (error) {
                    console.error('Error loading tools:', error);
                }
            };

            const clearChat = () => {
                setMessages([]);
                setCollapsedGroups({});
            };

            const sendQuery = async () => {
                if (!query.trim()) return;
                
                setLoading(true);
                const userMessage = { role: 'user', content: query };
                setMessages(prev => [...prev, userMessage]);
                
                try {
                    // Prefer WebSocket streaming if available
                    const wsUrl = (location.origin.replace('http', 'ws')) + '/ws/query';
                    const ws = new WebSocket(wsUrl);
                    let partialAnswer = '';
                    let streamedReasoning = [];
                    let finalized = false;
                    window.__cga_ws = ws;

                    ws.onopen = () => {
                        setIsStreaming(true);
                        ws.send(JSON.stringify({ query }));
                    };
                    ws.onmessage = (event) => {
                        try {
                            const msg = JSON.parse(event.data);
                            if (msg.type === 'llm_reasoning_update') {
                                streamedReasoning.push({
                                    step: 'query_understanding',
                                    description: 'LLM analysis update',
                                    understanding: msg.data.understanding,
                                    reasoning: msg.data.reasoning,
                                    llm_analysis: msg.data.llm_analysis,
                                    intelligence_level: msg.data.intelligence_level,
                                    llm_reasoning_details: msg.data.llm_reasoning_details,
                                });
                                // Rerender by setting state shallow copy
                                setMessages(prev => {
                                    const updated = [...prev];
                                    // Add a live assistant message if not present yet
                                    if (!updated.find(m => m.__live)) {
                                        updated.push({ role: 'assistant', content: '', reasoning: [], __live: true });
                                    }
                                    const last = updated[updated.length - 1];
                                    last.reasoning = [...streamedReasoning];
                                    return updated;
                                });
                            } else if (msg.type === 'tools_selected') {
                                streamedReasoning.push({
                                    step: 'tool_selection',
                                    description: 'Selected tools',
                                    selected_tools: msg.data.tools,
                                    intelligence_level: msg.data.fallback ? 'fallback' : 'LLM-powered'
                                });
                                setMessages(prev => {
                                    const updated = [...prev];
                                    if (!updated.find(m => m.__live)) {
                                        updated.push({ role: 'assistant', content: '', reasoning: [], __live: true });
                                    }
                                    const last = updated[updated.length - 1];
                                    last.reasoning = [...streamedReasoning];
                                    return updated;
                                });
                            } else if (msg.type === 'tool_execution_start') {
                                streamedReasoning.push({
                                    step: 'tool_execution',
                                    description: `Executing ${msg.data.tool}`,
                                    tool_name: msg.data.tool
                                });
                                setMessages(prev => {
                                    const updated = [...prev];
                                    if (!updated.find(m => m.__live)) {
                                        updated.push({ role: 'assistant', content: '', reasoning: [], __live: true });
                                    }
                                    const last = updated[updated.length - 1];
                                    last.reasoning = [...streamedReasoning];
                                    return updated;
                                });
                            } else if (msg.type === 'tool_execution_result') {
                                streamedReasoning.push({
                                    step: 'tool_execution',
                                    description: `Executed ${msg.data.tool}`,
                                    tool_name: msg.data.tool,
                                    result_count: msg.data.result_count,
                                    category: msg.data.category,
                                    db_metrics: msg.data.db_metrics || null,
                                });
                                setMessages(prev => {
                                    const updated = [...prev];
                                    if (!updated.find(m => m.__live)) {
                                        updated.push({ role: 'assistant', content: '', reasoning: [], __live: true });
                                    }
                                    const last = updated[updated.length - 1];
                                    last.reasoning = [...streamedReasoning];
                                    return updated;
                                });
                            } else if (msg.type === 'llm_response_update') {
                                partialAnswer = partialAnswer + msg.data.chunk;
                                setMessages(prev => {
                                    const updated = [...prev];
                                    if (!updated.find(m => m.__live)) {
                                        updated.push({ role: 'assistant', content: '', reasoning: [], __live: true });
                                    }
                                    const last = updated[updated.length - 1];
                                    last.content = partialAnswer;
                                    last.reasoning = [...streamedReasoning];
                                    return updated;
                                });
                            } else if (msg.type === 'reasoning_append') {
                                streamedReasoning.push(msg.data);
                                setMessages(prev => {
                                    const updated = [...prev];
                                    if (!updated.find(m => m.__live)) {
                                        updated.push({ role: 'assistant', content: '', reasoning: [], __live: true });
                                    }
                                    const last = updated[updated.length - 1];
                                    last.reasoning = [...streamedReasoning];
                                    return updated;
                                });
                            } else if (msg.type === 'final_response') {
                                setMessages(prev => {
                                    const updated = [...prev];
                                    // Replace live message with final
                                    const idx = updated.findIndex(m => m.__live);
                                    const finalMsg = { role: 'assistant', content: msg.data.text, reasoning: msg.data.reasoning };
                                    if (idx >= 0) {
                                        updated[idx] = finalMsg;
                                    } else {
                                        updated.push(finalMsg);
                                    }
                                    return updated;
                                });
                                setQuery('');
                                finalized = true;
                                ws.close();
                                setIsStreaming(false);
                            } else if (msg.type === 'error') {
                                setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, there was an error processing your request.' }]);
                                finalized = true;
                                ws.close();
                                setIsStreaming(false);
                            }
                        } catch (err) {
                            console.error('Error handling WS message', err);
                        }
                    };
                    const restFallback = async () => {
                        try {
                            const response = await fetch('/api/query', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ query })
                            });
                            const data = await response.json();
                            const assistantMessage = { role: 'assistant', content: data.response, reasoning: data.reasoning || [] };
                            setMessages(prev => [...prev, assistantMessage]);
                            setQuery('');
                        } catch (e) {
                            setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, there was an error processing your request.' }]);
                        }
                    };
                    ws.onclose = () => {
                        if (!finalized) {
                            restFallback();
                        }
                        setIsStreaming(false);
                    };
                    ws.onerror = () => {
                        if (!finalized) {
                            restFallback();
                        }
                        setIsStreaming(false);
                    };
                } catch (error) {
                    console.error('Error sending query:', error);
                    const errorMessage = { role: 'assistant', content: 'Sorry, there was an error processing your request.' };
                    setMessages(prev => [...prev, errorMessage]);
                } finally {
                    setLoading(false);
                }
            };

            const stopQuery = () => {
                try {
                    if (window.__cga_ws && window.__cga_ws.readyState === 1) {
                        window.__cga_ws.close();
                    }
                } catch (e) {}
                setIsStreaming(false);
            };

            const testTool = async (toolName) => {
                try {
                    const response = await fetch(`/api/tools/${toolName}/test`);
                    const data = await response.json();
                    alert(`Tool test result: ${JSON.stringify(data, null, 2)}`);
                } catch (error) {
                    console.error('Error testing tool:', error);
                    alert('Error testing tool');
                }
            };

            const createCustomTool = async () => {
                try {
                    const response = await fetch('/api/tools', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(newTool)
                    });
                    
                    if (response.ok) {
                        setShowCreateTool(false);
                        setNewTool({ name: '', description: '', category: 'Custom', query: '' });
                        loadTools();
                        alert('Tool created successfully!');
                    } else {
                        alert('Error creating tool');
                    }
                } catch (error) {
                    console.error('Error creating tool:', error);
                    alert('Error creating tool');
                }
            };

            const viewToolDetails = async (toolName) => {
                try {
                    const response = await fetch(`/api/tools/${toolName}/details`);
                    const data = await response.json();
                    setSelectedTool(data);
                    setEditingTool({
                        name: data.name || '',
                        description: data.description || '',
                        query: data.query || ''
                    });
                    setShowToolDetails(true);
                } catch (error) {
                    console.error('Error fetching tool details:', error);
                    alert('Error fetching tool details');
                }
            };

            const updateTool = async () => {
                if (!selectedTool) return;
                
                try {
                    const response = await fetch(`/api/tools/${selectedTool.name}/update`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(editingTool)
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        alert('Tool updated successfully!');
                        setShowToolDetails(false);
                        setSelectedTool(null);
                        loadTools();
                    } else {
                        const errorData = await response.json();
                        alert(`Error updating tool: ${errorData.detail}`);
                    }
                } catch (error) {
                    console.error('Error updating tool:', error);
                    alert('Error updating tool');
                }
            };

            const deleteCustomTool = async (toolName) => {
                if (!confirm(`Are you sure you want to delete the tool "${toolName}"?`)) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/tools/${toolName}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        alert('Tool deleted successfully!');
                        loadTools();
                    } else {
                        const errorData = await response.json();
                        alert(`Error deleting tool: ${errorData.detail}`);
                    }
                } catch (error) {
                    console.error('Error deleting tool:', error);
                    alert('Error deleting tool');
                }
            };

            const getToolsByCategory = (category) => {
                return tools.filter(tool => tool.category === category);
            };

            const getCategoryBadgeClass = (category) => {
                const classes = {
                    'Security': 'security-badge',
                    'Architecture': 'architecture-badge',
                    'Team': 'team-badge',
                    'Quality': 'quality-badge',
                    'Custom': 'custom-badge'
                };
                return classes[category] || 'category-badge';
            };

            const formatResponse = (content) => {
                try {
                    if (window.marked && window.DOMPurify) {
                        const html = window.marked.parse(content || '');
                        return window.DOMPurify.sanitize(html);
                    }
                } catch (e) {}
                // Fallback minimal formatting
                return (content || '').replace(/\\n/g, '<br>').replace(/\\"/g, '"');
            };

            const formatReasoning = (reasoning) => {
                if (!reasoning || !Array.isArray(reasoning)) return '';
                return reasoning.map((step, index) => {
                    let stepHtml = `
                        <div class="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border-l-4 border-blue-400 shadow-sm">
                            <div class="flex items-center justify-between mb-3">
                                <div class="font-bold text-blue-800 text-lg">
                                    Step ${index + 1}: ${step.description || step.step}
                                </div>
                                ${step.intelligence_level ? `<span class="px-3 py-1 bg-blue-200 text-blue-800 rounded-full text-xs font-semibold">${step.intelligence_level}</span>` : ''}
                            </div>
                    `;
                    
                    // Tool execution details
                    if (step.tool_name) {
                        stepHtml += `<div class="text-sm text-blue-600 mb-2">🔧 Tool: ${step.tool_name}</div>`;
                    }
                    if (step.result_count !== undefined) {
                        stepHtml += `<div class="text-sm text-blue-600 mb-2">📊 Results: ${step.result_count} items</div>`;
                    }
                    if (step.category) {
                        stepHtml += `<div class="text-sm text-blue-600 mb-2">🏷️ Category: ${step.category}</div>`;
                    }
                    if (step.db_metrics) {
                        const m = step.db_metrics;
                        const latency = (m && m.latency_ms != null) ? Number(m.latency_ms).toFixed(1) : '?';
                        const rows = (m && m.rows != null) ? m.rows : '?';
                        const avail = (m && m.available_after_ms != null) ? m.available_after_ms : '?';
                        const consumed = (m && m.consumed_after_ms != null) ? m.consumed_after_ms : '?';
                        stepHtml += `<div class="text-xs text-gray-600 mb-2">⏱️ Query Metrics: latency ${latency} ms, rows ${rows}, avail ${avail} ms, consumed ${consumed} ms</div>`;
                    }
                    
                    // Understanding and reasoning
                    if (step.understanding) {
                        stepHtml += `<div class="text-sm text-gray-700 mb-2"><strong>Understanding:</strong> ${step.understanding}</div>`;
                    }
                    if (step.reasoning) {
                        stepHtml += `<div class="text-sm text-gray-700 mb-2"><strong>Reasoning:</strong> ${step.reasoning}</div>`;
                    }
                    if (step.llm_analysis) {
                        stepHtml += `<div class="text-sm text-gray-700 mb-2"><strong>LLM Analysis:</strong> ${step.llm_analysis}</div>`;
                    }
                    
                    // LLM Reasoning Details (for query understanding and response generation)
                    if (step.llm_reasoning_details || step.llm_reasoning) {
                        const llmDetails = step.llm_reasoning_details || step.llm_reasoning;
                        stepHtml += `
                            <details class="mt-3 bg-white rounded-lg border border-blue-200">
                                <summary class="cursor-pointer font-semibold text-blue-700 p-3 flex items-center space-x-2 hover:bg-blue-50 rounded-t-lg transition-colors">
                                    <span>🤖</span>
                                    <span>LLM Reasoning Details</span>
                                    <span class="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs">
                                        ${llmDetails.intelligence_level || 'LLM-powered'}
                                    </span>
                                </summary>
                                <div class="p-3 border-t border-blue-200 space-y-3">
                                    ${llmDetails.llm_model ? `<div class="text-sm"><strong>Model:</strong> ${llmDetails.llm_model}</div>` : ''}
                                    ${llmDetails.temperature ? `<div class="text-sm"><strong>Temperature:</strong> ${llmDetails.temperature}</div>` : ''}
                                    ${llmDetails.max_tokens ? `<div class="text-sm"><strong>Max Tokens:</strong> ${llmDetails.max_tokens}</div>` : ''}
                                    ${llmDetails.metrics ? `
                                        <div class="text-sm">
                                            <strong>LLM Metrics:</strong>
                                            <ul class="ml-4 mt-1 list-disc">
                                                <li>Latency: ${Number(llmDetails.metrics.latency_ms).toFixed(1)} ms</li>
                                                <li>Prompt tokens: ${llmDetails.metrics.prompt_tokens ?? '?'}</li>
                                                <li>Completion tokens: ${llmDetails.metrics.completion_tokens ?? '?'}</li>
                                                <li>Total tokens: ${llmDetails.metrics.total_tokens ?? '?'}</li>
                                                
                                            </ul>
                                        </div>
                                    ` : ''}
                                    ${llmDetails.query_type ? `<div class="text-sm"><strong>Query Type:</strong> ${llmDetails.query_type}</div>` : ''}
                                    ${llmDetails.expected_insights ? `<div class="text-sm"><strong>Expected Insights:</strong> ${llmDetails.expected_insights}</div>` : ''}
                                    ${llmDetails.tool_results_summary ? `
                                        <div class="text-sm">
                                            <strong>Tool Results Summary:</strong>
                                            <ul class="ml-4 mt-1">
                                                <li>Total Tools: ${llmDetails.tool_results_summary.total_tools}</li>
                                                <li>Total Results: ${llmDetails.tool_results_summary.total_results}</li>
                                                <li>Tools Used: ${llmDetails.tool_results_summary.tools_used.join(', ')}</li>
                                            </ul>
                                        </div>
                                    ` : ''}
                                    ${llmDetails.prompt_sent ? `
                                        <details class="mt-2">
                                            <summary class="cursor-pointer text-sm font-semibold text-gray-600">📝 System Prompt</summary>
                                            <pre class="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">${llmDetails.prompt_sent}</pre>
                                        </details>
                                    ` : ''}
                                    ${llmDetails.user_message ? `
                                        <details class="mt-2">
                                            <summary class="cursor-pointer text-sm font-semibold text-gray-600">💬 User Message</summary>
                                            <pre class="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">${llmDetails.user_message}</pre>
                                        </details>
                                    ` : ''}
                                    ${llmDetails.raw_response ? `
                                        <details class="mt-2">
                                            <summary class="cursor-pointer text-sm font-semibold text-gray-600">🤖 LLM Response</summary>
                                            <pre class="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">${llmDetails.raw_response}</pre>
                                        </details>
                                    ` : ''}
                                </div>
                            </details>
                        `;
                    }
                    
                    stepHtml += '</div>';
                    return stepHtml;
                }).join('');
            };

            const groupMessages = (msgs) => {
                const groups = [];
                let i = 0;
                while (i < msgs.length) {
                    const current = msgs[i];
                    if (current.role === 'user') {
                        const next = msgs[i + 1];
                        if (next && next.role === 'assistant') {
                            groups.push({ question: current, answer: next });
                            i += 2;
                        } else {
                            groups.push({ question: current, answer: null });
                            i += 1;
                        }
                    } else {
                        groups.push({ question: null, answer: current });
                        i += 1;
                    }
                }
                return groups;
            };

            return (
                <div className="min-h-screen bg-gray-50">
                    {/* Header */}
                    <div className="neo4j-primary text-white p-12 shadow-lg">
                        <div className="container mx-auto">
                            <h1 className="text-5xl font-bold mb-4">Code Graph Agent</h1>
                            <p className="text-xl opacity-90">Powered by Neo4j</p>
                        </div>
                    </div>

                    {/* Navigation Tabs */}
                    <div className="container mx-auto px-6 py-8">
                        <div className="flex space-x-2 mb-8">
                            <button
                                onClick={() => setActiveTab('query')}
                                className={`tab-${activeTab === 'query' ? 'active' : 'inactive'} py-4 px-8 rounded-2xl font-bold text-xl transition-all duration-200 shadow-lg`}
                            >
                                💬 Ask Questions
                            </button>
                            <button
                                onClick={() => setActiveTab('tools')}
                                className={`tab-${activeTab === 'tools' ? 'active' : 'inactive'} py-4 px-8 rounded-2xl font-bold text-xl transition-all duration-200 shadow-lg`}
                            >
                                🛠️ Tools Management
                            </button>
                        </div>

                        {/* Query Tab */}
                        {activeTab === 'query' && (
                            <div className="space-y-8">
                                {/* Query Interface */}
                                <div className="glass-effect p-8 rounded-3xl shadow-xl border-2 border-blue-100">
                                    <h2 className="text-3xl font-bold mb-6 text-gray-800">Ask Your Code Graph Questions</h2>
                                    <div className="space-y-4">
                                        <textarea
                                            value={query}
                                            onChange={(e) => setQuery(e.target.value)}
                                            placeholder="Ask about code dependencies, security vulnerabilities, team collaboration, architecture patterns, or any code-related questions..."
                                            className="w-full p-6 border-2 border-gray-200 rounded-2xl text-lg resize-none focus:border-blue-500 focus:outline-none"
                                            rows="5"
                                            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendQuery()}
                                        />
                                        <div className="flex space-x-3">
                                            <button
                                                onClick={sendQuery}
                                                disabled={loading || isStreaming || !query.trim()}
                                                className="neo4j-primary text-white px-8 py-4 rounded-2xl font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all duration-200"
                                            >
                                                {loading || isStreaming ? '🤔 Thinking...' : '🚀 Ask Question'}
                                            </button>
                                            <button
                                                onClick={stopQuery}
                                                disabled={!isStreaming}
                                                className="bg-gray-500 text-white px-6 py-4 rounded-2xl font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed stop-btn transition-all duration-200"
                                            >
                                                ⏹ Stop
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                {/* Messages grouped into collapsible QnA pairs and Clear Chat button */}
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-xl font-semibold text-gray-800">Conversation</h3>
                                    {messages.length > 0 && (
                                        <button onClick={clearChat} className="bg-red-500 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors duration-200">
                                            Clear
                                        </button>
                                    )}
                                </div>

                                {messages.length > 0 && (
                                    <div className="space-y-4">
                                        {groupMessages(messages).map((group, idx) => {
                                            const groupId = `g-${idx}`;
                                            const collapsed = !!collapsedGroups[groupId];
                                            return (
                                                <div key={groupId} className="glass-effect rounded-2xl shadow-lg border border-gray-100">
                                                    <details open={!collapsed} onToggle={(e) => {
                                                        const isOpen = e.target.open;
                                                        setCollapsedGroups(prev => ({ ...prev, [groupId]: !isOpen }));
                                                    }}>
                                                        <summary className="cursor-pointer p-4 flex items-center justify-between hover:bg-gray-50 rounded-t-2xl">
                                                            <div className="flex items-center space-x-3">
                                                                <span className="text-blue-600">👤</span>
                                                                <span className="font-semibold text-gray-800 truncate max-w-[60vw]" title={group.question ? group.question.content : 'Answer'}>
                                                                    {group.question ? group.question.content : 'Answer'}
                                                                </span>
                                                            </div>
                                                            <span className="text-gray-500 text-sm">{collapsed ? 'Expand' : 'Collapse'}</span>
                                                        </summary>
                                                        <div className="p-4 border-t border-gray-100">
                                                            {group.question && (
                                                                <div className="mb-4">
                                                                    <div className="flex items-center mb-2">
                                                                        <span className="text-2xl mr-3 text-blue-600">👤</span>
                                                                        <span className="font-bold text-lg text-gray-700">You</span>
                                                                    </div>
                                                                    <div className="text-gray-800 leading-relaxed" dangerouslySetInnerHTML={{ __html: formatResponse(group.question.content) }} />
                                                                </div>
                                                            )}
                                                            {group.answer && (
                                                                <div className="">
                                                                    <div className="flex items-center mb-2">
                                                                        <span className="text-2xl mr-3 text-green-600">🤖</span>
                                                                        <span className="font-bold text-lg text-gray-700">Agent</span>
                                                                    </div>
                                                                    <div className="rich-text leading-relaxed" dangerouslySetInnerHTML={{ __html: formatResponse(group.answer.content) }} />
                                                                    {group.answer.reasoning && (
                                                                        <details className="mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
                                                                            <summary className="cursor-pointer font-semibold text-blue-800 p-4 flex items-center space-x-2 hover:bg-blue-100 rounded-t-xl transition-colors">
                                                                                <span>🤔</span>
                                                                                <span>Agent Reasoning Process</span>
                                                                                <span className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full text-xs">{group.answer.reasoning.length} steps</span>
                                                                            </summary>
                                                                            <div className="p-4 border-t border-blue-200">
                                                                                <div className="space-y-2" dangerouslySetInnerHTML={{ __html: formatReasoning(group.answer.reasoning) }} />
                                                                            </div>
                                                                        </details>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </details>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Tools Tab */}
                        {activeTab === 'tools' && (
                            <div className="space-y-8">
                                {/* Statistics Dashboard */}
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                    <div className="glass-effect p-6 rounded-2xl shadow-lg text-center">
                                        <div className="text-3xl font-bold text-blue-600">{tools.length}</div>
                                        <div className="text-base text-gray-600">Total Tools</div>
                                    </div>
                                    <div className="glass-effect p-6 rounded-2xl shadow-lg text-center">
                                        <div className="text-3xl font-bold text-red-600">{getToolsByCategory('Security').length}</div>
                                        <div className="text-base text-gray-600">Security Tools</div>
                                    </div>
                                    <div className="glass-effect p-6 rounded-2xl shadow-lg text-center">
                                        <div className="text-3xl font-bold text-purple-600">{getToolsByCategory('Architecture').length}</div>
                                        <div className="text-base text-gray-600">Architecture Tools</div>
                                    </div>
                                    <div className="glass-effect p-6 rounded-2xl shadow-lg text-center">
                                        <div className="text-3xl font-bold text-orange-600">{getToolsByCategory('Team').length}</div>
                                        <div className="text-base text-gray-600">Team Tools</div>
                                    </div>
                                </div>

                                {/* Create Tool Button */}
                                <div className="text-center">
                                    <button
                                        onClick={() => setShowCreateTool(!showCreateTool)}
                                        className="neo4j-secondary text-white px-8 py-4 rounded-2xl font-bold text-lg hover:shadow-lg transition-all duration-200"
                                    >
                                        {showCreateTool ? '❌ Cancel' : '➕ Create New Tool'}
                                    </button>
                                </div>

                                {/* Create Tool Form */}
                                {showCreateTool && (
                                    <div className="glass-effect p-8 rounded-2xl shadow-xl border-2 border-blue-100">
                                        <h3 className="text-2xl font-bold mb-6 text-gray-800">Create Custom Tool</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div>
                                                <label className="block text-lg font-semibold mb-2 text-gray-700">Tool Name</label>
                                                <input
                                                    type="text"
                                                    value={newTool.name}
                                                    onChange={(e) => setNewTool({...newTool, name: e.target.value})}
                                                    className="w-full p-4 border-2 border-gray-200 rounded-xl text-lg focus:border-blue-500 focus:outline-none"
                                                    placeholder="e.g., custom_analysis"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-lg font-semibold mb-2 text-gray-700">Category</label>
                                                <select
                                                    value={newTool.category}
                                                    onChange={(e) => setNewTool({...newTool, category: e.target.value})}
                                                    className="w-full p-4 border-2 border-gray-200 rounded-xl text-lg focus:border-blue-500 focus:outline-none"
                                                >
                                                    <option value="Custom">Custom</option>
                                                    <option value="Security">Security</option>
                                                    <option value="Architecture">Architecture</option>
                                                    <option value="Team">Team</option>
                                                    <option value="Quality">Quality</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="mt-6">
                                            <label className="block text-lg font-semibold mb-2 text-gray-700">Description</label>
                                            <input
                                                type="text"
                                                value={newTool.description}
                                                onChange={(e) => setNewTool({...newTool, description: e.target.value})}
                                                className="w-full p-4 border-2 border-gray-200 rounded-xl text-lg focus:border-blue-500 focus:outline-none"
                                                placeholder="What does this tool do?"
                                            />
                                        </div>
                                        <div className="mt-6">
                                            <label className="block text-lg font-semibold mb-2 text-gray-700">Cypher Query</label>
                                            <textarea
                                                value={newTool.query}
                                                onChange={(e) => setNewTool({...newTool, query: e.target.value})}
                                                className="w-full p-4 border-2 border-gray-200 rounded-xl text-lg focus:border-blue-500 focus:outline-none"
                                                rows="4"
                                                placeholder="MATCH (n) RETURN n LIMIT 10"
                                            />
                                        </div>
                                        <div className="mt-6 text-center">
                                            <button
                                                onClick={createCustomTool}
                                                className="neo4j-primary text-white px-8 py-4 rounded-2xl font-bold text-lg hover:shadow-lg transition-all duration-200"
                                            >
                                                🚀 Create Tool
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Tools by Category */}
                                {['Security', 'Architecture', 'Team', 'Quality', 'Custom'].map(category => {
                                    const categoryTools = getToolsByCategory(category);
                                    if (categoryTools.length === 0) return null;
                                    
                                    return (
                                        <div key={category} className="space-y-4">
                                            <h3 className="text-2xl font-bold text-gray-800 flex items-center">
                                                <span className={`inline-block w-4 h-4 rounded-full ${getCategoryBadgeClass(category)} mr-3`}></span>
                                                {category} Tools ({categoryTools.length})
                                            </h3>
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                                {categoryTools.map(tool => (
                                                    <div key={tool.name} className="tool-card p-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200">
                                                        <div className="flex items-start justify-between mb-4">
                                                            <h4 className="text-lg font-bold text-gray-800">{tool.name}</h4>
                                                            <span className={`px-3 py-1 rounded-xl text-white text-sm font-semibold ${getCategoryBadgeClass(tool.category)}`}>
                                                                {tool.category}
                                                            </span>
                                                        </div>
                                                        <p className="text-base text-gray-600 mb-4">{tool.description}</p>
                                                        <div className="flex space-x-3">
                                                            <button
                                                                onClick={() => testTool(tool.name)}
                                                                className="px-4 py-3 bg-blue-500 text-white rounded-xl text-base font-semibold hover:bg-blue-600 transition-colors duration-200"
                                                            >
                                                                🧪 Test
                                                            </button>
                                                            <button
                                                                onClick={() => viewToolDetails(tool.name)}
                                                                className="px-4 py-3 bg-gray-500 text-white rounded-xl text-base font-semibold hover:bg-gray-600 transition-colors duration-200"
                                                            >
                                                                📋 Details
                                                            </button>
                                                            {tool.category === 'Custom' && (
                                                                <button
                                                                    onClick={() => deleteCustomTool(tool.name)}
                                                                    className="px-4 py-3 bg-red-500 text-white rounded-xl text-base font-semibold hover:bg-red-600 transition-colors duration-200"
                                                                >
                                                                    🗑️ Delete
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                }                                 )}

                                {/* Tool Details Modal */}
                                {showToolDetails && selectedTool && (
                                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                                        <div className="glass-effect p-8 rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                                            <div className="flex items-center justify-between mb-6">
                                                <h3 className="text-2xl font-bold text-gray-800">Tool Details: {selectedTool.name}</h3>
                                                <button
                                                    onClick={() => setShowToolDetails(false)}
                                                    className="text-gray-500 hover:text-gray-700 text-2xl"
                                                >
                                                    ✕
                                                </button>
                                            </div>
                                            {selectedTool.category === 'Custom' && (
                                                <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                                                    <p className="text-blue-800 text-sm">
                                                        ✏️ <strong>Custom Tool:</strong> You can edit the name, description, and query for this tool.
                                                    </p>
                                                </div>
                                            )}
                                            
                                            <div className="space-y-6">
                                                {/* Tool Info */}
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div>
                                                        <label className="block text-lg font-semibold mb-2 text-gray-700">Name</label>
                                                        <input
                                                            type="text"
                                                            value={editingTool.name}
                                                            onChange={(e) => setEditingTool({...editingTool, name: e.target.value})}
                                                            disabled={selectedTool.category !== 'Custom'}
                                                            className={`w-full p-3 border-2 rounded-xl text-lg ${
                                                                selectedTool.category === 'Custom' 
                                                                    ? 'border-blue-200 focus:border-blue-500 focus:outline-none' 
                                                                    : 'border-gray-200 bg-gray-50'
                                                            }`}
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="block text-lg font-semibold mb-2 text-gray-700">Category</label>
                                                        <input
                                                            type="text"
                                                            value={selectedTool.category}
                                                            disabled
                                                            className="w-full p-3 border-2 border-gray-200 rounded-xl text-lg bg-gray-50"
                                                        />
                                                    </div>
                                                </div>
                                                
                                                <div>
                                                    <label className="block text-lg font-semibold mb-2 text-gray-700">Description</label>
                                                    <textarea
                                                        value={editingTool.description}
                                                        onChange={(e) => setEditingTool({...editingTool, description: e.target.value})}
                                                        disabled={selectedTool.category !== 'Custom'}
                                                        rows="3"
                                                        className={`w-full p-3 border-2 rounded-xl text-lg resize-none ${
                                                            selectedTool.category === 'Custom' 
                                                                ? 'border-blue-200 focus:border-blue-500 focus:outline-none' 
                                                                : 'border-gray-200 bg-gray-50'
                                                        }`}
                                                    />
                                                </div>
                                                
                                                {/* Cypher Query Editor */}
                                                <div>
                                                    <label className="block text-lg font-semibold mb-2 text-gray-700">Cypher Query</label>
                                                    <textarea
                                                        value={editingTool.query}
                                                        onChange={(e) => setEditingTool({...editingTool, query: e.target.value})}
                                                        rows="8"
                                                        className="w-full p-4 border-2 border-blue-200 rounded-xl text-sm font-mono focus:border-blue-500 focus:outline-none"
                                                        placeholder="MATCH (n) RETURN n LIMIT 10"
                                                    />
                                                    <div className="mt-2 text-sm text-gray-600">
                                                        💡 Edit the Cypher query to customize this tool's behavior
                                                    </div>
                                                </div>
                                                
                                                {/* Action Buttons */}
                                                <div className="flex space-x-4 pt-4">
                                                    <button
                                                        onClick={updateTool}
                                                        className="neo4j-primary text-white px-6 py-3 rounded-xl font-bold text-lg hover:shadow-lg transition-all duration-200"
                                                    >
                                                        💾 Save Changes
                                                    </button>
                                                    <button
                                                        onClick={() => setShowToolDetails(false)}
                                                        className="bg-gray-500 text-white px-6 py-3 rounded-xl font-bold text-lg hover:bg-gray-600 transition-all duration-200"
                                                    >
                                                        ❌ Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                             </div>
                         )}
                     </div>
                 </div>
             );
         }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
    """)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Code Graph Agent is running"}

@app.get("/api/tools")
async def list_tools():
    """List all available tools."""
    try:
        return tool_registry.list_tools()
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tools")
async def create_tool(request: Request):
    """Create a new custom tool."""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["name", "description", "category", "query"]
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create the tool in the registry
        new_tool = tool_registry.add_tool(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            query=data["query"],
            parameters=data.get("parameters")
        )
        
        return {
            "message": "Tool created successfully",
            "tool": {
                "name": new_tool.name,
                "description": new_tool.description,
                "category": new_tool.category,
                "has_parameters": new_tool.parameters is not None
            }
        }
    except ValueError as e:
        logger.error(f"Validation error creating tool: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tools/{tool_name}/test")
async def test_tool(tool_name: str):
    """Test a specific tool."""
    try:
        result = tool_registry.execute_tool(tool_name)
        return {"tool": tool_name, "result": result}
    except Exception as e:
        logger.error(f"Error testing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tools/{tool_name}/details")
async def get_tool_details(tool_name: str):
    """Get detailed information about a specific tool."""
    try:
        tool = tool_registry.get_tool_by_name(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "query": tool.query,
            "has_parameters": tool.parameters is not None
        }
    except Exception as e:
        logger.error(f"Error getting tool details for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tools/{tool_name}/update")
async def update_tool(tool_name: str, request: Request):
    """Update tool properties (name, description, query) for a specific tool."""
    try:
        data = await request.json()
        new_name = data.get("name", "")
        new_description = data.get("description", "")
        new_query = data.get("query", "")
        
        # Validate required fields
        if not new_name or not new_description or not new_query:
            raise HTTPException(status_code=400, detail="Name, description, and query are required")
        
        # Get the tool
        tool = tool_registry.get_tool_by_name(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Check if new name conflicts with existing tool (if name is being changed)
        if new_name != tool_name:
            existing_tool = tool_registry.get_tool_by_name(new_name)
            if existing_tool:
                raise HTTPException(status_code=400, detail=f"Tool with name '{new_name}' already exists")
        
        # Update the tool's properties
        old_name = tool.name
        tool.name = new_name
        tool.description = new_description
        tool.query = new_query
        
        # Save all tools to file
        tool_registry._save_all_tools()
        
        logger.info(f"Updated tool '{old_name}' to '{new_name}': {new_description[:50]}...")
        
        return {
            "message": "Tool updated successfully", 
            "old_name": old_name,
            "new_name": new_name
        }
    except Exception as e:
        logger.error(f"Error updating tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tools/{tool_name}")
async def delete_tool(tool_name: str):
    """Delete a custom tool."""
    try:
        success = tool_registry.remove_tool(tool_name)
        if not success:
            raise HTTPException(status_code=404, detail="Custom tool not found or cannot be deleted")
        
        return {"message": "Tool deleted successfully", "tool_name": tool_name}
    except Exception as e:
        logger.error(f"Error deleting tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query_agent(request: Request):
    """Process a query through the agent."""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Process the query through the agent
        result = await agent.process_query(query)
        
        return {
            "response": result["response"],
            "reasoning": result.get("reasoning", []),
            "tools_used": result.get("tools_used", []),
            "understanding": result.get("understanding", {})
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/query")
async def ws_query(websocket: WebSocket):
    await websocket.accept()
    try:
        init = await websocket.receive_json()
        user_query = init.get("query", "")
        if not user_query:
            await websocket.send_json({"type": "error", "data": {"message": "Query is required"}})
            await websocket.close()
            return

        # Stream events from agent
        async for event in agent.stream_query(user_query):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "data": {"message": "Internal error"}})
        except Exception:
            pass
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
