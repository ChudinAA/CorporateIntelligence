document.addEventListener('DOMContentLoaded', function() {
    // Handle chat deletion
    document.querySelectorAll('.chat-delete-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const chatId = this.getAttribute('data-chat-id');
            
            // Show confirmation dialog
            Swal.fire({
                title: 'Delete Chat',
                text: 'Are you sure you want to delete this chat? This action cannot be undone.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Yes, delete it',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show loading state
                    Swal.fire({
                        title: 'Deleting...',
                        text: 'Please wait while we delete the chat.',
                        allowOutsideClick: false,
                        allowEscapeKey: false,
                        showConfirmButton: false,
                        didOpen: () => {
                            Swal.showLoading();
                        }
                    });
                    
                    // Send delete request
                    fetch(`/delete-chat/${chatId}`, {
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
                                text: 'Chat has been deleted successfully.',
                                icon: 'success',
                                timer: 1500,
                                showConfirmButton: false
                            }).then(() => {
                                // Remove the chat card from the UI
                                const chatCard = button.closest('.card');
                                chatCard.style.opacity = '0';
                                setTimeout(() => {
                                    chatCard.style.display = 'none';
                                    // If no cards left, show empty state
                                    const remainingCards = document.querySelectorAll('.chat-list .card');
                                    if (remainingCards.length === 0) {
                                        const emptyState = document.createElement('div');
                                        emptyState.className = 'alert alert-info mt-4';
                                        emptyState.innerHTML = 'No chat sessions found. <a href="/new-chat" class="alert-link">Start a new chat</a>.';
                                        document.querySelector('.chat-list').appendChild(emptyState);
                                    }
                                }, 500);
                            });
                        } else {
                            // Error
                            Swal.fire({
                                title: 'Error!',
                                text: data.message || 'Failed to delete chat.',
                                icon: 'error'
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        Swal.fire({
                            title: 'Error!',
                            text: 'An unexpected error occurred.',
                            icon: 'error'
                        });
                    });
                }
            });
        });
    });
});
