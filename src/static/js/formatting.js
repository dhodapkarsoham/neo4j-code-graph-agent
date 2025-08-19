// Response formatting utilities
class ResponseFormatter {
    static formatResponse(content) {
        try {
            if (window.marked && window.DOMPurify) {
                const html = window.marked.parse(content || '');
                const sanitized = window.DOMPurify.sanitize(html);
                
                // Add CSS styling for tables to make them scrollable
                let enhancedHtml = sanitized.replace(
                    /<table>/g,
                    '<div style="max-height: 400px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px;"><table style="width: 100%; border-collapse: collapse;">'
                ).replace(
                    /<\/table>/g,
                    '</table></div>'
                ).replace(
                    /<thead>/g,
                    '<thead style="background-color: #f9fafb; position: sticky; top: 0; z-index: 10;">'
                ).replace(
                    /<th>/g,
                    '<th style="padding: 10px 12px; text-align: left; font-size: 14px; font-weight: 600; text-transform: uppercase; color: #6b7280; border-bottom: 1px solid #e5e7eb;">'
                ).replace(
                    /<td>/g,
                    '<td style="padding: 10px 12px; font-size: 14px; color: #111827; border-bottom: 1px solid #e5e7eb;">'
                );
                
                // Add scroll indicator for tables with many rows
                enhancedHtml = enhancedHtml.replace(
                    /(<\/table><\/div>)/g,
                    (match, p1) => {
                        // Count table rows to determine if we need a scroll indicator
                        const tableMatch = match.match(/<tr>/g);
                        const rowCount = tableMatch ? tableMatch.length - 1 : 0; // Subtract 1 for header row
                        
                        if (rowCount > 10) {
                            return p1 + `<div style="text-align: center; padding: 10px; font-size: 14px; color: #6b7280; background-color: #f9fafb; border-top: 1px solid #e5e7eb;">📜 Scroll to see all ${rowCount} results</div>`;
                        }
                        return p1;
                    }
                );
                
                return enhancedHtml;
            }
        } catch (e) {}
        // Fallback minimal formatting
        return (content || '').replace(/\\n/g, '<br>').replace(/\\"/g, '"');
    }

    static formatReasoning(reasoning) {
        if (!reasoning || !Array.isArray(reasoning)) return '';
        return reasoning.map((step, index) => {
            let stepHtml = `
                <div class="mb-4 p-4 rounded-xl border border-gray-100 shadow-sm" style="background: linear-gradient(135deg, rgba(252, 249, 246, 0.6) 0%, rgba(255, 255, 255, 0.8) 100%); border-left: 4px solid #0A6190;">
                    <div class="flex items-center justify-between mb-3">
                        <div class="font-bold text-lg" style="color: #0A6190;">
                            Step ${index + 1}: ${step.description || step.step}
                        </div>
                        ${step.intelligence_level ? `<span class="px-3 py-1 rounded-full text-xs font-semibold" style="background: rgba(252, 249, 246, 0.9); color: #0A6190; border: 1px solid rgba(10, 97, 144, 0.2);">${step.intelligence_level}</span>` : ''}
                    </div>
            `;
            
            // Tool execution details
            if (step.tool_name) {
                stepHtml += `<div class="text-sm mb-2" style="color: #0A6190;">🔧 Tool: ${step.tool_name}</div>`;
            }
            if (step.result_count !== undefined) {
                stepHtml += `<div class="text-sm mb-2" style="color: #0A6190;">📊 Results: ${step.result_count} items</div>`;
            }
            if (step.category) {
                stepHtml += `<div class="text-sm mb-2" style="color: #0A6190;">🏷️ Category: ${step.category}</div>`;
            }
            if (step.db_metrics) {
                const m = step.db_metrics;
                const latency = (m && m.latency_ms != null) ? Number(m.latency_ms).toFixed(1) : '?';
                const rows = (m && m.rows != null) ? m.rows : '?';
                const avail = (m && m.available_after_ms != null) ? m.available_after_ms : '?';
                const consumed = (m && m.consumed_after_ms != null) ? m.consumed_after_ms : '?';
                stepHtml += `<div class="text-xs mb-2" style="color: #6B7280;">⏱️ Query Metrics: latency ${latency} ms, rows ${rows}, avail ${avail} ms, consumed ${consumed} ms</div>`;
            }
            
            // Special display for text2cypher results
            if (step.tool_name === 'text2cypher' && step.generated_query) {
                stepHtml += `
                    <div class="mt-3">
                        <details class="rounded-lg border border-gray-200 bg-white">
                            <summary class="cursor-pointer p-3 flex items-center justify-between hover:bg-gray-50 transition-colors">
                                <div class="flex items-center space-x-2">
                                    <span class="text-blue-600">🔍</span>
                                    <span class="font-medium text-gray-900">Generated Cypher Query</span>
                                </div>
                                <span class="text-xs text-gray-500">Click to view</span>
                            </summary>
                            <div class="border-t border-gray-200 p-3 bg-gray-50">
                                <pre class="text-sm p-3 bg-white rounded border overflow-x-auto font-mono text-gray-800">${step.generated_query}</pre>
                            </div>
                        </details>
                        
                        ${step.explanation ? `
                            <div class="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                                <div class="text-sm text-gray-700">
                                    <span class="font-medium text-blue-800">💡 Explanation:</span> ${step.explanation}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            // Understanding and reasoning
            if (step.understanding) {
                stepHtml += `<div class="text-sm mb-2" style="color: #374151;"><strong style="color: #0A6190;">Understanding:</strong> ${step.understanding}</div>`;
            }
            if (step.reasoning) {
                stepHtml += `<div class="text-sm mb-2" style="color: #374151;"><strong style="color: #0A6190;">Reasoning:</strong> ${step.reasoning}</div>`;
            }
            if (step.llm_analysis) {
                stepHtml += `<div class="text-sm mb-2" style="color: #374151;"><strong style="color: #0A6190;">LLM Analysis:</strong> ${step.llm_analysis}</div>`;
            }
            
            // LLM Reasoning Details
            if (step.llm_reasoning_details || step.llm_reasoning) {
                const llmDetails = step.llm_reasoning_details || step.llm_reasoning;
                stepHtml += `
                    <details class="mt-3 rounded-lg border" style="background: rgba(255, 255, 255, 0.8); border-color: rgba(10, 97, 144, 0.2);">
                        <summary class="cursor-pointer font-semibold p-3 flex items-center space-x-2 rounded-t-lg transition-colors" style="color: #0A6190;" onmouseover="this.style.background='rgba(252, 249, 246, 0.5)'" onmouseout="this.style.background='transparent'">
                            <span>🤖</span>
                            <span>LLM Reasoning Details</span>
                            <span class="px-2 py-1 rounded-full text-xs" style="background: rgba(252, 249, 246, 0.9); color: #0A6190; border: 1px solid rgba(10, 97, 144, 0.2);">
                                ${llmDetails.intelligence_level || 'LLM-powered'}
                            </span>
                        </summary>
                        <div class="p-3 space-y-3" style="border-top: 1px solid rgba(10, 97, 144, 0.2);">
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
    }

    static getCategoryClass(category) {
        const classes = {
            'Security': 'bg-red-100 text-red-800',
            'Quality': 'bg-yellow-100 text-yellow-800',
            'Team': 'bg-blue-100 text-blue-800',
            'Architecture': 'bg-purple-100 text-purple-800',
            'Query': 'bg-green-100 text-green-800',
            'Custom': 'bg-gray-100 text-gray-800'
        };
        return classes[category] || 'bg-gray-100 text-gray-800';
    }

    static groupMessages(msgs) {
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
    }
}

// Export for use in other modules
window.ResponseFormatter = ResponseFormatter;
