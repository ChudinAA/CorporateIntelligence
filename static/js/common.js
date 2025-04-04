document.addEventListener('DOMContentLoaded', function() {
    // Document preview functionality
    const previewButtons = document.querySelectorAll('.document-preview');
    
    previewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const documentId = this.dataset.documentId;
            const previewArea = document.querySelector('.document-preview-area[data-document-id="' + documentId + '"]');
            
            if (previewArea) {
                // Show loading state in preview area
                previewArea.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-3">Loading document preview...</p></div>';
                
                // Fetch document content
                fetch(`/documents/preview/${documentId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Format the content based on file type
                            let formattedContent = data.content;
                            
                            // Add line breaks for text content
                            if (data.file_type === 'txt') {
                                formattedContent = data.content.replace(/\n/g, '<br>');
                            }
                            
                            // Update preview area with content
                            previewArea.innerHTML = `
                                <div class="document-preview-header">
                                    <h5 class="mb-2">${data.filename}</h5>
                                    <div class="document-meta">
                                        <span><i class="far fa-file me-1"></i>${data.file_type.toUpperCase()}</span>
                                        <span><i class="far fa-clock me-1"></i>${data.upload_date}</span>
                                        <span><i class="far fa-hdd me-1"></i>${Math.round(data.file_size / 1024)} KB</span>
                                    </div>
                                </div>
                                <div class="document-preview-content">${formattedContent}</div>
                            `;
                        } else {
                            previewArea.innerHTML = `<div class="alert alert-danger">Error loading document preview: ${data.message || 'Unknown error'}</div>`;
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching document preview:', error);
                        previewArea.innerHTML = '<div class="alert alert-danger">Error loading document preview. Please try again later.</div>';
                    });
            }
        });
    });
    
    // Create and append scroll-to-top button
    const scrollTopBtn = document.createElement('div');
    scrollTopBtn.className = 'scroll-top-btn';
    scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    document.body.appendChild(scrollTopBtn);
    
    // Show/hide scroll-to-top button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    });
    
    // Smooth scroll to top when button is clicked
    scrollTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // Add smooth transition to modal dialogs
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            setTimeout(() => {
                const modalDialog = this.querySelector('.modal-dialog');
                if (modalDialog) {
                    modalDialog.style.transform = 'scale(1)';
                    modalDialog.style.opacity = '1';
                }
            }, 50);
        });
        
        modal.addEventListener('hide.bs.modal', function() {
            const modalDialog = this.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.style.transform = 'scale(0.8)';
                modalDialog.style.opacity = '0';
            }
        });
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn:not(.btn-link)');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const x = e.clientX - e.target.getBoundingClientRect().left;
            const y = e.clientY - e.target.getBoundingClientRect().top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('btn-ripple');
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// Add ripple animation styles
document.addEventListener('DOMContentLoaded', function() {
    // Create style element
    const style = document.createElement('style');
    style.textContent = `
        .btn {
            position: relative;
            overflow: hidden;
        }
        
        .btn-ripple {
            position: absolute;
            width: 10px;
            height: 10px;
            background: rgba(255, 255, 255, 0.4);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple-effect 0.6s linear;
            pointer-events: none;
        }
        
        @keyframes ripple-effect {
            0% {
                transform: scale(0);
                opacity: 0.6;
            }
            100% {
                transform: scale(20);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});
