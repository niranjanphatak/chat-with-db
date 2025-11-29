// API Base URL
const API_BASE = '/api/v2';

// Global chart instance
let currentChart = null;

// Dashboard chart instances
let dashboardCharts = {
    statusPie: null,
    channelBar: null,
    typeDoughnut: null,
    priorityBar: null,
    dailyTrend: null,
    successRate: null,
    topCustomers: null,
    failedNotifications: null
};

// Event name chart instances
let eventNameCharts = {
    channelBreakdown: null,
    statusDistribution: null,
    successRates: null
};

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
        console.log('🏥 Checking health status...');
        const response = await fetch(`${API_BASE}/health`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ Health check response:', data);

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
        console.error('❌ Health check failed:', error);
        const apiStatus = document.getElementById('api-status');
        if (apiStatus) {
            apiStatus.textContent = 'Error';
            apiStatus.className = 'status-value unhealthy';
        }
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/dashboard`);
        const data = await response.json();

        // Calculate total from events
        const totalNotifications = data.events?.total || 0;
        document.getElementById('total-records').textContent = totalNotifications;

        const totalNotificationsEl = document.getElementById('total-notifications');
        if (totalNotificationsEl) {
            totalNotificationsEl.textContent = totalNotifications;
        }

        // Status breakdown from events
        const statusBreakdown = document.getElementById('status-breakdown');
        if (statusBreakdown && data.events?.by_status) {
            statusBreakdown.innerHTML = data.events.by_status
                .map(item => `
                    <div class="stat-item">
                        <span class="stat-item-label">${item._id}</span>
                        <span class="stat-item-value">${item.count}</span>
                    </div>
                `).join('');
        }

        // Channel breakdown
        const channelBreakdown = document.getElementById('channel-breakdown');
        if (channelBreakdown) {
            const channels = [
                { name: 'Email', count: data.email?.total || 0 },
                { name: 'SMS', count: data.sms?.total || 0 },
                { name: 'Push', count: data.push?.total || 0 },
                { name: 'In-App', count: data.inapp?.total || 0 }
            ];
            channelBreakdown.innerHTML = channels
                .map(ch => `
                    <div class="stat-item">
                        <span class="stat-item-label">${ch.name}</span>
                        <span class="stat-item-value">${ch.count}</span>
                    </div>
                `).join('');
        }
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
        document.getElementById('query-charts-section').classList.add('hidden');
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

    // Auto-generate all chart types
    renderAllQueryCharts(data.results);
}

async function generateAggregation(execute = false) {
    const input = document.getElementById('aggregation-input').value.trim();
    if (!input) {
        showError('Please enter an aggregation query');
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
            throw new Error(error.detail || 'Aggregation generation failed');
        }

        const data = await response.json();

        // Show results
        document.getElementById('agg-result-section').classList.remove('hidden');
        document.getElementById('agg-explanation').textContent = data.explanation;

        // V2 API returns generated_mql (not generated_pipeline)
        document.getElementById('agg-output').textContent = JSON.stringify(data.generated_mql, null, 2);

        if (execute && data.results) {
            displayAggregationResults(data);
            showSuccess(`Aggregation executed successfully in ${data.execution_time_ms}ms`);
        } else {
            document.getElementById('agg-execution-results').classList.add('hidden');
            showSuccess('MongoDB query generated successfully!');
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
        document.getElementById('agg-charts-section').classList.add('hidden');
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

    // Auto-generate all chart types
    renderAllAggCharts(data.results);
}

async function generateReport() {
    const input = document.getElementById('report-input').value.trim();
    const format = document.getElementById('report-format').value;
    const chartType = document.getElementById('chart-type').value;

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
                report_format: format,
                chart_type: chartType
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
            <strong>File:</strong> ${data.file_path}<br>
            <strong>Total Records:</strong> ${data.summary.total_records}
        `;

        // Display chart if requested
        if (chartType !== 'none' && data.data && data.data.length > 0) {
            renderChart(data.data, chartType);
        } else {
            document.getElementById('chart-container').classList.add('hidden');
        }

        // Display data table
        if (data.data && data.data.length > 0) {
            displayReportData(data.data);
        }

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

function displayReportData(data) {
    const dataSection = document.getElementById('report-data-section');
    dataSection.classList.remove('hidden');

    const tableContainer = document.getElementById('report-data-table');

    if (data.length === 0) {
        tableContainer.innerHTML = '<p>No data available</p>';
        return;
    }

    // Create table
    const keys = Object.keys(data[0]);
    const table = `
        <table>
            <thead>
                <tr>${keys.map(key => `<th>${key}</th>`).join('')}</tr>
            </thead>
            <tbody>
                ${data.map(row => `
                    <tr>${keys.map(key => `<td>${formatValue(row[key])}</td>`).join('')}</tr>
                `).join('')}
            </tbody>
        </table>
    `;
    tableContainer.innerHTML = table;
}

function renderChart(data, chartType) {
    // Destroy previous chart if exists
    if (currentChart) {
        currentChart.destroy();
    }

    const chartContainer = document.getElementById('chart-container');
    chartContainer.classList.remove('hidden');

    const canvas = document.getElementById('report-chart');
    const ctx = canvas.getContext('2d');

    // Prepare chart data
    const chartData = prepareChartData(data);

    // Chart configuration
    const config = {
        type: chartType,
        data: {
            labels: chartData.labels,
            datasets: [{
                label: chartData.datasetLabel,
                data: chartData.values,
                backgroundColor: generateColors(chartData.labels.length, 0.7),
                borderColor: generateColors(chartData.labels.length, 1),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Report Visualization',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y !== undefined ? context.parsed.y : context.parsed;
                            return label;
                        }
                    }
                }
            },
            scales: chartType === 'bar' || chartType === 'line' ? {
                y: {
                    beginAtZero: true
                }
            } : {}
        }
    };

    currentChart = new Chart(ctx, config);
}

