/**
 * German Federal Funding Catalog Dashboard
 * Main JavaScript for data loading and chart rendering
 */

// Chart.js default configuration
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748B';
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.9)';
Chart.defaults.plugins.tooltip.titleFont = { weight: '600' };
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;

// Color palettes
const CHART_COLORS = {
    primary: ['#6366F1', '#8B5CF6', '#A855F7', '#D946EF', '#EC4899'],
    secondary: ['#06B6D4', '#14B8A6', '#10B981', '#22C55E', '#84CC16'],
    accent: ['#F59E0B', '#F97316', '#EF4444', '#EC4899', '#8B5CF6'],
    gradient: [
        '#6366F1', '#7C3AED', '#A855F7', '#D946EF', '#EC4899',
        '#F43F5E', '#F97316', '#FBBF24', '#84CC16', '#22C55E',
        '#14B8A6', '#06B6D4', '#3B82F6', '#6366F1'
    ],
    states: {
        'Bayern': '#0088FE',
        'Nordrhein-Westfalen': '#00C49F',
        'Baden-Württemberg': '#FFBB28',
        'Niedersachsen': '#FF8042',
        'Hessen': '#8884D8',
        'Berlin': '#82CA9D',
        'Sachsen': '#A4DE6C',
        'Rheinland-Pfalz': '#D0ED57',
        'Hamburg': '#FFC658',
        'Schleswig-Holstein': '#8DD1E1',
        'Thüringen': '#A28BFE',
        'Brandenburg': '#FF6B6B',
        'Sachsen-Anhalt': '#4ECDC4',
        'Mecklenburg-Vorpommern': '#45B7D1',
        'Bremen': '#96CEB4',
        'Saarland': '#DDA0DD'
    }
};

