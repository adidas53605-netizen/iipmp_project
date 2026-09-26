/**
 * IIPMP Dashboard — Chart.js Visualizations & Interactivity
 * Integrated Infrastructure Project Monitoring Portal
 */

document.addEventListener('DOMContentLoaded', function() {

    // Sidebar Toggle Functionality
    const sidebar = document.getElementById('dashSidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebar_collapsed', sidebar.classList.contains('collapsed'));
        });
        if (localStorage.getItem('sidebar_collapsed') === 'true' && window.innerWidth >= 992) {
            sidebar.classList.add('collapsed');
        }
    }

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded.');
        return;
    }

    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 13;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.color = '#6C757D';

    // Data Objects
    const statusDataObj = window.statusData && window.statusData.labels ? window.statusData : {
        labels: ['Ongoing','Completed','Delayed','On Hold','New Added','At Risk'],
        data: [5, 6, 10, 2, 2, 15]
    };

    const progressDataObj = window.progressData && window.progressData.labels ? window.progressData : {
        labels: ['Syama Prasad Mookerjee Port Mod.','SSKM Super Specialty Wing','Purulia Pumped Storage Project','Kalyani AIIMS Campus Expansion','New Town Salt Lake Sector V Hub','Burdwan Railway Overbridge'],
        data: [92, 89, 87, 85, 83, 80]
    };

    const costDataObj = window.costData && window.costData.labels ? window.costData : {
        labels: ['SP Mookerjee Port','SSKM Hospital','Purulia Storage','Kalyani AIIMS','New Town Hub'],
        approved: [15200,4200,9800,6100,3600],
        revised: [16500,4200,10400,6100,3900],
        expenditure: [11200,3100,7200,3800,2100]
    };

    const stateDataObj = window.stateData && window.stateData.labels ? window.stateData : {
        labels: ['Darjeeling','Kolkata','North 24 Parganas','Hooghly','Paschim Medinipur','Bankura'],
        data: [14,9,7,6,5,4]
    };

    const ministryDataObj = window.ministryData && window.ministryData.labels ? window.ministryData : {
        labels: ['Railways','Road Transport','Power','Health','Water Resources'],
        data: [11,9,8,7,5]
    };

    const monthlyDataObj = window.monthlyData && window.monthlyData.labels ? window.monthlyData : {
        labels: ['Mar','Apr','May','Jun','Jul','Aug'],
        data: [48,52,55,58,60,61.3]
    };

    // 1. Status Distribution (Doughnut Chart with Center Text)
    const ctxStatus = document.getElementById('statusChart');
    if (ctxStatus) {
        new Chart(ctxStatus, {
            type: 'doughnut',
            data: {
                labels: statusDataObj.labels,
                datasets: [{
                    data: statusDataObj.data,
                    backgroundColor: ['#2196F3','#28A745','#DC3545','#6C757D','#6f42c1','#FFC107'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let l = context.label || '';
                                if (l) l += ': ';
                                l += context.raw + ' projects';
                                return l;
                            }
                        }
                    }
                }
            },
            plugins: [{
                id: 'centerText',
                beforeDraw: function(chart) {
                    const width = chart.width, height = chart.height, ctx = chart.ctx;
                    ctx.restore();
                    const fontSize = (height / 114).toFixed(2);
                    ctx.font = "bold " + fontSize + "em Inter";
                    ctx.textBaseline = "middle";
                    ctx.fillStyle = "#003366";
                    const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                    const text = total.toString() + " Total";
                    const textX = Math.round((width - ctx.measureText(text).width) / 2);
                    const textY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2;
                    ctx.fillText(text, textX, textY);

                    ctx.font = (fontSize * 0.4).toFixed(2) + "em Inter";
                    ctx.fillStyle = "#6C757D";
                    const subText = "Projects Monitored";
                    const subTextX = Math.round((width - ctx.measureText(subText).width) / 2);
                    ctx.fillText(subText, subTextX, textY + 22);
                    ctx.save();
                }
            }]
        });
    }

    // 2. Physical Progress (Horizontal Bar Chart with Linear Gradient)
    const ctxProgress = document.getElementById('progressChart');
    if (ctxProgress) {
        new Chart(ctxProgress, {
            type: 'bar',
            data: {
                labels: progressDataObj.labels,
                datasets: [{
                    label: 'Physical Progress (%)',
                    data: progressDataObj.data,
                    backgroundColor: function(context) {
                        const chart = context.chart;
                        const { ctx, chartArea } = chart;
                        if (!chartArea) return '#003366';
                        const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
                        gradient.addColorStop(0, '#003366');
                        gradient.addColorStop(1, '#2196F3');
                        return gradient;
                    },
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { beginAtZero: true, max: 100, grid: { color: '#F5F5F5' } },
                    y: {
                        grid: { display: false },
                        ticks: {
                            autoSkip: false,
                            callback: function(value) {
                                const label = this.getLabelForValue(value);
                                return label.length > 22 ? label.slice(0, 22) + '…' : label;
                            }
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: function(items) {
                                return progressDataObj.labels[items[0].dataIndex];
                            }
                        }
                    }
                }
            }
        });
    }

    // 3. Cost Analysis (Grouped Bar Chart)
    const ctxCost = document.getElementById('costChart');
    if (ctxCost) {
        new Chart(ctxCost, {
            type: 'bar',
            data: {
                labels: costDataObj.labels,
                datasets: [
                    { label: 'Approved Cost', data: costDataObj.approved, backgroundColor: '#003366', borderRadius: 4 },
                    { label: 'Revised Cost', data: costDataObj.revised, backgroundColor: '#FF9933', borderRadius: 4 },
                    { label: 'Expenditure', data: costDataObj.expenditure, backgroundColor: '#28A745', borderRadius: 4 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        beginAtZero: true,
                        grid: { color: '#F5F5F5' },
                        ticks: { callback: function(v) { return '₹ ' + v + ' Cr'; } }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) { return context.dataset.label + ': ₹ ' + context.raw + ' Cr'; }
                        }
                    }
                }
            }
        });
    }

    // 4. State-wise Projects (Horizontal Bar Chart)
    const ctxState = document.getElementById('stateChart');
    if (ctxState) {
        new Chart(ctxState, {
            type: 'bar',
            data: {
                labels: stateDataObj.labels,
                datasets: [{ label: 'Number of Projects', data: stateDataObj.data, backgroundColor: '#003366', borderRadius: 4 }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { beginAtZero: true, grid: { color: '#F5F5F5' }, ticks: { precision: 0 } },
                    y: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 5. Ministry-wise Projects (Horizontal Bar Chart with Saffron Gradient)
    const ctxMinistry = document.getElementById('ministryChart');
    if (ctxMinistry) {
        new Chart(ctxMinistry, {
            type: 'bar',
            data: {
                labels: ministryDataObj.labels,
                datasets: [{
                    label: 'Number of Projects',
                    data: ministryDataObj.data,
                    backgroundColor: function(context) {
                        const chart = context.chart;
                        const { ctx, chartArea } = chart;
                        if (!chartArea) return '#FF9933';
                        const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
                        gradient.addColorStop(0, '#FF9933');
                        gradient.addColorStop(1, '#FFB366');
                        return gradient;
                    },
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { beginAtZero: true, grid: { color: '#F5F5F5' }, ticks: { precision: 0 } },
                    y: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 6. Monthly Progress Trend (Smooth Line Chart with Fill)
    const ctxMonthly = document.getElementById('monthlyChart');
    if (ctxMonthly) {
        new Chart(ctxMonthly, {
            type: 'line',
            data: {
                labels: monthlyDataObj.labels,
                datasets: [{
                    label: 'Overall Progress (%)',
                    data: monthlyDataObj.data,
                    borderColor: '#003366',
                    backgroundColor: 'rgba(0, 51, 102, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#003366',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { color: '#F5F5F5' } },
                    x: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: function(context) { return context.dataset.label + ': ' + context.raw + '%'; } } }
                }
            }
        });
    }

    // Handlers for Refresh & Export Buttons
    const btnRefresh = document.getElementById('btnRefresh');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', async function() {
            btnRefresh.disabled = true;
            const origHTML = btnRefresh.innerHTML;
            btnRefresh.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Refreshing...';

            try {
                const res = await fetch('/api/dashboard/');
                if (res.ok) {
                    const data = await res.json();
                    if (data.total_projects !== undefined) {
                        const elTotal = document.getElementById('valTotalProjects');
                        if (elTotal) elTotal.textContent = data.total_projects;
                    }
                    if (data.ongoing_count !== undefined) {
                        const elOngoing = document.getElementById('valOngoing');
                        if (elOngoing) elOngoing.textContent = data.ongoing_count;
                    }
                    if (data.completed_count !== undefined) {
                        const elComp = document.getElementById('valCompleted');
                        if (elComp) elComp.textContent = data.completed_count;
                    }
                    if (data.delayed_count !== undefined) {
                        const elDel = document.getElementById('valDelayed');
                        if (elDel) elDel.textContent = data.delayed_count;
                    }
                    if (data.not_started_count !== undefined) {
                        const elHold = document.getElementById('valOnHold');
                        if (elHold) elHold.textContent = data.not_started_count;
                    }
                    if (data.at_risk_count !== undefined) {
                        const elRisk = document.getElementById('valAtRisk');
                        if (elRisk) elRisk.textContent = data.at_risk_count;
                    }
                    if (data.total_approved_cost !== undefined) {
                        const elCost = document.getElementById('valApprovedCost');
                        if (elCost) elCost.textContent = '₹' + Math.round(data.total_approved_cost).toLocaleString('en-IN') + ' Cr';
                    }
                    if (data.total_expenditure !== undefined) {
                        const elExp = document.getElementById('valExpenditure');
                        if (elExp) elExp.textContent = '₹' + Math.round(data.total_expenditure).toLocaleString('en-IN') + ' Cr';
                    }
                    if (data.avg_progress !== undefined) {
                        const elProg = document.getElementById('valAvgProgress');
                        if (elProg) elProg.textContent = data.avg_progress + '%';
                    }
                }
            } catch (e) {
                console.warn('[IIPMP] Refresh data notice:', e);
            }

            setTimeout(function() {
                btnRefresh.disabled = false;
                btnRefresh.innerHTML = origHTML;
            }, 600);
        });
    }

    const btnExport = document.getElementById('btnExport');
    if (btnExport) {
        btnExport.addEventListener('click', function() {
            window.location.href = '/dashboard/export/';
        });
    }
});
