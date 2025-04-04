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
    }

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
            uploadForm.submit();
        }
    }

    // Document search functionality
    const searchInput = document.getElementById('document-search');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const documentCards = document.querySelectorAll('.document-card');

            documentCards.forEach(card => {
                const title = card.querySelector('.document-title').textContent.toLowerCase();
                if (title.includes(searchTerm)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

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
});