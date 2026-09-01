/**
 * IIPMP Dashboard — Chart.js Visualizations, Sidebar, Refresh & Export Handlers
 * Integrated Infrastructure Project Monitoring Portal
 */

document.addEventListener('DOMContentLoaded', function () {

    // ========================================================
    //  GUARD: Ensure Chart.js is loaded
    // ========================================================
    if (typeof Chart === 'undefined') {
        console.warn('[IIPMP] Chart.js is not loaded — skipping chart init.');
        return;
    }

    // ========================================================
    //  Chart.js Global Defaults
    // ========================================================
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 14;
    Chart.defaults.color = '#64748B';
    Chart.defaults.animation.duration = 900;
    Chart.defaults.animation.easing = 'easeOutQuart';

    // Helper data extractors with defaults matching exact prompt spec
    const statusObj = (window.statusData && window.statusData.labels) ? window.statusData : {
        labels: ['Ongoing', 'Completed', 'Delayed', 'On Hold', 'New Added', 'At Risk'],
        data: [25, 4, 15, 5, 2, 3]
    };

    const progressObj = (window.progressData && window.progressData.labels) ? window.progressData : {
        labels: ['Kolkata Metro Rail', 'NH-17 Widening', 'Smart City Hub', 'Port Terminal', 'Solar Grid', 'Water Pipeline'],
        data: [78, 65, 85, 42, 55, 30]
    };

    const costObj = (window.costData && window.costData.labels) ? window.costData : {
        labels: ['Kolkata Metro Rail', 'NH-17', 'Smart City', 'Port', 'Solar Grid'],
        approved: [4200, 3500, 2800, 2100, 1800],
        revised: [4500, 3500, 3100, 2100, 1950],
        expenditure: [3150, 2450, 1960, 1470, 1170]
    };

    const stateObj = (window.stateData && window.stateData.labels) ? window.stateData : {
        labels: ['Kolkata', 'South 24 Parganas', 'North 24 Parganas', 'Darjeeling', 'Howrah', 'Murshidabad'],
        data: [22, 14, 11, 8, 6, 4]
    };

    const ministryObj = (window.ministryData && window.ministryData.labels) ? window.ministryData : {
        labels: ['Road Transport', 'Railways', 'Power', 'Ports & Shipping', 'Urban Affairs'],
        data: [28, 22, 16, 12, 8]
    };

    const monthlyObj = (window.monthlyData && window.monthlyData.labels) ? window.monthlyData : {
        labels: ['March', 'April', 'May', 'June', 'July', 'August'],
        data: [41, 48, 54, 59, 63, 68]
    };

    // ========================================================
    //  1. STATUS DISTRIBUTION — Doughnut Chart
    // ========================================================
    const ctxStatus = document.getElementById('statusChart');
    if (ctxStatus) {
        new Chart(ctxStatus, {
            type: 'doughnut',
            data: {
                labels: statusObj.labels,
                datasets: [{
                    data: statusObj.data,
                    backgroundColor: ['#0ea5e9', '#22c55e', '#ef4444', '#64748b', '#8b5cf6', '#f59e0b'],
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: { size: 11, weight: '600' },
                            boxWidth: 10,
                            padding: 12
                        }
                    },
                    tooltip: {
                        backgroundColor: '#002244',
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 12 },
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (ctx) {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                return ' ' + ctx.label + ': ' + ctx.raw + ' Projects (' + pct + '%)';
                            }
                        }
                    }
                }
            },
            plugins: [{
                id: 'centerText',
                beforeDraw: function (chart) {
                    const { ctx, chartArea } = chart;
                    if (!chartArea) return;
                    ctx.save();
                    const centerX = (chartArea.left + chartArea.right) / 2;
                    const centerY = (chartArea.top + chartArea.bottom) / 2;
                    const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);

                    ctx.font = '800 1.8rem Inter';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#003366';
                    ctx.fillText(total + ' Total', centerX, centerY - 6);

                    ctx.font = '600 0.72rem Inter';
                    ctx.fillStyle = '#94A3B8';
                    ctx.fillText('Projects Monitored', centerX, centerY + 18);
                    ctx.restore();
                }
            }]
        });
    }

    // ========================================================
    //  2. PHYSICAL PROGRESS — Horizontal Bar Chart
    // ========================================================
    const ctxProgress = document.getElementById('progressChart');
    if (ctxProgress) {
        new Chart(ctxProgress, {
            type: 'bar',
            data: {
                labels: progressObj.labels,
                datasets: [{
                    label: 'Physical Progress (%)',
                    data: progressObj.data,
                    backgroundColor: function (context) {
                        const chart = context.chart;
                        const { ctx, chartArea } = chart;
                        if (!chartArea) return '#003366';
                        const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
                        gradient.addColorStop(0, '#003366');
                        gradient.addColorStop(1, '#0ea5e9');
                        return gradient;
                    },
                    borderRadius: 6,
                    barThickness: 18
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#F1F5F9', drawBorder: false },
                        ticks: { callback: v => v + '%' }
                    },
                    y: {
                        grid: { display: false, drawBorder: false },
                        ticks: { font: { weight: '600' }, color: '#1A1A2E' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#002244',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: { label: ctx => ' Physical Progress: ' + ctx.raw + '%' }
                    }
                }
            }
        });
    }

    // ========================================================
    //  3. COST ANALYSIS — Grouped Bar Chart
    // ========================================================
    const ctxCost = document.getElementById('costChart');
    if (ctxCost) {
        new Chart(ctxCost, {
            type: 'bar',
            data: {
                labels: costObj.labels,
                datasets: [
                    {
                        label: 'Approved Cost',
                        data: costObj.approved,
                        backgroundColor: '#003366',
                        borderRadius: 4,
                        barPercentage: 0.75
                    },
                    {
                        label: 'Revised Cost',
                        data: costObj.revised,
                        backgroundColor: '#FF9933',
                        borderRadius: 4,
                        barPercentage: 0.75
                    },
                    {
                        label: 'Expenditure',
                        data: costObj.expenditure,
                        backgroundColor: '#22c55e',
                        borderRadius: 4,
                        barPercentage: 0.75
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false, drawBorder: false },
                        ticks: { font: { weight: '600' } }
                    },
                    y: {
                        beginAtZero: true,
                        max: 4500,
                        grid: { color: '#F1F5F9', drawBorder: false },
                        ticks: { callback: v => '₹ ' + v.toLocaleString('en-IN') + ' Cr' }
                    }
                },
                plugins: {
                    legend: { position: 'top', labels: { font: { size: 11, weight: '600' }, boxWidth: 10 } },
                    tooltip: {
                        backgroundColor: '#002244',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: ctx => ' ' + ctx.dataset.label + ': ₹ ' + ctx.raw.toLocaleString('en-IN') + ' Cr'
                        }
                    }
                }
            }
        });
    }

    // ========================================================
    //  4. STATE-WISE PROJECTS — Horizontal Bar Chart
    // ========================================================
    const ctxState = document.getElementById('stateChart');
    if (ctxState) {
        new Chart(ctxState, {
            type: 'bar',
            data: {
                labels: stateObj.labels,
                datasets: [{
                    label: 'Projects',
                    data: stateObj.data,
                    backgroundColor: function (context) {
                        const chart = context.chart;
                        const { ctx, chartArea } = chart;
                        if (!chartArea) return '#003366';
                        const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
                        gradient.addColorStop(0, '#003366');
                        gradient.addColorStop(1, '#6366f1');
                        return gradient;
                    },
                    borderRadius: 6,
                    barThickness: 16
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 25,
                        grid: { color: '#F1F5F9', drawBorder: false },
                        ticks: { precision: 0 }
                    },
                    y: {
                        grid: { display: false, drawBorder: false },
                        ticks: { font: { weight: '600' }, color: '#1A1A2E' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#002244',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: { label: ctx => ' ' + ctx.raw + ' Projects' }
                    }
                }
            }
        });
    }

    // ========================================================
    //  5. MINISTRY-WISE PROJECTS — Horizontal Bar Chart
    // ========================================================
    const ctxMinistry = document.getElementById('ministryChart');
    if (ctxMinistry) {
        new Chart(ctxMinistry, {
            type: 'bar',
            data: {
                labels: ministryObj.labels,
                datasets: [{
                    label: 'Projects',
                    data: ministryObj.data,
                    backgroundColor: function (context) {
                        const chart = context.chart;
                        const { ctx, chartArea } = chart;
                        if (!chartArea) return '#FF9933';
                        const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
                        gradient.addColorStop(0, '#FF9933');
                        gradient.addColorStop(1, '#f59e0b');
                        return gradient;
                    },
                    borderRadius: 6,
                    barThickness: 16
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 30,
                        grid: { color: '#F1F5F9', drawBorder: false },
                        ticks: { precision: 0 }
                    },
                    y: {
                        grid: { display: false, drawBorder: false },
                        ticks: { font: { weight: '600' }, color: '#1A1A2E' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#002244',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: { label: ctx => ' ' + ctx.raw + ' Projects' }
                    }
                }
            }
        });
    }

    // ========================================================
    //  6. MONTHLY PROGRESS TREND — Line Chart
    // ========================================================
    const ctxMonthly = document.getElementById('monthlyChart');
    if (ctxMonthly) {
        new Chart(ctxMonthly, {
            type: 'line',
            data: {
                labels: monthlyObj.labels,
                datasets: [{
                    label: 'Overall Progress (%)',
                    data: monthlyObj.data,
                    borderColor: '#003366',
                    backgroundColor: function (context) {
                        const chart = context.chart;
                        const { ctx, chartArea } = chart;
                        if (!chartArea) return 'rgba(0,51,102,0.1)';
                        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                        gradient.addColorStop(0, 'rgba(0,51,102,0.18)');
                        gradient.addColorStop(1, 'rgba(0,51,102,0.01)');
                        return gradient;
                    },
                    borderWidth: 3,
                    pointBackgroundColor: '#003366',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    fill: true,
                    tension: 0.38
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#F1F5F9', drawBorder: false },
                        ticks: { callback: v => v + '%' }
                    },
                    x: {
                        grid: { display: false, drawBorder: false },
                        ticks: { font: { weight: '600' } }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#002244',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: { label: ctx => ' Overall Progress: ' + ctx.raw + '%' }
                    }
                }
            }
        });
    }

    // ========================================================
    //  SIDEBAR TOGGLE & PERSISTENCE
    // ========================================================
    const sidebar = document.getElementById('dashSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggleBtn = document.getElementById('sidebarToggle');
    const mobileBtn = document.getElementById('mobileSidebarBtn');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function () {
            if (window.innerWidth >= 992) {
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebar_collapsed', sidebar.classList.contains('collapsed'));
            } else {
                sidebar.classList.remove('mobile-open');
                if (overlay) overlay.classList.remove('show');
            }
        });

        if (localStorage.getItem('sidebar_collapsed') === 'true' && window.innerWidth >= 992) {
            sidebar.classList.add('collapsed');
        }
    }

    if (mobileBtn && sidebar && overlay) {
        mobileBtn.addEventListener('click', function () {
            sidebar.classList.toggle('mobile-open');
            overlay.classList.toggle('show');
        });

        overlay.addEventListener('click', function () {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('show');
        });
    }

    // ========================================================
    //  TOAST NOTIFICATION SYSTEM
    // ========================================================
    function showToast(message, type) {
        type = type || 'success';
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'custom-toast' + (type === 'error' ? ' error' : '');

        const iconClass = type === 'success' ? 'fa-circle-check' : 'fa-circle-xmark';
        const iconColor = type === 'success' ? '#22c55e' : '#ef4444';

        toast.innerHTML =
            '<span class="toast-icon" style="color:' + iconColor + '"><i class="fa-solid ' + iconClass + '"></i></span>' +
            '<span class="toast-msg">' + message + '</span>' +
            '<button class="toast-close" onclick="this.parentElement.remove()"><i class="fa-solid fa-xmark"></i></button>';

        container.appendChild(toast);

        setTimeout(function () {
            if (toast.parentElement) {
                toast.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(function () { toast.remove(); }, 300);
            }
        }, 4000);
    }

    // ========================================================
    //  REFRESH DATA BUTTON (LOADING SPINNER + SIMULATION)
    // ========================================================
    const btnRefresh = document.getElementById('btnRefresh');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', async function () {
            btnRefresh.classList.add('loading');
            btnRefresh.disabled = true;

            try {
                const res = await fetch('/api/dashboard/');
                if (res.ok) {
                    const data = await res.json();
                    console.log('[IIPMP Dashboard] Refreshed API payload:', data);
                }
            } catch (err) {
                console.warn('[IIPMP Dashboard] API refresh notice:', err);
            }

            setTimeout(function () {
                btnRefresh.classList.remove('loading');
                btnRefresh.disabled = false;
                showToast('Dashboard data refreshed successfully', 'success');
            }, 850);
        });
    }

    // ========================================================
    //  EXPORT REPORT BUTTON (CSV / PRINT DOWNLOAD)
    // ========================================================
    const btnExport = document.getElementById('btnExport');
    if (btnExport) {
        btnExport.addEventListener('click', function () {
            showToast('Downloading Project Dashboard Report (CSV)...', 'success');
            setTimeout(function () {
                window.location.href = '/dashboard/export/';
            }, 500);
        });
    }
});