function prepareChartData(data) {
    // Analyze data structure to determine best chart representation
    const keys = Object.keys(data[0]);

    // Find the best label and value fields
    let labelField = keys.find(k => k.includes('_id') || k.includes('name') || k.includes('status') || k.includes('channel') || k.includes('type')) || keys[0];
    let valueField = keys.find(k => k.includes('count') || k.includes('total') || k.includes('amount') || k.includes('sum')) || keys[1];

    const labels = data.map(item => {
        const val = item[labelField];
        return val === null || val === undefined ? 'Unknown' : String(val);
    });

    const values = data.map(item => {
        const val = item[valueField];
        return typeof val === 'number' ? val : 0;
    });

    return {
        labels: labels,
        values: values,
        datasetLabel: valueField || 'Value'
    };
}

function generateColors(count, alpha = 1) {
    const colors = [
        `rgba(37, 99, 235, ${alpha})`,    // Blue
        `rgba(16, 185, 129, ${alpha})`,   // Green
        `rgba(239, 68, 68, ${alpha})`,    // Red
        `rgba(245, 158, 11, ${alpha})`,   // Orange
        `rgba(124, 58, 237, ${alpha})`,   // Purple
        `rgba(236, 72, 153, ${alpha})`,   // Pink
        `rgba(20, 184, 166, ${alpha})`,   // Teal
        `rgba(251, 191, 36, ${alpha})`,   // Yellow
        `rgba(99, 102, 241, ${alpha})`,   // Indigo
        `rgba(244, 63, 94, ${alpha})`,    // Rose
    ];

    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
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

// Dashboard Functions
async function loadDashboard() {
    console.log('=== LOADING DASHBOARD ===');
    console.log('Browser:', navigator.userAgent.includes('Chrome') ? 'Chrome' : navigator.userAgent.includes('Safari') ? 'Safari' : 'Other');

    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.js library not loaded');
        console.error('Window object keys containing "chart":', Object.keys(window).filter(k => k.toLowerCase().includes('chart')));
        showError('Chart library not loaded. Please refresh the page.');
        return;
    }
    console.log('✅ Chart.js loaded, version:', Chart.version);

    // Verify Chart.js methods are available
    try {
        console.log('Chart constructor:', typeof Chart);
        console.log('Chart.register:', typeof Chart.register);
    } catch (e) {
        console.error('Error accessing Chart object:', e);
    }

    showLoading();
    try {
        console.log('📡 Fetching dashboard data from:', `${API_BASE}/dashboard`);
        const response = await fetch(`${API_BASE}/dashboard`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        console.log('✅ Dashboard data received (V2):', data);

        // Transform V2 API data structure to V1 format expected by charts
        const transformedData = {
            status_distribution: data.events?.by_status || [],
            channel_performance: [
                { _id: 'Email', count: data.email?.total || 0 },
                { _id: 'SMS', count: data.sms?.total || 0 },
                { _id: 'Push', count: data.push?.total || 0 },
                { _id: 'In-App', count: data.inapp?.total || 0 }
            ],
            notification_types: data.events?.by_type || [],
            priority_distribution: data.events?.by_priority || [],
            daily_trend: data.trends?.daily_events || [],
            success_rate_by_channel: [
                { channel: 'Email', success_rate: data.email?.delivery_rate?.rate || 0 },
                { channel: 'SMS', success_rate: data.sms?.delivery_rate?.rate || 0 },
                { channel: 'Push', success_rate: data.push?.delivery_rate?.rate || 0 },
                { channel: 'In-App', success_rate: data.inapp?.delivery_rate?.rate || 0 }
            ],
            top_customers: data.events?.by_event_name || [],
            failed_notifications: calculateFailedNotifications(data)
        };

        function calculateFailedNotifications(data) {
            const failedByChannel = [];

            // Count failed for each channel
            ['email', 'sms', 'push', 'inapp'].forEach(channel => {
                if (data[channel] && data[channel].by_status) {
                    let failedCount = 0;
                    data[channel].by_status.forEach(status => {
                        if (status._id === 'failed' || status._id === 'bounced') {
                            failedCount += status.count;
                        }
                    });

                    if (failedCount > 0) {
                        const channelName = channel === 'inapp' ? 'In-App' :
                                          channel.charAt(0).toUpperCase() + channel.slice(1);
                        failedByChannel.push({
                            _id: channelName,
                            count: failedCount
                        });
                    }
                }
            });

            return failedByChannel;
        }

        console.log('  - status_distribution:', transformedData.status_distribution?.length, 'items');
        console.log('  - channel_performance:', transformedData.channel_performance?.length, 'items');
        console.log('  - notification_types:', transformedData.notification_types?.length, 'items');
        console.log('  - priority_distribution:', transformedData.priority_distribution?.length, 'items');
        console.log('  - daily_trend:', transformedData.daily_trend?.length, 'items');
        console.log('  - success_rate_by_channel:', transformedData.success_rate_by_channel?.length, 'items');
        console.log('  - top_customers:', transformedData.top_customers?.length, 'items');
        console.log('  - failed_notifications:', transformedData.failed_notifications?.length, 'items');

        // Render all dashboard charts
        console.log('🎨 Starting to render charts...');

        if (transformedData.status_distribution && transformedData.status_distribution.length > 0) {
            console.log('  → Rendering status pie chart...');
            renderStatusPieChart(transformedData.status_distribution);
        } else {
            console.log('  ⚠️ Skipping status pie chart - no data');
        }

        if (transformedData.channel_performance && transformedData.channel_performance.length > 0) {
            console.log('  → Rendering channel bar chart...');
            renderChannelBarChart(transformedData.channel_performance);
        } else {
            console.log('  ⚠️ Skipping channel bar chart - no data');
        }

        if (transformedData.notification_types && transformedData.notification_types.length > 0) {
            console.log('  → Rendering type doughnut chart...');
            renderTypeDoughnutChart(transformedData.notification_types);
        } else {
            console.log('  ⚠️ Skipping type doughnut chart - no data');
        }

        if (transformedData.priority_distribution && transformedData.priority_distribution.length > 0) {
            console.log('  → Rendering priority bar chart...');
            renderPriorityBarChart(transformedData.priority_distribution);
        } else {
            console.log('  ⚠️ Skipping priority bar chart - no data');
        }

        if (transformedData.daily_trend && transformedData.daily_trend.length > 0) {
            console.log('  → Rendering daily trend chart...');
            renderDailyTrendChart(transformedData.daily_trend);
        } else {
            console.log('  ⚠️ Skipping daily trend chart - no data');
        }

        if (transformedData.success_rate_by_channel && transformedData.success_rate_by_channel.length > 0) {
            console.log('  → Rendering success rate chart...');
            renderSuccessRateChart(transformedData.success_rate_by_channel);
        } else {
            console.log('  ⚠️ Skipping success rate chart - no data');
        }

        if (transformedData.top_customers && transformedData.top_customers.length > 0) {
            console.log('  → Rendering top event names chart...');
            renderTopCustomersChart(transformedData.top_customers);
        } else {
            console.log('  ⚠️ Skipping top event names chart - no data');
        }

        if (transformedData.failed_notifications && transformedData.failed_notifications.length > 0) {
            console.log('  → Rendering failed notifications chart...');
            renderFailedNotificationsChart(transformedData.failed_notifications);
        } else {
            console.log('  ⚠️ Skipping failed notifications chart - no data');
        }

        console.log('✅ All charts rendered successfully!');

        showSuccess('Dashboard loaded successfully!');
    } catch (error) {
        console.error('❌ Dashboard error:', error);
        showError('Failed to load dashboard data: ' + error.message);
    } finally {
        hideLoading();
    }
}

function renderStatusPieChart(data) {
    try {
        console.log('    🔵 renderStatusPieChart called with', data.length, 'items');

        if (dashboardCharts.statusPie) {
            console.log('    🗑️ Destroying previous status pie chart');
            dashboardCharts.statusPie.destroy();
        }

        const canvas = document.getElementById('status-pie-chart');
        if (!canvas) {
            console.error('    ❌ Canvas element status-pie-chart not found');
            return;
        }
        console.log('    ✅ Canvas element found:', canvas.tagName, canvas.width, 'x', canvas.height);

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('    ❌ Failed to get 2d context from canvas');
            return;
        }
        console.log('    ✅ Canvas 2D context obtained');

        dashboardCharts.statusPie = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(item => item._id || 'Unknown'),
                datasets: [{
                    data: data.map(item => item.count),
                    backgroundColor: generateColors(data.length, 0.8),
                    borderColor: generateColors(data.length, 1),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: false }
                }
            }
        });
        console.log('    ✅ Status pie chart created successfully');
    } catch (error) {
        console.error('    ❌ Error rendering status pie chart:', error);
    }
}

