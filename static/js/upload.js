// Brain Tumor Segmentation App - Upload Functionality
// Drag and Drop + AJAX Upload

document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('mri-file-input');
    const uploadForm = document.getElementById('upload-form');
    const uploadButton = document.getElementById('upload-button');
    const progressBar = document.getElementById('upload-progress');
    const progressContainer = document.getElementById('progress-container');
    
    if (!uploadArea || !fileInput) return; // Exit if elements not found

    // Drag and drop functionality
    let dragCounter = 0;

    uploadArea.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter++;
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter--;
        if (dragCounter === 0) {
            uploadArea.classList.remove('dragover');
        }
    });

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter = 0;
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // Click to upload
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Handle file selection
    function handleFileSelect(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            showAlert('Please select a valid image file.', 'danger');
            return;
        }

        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            showAlert('File size must be less than 10MB.', 'danger');
            return;
        }

        // Update UI
        updateUploadArea(file);
        
        // Auto-upload if AJAX is enabled
        if (document.querySelector('[data-ajax-upload="true"]')) {
            uploadFileAjax(file);
        }
    }

    // Update upload area with file info
    function updateUploadArea(file) {
        const uploadIcon = uploadArea.querySelector('.upload-icon');
        const uploadText = uploadArea.querySelector('.upload-text');
        const uploadSubtext = uploadArea.querySelector('.upload-subtext');
        
        if (uploadIcon) uploadIcon.innerHTML = '📁';
        if (uploadText) uploadText.textContent = file.name;
        if (uploadSubtext) uploadSubtext.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
        
        uploadArea.classList.add('file-selected');
    }

    // AJAX upload function
    function uploadFileAjax(file) {
        const formData = new FormData();
        formData.append('uploaded_image', file);
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        // Show progress
        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
        
        if (uploadButton) {
            uploadButton.disabled = true;
            uploadButton.innerHTML = '<span class="loading"></span> Processing...';
        }

        // Upload with progress
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable && progressBar) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBar.style.width = percentComplete + '%';
                progressBar.setAttribute('aria-valuenow', percentComplete);
            }
        });

        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        showAlert(response.message, 'success');
                        if (response.redirect_url) {
                            setTimeout(() => {
                                window.location.href = response.redirect_url;
                            }, 2000);
                        }
                    } else {
                        showAlert(response.message, 'danger');
                    }
                } catch (e) {
                    showAlert('Upload successful! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                }
            } else {
                showAlert('Upload failed. Please try again.', 'danger');
            }
            
            resetUploadState();
        });

        xhr.addEventListener('error', function() {
            showAlert('Upload failed. Please check your connection and try again.', 'danger');
            resetUploadState();
        });

        xhr.open('POST', '/api/upload/');
        xhr.send(formData);
    }

    // Reset upload state
    function resetUploadState() {
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        if (uploadButton) {
            uploadButton.disabled = false;
            uploadButton.innerHTML = 'Upload & Analyze';
        }
        
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
        }
    }

    // Show alert message
    function showAlert(message, type) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert.auto-dismiss');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} auto-dismiss`;
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="me-2">
                    ${type === 'success' ? '✅' : type === 'danger' ? '❌' : '⚠️'}
                </div>
                <div>${message}</div>
            </div>
        `;

        // Insert at top of main content
        const mainContent = document.querySelector('.container') || document.querySelector('main') || document.body;
        mainContent.insertBefore(alertDiv, mainContent.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Image preview functionality
    function createImagePreview(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewContainer = document.getElementById('image-preview');
            if (previewContainer) {
                previewContainer.innerHTML = `
                    <img src="${e.target.result}" class="img-fluid rounded" alt="MRI Preview" style="max-height: 300px;">
                    <p class="mt-2 text-muted-custom">${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)</p>
                `;
                previewContainer.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
    }

    // Form validation
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('input[type="file"]');
            if (!fileInput || !fileInput.files.length) {
                e.preventDefault();
                showAlert('Please select an MRI image to upload.', 'warning');
                return false;
            }
        });
    }
});

// Utility functions for other pages
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('Copied to clipboard!', 'success');
    }).catch(function() {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('Copied to clipboard!', 'success');
    });
}

// Image zoom functionality
function initImageZoom() {
    const images = document.querySelectorAll('.zoomable-image');
    images.forEach(img => {
        img.addEventListener('click', function() {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Image Preview</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <img src="${this.src}" class="img-fluid" alt="Zoomed Image">
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            modal.addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(modal);
            });
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initImageZoom();
});