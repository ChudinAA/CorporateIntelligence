document.addEventListener('DOMContentLoaded', function() {
    // Function to setup chat deletion handlers
    function setupChatDeletionHandlers() {
        document.querySelectorAll('.chat-delete-btn').forEach(button => {
            // Remove existing event listeners to prevent duplicates
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                const chatId = this.getAttribute('data-chat-id');
                
                // Show confirmation dialog with smoother animation
                Swal.fire({
                    title: 'Delete Chat',
                    text: 'Are you sure you want to delete this chat? This action cannot be undone.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#dc3545',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Yes, delete it',
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
                        // Show loading state with smooth animation
                        Swal.fire({
                            title: 'Deleting...',
                            text: 'Please wait while we delete the chat.',
                            allowOutsideClick: false,
                            allowEscapeKey: false,
                            showConfirmButton: false,
                            showClass: {
                                popup: 'swal2-show',
                                backdrop: 'swal2-backdrop-show'
                            },
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
                                    // Remove the chat card from the UI with smooth animation
                                    const chatCard = newButton.closest('.card');
                                    chatCard.style.transition = 'all 0.5s ease';
                                    chatCard.style.opacity = '0';
                                    chatCard.style.transform = 'translateY(-20px)';
                                    
                                    setTimeout(() => {
                                        chatCard.remove();
                                        // Update chat counter
                                        updateChatCounter();
                                        // If no cards left, show empty state
                                        checkEmptyState();
                                    }, 500);
                                });
                            } else {
                                // Error
                                Swal.fire({
                                    title: 'Error!',
                                    text: data.message || 'Failed to delete chat.',
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
    }
    
    // Function to check if there are no chats left and display empty state
    function checkEmptyState() {
        const remainingCards = document.querySelectorAll('.chat-list .card:not([style*="opacity: 0"])');
        const chatList = document.querySelector('.chat-list');
        const existingEmptyState = document.querySelector('.chat-list .alert');
        
        if (remainingCards.length === 0 && chatList && !existingEmptyState) {
            const emptyState = document.createElement('div');
            emptyState.className = 'alert alert-info mt-4';
            emptyState.style.opacity = '0';
            emptyState.style.transform = 'translateY(20px)';
            emptyState.style.transition = 'all 0.5s ease';
            emptyState.innerHTML = 'No chat sessions found. <a href="/new-chat" class="alert-link">Start a new chat</a>.';
            chatList.appendChild(emptyState);
            
            // Trigger animation
            setTimeout(() => {
                emptyState.style.opacity = '1';
                emptyState.style.transform = 'translateY(0)';
            }, 50);
        }
    }
    
    // Function to update the chat counter in the stats
    function updateChatCounter() {
        const statValue = document.querySelector('.stat-item:nth-child(2) .stat-value');
        if (statValue) {
            const currentCount = parseInt(statValue.textContent);
            if (!isNaN(currentCount) && currentCount > 0) {
                statValue.textContent = (currentCount - 1).toString();
            }
        }
    }
    
    // Set up the initial handlers
    setupChatDeletionHandlers();
});
