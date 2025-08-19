// Reasoning display logic
class ReasoningDisplay {
    constructor() {
        this.currentReasoning = [];
    }

    addReasoningStep(step) {
        this.currentReasoning.push(step);
        this.renderReasoning();
    }

    clearReasoning() {
        this.currentReasoning = [];
        this.renderReasoning();
    }

    renderReasoning() {
        const reasoningContainer = document.getElementById('reasoningContainer');
        if (!reasoningContainer) return;

        if (this.currentReasoning.length === 0) {
            reasoningContainer.innerHTML = '';
            return;
        }

        const reasoningHtml = ResponseFormatter.formatReasoning(this.currentReasoning);
        reasoningContainer.innerHTML = reasoningHtml;
    }

    // Enhanced reasoning step display with collapsible sections
    static createCollapsibleReasoningStep(step, index) {
        let stepHtml = `
            <div class="reasoning-step mb-4">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-semibold text-lg" style="color: #0A6190;">
                        Step ${index + 1}: ${step.description || step.step}
                    </h3>
                    ${step.intelligence_level ? 
                        `<span class="px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                            ${step.intelligence_level}
                        </span>` : ''
                    }
                </div>
        `;

        // Tool information
        if (step.tool_name) {
            stepHtml += `
                <div class="mb-2">
                    <span class="text-sm font-medium text-gray-700">🔧 Tool:</span>
                    <span class="text-sm text-gray-600 ml-1">${step.tool_name}</span>
                </div>
            `;
        }

        // Results count
        if (step.result_count !== undefined) {
            stepHtml += `
                <div class="mb-2">
                    <span class="text-sm font-medium text-gray-700">📊 Results:</span>
                    <span class="text-sm text-gray-600 ml-1">${step.result_count} items</span>
                </div>
            `;
        }

        // Category
        if (step.category) {
            stepHtml += `
                <div class="mb-2">
                    <span class="text-sm font-medium text-gray-700">🏷️ Category:</span>
                    <span class="text-sm text-gray-600 ml-1">${step.category}</span>
                </div>
            `;
        }

        // Database metrics
        if (step.db_metrics) {
            const metrics = step.db_metrics;
            const latency = metrics.latency_ms ? Number(metrics.latency_ms).toFixed(1) : '?';
            const rows = metrics.rows || '?';
            
            stepHtml += `
                <div class="mb-2">
                    <span class="text-sm font-medium text-gray-700">⏱️ Query Metrics:</span>
                    <span class="text-sm text-gray-600 ml-1">
                        latency ${latency}ms, rows ${rows}
                    </span>
                </div>
            `;
        }

        // Special handling for text2cypher results
        if (step.tool_name === 'text2cypher' && step.generated_query) {
            stepHtml += this.createText2CypherSection(step);
        }

        // Understanding and reasoning
        if (step.understanding) {
            stepHtml += `
                <div class="mb-2">
                    <span class="text-sm font-medium text-gray-700">Understanding:</span>
                    <span class="text-sm text-gray-600 ml-1">${step.understanding}</span>
                </div>
            `;
        }

        if (step.reasoning) {
            stepHtml += `
                <div class="mb-2">
                    <span class="text-sm font-medium text-gray-700">Reasoning:</span>
                    <span class="text-sm text-gray-600 ml-1">${step.reasoning}</span>
                </div>
            `;
        }

        // LLM reasoning details (collapsible)
        if (step.llm_reasoning_details || step.llm_reasoning) {
            stepHtml += this.createLLMDetailsSection(step);
        }

        stepHtml += '</div>';
        return stepHtml;
    }

    static createText2CypherSection(step) {
        return `
            <div class="mt-3 space-y-3">
                <!-- Generated Cypher Query -->
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
                
                <!-- Explanation -->
                ${step.explanation ? `
                    <div class="p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <div class="text-sm text-gray-700">
                            <span class="font-medium text-blue-800">💡 Explanation:</span> ${step.explanation}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Results Table -->
                ${step.results && step.results.length > 0 ? `
                    <div class="mt-3">
                        <div class="text-sm font-medium text-gray-700 mb-2">
                            📊 Results (${step.results.length}):
                        </div>
                        <div class="overflow-x-auto">
                            <table class="min-w-full bg-white border border-gray-200 rounded-lg">
                                <thead class="bg-gray-50">
                                    <tr>
                                        ${Object.keys(step.results[0]).map(key => 
                                            `<th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">${key}</th>`
                                        ).join('')}
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-200">
                                    ${step.results.map((result, idx) => `
                                        <tr class="hover:bg-gray-50">
                                            ${Object.values(result).map(value => 
                                                `<td class="px-3 py-2 text-xs text-gray-900 border-b">${value}</td>`
                                            ).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    static createLLMDetailsSection(step) {
        const llmDetails = step.llm_reasoning_details || step.llm_reasoning;
        
        return `
            <details class="mt-3 rounded-lg border border-gray-200 bg-white">
                <summary class="cursor-pointer font-semibold p-3 flex items-center space-x-2 rounded-t-lg transition-colors text-blue-600 hover:bg-blue-50">
                    <span>🤖</span>
                    <span>LLM Reasoning Details</span>
                    <span class="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                        ${llmDetails.intelligence_level || 'LLM-powered'}
                    </span>
                </summary>
                <div class="p-3 space-y-3 border-t border-gray-200">
                    ${llmDetails.llm_model ? `
                        <div class="text-sm">
                            <strong>Model:</strong> ${llmDetails.llm_model}
                        </div>
                    ` : ''}
                    
                    ${llmDetails.temperature ? `
                        <div class="text-sm">
                            <strong>Temperature:</strong> ${llmDetails.temperature}
                        </div>
                    ` : ''}
                    
                    ${llmDetails.max_tokens ? `
                        <div class="text-sm">
                            <strong>Max Tokens:</strong> ${llmDetails.max_tokens}
                        </div>
                    ` : ''}
                    
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
                    
                    ${llmDetails.query_type ? `
                        <div class="text-sm">
                            <strong>Query Type:</strong> ${llmDetails.query_type}
                        </div>
                    ` : ''}
                    
                    ${llmDetails.expected_insights ? `
                        <div class="text-sm">
                            <strong>Expected Insights:</strong> ${llmDetails.expected_insights}
                        </div>
                    ` : ''}
                    
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
}

// Export for use in other modules
window.ReasoningDisplay = ReasoningDisplay;
