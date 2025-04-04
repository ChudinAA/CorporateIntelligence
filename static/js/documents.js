document.addEventListener('DOMContentLoaded', function() {
    // Handle document preview functionality
    const previewElements = document.querySelectorAll('.document-preview');
    
    previewElements.forEach(element => {
        element.addEventListener('click', function(e) {
            // Prevent default action if it's a link or inside a link
            if (e.target.tagName === 'A' || e.target.closest('a')) {
                return; // Don't interfere with link clicks
            }
            
            // Get document ID from data attribute
            const documentId = this.dataset.documentId;
            
            // Show loading state
            Swal.fire({
                title: 'Загрузка документа...',
                text: 'Пожалуйста, подождите, идет подготовка документа',
                allowOutsideClick: false,
                showConfirmButton: false,
                willOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Fetch document preview from server
            fetch(`/documents/preview/${documentId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to load document preview');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Close loading dialog and show preview
                        Swal.close();
                        
                        // Display document preview in a modal
                        Swal.fire({
                            title: data.document.name,
                            html: `
                                <div class="document-preview-info mb-3">
                                    <div><strong>Type:</strong> ${data.document.type.toUpperCase()}</div>
                                    <div><strong>Uploaded:</strong> ${data.document.upload_date}</div>
                                </div>
                                <div class="document-preview-content">
                                    <pre class="preview-text">${data.document.preview}</pre>
                                </div>
                            `,
                            width: '70%',
                            showConfirmButton: true,
                            confirmButtonText: 'Close',
                            customClass: {
                                content: 'preview-content',
                                container: 'preview-container'
                            }
                        });
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Preview Failed',
                            text: data.error || 'Could not load document preview'
                        });
                    }
                })
                .catch(error => {
                    Swal.fire({
                        icon: 'error',
                        title: 'Preview Failed',
                        text: error.message
                    });
                });
        });
    });
    
    // Document upload functionality
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('document');
    const uploadForm = document.getElementById('upload-form');
    const emptyUploadBtn = document.getElementById('empty-upload-btn');
    
    // Empty state upload button
    if (emptyUploadBtn) {
        emptyUploadBtn.addEventListener('click', function() {
            dropZone.scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => {
                // Add a pulse animation to highlight the drop zone
                dropZone.classList.add('dragover');
                setTimeout(() => {
                    dropZone.classList.remove('dragover');
                }, 1500);
            }, 500);
        });
    }

    // Drag and drop handling
    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            dropZone.classList.add('dragover');
        }

        function unhighlight(e) {
            dropZone.classList.remove('dragover');
        }

        // Handle click on drop zone
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // Handle file drop
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                // Manually set the file in the input
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(files[0]);
                fileInput.files = dataTransfer.files;
                
                // Show loader
                Swal.fire({
                    title: 'Загрузка документа...',
                    text: 'Пожалуйста, подождите, идет загрузка',
                    allowOutsideClick: false,
                    showConfirmButton: false,
                    willOpen: () => {
                        Swal.showLoading();
                    }
                });
                
                // Submit the form
                uploadForm.submit();
            }
        }
    }
    
    // Handle file selection
    if (fileInput) {
        fileInput.addEventListener('change', handleFiles, false);
        
        function handleFiles(e) {
            if (e.target.files && e.target.files.length) {
                // Show loader
                Swal.fire({
                    title: 'Загрузка документа...',
                    text: 'Пожалуйста, подождите, идет загрузка',
                    allowOutsideClick: false,
                    showConfirmButton: false,
                    willOpen: () => {
                        Swal.showLoading();
                    }
                });
                
                // Submit the form
                uploadForm.submit();
            }
        }
    }
    
    // Document search functionality
    const searchInput = document.getElementById('document-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const documentCards = document.querySelectorAll('.document-card');
            
            documentCards.forEach(card => {
                const title = card.querySelector('.document-title').textContent.toLowerCase();
                const parent = card.closest('.col-lg-4, .col-md-6');
                
                if (title.includes(searchTerm)) {
                    parent.style.display = '';
                } else {
                    parent.style.display = 'none';
                }
            });
        });
    }
    
    // Scroll animations for document cards
    const animateOnScroll = function() {
        const documentCards = document.querySelectorAll('.document-card');
        
        documentCards.forEach(card => {
            const cardPosition = card.getBoundingClientRect();
            
            // If card is in viewport
            if (cardPosition.top < window.innerHeight && cardPosition.bottom >= 0) {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    };
    
    // Initialize card animations
    document.querySelectorAll('.document-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
    
    // Run animation on load and scroll
    window.addEventListener('load', animateOnScroll);
    window.addEventListener('scroll', animateOnScroll);

    // Handle document deletion with SweetAlert2 confirmation
    const deleteButtons = document.querySelectorAll('.delete-document');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent triggering the document preview
            
            const documentId = this.dataset.documentId;
            
            Swal.fire({
                title: 'Удаление документа',
                text: 'Вы уверены, что хотите удалить этот документ? Это действие нельзя отменить.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Да, удалить!',
                cancelButtonText: 'Отмена'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show loading state
                    Swal.fire({
                        title: 'Удаление...',
                        text: 'Пожалуйста, подождите, идет удаление документа',
                        allowOutsideClick: false,
                        showConfirmButton: false,
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
                            Swal.fire({
                                icon: 'success',
                                title: 'Удалено!',
                                text: 'Документ успешно удален',
                                showConfirmButton: false,
                                timer: 1500
                            }).then(() => {
                                // Remove the document card from the UI
                                const documentCard = document.querySelector(`.document-card[data-document-id="${documentId}"]`);
                                if (documentCard) {
                                    const parentCol = documentCard.closest('.col-lg-4, .col-md-6');
                                    if (parentCol) {
                                        parentCol.remove();
                                        
                                        // If no documents left, show empty state
                                        if (document.querySelectorAll('.document-card').length === 0) {
                                            const emptyState = `
                                                <div class="col-12">
                                                    <div class="empty-state">
                                                        <i class="fas fa-file-upload empty-state-icon pulse-animation"></i>
                                                        <h3 class="empty-state-title">No documents yet</h3>
                                                        <p class="text-muted">Upload your first document to get started with AI-powered search</p>
                                                        <button class="btn btn-primary mt-3" id="empty-upload-btn">
                                                            <i class="fas fa-upload me-1"></i> Upload Document
                                                        </button>
                                                    </div>
                                                </div>
                                            `;
                                            document.getElementById('documents-container').innerHTML = emptyState;
                                            
                                            // Reattach event listener to the new button
                                            const newEmptyBtn = document.getElementById('empty-upload-btn');
                                            if (newEmptyBtn) {
                                                newEmptyBtn.addEventListener('click', function() {
                                                    const dropZone = document.getElementById('drop-zone');
                                                    dropZone.scrollIntoView({ behavior: 'smooth' });
                                                    setTimeout(() => {
                                                        dropZone.classList.add('dragover');
                                                        setTimeout(() => {
                                                            dropZone.classList.remove('dragover');
                                                        }, 1500);
                                                    }, 500);
                                                });
                                            }
                                        }
                                    }
                                }
                            });
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Ошибка',
                                text: data.error || 'Failed to delete document'
                            });
                        }
                    })
                    .catch(error => {
                        Swal.fire({
                            icon: 'error',
                            title: 'Ошибка',
                            text: 'An error occurred while deleting the document'
                        });
                    });
                }
            });
        });
    });
});
