// API Base URL
const API_BASE = '/credit-card/api';

// Global chart instance
let currentChart = null;

// Utility Functions
const showLoading = () => document.getElementById('loading-overlay').classList.remove('hidden');
const hideLoading = () => document.getElementById('loading-overlay').classList.add('hidden');

const showError = (message) => {
    const toast = document.getElementById('error-toast');
    const messageEl = document.getElementById('error-message');
    messageEl.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 5000);
};

const showSuccess = (message) => {
    const toast = document.getElementById('success-toast');
    const messageEl = document.getElementById('success-message');
    messageEl.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
};

// API Functions
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        const serviceStatus = document.getElementById('service-status');

        if (data.status === 'healthy') {
            serviceStatus.textContent = 'Healthy';
            serviceStatus.className = 'status-value healthy';
        } else {
            serviceStatus.textContent = 'Unhealthy';
            serviceStatus.className = 'status-value unhealthy';
        }
    } catch (error) {
        document.getElementById('service-status').textContent = 'Error';
        document.getElementById('service-status').className = 'status-value unhealthy';
        console.error('Health check failed:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        document.getElementById('total-transactions').textContent = data.total_transactions;
        document.getElementById('total-spending').textContent = `$${data.total_spending.toFixed(2)}`;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function searchTransactions() {
    const input = document.getElementById('query-input').value.trim();
    const generateSummary = document.getElementById('generate-summary').checked;

    if (!input) {
        showError('Please enter a search query');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: input,
                execute: true,
                summarize: generateSummary
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Query failed');
        }

        const data = await response.json();

        // Show summary if generated
        if (data.summary && generateSummary) {
            document.getElementById('query-summary-section').classList.remove('hidden');
            document.getElementById('query-summary-text').textContent = data.summary;
        } else {
            document.getElementById('query-summary-section').classList.add('hidden');
        }

        // Show query results
        document.getElementById('query-result-section').classList.remove('hidden');
        document.getElementById('query-explanation').textContent = data.explanation;
        document.getElementById('query-output').textContent = JSON.stringify(data.generated_mql, null, 2);

        if (data.results) {
            displayTransactionResults(data);
            showSuccess(`Found ${data.count} transactions in ${data.execution_time_ms}ms`);
        }
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function displayTransactionResults(data) {
    const resultsSection = document.getElementById('query-execution-results');
    resultsSection.classList.remove('hidden');

    document.getElementById('query-result-count').textContent = `${data.count} transactions`;
    document.getElementById('query-execution-time').textContent = `${data.execution_time_ms}ms`;

    const tableContainer = document.getElementById('query-results-table');

    if (data.results.length === 0) {
        tableContainer.innerHTML = '<p>No transactions found</p>';
        return;
    }

    // Create table with relevant fields
    const relevantFields = ['transaction_date', 'merchant_name', 'category', 'amount',
                           'transaction_type', 'status', 'description'];

    const table = `
        <table>
            <thead>
                <tr>
                    ${relevantFields.map(field => `<th>${formatFieldName(field)}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${data.results.map(row => `
                    <tr>
                        ${relevantFields.map(field => `<td>${formatValue(row[field])}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    tableContainer.innerHTML = table;
}

async function analyzeTransactions() {
    const input = document.getElementById('analyze-input').value.trim();

    if (!input) {
        showError('Please enter an analysis request');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: input
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const data = await response.json();

        // Show results
        document.getElementById('analyze-result-section').classList.remove('hidden');
        document.getElementById('analysis-summary').textContent = data.summary;
        document.getElementById('analysis-total-txns').textContent = data.total_transactions;
        document.getElementById('analysis-total-amount').textContent = `$${data.total_amount.toFixed(2)}`;

        // Display insights
        const insightsList = document.getElementById('insights-list');
        insightsList.innerHTML = data.insights.map(insight => `<li>${insight}</li>`).join('');

        // Display detailed statistics
        const detailedStats = document.getElementById('detailed-stats');
        detailedStats.innerHTML = Object.entries(data.statistics)
            .map(([key, value]) => {
                if (typeof value === 'object') {
                    return `
                        <div class="stat-group">
                            <h4>${formatFieldName(key)}</h4>
                            ${Object.entries(value).map(([k, v]) => `
                                <div class="stat-item">
                                    <span class="stat-item-label">${k}</span>
                                    <span class="stat-item-value">${v}</span>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    return `
                        <div class="stat-item">
                            <span class="stat-item-label">${formatFieldName(key)}</span>
                            <span class="stat-item-value">${value}</span>
                        </div>
                    `;
                }
            }).join('');

        showSuccess('Analysis completed successfully!');
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

async function loadDashboard() {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        // Overview
        document.getElementById('dash-total-txns').textContent = data.total_transactions;
        document.getElementById('dash-total-spending').textContent = `$${data.total_spending.toFixed(2)}`;

        // Fees & Charges Summary
        const feesSummary = document.getElementById('fees-summary');
        if (data.fees_summary) {
            const fees = data.fees_summary;
            feesSummary.innerHTML = `
                <div class="breakdown-item">
                    <span class="breakdown-label">Total Interest Charged</span>
                    <span class="breakdown-value fee-value">$${fees.total_interest_charged.toFixed(2)}</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Total Late Fees</span>
                    <span class="breakdown-value fee-value">$${fees.total_late_fees.toFixed(2)}</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Total Annual Fees</span>
                    <span class="breakdown-value fee-value">$${fees.total_annual_fees.toFixed(2)}</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Foreign Transaction Fees</span>
                    <span class="breakdown-value fee-value">$${fees.total_foreign_transaction_fees.toFixed(2)}</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Other Fees</span>
                    <span class="breakdown-value fee-value">$${fees.total_other_fees.toFixed(2)}</span>
                </div>
                <div class="breakdown-item highlight">
                    <span class="breakdown-label">Total Rewards Earned</span>
                    <span class="breakdown-value reward-value">$${fees.total_rewards_earned.toFixed(2)}</span>
                </div>
            `;
        }

        // Account/Card-wise breakdown
        const cardBreakdown = document.getElementById('card-breakdown');
        if (data.by_card && data.by_card.length > 0) {
            cardBreakdown.innerHTML = data.by_card
                .map(card => {
                    const netCost = card.total_spending + card.total_interest + card.total_fees - card.total_rewards;
                    return `
                        <div class="card-breakdown-item">
                            <div class="card-header">
                                <strong>${card._id.cardholder_name}</strong> - ${card._id.card_number}
                            </div>
                            <div class="card-stats">
                                <div class="stat-item-inline">
                                    <span class="stat-label-inline">Transactions:</span>
                                    <span class="stat-value-inline">${card.count}</span>
                                </div>
                                <div class="stat-item-inline">
                                    <span class="stat-label-inline">Spending:</span>
                                    <span class="stat-value-inline">$${card.total_spending.toFixed(2)}</span>
                                </div>
                                <div class="stat-item-inline">
                                    <span class="stat-label-inline">Interest:</span>
                                    <span class="stat-value-inline fee-value">$${card.total_interest.toFixed(2)}</span>
                                </div>
                                <div class="stat-item-inline">
                                    <span class="stat-label-inline">Fees:</span>
                                    <span class="stat-value-inline fee-value">$${card.total_fees.toFixed(2)}</span>
                                </div>
                                <div class="stat-item-inline">
                                    <span class="stat-label-inline">Rewards:</span>
                                    <span class="stat-value-inline reward-value">-$${card.total_rewards.toFixed(2)}</span>
                                </div>
                                <div class="stat-item-inline highlight">
                                    <span class="stat-label-inline"><strong>Net Cost:</strong></span>
                                    <span class="stat-value-inline"><strong>$${netCost.toFixed(2)}</strong></span>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
        } else {
            cardBreakdown.innerHTML = '<p>No card data available</p>';
        }

        // Category breakdown
        const categoryBreakdown = document.getElementById('category-breakdown');
        categoryBreakdown.innerHTML = data.by_category
            .map(cat => `
                <div class="breakdown-item">
                    <span class="breakdown-label">${cat._id}</span>
                    <span class="breakdown-value">$${cat.total.toFixed(2)} (${cat.count})</span>
                </div>
            `).join('');

        // Monthly breakdown
        const monthlyBreakdown = document.getElementById('monthly-breakdown');
        monthlyBreakdown.innerHTML = data.by_month
            .map(month => `
                <div class="breakdown-item">
                    <span class="breakdown-label">${month._id.year}-${String(month._id.month).padStart(2, '0')}</span>
                    <span class="breakdown-value">$${month.total.toFixed(2)} (${month.count})</span>
                </div>
            `).join('');

        // Type breakdown
        const typeBreakdown = document.getElementById('type-breakdown');
        typeBreakdown.innerHTML = data.by_type
            .map(type => `
                <div class="breakdown-item">
                    <span class="breakdown-label">${type._id}</span>
                    <span class="breakdown-value">$${type.total.toFixed(2)} (${type.count})</span>
                </div>
            `).join('');

        showSuccess('Dashboard refreshed!');
    } catch (error) {
        showError('Failed to load dashboard');
    } finally {
        hideLoading();
    }
}

function formatFieldName(field) {
    return field.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function formatValue(value) {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'object') {
        if (value.$date) return new Date(value.$date).toLocaleString();
        return JSON.stringify(value);
    }
    if (typeof value === 'number') {
        return value.toFixed(2);
    }
    return String(value);
}

// Tab Management
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');

            if (tabName === 'dashboard') {
                loadDashboard();
            }
        });
    });
}

// Example Click Handlers
function initExamples() {
    document.querySelectorAll('.example-item').forEach(item => {
        item.addEventListener('click', () => {
            const query = item.dataset.query;
            const parentTab = item.closest('.tab-content');

            if (parentTab.id === 'query-tab') {
                document.getElementById('query-input').value = query;
            } else if (parentTab.id === 'analyze-tab') {
                document.getElementById('analyze-input').value = query;
            }
        });
    });
}

// Toast Close Handlers
function initToasts() {
    document.querySelectorAll('.toast-close').forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.toast').classList.add('hidden');
        });
    });
}

// Smart Search with Charts
async function performSmartSearch() {
    const input = document.getElementById('smart-search-input').value.trim();
    const autoChart = document.getElementById('auto-chart').checked;

    if (!input) {
        showError('Please enter a search query');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: input,
                execute: true
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Query failed');
        }

        const data = await response.json();

        console.log('Query response received:', {
            count: data.count,
            hasChartMetadata: !!data.chart_metadata,
            chartable: data.chart_metadata?.chartable,
            chartType: data.chart_metadata?.chart_type,
            xField: data.chart_metadata?.x_field,
            autoChart: autoChart
        });

        // Show results section
        document.getElementById('smart-search-results').classList.remove('hidden');

        // Populate query details
        document.getElementById('smart-query-explanation').textContent = data.explanation;
        document.getElementById('smart-query-code').textContent = JSON.stringify(data.generated_mql, null, 2);
        document.getElementById('smart-query-count').textContent = `${data.count} results`;
        document.getElementById('smart-query-time').textContent = `${data.execution_time_ms}ms`;

        // Populate table view
        displaySmartTable(data.results);

        // Generate chart if possible
        if (autoChart && data.chart_metadata && data.chart_metadata.chartable) {
            console.log('Rendering chart...');
            renderSmartChart(data.results, data.chart_metadata);
            // Switch to chart view
            switchResultsView('chart');
        } else {
            console.log('Not rendering chart:', {
                autoChart,
                hasMetadata: !!data.chart_metadata,
                chartable: data.chart_metadata?.chartable
            });
            // Switch to table view if no chart
            switchResultsView('table');
            const chartView = document.getElementById('chart-view');
            chartView.innerHTML = '<p class="no-chart-message">This query is not suitable for chart visualization. Showing table view instead.</p>';
        }

        showSuccess(`Found ${data.count} results in ${data.execution_time_ms}ms`);
    } catch (error) {
        showError(error.message);
        document.getElementById('smart-search-results').classList.add('hidden');
    } finally {
        hideLoading();
    }
}

function renderSmartChart(results, metadata) {
    console.log('renderSmartChart called with:', {
        resultCount: results.length,
        metadata: metadata
    });

    const chartView = document.getElementById('chart-view');

    // Ensure canvas exists (it may have been replaced by a message)
    let canvas = document.getElementById('smart-chart');
    if (!canvas) {
        console.log('Canvas not found, recreating...');
        chartView.innerHTML = `
            <div class="chart-container-wrapper">
                <canvas id="smart-chart"></canvas>
            </div>
            <div id="chart-insights" class="chart-insights"></div>
        `;
        canvas = document.getElementById('smart-chart');
    }

    try {
        const ctx = canvas.getContext('2d');

        // Destroy previous chart if exists
        if (currentChart) {
            currentChart.destroy();
        }

        // Prepare data based on chart type
        const chartData = prepareChartData(results, metadata);

        // Check if we have valid data to chart
        if (!chartData.labels.length || !chartData.datasets[0].data.length) {
            throw new Error('No valid data for charting');
        }

        // Chart configuration
        const config = {
            type: metadata.chart_type,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: metadata.chart_type === 'pie' || metadata.chart_type === 'doughnut',
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: metadata.label || 'Results',
                        font: { size: 18, weight: 'bold' }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += '$' + context.parsed.toFixed(2);
                                return label;
                            }
                        }
                    }
                },
                scales: metadata.chart_type !== 'pie' && metadata.chart_type !== 'doughnut' ? {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                } : {}
            }
        };

        currentChart = new Chart(ctx, config);

        // Generate insights
        generateChartInsights(results, metadata);
    } catch (error) {
        console.error('Chart rendering error:', error);
        chartView.innerHTML = `<p class="no-chart-message">Unable to render chart: ${error.message}</p>`;
    }
}

function prepareChartData(results, metadata) {
    console.log('prepareChartData called with:', {
        resultCount: results.length,
        metadata: metadata,
        sampleResult: results[0]
    });

    const labels = [];
    const values = [];

    results.forEach((item, index) => {
        // Handle grouped results (aggregations)
        if (item._id !== undefined && item._id !== null) {
            let label;
            if (typeof item._id === 'object') {
                // Time-based grouping
                if (item._id.year && item._id.month) {
                    label = `${item._id.year}-${String(item._id.month).padStart(2, '0')}`;
                } else {
                    label = JSON.stringify(item._id);
                }
            } else {
                label = String(item._id);
            }
            labels.push(label);
            values.push(Math.abs(item.total || item.count || 0));
        } else {
            // Handle individual transactions - try different fields for labels
            let label = null;

            // Try merchant_name first
            if (item.merchant_name) {
                label = item.merchant_name;
            }
            // Try transaction_date
            else if (item.transaction_date) {
                const dateObj = item.transaction_date.$date
                    ? new Date(item.transaction_date.$date)
                    : new Date(item.transaction_date);
                label = dateObj.toLocaleDateString();
            }
            // Try category
            else if (item.category) {
                label = item.category;
            }
            // Try transaction_id or just use index
            else if (item.transaction_id) {
                label = item.transaction_id;
            } else {
                label = `Item ${index + 1}`;
            }

            labels.push(label);
            values.push(Math.abs(item.amount || item.total || 0));
        }
    });

    // Limit to top 15 for readability
    const maxItems = 15;
    if (labels.length > maxItems) {
        labels.splice(maxItems);
        values.splice(maxItems);
    }

    // Color schemes
    const colorScheme = generateColorScheme(values.length);

    console.log('prepareChartData generated:', {
        labelCount: labels.length,
        valueCount: values.length,
        sampleLabels: labels.slice(0, 5),
        sampleValues: values.slice(0, 5)
    });

    return {
        labels: labels,
        datasets: [{
            label: metadata.label || 'Amount ($)',
            data: values,
            backgroundColor: colorScheme.backgrounds,
            borderColor: colorScheme.borders,
            borderWidth: 2
        }]
    };
}

function generateColorScheme(count) {
    const baseColors = [
        { r: 139, g: 92, b: 246 },   // Purple
        { r: 59, g: 130, b: 246 },   // Blue
        { r: 16, g: 185, b: 129 },   // Green
        { r: 245, g: 158, b: 11 },   // Orange
        { r: 239, g: 68, b: 68 },    // Red
        { r: 236, g: 72, b: 153 },   // Pink
        { r: 14, g: 165, b: 233 },   // Cyan
        { r: 168, g: 85, b: 247 },   // Violet
    ];

    const backgrounds = [];
    const borders = [];

    for (let i = 0; i < count; i++) {
        const color = baseColors[i % baseColors.length];
        backgrounds.push(`rgba(${color.r}, ${color.g}, ${color.b}, 0.7)`);
        borders.push(`rgba(${color.r}, ${color.g}, ${color.b}, 1)`);
    }

    return { backgrounds, borders };
}

function generateChartInsights(results, metadata) {
    const insightsDiv = document.getElementById('chart-insights');
    const insights = [];

    if (results.length === 0) {
        insightsDiv.innerHTML = '<p>No data to analyze</p>';
        return;
    }

    // Calculate total
    const total = results.reduce((sum, item) => {
        return sum + Math.abs(item.total || item.amount || 0);
    }, 0);

    insights.push(`Total: $${total.toFixed(2)}`);

    // Find highest
    const sorted = [...results].sort((a, b) => {
        const aVal = Math.abs(a.total || a.amount || 0);
        const bVal = Math.abs(b.total || b.amount || 0);
        return bVal - aVal;
    });

    if (sorted.length > 0) {
        const highest = sorted[0];
        let highestLabel = highest._id || highest.merchant_name || 'Unknown';
        if (typeof highestLabel === 'object') {
            highestLabel = JSON.stringify(highestLabel);
        }
        const highestValue = Math.abs(highest.total || highest.amount || 0);
        insights.push(`Highest: ${highestLabel} ($${highestValue.toFixed(2)})`);
    }

    // Average
    const avg = total / results.length;
    insights.push(`Average: $${avg.toFixed(2)}`);

    insightsDiv.innerHTML = insights.map(i => `<div class="insight-item">💡 ${i}</div>`).join('');
}

function displaySmartTable(results) {
    const tableDiv = document.getElementById('smart-table');

    if (!results || results.length === 0) {
        tableDiv.innerHTML = '<p>No results found</p>';
        return;
    }

    // Determine fields to display
    const sampleRow = results[0];
    const fields = Object.keys(sampleRow).filter(k => k !== '__v');

    const table = `
        <table>
            <thead>
                <tr>
                    ${fields.map(field => `<th>${formatFieldName(field)}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${results.slice(0, 50).map(row => `
                    <tr>
                        ${fields.map(field => `<td>${formatValue(row[field])}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
        ${results.length > 50 ? `<p class="table-note">Showing first 50 of ${results.length} results</p>` : ''}
    `;
    tableDiv.innerHTML = table;
}

function switchResultsView(viewName) {
    // Update tab buttons
    document.querySelectorAll('.results-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    // Update view content
    document.querySelectorAll('.results-view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`${viewName}-view`).classList.add('active');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initExamples();
    initToasts();
    checkHealth();
    loadStats();

    // Query Tab
    document.getElementById('execute-query-btn').addEventListener('click', searchTransactions);
    document.getElementById('clear-query-btn').addEventListener('click', () => {
        document.getElementById('query-input').value = '';
        document.getElementById('query-result-section').classList.add('hidden');
        document.getElementById('query-summary-section').classList.add('hidden');
    });

    // Analyze Tab
    document.getElementById('analyze-btn').addEventListener('click', analyzeTransactions);
    document.getElementById('clear-analyze-btn').addEventListener('click', () => {
        document.getElementById('analyze-input').value = '';
        document.getElementById('analyze-result-section').classList.add('hidden');
    });

    // Dashboard Tab
    document.getElementById('refresh-dashboard-btn').addEventListener('click', loadDashboard);

    // Smart Search
    document.getElementById('smart-search-btn').addEventListener('click', performSmartSearch);
    document.getElementById('smart-search-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            performSmartSearch();
        }
    });

    // Results view switching
    document.querySelectorAll('.results-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchResultsView(btn.dataset.view);
        });
    });

    // Enter key support
    document.querySelectorAll('.input-textarea').forEach(textarea => {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                const parentTab = textarea.closest('.tab-content');
                if (parentTab.id === 'query-tab') {
                    searchTransactions();
                } else if (parentTab.id === 'analyze-tab') {
                    analyzeTransactions();
                }
            }
        });
    });
});
