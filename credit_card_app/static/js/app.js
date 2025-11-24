// API Base URL
const API_BASE = '/credit-card/api';

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
