document.addEventListener('DOMContentLoaded', function() {
    initializeDocumentUpload();
    initializeDocumentDeletion();
});

function initializeDocumentUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('document');
    const uploadForm = document.getElementById('upload-form');

    if (!dropZone || !fileInput || !uploadForm) return;

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

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    dropZone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFiles, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles({ target: { files: files } });
    }

    function handleFiles(e) {
        if (e.target.files.length) {
            // Show loading state
            showUploadingState(dropZone);

            // Submit the form
            uploadForm.submit();
        }
    }

    // Create a loading overlay for the upload zone
    function showUploadingState(element) {
        // Store original content
        const originalContent = element.innerHTML;

        // Create loading overlay
        element.innerHTML = `
            <div class="upload-loading">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Uploading and processing document...</p>
                <p class="small text-muted">This may take a moment depending on the file size</p>
            </div>
        `;

        element.classList.add('uploading');

        // Disable further uploads
        element.style.pointerEvents = 'none';
    }

    // Check if we've just returned from an upload (flash message exists)
    const flashMessage = document.querySelector('.alert');
    if (flashMessage && (flashMessage.textContent.includes('uploaded') || flashMessage.textContent.includes('Error'))) {
        // Reset the upload zone styling
        dropZone.classList.remove('uploading');
        dropZone.style.pointerEvents = '';
    }
}


function initializeDocumentDeletion() {
    // Handle document deletion
    const deleteButtons = document.querySelectorAll('.delete-document');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const documentId = this.dataset.documentId;

            Swal.fire({
                title: 'Delete Document',
                text: 'Are you sure you want to delete this document?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Delete',
                showClass: {
                    popup: 'animate__animated animate__fadeIn'
                },
                hideClass: {
                    popup: 'animate__animated animate__fadeOut'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/documents/delete/${documentId}`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const card = button.closest('.document-card').parentElement;
                            card.style.transform = 'scale(0.8)';
                            card.style.opacity = '0';
                            setTimeout(() => {
                                card.remove();
                                // Re-arrange remaining cards
                                const container = document.querySelector('.row');
                                const cards = container.querySelectorAll('.col-lg-4');
                                cards.forEach(card => {
                                    card.style.transition = 'all 0.3s ease';
                                });
                            }, 300);

                            Swal.fire({
                                title: 'Deleted!',
                                text: 'Document has been deleted.',
                                icon: 'success',
                                timer: 1500,
                                showConfirmButton: false
                            });
                        }
                    });
                }
            });
        });
    });
}

// Document preview in modal
const previewButtons = document.querySelectorAll('.document-preview');
previewButtons.forEach(button => {
    button.addEventListener('click', function(e) {
        e.preventDefault();
        const documentId = this.dataset.documentId;

        Swal.fire({
            title: 'Loading Preview...',
            html: '<div class="text-center"><div class="spinner-border text-primary"></div></div>',
            showConfirmButton: false,
            showClass: {
                popup: 'animate__animated animate__fadeIn'
            }
        });

        fetch(`/documents/preview/${documentId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let formattedContent = data.content;
                    if (data.file_type === 'txt') {
                        formattedContent = data.content.replace(/\n/g, '<br>');
                    }

                    Swal.fire({
                        title: data.filename,
                        html: `
                            <div class="small text-muted mb-2">
                                ${data.file_type.toUpperCase()} · ${Math.round(data.file_size / 1024)} KB
                            </div>
                            <div class="preview-content bg-white p-3 rounded border">
                                ${formattedContent}
                            </div>
                        `,
                        width: '800px',
                        showClass: {
                            popup: 'animate__animated animate__fadeIn'
                        },
                        hideClass: {
                            popup: 'animate__animated animate__fadeOut'
                        }
                    });
                }
            });
    });
});