// API Base URL
const API_BASE = '/api/v1';

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

        const apiStatus = document.getElementById('api-status');
        const dbStatus = document.getElementById('db-status');

        if (data.status === 'healthy') {
            apiStatus.textContent = 'Healthy';
            apiStatus.className = 'status-value healthy';
            dbStatus.textContent = 'Connected';
            dbStatus.className = 'status-value healthy';
        } else {
            apiStatus.textContent = 'Unhealthy';
            apiStatus.className = 'status-value unhealthy';
            dbStatus.textContent = data.database;
            dbStatus.className = 'status-value unhealthy';
        }
    } catch (error) {
        document.getElementById('api-status').textContent = 'Error';
        document.getElementById('api-status').className = 'status-value unhealthy';
        console.error('Health check failed:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        document.getElementById('total-records').textContent = data.total_notifications;
        document.getElementById('total-notifications').textContent = data.total_notifications;

        // Status breakdown
        const statusBreakdown = document.getElementById('status-breakdown');
        statusBreakdown.innerHTML = Object.entries(data.by_status || {})
            .map(([key, value]) => `
                <div class="stat-item">
                    <span class="stat-item-label">${key}</span>
                    <span class="stat-item-value">${value}</span>
                </div>
            `).join('');

        // Channel breakdown
        const channelBreakdown = document.getElementById('channel-breakdown');
        channelBreakdown.innerHTML = Object.entries(data.by_channel || {})
            .map(([key, value]) => `
                <div class="stat-item">
                    <span class="stat-item-label">${key}</span>
                    <span class="stat-item-value">${value}</span>
                </div>
            `).join('');
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function generateQuery(execute = false) {
    const input = document.getElementById('query-input').value.trim();
    if (!input) {
        showError('Please enter a query');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: input,
                execute: execute
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Query generation failed');
        }

        const data = await response.json();

        // Show results
        document.getElementById('query-result-section').classList.remove('hidden');
        document.getElementById('query-explanation').textContent = data.explanation;
        document.getElementById('query-output').textContent = JSON.stringify(data.generated_mql, null, 2);

        if (execute && data.results) {
            displayQueryResults(data);
            showSuccess(`Query executed successfully! Found ${data.count} results in ${data.execution_time_ms}ms`);
        } else {
            document.getElementById('query-execution-results').classList.add('hidden');
            showSuccess('Query generated successfully!');
        }
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function displayQueryResults(data) {
    const resultsSection = document.getElementById('query-execution-results');
    resultsSection.classList.remove('hidden');

    document.getElementById('query-result-count').textContent = `${data.count} results`;
    document.getElementById('query-execution-time').textContent = `Executed in ${data.execution_time_ms}ms`;

    const tableContainer = document.getElementById('query-results-table');

    if (data.results.length === 0) {
        tableContainer.innerHTML = '<p>No results found</p>';
        return;
    }

    // Create table
    const keys = Object.keys(data.results[0]);
    const table = `
        <table>
            <thead>
                <tr>${keys.map(key => `<th>${key}</th>`).join('')}</tr>
            </thead>
            <tbody>
                ${data.results.map(row => `
                    <tr>${keys.map(key => `<td>${formatValue(row[key])}</td>`).join('')}</tr>
                `).join('')}
            </tbody>
        </table>
    `;
    tableContainer.innerHTML = table;
}

async function generateAggregation(execute = false) {
    const input = document.getElementById('aggregation-input').value.trim();
    if (!input) {
        showError('Please enter an aggregation query');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/aggregation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: input,
                execute: execute
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Aggregation generation failed');
        }

        const data = await response.json();

        // Show results
        document.getElementById('agg-result-section').classList.remove('hidden');
        document.getElementById('agg-explanation').textContent = data.explanation;
        document.getElementById('agg-output').textContent = JSON.stringify(data.generated_pipeline, null, 2);

        if (execute && data.results) {
            displayAggregationResults(data);
            showSuccess(`Aggregation executed successfully in ${data.execution_time_ms}ms`);
        } else {
            document.getElementById('agg-execution-results').classList.add('hidden');
            showSuccess('Aggregation pipeline generated successfully!');
        }
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function displayAggregationResults(data) {
    const resultsSection = document.getElementById('agg-execution-results');
    resultsSection.classList.remove('hidden');

    document.getElementById('agg-execution-time').textContent = `Executed in ${data.execution_time_ms}ms`;

    const tableContainer = document.getElementById('agg-results-table');

    if (data.results.length === 0) {
        tableContainer.innerHTML = '<p>No results found</p>';
        return;
    }

    // Create table
    const keys = Object.keys(data.results[0]);
    const table = `
        <table>
            <thead>
                <tr>${keys.map(key => `<th>${key}</th>`).join('')}</tr>
            </thead>
            <tbody>
                ${data.results.map(row => `
                    <tr>${keys.map(key => `<td>${formatValue(row[key])}</td>`).join('')}</tr>
                `).join('')}
            </tbody>
        </table>
    `;
    tableContainer.innerHTML = table;
}

async function generateReport() {
    const input = document.getElementById('report-input').value.trim();
    const format = document.getElementById('report-format').value;

    if (!input) {
        showError('Please enter a report description');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_input: input,
                report_format: format
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Report generation failed');
        }

        const data = await response.json();

        // Show results
        document.getElementById('report-result-section').classList.remove('hidden');

        const reportInfo = document.getElementById('report-info');
        reportInfo.innerHTML = `
            <strong>Report Generated:</strong> ${data.report_name}<br>
            <strong>Format:</strong> ${data.format.toUpperCase()}<br>
            <strong>File:</strong> ${data.file_path}
        `;

        const downloadSection = document.getElementById('report-download');
        downloadSection.innerHTML = `
            <p><strong>Report saved to:</strong> <code>${data.file_path}</code></p>
            <p>The report has been generated and saved on the server.</p>
        `;

        showSuccess('Report generated successfully!');
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

async function viewSchema() {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/schema`);
        const data = await response.json();

        const schemaDisplay = document.getElementById('schema-display');
        schemaDisplay.innerHTML = `<pre class="code-output">${JSON.stringify(data, null, 2)}</pre>`;
        schemaDisplay.classList.remove('hidden');
    } catch (error) {
        showError('Failed to load schema');
    } finally {
        hideLoading();
    }
}

function formatValue(value) {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'object') {
        if (value.$date) return new Date(value.$date).toLocaleString();
        return JSON.stringify(value);
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

            // Update buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Update content
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Load stats when stats tab is opened
            if (tabName === 'stats') {
                loadStats();
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
            } else if (parentTab.id === 'aggregation-tab') {
                document.getElementById('aggregation-input').value = query;
            } else if (parentTab.id === 'report-tab') {
                document.getElementById('report-input').value = query;
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
    // Initialize
    initTabs();
    initExamples();
    initToasts();
    checkHealth();
    loadStats();

    // Query Tab
    document.getElementById('generate-query-btn').addEventListener('click', () => generateQuery(false));
    document.getElementById('execute-query-btn').addEventListener('click', () => generateQuery(true));
    document.getElementById('clear-query-btn').addEventListener('click', () => {
        document.getElementById('query-input').value = '';
        document.getElementById('query-result-section').classList.add('hidden');
    });

    // Aggregation Tab
    document.getElementById('generate-agg-btn').addEventListener('click', () => generateAggregation(false));
    document.getElementById('execute-agg-btn').addEventListener('click', () => generateAggregation(true));
    document.getElementById('clear-agg-btn').addEventListener('click', () => {
        document.getElementById('aggregation-input').value = '';
        document.getElementById('agg-result-section').classList.add('hidden');
    });

    // Report Tab
    document.getElementById('generate-report-btn').addEventListener('click', generateReport);
    document.getElementById('clear-report-btn').addEventListener('click', () => {
        document.getElementById('report-input').value = '';
        document.getElementById('report-result-section').classList.add('hidden');
    });

    // Stats Tab
    document.getElementById('view-schema-btn').addEventListener('click', viewSchema);

    // Enter key support for textareas
    document.querySelectorAll('.input-textarea').forEach(textarea => {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                const parentTab = textarea.closest('.tab-content');
                if (parentTab.id === 'query-tab') {
                    generateQuery(true);
                } else if (parentTab.id === 'aggregation-tab') {
                    generateAggregation(true);
                }
            }
        });
    });
});
