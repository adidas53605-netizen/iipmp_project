document.addEventListener('DOMContentLoaded', function() {
    // 1. Global Search with Debounce and Live Overlay
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        let searchContainer = searchInput.closest('.search-container') || searchInput.parentElement;
        if (!searchContainer.classList.contains('search-container')) {
            searchContainer.classList.add('search-container');
        }

        let dropdown = searchContainer.querySelector('.search-results-dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.className = 'search-results-dropdown';
            searchContainer.appendChild(dropdown);
        }

        let debounceTimer;

        function performSearch(query) {
            clearTimeout(debounceTimer);
            if (!query || query.length < 1) {
                dropdown.classList.remove('show');
                dropdown.innerHTML = '';
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        dropdown.innerHTML = '';
                        const items = Array.isArray(data) ? data : (data.results || []);
                        
                        if (items.length > 0) {
                            items.forEach(item => {
                                const a = document.createElement('a');
                                a.href = item.url || `/projects/${item.project_id || item.id}/`;
                                a.className = 'search-result-item';
                                
                                const statusBadgeClass = item.status === 'completed' ? 'bg-success' :
                                                        item.status === 'delayed' ? 'bg-danger' :
                                                        item.status === 'ongoing' ? 'bg-primary' : 'bg-secondary';
                                
                                a.innerHTML = `
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="result-name text-truncate">${item.name}</span>
                                        <span class="badge ${statusBadgeClass} ms-2" style="font-size: 0.65rem;">${item.status ? item.status.replace('_', ' ').toUpperCase() : ''}</span>
                                    </div>
                                    <div class="result-meta mt-1">
                                        <span class="fw-bold text-muted">${item.project_id || ''}</span>
                                        <span class="text-secondary">${item.ministry || ''} • ${item.state || ''}</span>
                                    </div>
                                `;
                                dropdown.appendChild(a);
                            });
                            dropdown.classList.add('show');
                        } else {
                            dropdown.innerHTML = '<div class="p-3 text-center text-muted small"><i class="fa-solid fa-circle-exclamation me-1"></i>No projects found</div>';
                            dropdown.classList.add('show');
                        }
                    })
                    .catch(err => {
                        console.error('Global search error:', err);
                        dropdown.innerHTML = '<div class="p-3 text-center text-danger small">Error searching projects.</div>';
                        dropdown.classList.add('show');
                    });
            }, 200);
        }

        searchInput.addEventListener('input', function(e) {
            performSearch(e.target.value.trim());
        });

        searchInput.addEventListener('focus', function(e) {
            if (e.target.value.trim().length > 0) {
                performSearch(e.target.value.trim());
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchContainer.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                dropdown.classList.remove('show');
                searchInput.blur();
            }
        });
    }

    // 2. Navbar Active Link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else if (currentPath.startsWith(link.getAttribute('href')) && link.getAttribute('href') !== '/') {
            // For sub-paths, except the root '/'
            link.classList.add('active');
        }
    });

    // 4. Smooth Scroll for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 5. Form Validation Helpers (Bootstrap)
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 6. Delete Confirmation
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // 7. Auto-hide Django Messages Alerts
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                // Check if bootstrap is available globally
                if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                } else {
                    // Fallback fade out
                    alert.style.transition = 'opacity 0.5s ease';
                    alert.style.opacity = '0';
                    setTimeout(() => alert.remove(), 500);
                }
            });
        }, 5000);
    }
});