function renderChannelBarChart(data) {
    try {
        if (dashboardCharts.channelBar) dashboardCharts.channelBar.destroy();

        const canvas = document.getElementById('channel-bar-chart');
        if (!canvas) {
            console.error('Canvas element channel-bar-chart not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        dashboardCharts.channelBar = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item._id || 'Unknown'),
                datasets: [{
                    label: 'Count',
                    data: data.map(item => item.count),
                    backgroundColor: generateColors(data.length, 0.7),
                    borderColor: generateColors(data.length, 1),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering channel bar chart:', error);
    }
}

function renderTypeDoughnutChart(data) {
    try {
        if (dashboardCharts.typeDoughnut) dashboardCharts.typeDoughnut.destroy();

        const canvas = document.getElementById('type-doughnut-chart');
        if (!canvas) {
            console.error('Canvas element type-doughnut-chart not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        dashboardCharts.typeDoughnut = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(item => item._id || 'Unknown'),
                datasets: [{
                    data: data.map(item => item.count),
                    backgroundColor: generateColors(data.length, 0.8),
                    borderColor: generateColors(data.length, 1),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering type doughnut chart:', error);
    }
}

function renderPriorityBarChart(data) {
    try {
        if (dashboardCharts.priorityBar) dashboardCharts.priorityBar.destroy();

        const canvas = document.getElementById('priority-bar-chart');
        if (!canvas) {
            console.error('Canvas element priority-bar-chart not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        dashboardCharts.priorityBar = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => `Priority ${item._id}`),
                datasets: [{
                    label: 'Count',
                    data: data.map(item => item.count),
                    backgroundColor: 'rgba(124, 58, 237, 0.7)',
                    borderColor: 'rgba(124, 58, 237, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering priority bar chart:', error);
    }
}

function renderDailyTrendChart(data) {
    try {
        if (dashboardCharts.dailyTrend) dashboardCharts.dailyTrend.destroy();

        const canvas = document.getElementById('daily-trend-chart');
        if (!canvas) {
            console.error('Canvas element daily-trend-chart not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        dashboardCharts.dailyTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(item => item._id),
                datasets: [{
                    label: 'Notifications',
                    data: data.map(item => item.count),
                    backgroundColor: 'rgba(37, 99, 235, 0.2)',
                    borderColor: 'rgba(37, 99, 235, 1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering daily trend chart:', error);
    }
}

function renderSuccessRateChart(data) {
    try {
        if (dashboardCharts.successRate) dashboardCharts.successRate.destroy();

        const canvas = document.getElementById('success-rate-chart');
        if (!canvas) {
            console.error('Canvas element success-rate-chart not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        dashboardCharts.successRate = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.channel),
                datasets: [{
                    label: 'Success Rate (%)',
                    data: data.map(item => item.success_rate),
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering success rate chart:', error);
    }
}

function renderTopCustomersChart(data) {
    try {
        if (dashboardCharts.topCustomers) dashboardCharts.topCustomers.destroy();

        const canvas = document.getElementById('top-customers-chart');
        if (!canvas) {
            console.error('Canvas element top-customers-chart not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        dashboardCharts.topCustomers = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item._id || 'Unknown'),
                datasets: [{
                    label: 'Notification Count',
                    data: data.map(item => item.count),
                    backgroundColor: generateColors(data.length, 0.7),
                    borderColor: generateColors(data.length, 1),
                    borderWidth: 2
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering top customers chart:', error);
    }
}

function renderFailedNotificationsChart(data) {
    try {
        if (dashboardCharts.failedNotifications) dashboardCharts.failedNotifications.destroy();

        const canvas = document.getElementById('failed-notifications-chart');
        if (!canvas) {
            console.error('Canvas element failed-notifications-chart not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        dashboardCharts.failedNotifications = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(item => item._id || 'Unknown'),
                datasets: [{
                    data: data.map(item => item.count),
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(234, 179, 8, 0.8)',
                        'rgba(168, 85, 247, 0.8)'
                    ],
                    borderColor: [
                        'rgba(239, 68, 68, 1)',
                        'rgba(245, 158, 11, 1)',
                        'rgba(234, 179, 8, 1)',
                        'rgba(168, 85, 247, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering failed notifications chart:', error);
    }
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

            // Load data when tabs are opened
            if (tabName === 'stats') {
                loadStats();
            } else if (tabName === 'dashboard') {
                loadDashboard();
            } else if (tabName === 'event-analysis') {
                populateEventNameSelector();
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

// Auto-generate charts for query/aggregation results
let queryCharts = {
    bar: null,
    pie: null,
    line: null,
    doughnut: null
};

let aggCharts = {
    bar: null,
    pie: null,
    line: null,
    doughnut: null
};

function renderAllQueryCharts(data) {
    if (!data || data.length === 0) {
        document.getElementById('query-charts-section').classList.add('hidden');
        return;
    }

    // Check if data is suitable for visualization (has numeric values)
    if (!canVisualizeData(data)) {
        document.getElementById('query-charts-section').classList.add('hidden');
        return;
    }

    document.getElementById('query-charts-section').classList.remove('hidden');
    const chartData = prepareChartData(data);

    // Render all chart types
    renderMultiTypeChart(queryCharts, 'query-bar-chart', 'bar', chartData);
    renderMultiTypeChart(queryCharts, 'query-pie-chart', 'pie', chartData);
    renderMultiTypeChart(queryCharts, 'query-line-chart', 'line', chartData);
    renderMultiTypeChart(queryCharts, 'query-doughnut-chart', 'doughnut', chartData);
}

function renderAllAggCharts(data) {
    if (!data || data.length === 0) {
        document.getElementById('agg-charts-section').classList.add('hidden');
        return;
    }

    if (!canVisualizeData(data)) {
        document.getElementById('agg-charts-section').classList.add('hidden');
        return;
    }

    document.getElementById('agg-charts-section').classList.remove('hidden');
    const chartData = prepareChartData(data);

    // Render all chart types
    renderMultiTypeChart(aggCharts, 'agg-bar-chart', 'bar', chartData);
    renderMultiTypeChart(aggCharts, 'agg-pie-chart', 'pie', chartData);
    renderMultiTypeChart(aggCharts, 'agg-line-chart', 'line', chartData);
    renderMultiTypeChart(aggCharts, 'agg-doughnut-chart', 'doughnut', chartData);
}

function canVisualizeData(data) {
    if (!data || !Array.isArray(data) || data.length === 0) return false;

    const firstItem = data[0];
    const keys = Object.keys(firstItem);

    // Check if there's at least one numeric field
    return keys.some(key => typeof firstItem[key] === 'number');
}

function renderMultiTypeChart(chartStore, canvasId, chartType, chartData) {
    try {
        // Destroy previous chart if exists
        if (chartStore[chartType]) {
            chartStore[chartType].destroy();
        }

        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element ${canvasId} not found`);
            return;
        }

        const ctx = canvas.getContext('2d');

        const config = {
            type: chartType,
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: chartData.datasetLabel,
                    data: chartData.values,
                    backgroundColor: generateColors(chartData.labels.length, 0.7),
                    borderColor: generateColors(chartData.labels.length, 1),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: chartType === 'pie' || chartType === 'doughnut',
                        position: 'bottom'
                    }
                },
                scales: chartType === 'bar' || chartType === 'line' ? {
                    y: { beginAtZero: true }
                } : {}
            }
        };

        chartStore[chartType] = new Chart(ctx, config);
    } catch (error) {
        console.error(`Error rendering ${chartType} chart on ${canvasId}:`, error);
    }
}

// Wait for Chart.js to load
function waitForChartJS(callback) {
    // Check immediately first
    if (typeof Chart !== 'undefined') {
        console.log('✅ Chart.js already loaded, version:', Chart.version);
        // Use setTimeout to ensure DOM is fully ready
        setTimeout(callback, 0);
        return;
    }

    console.log('⏳ Chart.js not immediately available, waiting...');
    let attempts = 0;
    const maxAttempts = 100; // 10 seconds max

    const checkChart = setInterval(() => {
        attempts++;

        if (typeof Chart !== 'undefined') {
            console.log(`✅ Chart.js loaded after ${attempts} attempts, version:`, Chart.version);
            clearInterval(checkChart);
            callback();
        } else if (attempts >= maxAttempts) {
            console.error('❌ Chart.js failed to load after', attempts, 'attempts');
            console.error('Window.Chart:', typeof window.Chart);
            console.error('Available globals:', Object.keys(window).filter(k => k.toLowerCase().includes('chart')));
            clearInterval(checkChart);
            showError('Chart library failed to load. Please check your internet connection and refresh.');
        } else if (attempts % 10 === 0) {
            console.log(`Still waiting for Chart.js... (${attempts}/${maxAttempts})`);
        }
    }, 100);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== APP INITIALIZED ===');
    console.log('DOM Content Loaded');
    console.log('User Agent:', navigator.userAgent);

    // Initialize non-chart components immediately
    initTabs();
    initExamples();
    initToasts();
    checkHealth();
    loadStats();

    // Wait for Chart.js to load before initializing dashboard
    console.log('Waiting for Chart.js to load...');
    waitForChartJS(() => {
        console.log('Chart.js ready, loading dashboard...');
        loadDashboard();
    });

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

    // Dashboard Tab
    document.getElementById('refresh-dashboard-btn').addEventListener('click', loadDashboard);
    document.getElementById('quick-report-btn').addEventListener('click', async () => {
        const input = document.getElementById('quick-report-query').value.trim();
        const format = document.getElementById('quick-report-format').value;
        const chartType = document.getElementById('quick-report-chart').value;
        const statusDiv = document.getElementById('quick-report-status');

        if (!input) {
            statusDiv.style.display = 'block';
            statusDiv.style.background = '#fee2e2';
            statusDiv.style.color = '#991b1b';
            statusDiv.textContent = 'Please enter a report description';
            return;
        }

        try {
            statusDiv.style.display = 'block';
            statusDiv.style.background = '#dbeafe';
            statusDiv.style.color = '#1e40af';
            statusDiv.textContent = 'Generating report...';

            const response = await fetch(`${API_BASE}/report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_input: input,
                    report_format: format,
                    chart_type: chartType
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Report generation failed');
            }

            const data = await response.json();

            statusDiv.style.background = '#d1fae5';
            statusDiv.style.color = '#065f46';
            statusDiv.innerHTML = `
                <strong>Report generated successfully!</strong><br>
                <strong>File:</strong> ${data.file_path}<br>
                <strong>Records:</strong> ${data.summary.total_records}
            `;

            document.getElementById('quick-report-query').value = '';
        } catch (error) {
            statusDiv.style.display = 'block';
            statusDiv.style.background = '#fee2e2';
            statusDiv.style.color = '#991b1b';
            statusDiv.textContent = 'Error: ' + error.message;
        }
    });

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

    // Event Name Analysis event listeners
    const loadEventChartsBtn = document.getElementById('load-event-charts-btn');
    if (loadEventChartsBtn) {
        loadEventChartsBtn.addEventListener('click', loadEventNameCharts);
    }
});

// ==================== EVENT NAME ANALYSIS FUNCTIONS ====================

async function populateEventNameSelector() {
    try {
        const response = await fetch(`${API_BASE}/stats/event-name`);
        const data = await response.json();

        const selector = document.getElementById('event-name-selector');
        if (!selector) return;

        // Clear existing options except the first one
        selector.innerHTML = '<option value="">Select an event name...</option>';

        // Add event names from the data
        data.forEach(item => {
            const option = document.createElement('option');
            option.value = item._id;
            option.textContent = `${item._id} (${item.count} events)`;
            selector.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load event names:', error);
    }
}

async function loadEventNameCharts() {
    const selector = document.getElementById('event-name-selector');
    const selectedEvent = selector.value;

    if (!selectedEvent) {
        showError('Please select an event name first');
        return;
    }

    showLoading();
    try {
        console.log(`📊 Loading charts for event: ${selectedEvent}`);

        // Fetch event breakdown data
        const response = await fetch(`${API_BASE}/stats/event-name/${selectedEvent}`);
        const data = await response.json();

        console.log('Event breakdown data:', data);

        // Show the charts section
        document.getElementById('event-name-charts').style.display = 'block';

        // Update titles
        document.getElementById('event-channel-breakdown-title').textContent =
            `${selectedEvent} - Channel Breakdown`;
        document.getElementById('event-status-distribution-title').textContent =
            `${selectedEvent} - Status`;
        document.getElementById('event-stats-title').textContent =
            `${selectedEvent} - Statistics`;
        document.getElementById('event-success-rates-title').textContent =
            `${selectedEvent} - Success Rates`;

        // Render charts
        renderEventChannelBreakdownChart(data);
        renderEventStatusDistributionChart(data);
        renderEventStatsSummary(data);
        renderEventSuccessRatesChart(data);

        showSuccess(`Charts loaded for ${selectedEvent}`);
    } catch (error) {
        console.error('Failed to load event charts:', error);
        showError('Failed to load event charts: ' + error.message);
    } finally {
        hideLoading();
    }
}

function renderEventChannelBreakdownChart(data) {
    try {
        if (eventNameCharts.channelBreakdown) {
            eventNameCharts.channelBreakdown.destroy();
        }

        const canvas = document.getElementById('event-channel-breakdown-chart');
        if (!canvas) return;

        // Prepare data for channels
        const channels = [];
        const counts = [];

        if (data.email && data.email.total > 0) {
            channels.push('Email');
            counts.push(data.email.total);
        }
        if (data.sms && data.sms.total > 0) {
            channels.push('SMS');
            counts.push(data.sms.total);
        }
        if (data.push && data.push.total > 0) {
            channels.push('Push');
            counts.push(data.push.total);
        }
        if (data.inapp && data.inapp.total > 0) {
            channels.push('In-App');
            counts.push(data.inapp.total);
        }

        const ctx = canvas.getContext('2d');
        eventNameCharts.channelBreakdown = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: channels,
                datasets: [{
                    label: 'Notifications Sent',
                    data: counts,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(139, 92, 246, 0.7)'
                    ],
                    borderColor: [
                        'rgba(59, 130, 246, 1)',
                        'rgba(16, 185, 129, 1)',
                        'rgba(245, 158, 11, 1)',
                        'rgba(139, 92, 246, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Total Notifications per Channel'
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering event channel breakdown chart:', error);
    }
}

function renderEventStatusDistributionChart(data) {
    try {
        if (eventNameCharts.statusDistribution) {
            eventNameCharts.statusDistribution.destroy();
        }

        const canvas = document.getElementById('event-status-distribution-chart');
        if (!canvas) return;

        // Aggregate status counts from all channels
        const statusCounts = {};

        ['email', 'sms', 'push', 'inapp'].forEach(channel => {
            if (data[channel] && data[channel].by_status) {
                data[channel].by_status.forEach(item => {
                    statusCounts[item._id] = (statusCounts[item._id] || 0) + item.count;
                });
            }
        });

        const labels = Object.keys(statusCounts);
        const counts = Object.values(statusCounts);

        const ctx = canvas.getContext('2d');
        eventNameCharts.statusDistribution = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: generateColors(labels.length, 0.7),
                    borderColor: generateColors(labels.length, 1),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering event status distribution chart:', error);
    }
}

function renderEventStatsSummary(data) {
    try {
        const summaryDiv = document.getElementById('event-stats-summary');
        if (!summaryDiv) return;

        const totalEvents = data.total_events || 0;
        const totalNotifications = (data.email?.total || 0) + (data.sms?.total || 0) +
                                    (data.push?.total || 0) + (data.inapp?.total || 0);

        summaryDiv.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 15px;">
                <div class="stat-item" style="padding: 10px; background: rgba(59, 130, 246, 0.1); border-radius: 6px;">
                    <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Total Events</div>
                    <div style="font-size: 24px; font-weight: bold; color: #3b82f6;">${totalEvents}</div>
                </div>
                <div class="stat-item" style="padding: 10px; background: rgba(16, 185, 129, 0.1); border-radius: 6px;">
                    <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Total Notifications</div>
                    <div style="font-size: 24px; font-weight: bold; color: #10b981;">${totalNotifications}</div>
                </div>
                <div class="stat-item" style="padding: 10px; background: rgba(245, 158, 11, 0.1); border-radius: 6px;">
                    <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Avg per Event</div>
                    <div style="font-size: 24px; font-weight: bold; color: #f59e0b;">${totalEvents > 0 ? (totalNotifications / totalEvents).toFixed(1) : 0}</div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error rendering event stats summary:', error);
    }
}

function renderEventSuccessRatesChart(data) {
    try {
        if (eventNameCharts.successRates) {
            eventNameCharts.successRates.destroy();
        }

        const canvas = document.getElementById('event-success-rates-chart');
        if (!canvas) return;

        // Prepare success rate data
        const channels = [];
        const rates = [];

        if (data.email && data.email.delivery_rate) {
            channels.push('Email');
            rates.push(data.email.delivery_rate.rate || 0);
        }
        if (data.sms && data.sms.delivery_rate) {
            channels.push('SMS');
            rates.push(data.sms.delivery_rate.rate || 0);
        }
        if (data.push && data.push.delivery_rate) {
            channels.push('Push');
            rates.push(data.push.delivery_rate.rate || 0);
        }
        if (data.inapp && data.inapp.delivery_rate) {
            channels.push('In-App');
            rates.push(data.inapp.delivery_rate.rate || 0);
        }

        const ctx = canvas.getContext('2d');
        eventNameCharts.successRates = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: channels,
                datasets: [{
                    label: 'Delivery Rate (%)',
                    data: rates,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering event success rates chart:', error);
    }
}
