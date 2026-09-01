document.addEventListener('DOMContentLoaded', function() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded.');
        return;
    }

    // Set Chart.js global defaults
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.color = '#6C757D';

    // Helper: Use server data if valid and non-empty, otherwise use fallback data
    function getValidData(serverData, fallback) {
        if (serverData && (
            (serverData.labels && serverData.labels.length > 0) ||
            (serverData.approved && serverData.approved.length > 0) ||
            (serverData.data && serverData.data.length > 0)
        )) {
            return serverData;
        }
        return fallback;
    }

    // ========================================================
    // 1. Risk Level Distribution (Doughnut Chart)
    // ========================================================
    const ctxRisk = document.getElementById('riskChart');
    if (ctxRisk) {
        const riskData = getValidData(window.riskData, {
            labels: ['Low Risk', 'Medium Risk', 'High Risk'],
            data: [32, 14, 8]
        });

        new Chart(ctxRisk, {
            type: 'doughnut',
            data: {
                labels: riskData.labels,
                datasets: [{
                    data: riskData.data,
                    backgroundColor: ['#28A745', '#FF9933', '#DC3545'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
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
    }

    // ========================================================
    // 2. Progress Distribution (Bar Chart)
    // ========================================================
    const ctxDist = document.getElementById('distributionChart');
    if (ctxDist) {
        const distData = getValidData(window.distributionData, {
            labels: ['0-25%', '25-50%', '50-75%', '75-100%'],
            data: [6, 12, 24, 12]
        });

        new Chart(ctxDist, {
            type: 'bar',
            data: {
                labels: distData.labels,
                datasets: [{
                    label: 'Number of Projects',
                    data: distData.data,
                    backgroundColor: ['#DC3545', '#FF9933', '#2196F3', '#28A745'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#F1F5F9' },
                        ticks: { precision: 0 }
                    },
                    x: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // ========================================================
    // 3. Ministry-wise Cost Comparison (Grouped Bar Chart)
    // ========================================================
    const ctxMinistryCost = document.getElementById('ministryCostChart');
    if (ctxMinistryCost) {
        const ministryCostData = getValidData(window.ministryCostData, {
            labels: ['Road Transport', 'Railways', 'Power', 'Ports & Shipping', 'Urban Affairs'],
            approved: [28000, 22000, 16000, 12000, 8000],
            revised: [29500, 23800, 16500, 12000, 8500],
            expenditure: [14200, 11800, 9400, 6200, 4100]
        });

        new Chart(ctxMinistryCost, {
            type: 'bar',
            data: {
                labels: ministryCostData.labels,
                datasets: [
                    {
                        label: 'Approved Cost (₹ Cr)',
                        data: ministryCostData.approved,
                        backgroundColor: '#003366',
                        borderRadius: 4
                    },
                    {
                        label: 'Revised Cost (₹ Cr)',
                        data: ministryCostData.revised,
                        backgroundColor: '#FF9933',
                        borderRadius: 4
                    },
                    {
                        label: 'Expenditure (₹ Cr)',
                        data: ministryCostData.expenditure,
                        backgroundColor: '#28A745',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#F1F5F9' },
                        ticks: {
                            callback: function(v) { return '₹' + v; }
                        }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // ========================================================
    // 4. State-wise Cost Analysis (Horizontal Bar Chart)
    // ========================================================
    const ctxStateCost = document.getElementById('stateCostChart');
    if (ctxStateCost) {
        const stateCostData = getValidData(window.stateCostData, {
            labels: ['Kolkata', 'South 24 Parganas', 'North 24 Parganas', 'Darjeeling', 'Howrah', 'Murshidabad'],
            data: [24500, 18200, 14100, 9800, 7400, 4800]
        });

        new Chart(ctxStateCost, {
            type: 'bar',
            data: {
                labels: stateCostData.labels,
                datasets: [{
                    label: 'Approved Allocation (₹ Cr)',
                    data: stateCostData.data,
                    backgroundColor: '#0ea5e9',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: '#F1F5F9' },
                        ticks: {
                            callback: function(v) { return '₹' + v; }
                        }
                    },
                    y: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // ========================================================
    // 5. Project Status Overview (Pie Chart)
    // ========================================================
    const ctxStatus = document.getElementById('analyticsStatusChart');
    if (ctxStatus) {
        const statusData = getValidData(window.statusData, {
            labels: ['Ongoing', 'Completed', 'Delayed', 'On Hold', 'New Added', 'At Risk'],
            data: [25, 4, 15, 5, 2, 3]
        });

        new Chart(ctxStatus, {
            type: 'pie',
            data: {
                labels: statusData.labels,
                datasets: [{
                    data: statusData.data,
                    backgroundColor: ['#2196F3', '#28A745', '#DC3545', '#6C757D', '#9333EA', '#F59E0B'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' }
                }
            }
        });
    }

    // ========================================================
    // 6. Cost vs Progress Correlation (Scatter Chart)
    // ========================================================
    const ctxCorr = document.getElementById('correlationChart');
    if (ctxCorr) {
        const corrData = getValidData(window.costProgressData, {
            labels: ['Kolkata Metro Rail', 'NH-17 Widening', 'Smart City Hub', 'Port Terminal', 'Solar Grid', 'Water Pipeline'],
            approved: [4200, 3500, 2800, 2100, 1800, 1200],
            progress: [78, 65, 85, 42, 55, 30]
        });

        const scatterPoints = [];
        const pointColors = ['#003366', '#FF9933', '#28A745', '#DC3545', '#9333EA', '#0EA5E9'];
        
        if (corrData && corrData.labels && corrData.approved) {
            for (let i = 0; i < corrData.labels.length; i++) {
                scatterPoints.push({
                    x: corrData.approved[i] || 0,
                    y: (corrData.progress && corrData.progress[i] !== undefined) ? corrData.progress[i] : 50,
                    name: corrData.labels[i]
                });
            }
        }

        new Chart(ctxCorr, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Projects',
                    data: scatterPoints,
                    backgroundColor: pointColors,
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    pointRadius: 9,
                    pointHoverRadius: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        title: { display: true, text: 'Approved Cost (₹ Cr)', color: '#003366', font: { weight: 'bold' } },
                        grid: { color: '#F1F5F9' },
                        ticks: { callback: v => '₹' + v }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: { display: true, text: 'Physical Progress (%)', color: '#003366', font: { weight: 'bold' } },
                        grid: { color: '#F1F5F9' },
                        ticks: { callback: v => v + '%' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                const pt = ctx.raw;
                                return `${pt.name}: Cost ₹${pt.x} Cr | Progress ${pt.y}%`;
                            }
                        }
                    }
                }
            }
        });
    }
});
