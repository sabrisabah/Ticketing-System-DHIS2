document.addEventListener('DOMContentLoaded', function() {
    // File upload validation
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
            const maxSize = 5 * 1024 * 1024; // 5MB

            if (this.files.length > 0) {
                const file = this.files[0];
                if (!allowedTypes.includes(file.type)) {
                    alert('Invalid file type. Please upload an image (JPG, PNG, GIF) or PDF.');
                    this.value = '';
                } else if (file.size > maxSize) {
                    alert('File is too large. Maximum size is 5MB.');
                    this.value = '';
                }
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });

    // Enable tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Dynamic form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Search form debounce
    let searchTimeout;
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.closest('form').submit();
            }, 500);
        });
    }
});