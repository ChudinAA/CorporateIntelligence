document.addEventListener('DOMContentLoaded', function() {
    // Drag and drop file upload
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('document-file');
    const uploadForm = document.getElementById('upload-form');
    
    if (uploadZone && fileInput) {
        // Make the upload zone clickable to select files
        uploadZone.addEventListener('click', function() {
            fileInput.click();
        });
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, unhighlight, false);
        });
        
        uploadZone.addEventListener('drop', handleDrop, false);
        fileInput.addEventListener('change', handleFiles, false);
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        function highlight(e) {
            uploadZone.classList.add('highlight');
        }
        
        function unhighlight(e) {
            uploadZone.classList.remove('highlight');
        }
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            handleFiles(e);
        }
        
        function handleFiles(e) {
            const files = fileInput.files;
            if (files.length) {
                const uploadBtn = uploadForm.querySelector('.btn-upload');
                if (uploadBtn) {
                    uploadBtn.textContent = 'Uploading...';
                }
                uploadForm.submit();
            }
        }
    }
    
    // Handle document deletion with SweetAlert2 confirmation
    const deleteButtons = document.querySelectorAll('.delete-document');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent triggering the document preview
            
            const documentId = this.dataset.documentId;
            
            Swal.fire({
                title: 'Delete Document',
                text: 'Are you sure you want to delete this document? This action cannot be undone.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, delete it!',
                cancelButtonText: 'Cancel',
                showClass: {
                    popup: 'swal2-show',
                    backdrop: 'swal2-backdrop-show',
                    icon: 'swal2-icon-show'
                },
                hideClass: {
                    popup: 'swal2-hide',
                    backdrop: 'swal2-backdrop-hide',
                    icon: 'swal2-icon-hide'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show loading state
                    Swal.fire({
                        title: 'Deleting...',
                        text: 'Please wait while we delete the document',
                        allowOutsideClick: false,
                        showConfirmButton: false,
                        showClass: {
                            popup: 'swal2-show',
                            backdrop: 'swal2-backdrop-show'
                        },
                        willOpen: () => {
                            Swal.showLoading();
                        }
                    });
                    
                    // Send DELETE request
                    fetch(`/documents/delete/${documentId}`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Success - show message and remove element
                            Swal.fire({
                                title: 'Deleted!',
                                text: data.message || 'Document deleted successfully.',
                                icon: 'success',
                                timer: 1500,
                                showConfirmButton: false,
                                showClass: {
                                    popup: 'swal2-show',
                                    backdrop: 'swal2-backdrop-show',
                                    icon: 'swal2-icon-show'
                                },
                                hideClass: {
                                    popup: 'swal2-hide',
                                    backdrop: 'swal2-backdrop-hide',
                                    icon: 'swal2-icon-hide'
                                }
                            }).then(() => {
                                // Find the document card and animate its removal
                                const docCard = button.closest('.document-card');
                                if (docCard) {
                                    docCard.style.transition = 'all 0.5s ease';
                                    docCard.style.opacity = '0';
                                    docCard.style.transform = 'translateY(-20px)';
                                    
                                    setTimeout(() => {
                                        docCard.remove();
                                        
                                        // Check if there are no documents left and display empty state if needed
                                        const remainingDocs = document.querySelectorAll('.document-card:not([style*="opacity: 0"])');
                                        if (remainingDocs.length === 0) {
                                            const documentsContainer = document.querySelector('.documents-container');
                                            if (documentsContainer) {
                                                const emptyState = document.createElement('div');
                                                emptyState.className = 'empty-state';
                                                emptyState.style.opacity = '0';
                                                emptyState.style.transform = 'translateY(20px)';
                                                emptyState.style.transition = 'all 0.5s ease';
                                                emptyState.innerHTML = `
                                                    <div class="empty-state-icon">
                                                        <i class="fas fa-file-upload"></i>
                                                    </div>
                                                    <h3 class="empty-state-title">No Documents Yet</h3>
                                                    <p class="empty-state-text">Upload your first document to get started</p>
                                                `;
                                                documentsContainer.appendChild(emptyState);
                                                
                                                // Trigger animation
                                                setTimeout(() => {
                                                    emptyState.style.opacity = '1';
                                                    emptyState.style.transform = 'translateY(0)';
                                                }, 50);
                                            }
                                        }
                                        
                                        // Update document counter if it exists
                                        const docCounter = document.querySelector('.document-counter');
                                        if (docCounter) {
                                            const currentCount = parseInt(docCounter.textContent);
                                            if (!isNaN(currentCount) && currentCount > 0) {
                                                docCounter.textContent = (currentCount - 1).toString();
                                            }
                                        }
                                    }, 500);
                                }
                            });
                        } else {
                            // Error
                            Swal.fire({
                                title: 'Error!',
                                text: data.message || 'Failed to delete document.',
                                icon: 'error',
                                showClass: {
                                    popup: 'swal2-show',
                                    backdrop: 'swal2-backdrop-show'
                                }
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        Swal.fire({
                            title: 'Error!',
                            text: 'An unexpected error occurred.',
                            icon: 'error',
                            showClass: {
                                popup: 'swal2-show',
                                backdrop: 'swal2-backdrop-show'
                            }
                        });
                    });
                }
            });
        });
    });
    
    // Animation for document cards on scroll
    function animateOnScroll() {
        document.querySelectorAll('.document-card').forEach(card => {
            const cardTop = card.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (cardTop < windowHeight - 100) {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    }
    
    // Set initial state for document cards
    document.querySelectorAll('.document-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
    
    // Run animation on load and scroll
    window.addEventListener('load', animateOnScroll);
    window.addEventListener('scroll', animateOnScroll);
    
    // Document preview functionality has been moved to common.js
});