// Utility functions
function formatCurrency(value, compact = false) {
    if (compact) {
        if (value >= 1e12) return `€${(value / 1e12).toFixed(1)}T`;
        if (value >= 1e9) return `€${(value / 1e9).toFixed(1)}B`;
        if (value >= 1e6) return `€${(value / 1e6).toFixed(1)}M`;
        if (value >= 1e3) return `€${(value / 1e3).toFixed(0)}K`;
        return `€${value.toFixed(0)}`;
    }
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatNumber(value, compact = false) {
    if (compact && value >= 1000) {
        return new Intl.NumberFormat('de-DE', {
            notation: 'compact',
            compactDisplay: 'short'
        }).format(value);
    }
    return new Intl.NumberFormat('de-DE').format(value);
}

// Global data store
let globalData = {};
let charts = {};

// Data loading
async function loadData() {
    const files = [
        'summary_stats.json',
        'ministry_funding.json',
        'geographic_distribution.json',
        'temporal_trends.json',
        'top_recipients.json',
        'topic_analysis.json',
        'duration_analysis.json',
        'funding_types.json',
        'joint_projects.json',
        'projekttraeger.json',
        'keyword_trends.json',
        'entity_trends.json',
        'funding_forecast.json'
    ];

    try {
        const promises = files.map(file =>
            fetch(`data/${file}`).then(res => {
                if (!res.ok) throw new Error(`Failed to load ${file}`);
                return res.json();
            })
        );

        const results = await Promise.all(promises);

        globalData = {
            summary: results[0],
            ministry: results[1],
            geographic: results[2],
            temporal: results[3],
            recipients: results[4],
            topics: results[5],
            duration: results[6],
            fundingTypes: results[7],
            jointProjects: results[8],
            projekttraeger: results[9],
            keywordTrends: results[10],
            entityTrends: results[11],
            forecast: results[12]
        };

        initializeDashboard();
    } catch (error) {
        console.error('Error loading data:', error);
        document.querySelector('.main-content').innerHTML = `
            <div class="chart-card chart-full" style="text-align: center; padding: 3rem;">
                <h2 style="color: #EF4444;">Error Loading Data</h2>
                <p style="margin-top: 1rem;">Please make sure the data files are in the <code>web/data/</code> folder.</p>
                <p style="margin-top: 0.5rem; color: #64748B;">Run <code>python analyze_funding.py</code> first, then copy the output files.</p>
            </div>
        `;
    }
}

// Initialize dashboard
function initializeDashboard() {
    updateOverviewCards();
    updateLastUpdate();
    createTemporalChart();
    createMonthlyChart();
    createDecadeMinistryChart();
    createMinistryChart();
    createInternationalChart();
    createGeoChart();
    createCityChart();
    createRecipientChart();
    createFundingTypeChart();
    createDurationChart();
    createTopicChart();
    createJointChart();
    createProjekttraegerChart();
    createFoerderprofilChart();
    createKeywordsCloud();
    populateRecipientsTable();
    initializeEventListeners();
}

// Update overview cards
function updateOverviewCards() {
    const summary = globalData.summary;

    document.getElementById('totalFunding').textContent = formatCurrency(summary.total_funding, true);
    document.getElementById('totalProjects').textContent = formatNumber(summary.total_projects);
    // Show as minimum since "Keine Anzeige" entries represent multiple hidden recipients
    document.getElementById('uniqueRecipients').textContent = formatNumber(summary.unique_recipients - 1) + '+';
    document.getElementById('avgFunding').textContent = formatCurrency(summary.highlights.avg_project_funding, true);
}

// Update last update timestamp
function updateLastUpdate() {
    const date = new Date(globalData.summary.generated_at);
    // Format: "10. December 2025 at 11:44"
    const day = date.getDate();
    const month = date.toLocaleDateString('en-US', { month: 'long' });
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const formatted = `${day}. ${month} ${year} at ${hours}:${minutes}`;
    document.getElementById('lastUpdate').textContent = `Updated: ${formatted}`;
    document.getElementById('footerUpdate').textContent = formatted;
}


// Ministry funding chart
function createMinistryChart() {
    const ctx = document.getElementById('ministryChart').getContext('2d');
    const data = globalData.ministry.ministries;

    charts.ministry = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.code),
            datasets: [{
                label: 'Total Funding',
                data: data.map(d => d.total_funding),
                backgroundColor: CHART_COLORS.gradient.slice(0, data.length),
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => data[items[0].dataIndex].name,
                        label: (item) => [
                            `Total: ${formatCurrency(item.raw)}`,
                            `Projects: ${formatNumber(data[item.dataIndex].project_count)}`,
                            `Avg: ${formatCurrency(data[item.dataIndex].avg_funding)}`
                        ]
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

// International funding chart
function createInternationalChart() {
    const ctx = document.getElementById('internationalChart').getContext('2d');
    const intlData = globalData.geographic.international;

    if (!intlData || !intlData.countries || intlData.countries.length === 0) {
        // No international data available
        document.getElementById('internationalChart').parentElement.innerHTML =
            '<p style="text-align: center; color: #64748B; padding: 2rem;">No international funding data available</p>';
        return;
    }

    const data = intlData.countries.slice(0, 15);

    charts.international = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                label: 'Total Funding',
                data: data.map(d => d.total_funding),
                backgroundColor: CHART_COLORS.gradient.slice(0, data.length),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => [
                            `Funding: ${formatCurrency(item.raw)}`,
                            `Projects: ${formatNumber(data[item.dataIndex].project_count)}`
                        ]
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                },
                y: {
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// Geographic distribution chart - clickable bars for drill-down, supports per capita toggle
function createGeoChart(mode = 'total') {
    const ctx = document.getElementById('geoChart').getContext('2d');
    const rawData = globalData.geographic.states.slice(0, 16);

    // Sort by appropriate metric
    let data;
    if (mode === 'percapita') {
        data = [...rawData].filter(d => d.per_capita_funding).sort((a, b) => b.per_capita_funding - a.per_capita_funding);
    } else {
        data = rawData;
    }

    // Destroy existing chart if exists
    if (charts.geo) {
        charts.geo.destroy();
    }

    const chartData = mode === 'percapita'
        ? data.map(d => d.per_capita_funding)
        : data.map(d => d.total_funding);

    const chartLabel = mode === 'percapita' ? 'Per Capita Funding (€)' : 'Total Funding';

    charts.geo = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                label: chartLabel,
                data: chartData,
                backgroundColor: data.map(d => CHART_COLORS.states[d.name] || '#6366F1'),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => {
                            const stateData = data[item.dataIndex];
                            if (mode === 'percapita') {
                                return [
                                    `Per Capita: ${formatCurrency(stateData.per_capita_funding)}`,
                                    `Total: ${formatCurrency(stateData.total_funding)}`,
                                    `Population: ${formatNumber(stateData.population)}`
                                ];
                            }
                            return [
                                `Funding: ${formatCurrency(item.raw)}`,
                                `Projects: ${formatNumber(stateData.project_count)}`,
                                `Click to see trends`
                            ];
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                // Only enable click in total mode (trends are for total funding)
                if (mode === 'total' && elements.length > 0) {
                    const stateName = data[elements[0].index].name;
                    if (globalData.entityTrends?.states?.[stateName]) {
                        showStateTrends(stateName);
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        font: { size: 10 }
                    },
                    grid: { display: false }
                },
                y: {
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                }
            }
        }
    });
}


// Temporal trends chart
function createTemporalChart(range = 'all') {
    const ctx = document.getElementById('temporalChart').getContext('2d');

    // Destroy existing chart if exists
    if (charts.temporal) {
        charts.temporal.destroy();
    }

    // Handle forecast mode separately
    if (range === 'forecast') {
        createForecastChart(ctx);
        return;
    }

    let data = globalData.temporal.yearly_totals;

    // Filter by range
    const currentYear = 2025; // December 2025
    if (range === 'recent') {
        data = data.filter(d => d.year >= currentYear - 20);
    } else if (range === 'decade') {
        data = data.filter(d => d.year >= currentYear - 10);
    }

    charts.temporal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.year),
            datasets: [
                {
                    label: 'Total Funding (€)',
                    data: data.map(d => d.total_funding),
                    borderColor: '#6366F1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y',
                    pointRadius: 2,
                    pointHoverRadius: 6
                },
                {
                    label: 'Project Count',
                    data: data.map(d => d.project_count),
                    borderColor: '#F59E0B',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.4,
                    yAxisID: 'y1',
                    pointRadius: 2,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (item) => {
                            if (item.datasetIndex === 0) {
                                return `Funding: ${formatCurrency(item.raw)}`;
                            }
                            return `Projects: ${formatNumber(item.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#E2E8F0' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Funding (€)' },
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Projects' },
                    ticks: {
                        callback: (value) => formatNumber(value, true)
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

// Forecast chart with confidence intervals
function createForecastChart(ctx) {
    const forecast = globalData.forecast;
    const historicalData = globalData.temporal.yearly_totals;

    // Get last 10 years of historical data + forecast
    const currentYear = forecast.current_year;
    const recentHistory = historicalData.filter(d => d.year >= currentYear - 10 && d.year <= currentYear);
    const forecastData = forecast.forecast;

    // Combine labels: historical years + forecast years
    const allYears = [
        ...recentHistory.map(d => d.year),
        ...forecastData.map(d => d.year)
    ];

    // Historical funding (with nulls for forecast years)
    const historicalFunding = [
        ...recentHistory.map(d => d.total_funding),
        ...forecastData.map(() => null)
    ];

    // Predicted funding (with nulls for historical years, starting from last historical point)
    const lastHistoricalValue = recentHistory[recentHistory.length - 1]?.total_funding || 0;
    const predictedFunding = [
        ...recentHistory.slice(0, -1).map(() => null),
        lastHistoricalValue,  // Connect to last historical point
        ...forecastData.map(d => d.predicted_funding)
    ];

    // Confidence interval bounds
    const upperBound = [
        ...recentHistory.slice(0, -1).map(() => null),
        lastHistoricalValue,
        ...forecastData.map(d => d.upper_bound)
    ];

    const lowerBound = [
        ...recentHistory.slice(0, -1).map(() => null),
        lastHistoricalValue,
        ...forecastData.map(d => d.lower_bound)
    ];

    // Already approved funding (for comparison)
    const approvedFunding = [
        ...recentHistory.map(() => null),
        ...forecastData.map(d => d.approved_funding || null)
    ];

    charts.temporal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allYears,
            datasets: [
                {
                    label: 'Historical Funding',
                    data: historicalFunding,
                    borderColor: '#6366F1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    order: 2
                },
                {
                    label: 'Forecast (Prophet ML)',
                    data: predictedFunding,
                    borderColor: '#10B981',
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    borderDash: [8, 4],
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 8,
                    pointStyle: 'triangle',
                    order: 1
                },
                {
                    label: '80% Confidence Upper',
                    data: upperBound,
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: '+1',
                    tension: 0.3,
                    pointRadius: 0,
                    borderWidth: 1,
                    order: 3
                },
                {
                    label: '80% Confidence Lower',
                    data: lowerBound,
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    pointRadius: 0,
                    borderWidth: 1,
                    order: 4
                },
                {
                    label: 'Already Approved',
                    data: approvedFunding,
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                    fill: true,
                    tension: 0,
                    pointRadius: 5,
                    pointStyle: 'rect',
                    order: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        filter: (item) => !item.text.includes('Confidence')
                    }
                },
                tooltip: {
                    callbacks: {
                        title: (items) => {
                            const year = items[0].label;
                            const isHistorical = parseInt(year) <= currentYear;
                            return `${year} ${isHistorical ? '' : '(Forecast)'}`;
                        },
                        label: (item) => {
                            if (item.raw === null) return null;
                            const datasetLabel = item.dataset.label;
                            if (datasetLabel.includes('Confidence')) return null;

                            if (datasetLabel === 'Already Approved') {
                                const forecastItem = forecastData.find(f => f.year === parseInt(item.label));
                                if (forecastItem && forecastItem.approved_projects) {
                                    return `Approved: ${formatCurrency(item.raw)} (${forecastItem.approved_projects} projects)`;
                                }
                                return `Approved: ${formatCurrency(item.raw)}`;
                            }
                            return `${datasetLabel}: ${formatCurrency(item.raw)}`;
                        },
                        afterBody: (items) => {
                            const year = parseInt(items[0].label);
                            if (year > currentYear) {
                                const forecastItem = forecastData.find(f => f.year === year);
                                if (forecastItem) {
                                    return [
                                        '',
                                        `Confidence: ${formatCurrency(forecastItem.lower_bound, true)} - ${formatCurrency(forecastItem.upper_bound, true)}`
                                    ];
                                }
                            }
                            return [];
                        }
                    }
                },
                annotation: {
                    annotations: {
                        currentYearLine: {
                            type: 'line',
                            xMin: currentYear,
                            xMax: currentYear,
                            borderColor: '#94A3B8',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {
                                display: true,
                                content: 'Now',
                                position: 'start'
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#E2E8F0' },
                    ticks: {
                        callback: function (value, index) {
                            const year = this.getLabelForValue(value);
                            return year;
                        }
                    }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Funding (€)' },
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                }
            }
        }
    });
}

// Monthly distribution chart (seasonal patterns)
function createMonthlyChart() {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    const data = globalData.temporal.monthly_distribution || [];

    if (data.length === 0) {
        console.log('No monthly data available');
        return;
    }

    charts.monthly = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.month_name),
            datasets: [
                {
                    label: 'Projects',
                    data: data.map(d => d.project_count),
                    backgroundColor: '#6366F1',
                    borderRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: 'Funding (€)',
                    data: data.map(d => d.total_funding),
                    backgroundColor: 'rgba(34, 197, 94, 0.7)',
                    borderRadius: 4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: (item) => {
                            if (item.datasetIndex === 0) {
                                return `Projects: ${formatNumber(item.raw)}`;
                            }
                            return `Funding: ${formatCurrency(item.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Projects' },
                    ticks: { callback: (value) => formatNumber(value, true) },
                    grid: { color: '#E2E8F0' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Funding' },
                    ticks: { callback: (value) => formatCurrency(value, true) },
                    grid: { display: false }
                }
            }
        }
    });
}

// Ministry share by decade chart (stacked bar showing evolution)
function createDecadeMinistryChart() {
    const ctx = document.getElementById('decadeMinistryChart').getContext('2d');
    const decadeData = globalData.temporal.decade_ministry_share || {};

    // Get all decades from data (dynamic, sorted)
    const decades = Object.keys(decadeData).sort();

    // Get all unique ministries from the data
    const allMinistries = new Set();
    Object.values(decadeData).forEach(entries => {
        entries.forEach(entry => allMinistries.add(entry.ministry));
    });
    const ministries = Array.from(allMinistries);

    const ministryColors = {
        'BMFTR': '#6366F1',
        'BMV': '#F59E0B',
        'BMWE': '#10B981',
        'BMLEH': '#EC4899',
        'BMUKN': '#8B5CF6',
        'BMJV_BLE': '#06B6D4'
    };

    // Build datasets for each ministry
    const datasets = ministries.map((ministry, i) => ({
        label: ministry,
        data: decades.map(decade => {
            const decadeInfo = decadeData[decade] || [];
            const ministryInfo = decadeInfo.find(m => m.ministry === ministry);
            return ministryInfo ? ministryInfo.share_pct : 0;
        }),
        backgroundColor: ministryColors[ministry] || CHART_COLORS.gradient[i % CHART_COLORS.gradient.length],
        borderRadius: 4
    }));

    charts.decadeMinistry = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: decades.map(d => d + 's'),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: (item) => `${item.dataset.label}: ${item.raw.toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false }
                },
                y: {
                    stacked: true,
                    max: 100,
                    title: { display: true, text: 'Share (%)' },
                    ticks: { callback: (value) => value + '%' },
                    grid: { color: '#E2E8F0' }
                }
            }
        }
    });
}


function createRecipientChart() {
    const ctx = document.getElementById('recipientChart').getContext('2d');
    const data = globalData.recipients.top_by_funding.slice(0, 10);

    charts.recipient = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => truncateLabel(d.name, 30)),
            datasets: [{
                label: 'Total Funding',
                data: data.map(d => d.total_funding),
                backgroundColor: CHART_COLORS.secondary,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => data[items[0].dataIndex].name,
                        label: (item) => [
                            `Funding: ${formatCurrency(item.raw)}`,
                            `Projects: ${formatNumber(data[item.dataIndex].project_count)}`
                        ]
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                },
                y: {
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// Funding types chart
function createFundingTypeChart() {
    const ctx = document.getElementById('fundingTypeChart').getContext('2d');
    const data = globalData.fundingTypes.funding_types.slice(0, 5);

    charts.fundingType = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => truncateLabel(d.name, 25)),
            datasets: [{
                data: data.map(d => d.total_funding),
                backgroundColor: CHART_COLORS.gradient.slice(0, data.length),
                borderWidth: 0,
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 10 } }
                },
                tooltip: {
                    callbacks: {
                        label: (item) => `${formatCurrency(item.raw)} (${((item.raw / globalData.summary.total_funding) * 100).toFixed(1)}%)`
                    }
                }
            }
        }
    });
}

// Duration distribution chart
function createDurationChart() {
    const ctx = document.getElementById('durationChart').getContext('2d');
    const data = globalData.duration.distribution;

    charts.duration = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.range),
            datasets: [{
                label: 'Projects',
                data: data.map(d => d.count),
                backgroundColor: CHART_COLORS.accent,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => `${formatNumber(item.raw)} projects`
                    }
                }
            },
            scales: {
                x: {
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                },
                y: {
                    ticks: {
                        callback: (value) => formatNumber(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                }
            }
        }
    });
}

// Research topics chart
function createTopicChart() {
    const ctx = document.getElementById('topicChart').getContext('2d');
    const data = globalData.topics.classifications.slice(0, 10);

    charts.topic = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => truncateLabel(d.description || d.code, 40)),
            datasets: [{
                label: 'Funding',
                data: data.map(d => d.total_funding),
                backgroundColor: CHART_COLORS.primary,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => data[items[0].dataIndex].description || data[items[0].dataIndex].code,
                        label: (item) => [
                            `Code: ${data[item.dataIndex].code}`,
                            `Funding: ${formatCurrency(item.raw)}`,
                            `Projects: ${formatNumber(data[item.dataIndex].project_count)}`
                        ]
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                },
                y: {
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// Joint projects chart
function createJointChart() {
    const ctx = document.getElementById('jointChart').getContext('2d');
    const data = globalData.jointProjects.summary;

    charts.joint = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Verbundprojekt (Joint)', 'Individual Projects'],
            datasets: [{
                data: [data.joint_funding, data.individual_funding],
                backgroundColor: ['#6366F1', '#22C55E'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: (item) => {
                            const count = item.dataIndex === 0 ? data.joint_project_count : data.individual_project_count;
                            return [
                                formatCurrency(item.raw),
                                `${formatNumber(count)} projects`
                            ];
                        }
                    }
                }
            }
        }
    });
}

// Projektträger (Project Sponsors) chart
function createProjekttraegerChart() {
    const ctx = document.getElementById('projekttraegerChart').getContext('2d');
    const data = globalData.projekttraeger.projekttraeger.slice(0, 12);

    charts.projekttraeger = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.code),
            datasets: [{
                label: 'Total Funding',
                data: data.map(d => d.total_funding),
                backgroundColor: CHART_COLORS.gradient.slice(0, data.length),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => data[items[0].dataIndex].name,
                        label: (item) => [
                            `Funding: ${formatCurrency(item.raw)}`,
                            `Projects: ${formatNumber(data[item.dataIndex].project_count)}`,
                            `Ministries: ${data[item.dataIndex].ministries.join(', ')}`
                        ]
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                },
                y: {
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// Förderprofil (Funding Profile) chart
function createFoerderprofilChart() {
    const ctx = document.getElementById('foerderprofilChart').getContext('2d');
    const data = globalData.fundingTypes.funding_profiles.slice(0, 6);

    charts.foerderprofil = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => truncateLabel(d.name, 30)),
            datasets: [{
                data: data.map(d => d.total_funding),
                backgroundColor: ['#6366F1', '#A855F7', '#EC4899', '#F59E0B', '#10B981', '#06B6D4'],
                borderWidth: 0,
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { size: 9 },
                        padding: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (item) => [
                            formatCurrency(item.raw),
                            `${formatNumber(data[item.dataIndex].project_count)} projects`
                        ]
                    }
                }
            }
        }
    });
}

// Top cities chart - clickable bars for drill-down
function createCityChart() {
    const ctx = document.getElementById('cityChart').getContext('2d');
    const data = globalData.geographic.top_cities.slice(0, 15);

    charts.city = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.city),
            datasets: [{
                label: 'Funding',
                data: data.map(d => d.total_funding),
                backgroundColor: data.map(d => CHART_COLORS.states[d.state] || '#6366F1'),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => `${data[items[0].dataIndex].city}, ${data[items[0].dataIndex].state}`,
                        label: (item) => [
                            `Funding: ${formatCurrency(item.raw)}`,
                            `Projects: ${formatNumber(data[item.dataIndex].project_count)}`,
                            `Click to see trends`
                        ]
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const cityName = data[elements[0].index].city;
                    if (globalData.entityTrends?.cities?.[cityName]) {
                        showCityTrends(cityName);
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        font: { size: 10 }
                    },
                    grid: { display: false }
                },
                y: {
                    ticks: {
                        callback: (value) => formatCurrency(value, true)
                    },
                    grid: { color: '#E2E8F0' }
                }
            }
        }
    });
}

// Keywords cloud - clickable for drill-down
function createKeywordsCloud() {
    const container = document.getElementById('keywordsCloud');
    const keywords = globalData.topics.keywords.slice(0, 50);
    const maxCount = Math.max(...keywords.map(k => k.count));

    container.innerHTML = keywords.map(keyword => {
        const ratio = keyword.count / maxCount;
        let sizeClass = 'keyword-small';
        if (ratio > 0.7) sizeClass = 'keyword-xlarge';
        else if (ratio > 0.4) sizeClass = 'keyword-large';
        else if (ratio > 0.2) sizeClass = 'keyword-medium';

        // Check if we have trend data for this keyword
        const hasTrends = globalData.keywordTrends?.keywords?.[keyword.word];
        const clickAttr = hasTrends ? `onclick="showKeywordTrends('${keyword.word}')"` : '';
        const cursorStyle = hasTrends ? '' : 'style="cursor: default;"';
        const titleText = hasTrends
            ? `${keyword.count} word matches - Click to see related projects`
            : `${keyword.count} word matches`;

        return `<span class="keyword-tag ${sizeClass}" ${clickAttr} ${cursorStyle} title="${titleText}">${keyword.word}</span>`;
    }).join('');
}

// =====================================================
// DRILL-DOWN MODAL - Generic for all entity types
// =====================================================
let drilldownChart = null;

function showDrilldown(type, name) {
    let data, title, subtitle;

    switch (type) {
        case 'keyword':
            data = globalData.keywordTrends?.keywords?.[name];
            title = `"${name}"`;
            subtitle = 'Projects containing this keyword (includes compound words)';
            break;
        case 'state':
            data = globalData.entityTrends?.states?.[name];
            title = name;
            subtitle = 'State funding trends over time';
            break;
        case 'city':
            data = globalData.entityTrends?.cities?.[name];
            title = name + (data?.state ? ` (${data.state})` : '');
            subtitle = 'City funding trends over time';
            break;
        case 'recipient':
            data = globalData.entityTrends?.recipients?.[name];
            title = name.length > 50 ? name.substring(0, 47) + '...' : name;
            subtitle = 'Recipient funding trends over time';
            break;
        default:
            console.error('Unknown drilldown type:', type);
            return;
    }

    if (!data) {
        console.error(`No trend data for ${type}:`, name);
        return;
    }

    // Update modal content
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalSubtitle').textContent = subtitle;
    document.getElementById('modalTotalProjects').textContent = formatNumber(data.total_projects);
    document.getElementById('modalTotalFunding').textContent = formatCurrency(data.total_funding, true);

    // Show modal
    document.getElementById('drilldownModal').style.display = 'flex';

    // Destroy previous chart if exists
    if (drilldownChart) {
        drilldownChart.destroy();
    }

    // Create chart
    const ctx = document.getElementById('drilldownChart').getContext('2d');
    drilldownChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.yearly.map(d => d.year),
            datasets: [
                {
                    label: 'Funding (€)',
                    data: data.yearly.map(d => d.funding),
                    backgroundColor: 'rgba(99, 102, 241, 0.7)',
                    borderColor: '#6366F1',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Projects',
                    data: data.yearly.map(d => d.projects),
                    type: 'line',
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            if (ctx.dataset.label === 'Funding (€)') {
                                return `Funding: ${formatCurrency(ctx.raw)}`;
                            }
                            return `Projects: ${formatNumber(ctx.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Funding (€)' },
                    ticks: { callback: (value) => formatCurrency(value, true) }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Projects' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// Wrapper functions for each type
function showKeywordTrends(keyword) { showDrilldown('keyword', keyword); }
function showStateTrends(state) { showDrilldown('state', state); }
function showCityTrends(city) { showDrilldown('city', city); }
function showRecipientTrends(recipient) { showDrilldown('recipient', recipient); }

function closeModal() {
    document.getElementById('drilldownModal').style.display = 'none';
    if (drilldownChart) {
        drilldownChart.destroy();
        drilldownChart = null;
    }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.id === 'drilldownModal') {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});



// Recipients table - clickable rows for drill-down
function populateRecipientsTable(sortBy = 'funding') {
    const tbody = document.querySelector('#recipientTable tbody');

    // Note: "Keine Anzeige" entries represent multiple protected entities aggregated together
    // All data (funding, location, ministry) is available - only the recipient name is hidden
    let data = sortBy === 'funding'
        ? globalData.recipients.top_by_funding.slice(0, 20)
        : globalData.recipients.top_by_count.slice(0, 20);

    tbody.innerHTML = data.map((recipient, index) => {
        // Check if we have trend data for this recipient
        const hasTrends = globalData.entityTrends?.recipients?.[recipient.name];
        const clickAttr = hasTrends ? `onclick="showRecipientTrends('${recipient.name.replace(/'/g, "\\'")}')"` : '';
        const rowClass = hasTrends ? 'class="clickable-row"' : '';
        const titleAttr = hasTrends ? 'Click to see funding trends' : recipient.name;

        return `
        <tr ${rowClass} ${clickAttr} title="${titleAttr}">
            <td>${index + 1}</td>
            <td>${truncateLabel(recipient.name, 50)}</td>
            <td>${formatCurrency(recipient.total_funding)}</td>
            <td>${formatNumber(recipient.project_count)}</td>
            <td>${formatCurrency(recipient.avg_funding || recipient.total_funding / recipient.project_count)}</td>
        </tr>`;
    }).join('');
}





// Event listeners
function initializeEventListeners() {
    // Temporal chart range buttons
    document.querySelectorAll('[data-range]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.chart-controls').querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            createTemporalChart(e.target.dataset.range);
        });
    });

    // Geo chart mode toggle (total/per capita)
    document.querySelectorAll('[data-geo-mode]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.chart-controls').querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            createGeoChart(e.target.dataset.geoMode);
        });
    });

    // Table sort buttons
    document.querySelectorAll('.table-controls .table-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.table-controls .table-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            populateRecipientsTable(e.target.dataset.sort);
        });
    });
}

// Helper function
function truncateLabel(label, maxLength) {
    if (!label) return '';
    return label.length > maxLength ? label.substring(0, maxLength) + '...' : label;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', loadData);
