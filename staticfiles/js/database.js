document.addEventListener('DOMContentLoaded', function() {
    
    // 1. CSV Preview functionality
    const csvFileInput = document.getElementById('csvFileInput');
    const previewContainer = document.getElementById('csvPreviewContainer');
    const previewTable = document.getElementById('csvPreviewTable');

    if (csvFileInput && previewContainer && previewTable) {
        csvFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) {
                previewContainer.style.display = 'none';
                return;
            }

            // Must be a csv file
            if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
                alert('Please select a valid CSV file.');
                csvFileInput.value = '';
                previewContainer.style.display = 'none';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(event) {
                const text = event.target.result;
                const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
                
                if (lines.length === 0) {
                    alert('The CSV file is empty.');
                    return;
                }

                // Show preview container
                previewContainer.style.display = 'block';
                previewTable.innerHTML = ''; // clear previous

                // We'll show max 5 rows (including header)
                const rowsToShow = Math.min(6, lines.length);
                
                // Create table head
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                const headers = lines[0].split(',');
                
                // Check required columns (example list)
                const requiredColumns = ['project_id', 'name', 'ministry'];
                let missingColumns = [];
                const lowerHeaders = headers.map(h => h.toLowerCase().trim());
                
                requiredColumns.forEach(req => {
                    if (!lowerHeaders.includes(req)) {
                        missingColumns.push(req);
                    }
                });
                
                if (missingColumns.length > 0) {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-warning mb-3';
                    alertDiv.textContent = 'Warning: Missing standard columns: ' + missingColumns.join(', ');
                    previewContainer.insertBefore(alertDiv, previewTable);
                }

                headers.forEach(headerText => {
                    const th = document.createElement('th');
                    th.textContent = headerText;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);
                previewTable.appendChild(thead);

                // Create table body
                const tbody = document.createElement('tbody');
                for (let i = 1; i < rowsToShow; i++) {
                    const row = document.createElement('tr');
                    // simple split by comma, naive implementation (doesn't handle quotes perfectly, but enough for basic preview)
                    const cells = lines[i].split(',');
                    for(let j=0; j < headers.length; j++) {
                        const td = document.createElement('td');
                        td.textContent = cells[j] || '';
                        row.appendChild(td);
                    }
                    tbody.appendChild(row);
                }
                
                if (lines.length > 6) {
                    const extraRow = document.createElement('tr');
                    const extraCell = document.createElement('td');
                    extraCell.colSpan = headers.length;
                    extraCell.className = 'text-center text-muted font-italic';
                    extraCell.textContent = `... and ${lines.length - 6} more rows`;
                    extraRow.appendChild(extraCell);
                    tbody.appendChild(extraRow);
                }

                previewTable.appendChild(tbody);
            };
            
            reader.readAsText(file);
        });
    }

    // 2. Project Form Validation
    const projectForms = document.querySelectorAll('.project-form');
    projectForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Required text fields
            const reqFields = ['project_id', 'name'];
            reqFields.forEach(id => {
                const el = form.querySelector(`[name="${id}"]`);
                if (el && el.value.trim() === '') {
                    isValid = false;
                    el.classList.add('is-invalid');
                } else if (el) {
                    el.classList.remove('is-invalid');
                    el.classList.add('is-valid');
                }
            });

            // Cost validations (must be positive)
            const costFields = ['approved_cost', 'revised_cost', 'expenditure'];
            costFields.forEach(id => {
                const el = form.querySelector(`[name="${id}"]`);
                if (el) {
                    const val = parseFloat(el.value);
                    if (isNaN(val) || val < 0) {
                        isValid = false;
                        el.classList.add('is-invalid');
                    } else {
                        el.classList.remove('is-invalid');
                        el.classList.add('is-valid');
                    }
                }
            });

            // Progress validations (0-100)
            const progressFields = ['physical_progress', 'financial_progress'];
            progressFields.forEach(id => {
                const el = form.querySelector(`[name="${id}"]`);
                if (el) {
                    const val = parseFloat(el.value);
                    if (isNaN(val) || val < 0 || val > 100) {
                        isValid = false;
                        el.classList.add('is-invalid');
                    } else {
                        el.classList.remove('is-invalid');
                        el.classList.add('is-valid');
                    }
                }
            });

            // Date validation (start < expected)
            const startDateEl = form.querySelector('[name="start_date"]');
            const expectedDateEl = form.querySelector('[name="expected_completion_date"]');
            
            if (startDateEl && expectedDateEl && startDateEl.value && expectedDateEl.value) {
                const start = new Date(startDateEl.value);
                const end = new Date(expectedDateEl.value);
                if (start > end) {
                    isValid = false;
                    expectedDateEl.classList.add('is-invalid');
                    // Add custom error message text if a feedback div exists
                    const feedback = expectedDateEl.parentElement.querySelector('.invalid-feedback');
                    if (feedback) feedback.textContent = 'Completion date must be after start date.';
                } else {
                    expectedDateEl.classList.remove('is-invalid');
                    expectedDateEl.classList.add('is-valid');
                }
            }

            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });

    // 3. Database Page Delete Confirmation Modals
    // For standalone delete buttons not covered by global main.js
    const dbDeleteBtns = document.querySelectorAll('.db-delete-btn');
    dbDeleteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you absolutely sure you want to delete this record?')) {
                e.preventDefault();
            }
        });
    });

    // 4. Live Progress Slider Update
    const progressSliders = document.querySelectorAll('input[type="range"].progress-slider');
    progressSliders.forEach(slider => {
        // Look for adjacent output element
        const output = slider.parentElement.querySelector('.progress-output');
        if (output) {
            output.textContent = slider.value + '%';
            slider.addEventListener('input', function() {
                output.textContent = this.value + '%';
            });
        }
    });
});
