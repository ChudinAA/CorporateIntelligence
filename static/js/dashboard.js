document.addEventListener('DOMContentLoaded', function() {
    // Setup all delete buttons
    setupChatDeletionHandlers();

    // Setup conversation preview handlers
    setupConversationHandlers();

    // Document preview handlers
    setupDocumentPreviewHandlers();

    // Setup chat message handling
    const socket = io();
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const chatContainer = document.getElementById('chat-container');
    const sessionIdInput = document.getElementById('session-id-input');
    const typingIndicator = document.getElementById('typing-indicator');

    // Check for URL parameters for a session ID
    const urlParams = new URLSearchParams(window.location.search);
    const sessionIdParam = urlParams.get('session_id');

    // Set current session ID from URL parameter if available
    if (sessionIdParam) {
        document.getElementById('session-id-input').value = sessionIdParam;
        loadChatMessages(sessionIdParam);
    } else {
        // Clear existing session ID to ensure new chats start properly
        document.getElementById('session-id-input').value = '';
        document.getElementById('chat-container').innerHTML = '';
    }


    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (!message) return;

            let sessionId = sessionIdInput.value;

            // If no session ID, create one first
            if (!sessionId) {
                // Create a new session
                fetch('/chat/new_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        sessionIdInput.value = data.session_id;
                        sendMessage(message, data.session_id);
                    } else {
                        console.error('Failed to create new session');
                        addErrorMessage('Failed to create new chat session. Please try again.');
                    }
                })
                .catch(err => {
                    console.error('Error creating session:', err);
                    addErrorMessage('Error creating chat session. Please try again.');
                });
            } else {
                sendMessage(message, sessionId);
            }
        });
    }

    function sendMessage(message, sessionId) {
        // Add user message to chat
        addChatMessage(message, true);
        messageInput.value = '';

        // Show typing indicator
        if (typingIndicator) {
            typingIndicator.style.display = 'flex';
        }

        // Emit message via Socket.IO
        socket.emit('send_message', {
            message: message,
            session_id: sessionId
        });
    }

    socket.on('connect', function() {
        console.log('Connected to Socket.IO server');
    });

    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        addErrorMessage('Unable to connect to the server. Please refresh the page.');
    });

    socket.on('receive_message', function(data) {
        // Hide typing indicator
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
        addChatMessage(data.message, false);
    });

    socket.on('error', function(data) {
        // Hide typing indicator
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
        addErrorMessage(data.message || 'An error occurred during processing.');
    });

    function addChatMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'} animate__animated animate__fadeInUp`;

        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });

        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">
                ${timeString}
                <i class="fas fa-${isUser ? 'user' : 'robot'} ms-1"></i>
            </div>
        `;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function addErrorMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message animate__animated animate__fadeInUp';

        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });

        messageDiv.innerHTML = `
            <div class="message-content text-danger">
                <i class="fas fa-exclamation-triangle me-1"></i> ${message}
            </div>
            <div class="message-time">
                ${timeString}
                <i class="fas fa-robot ms-1"></i>
            </div>
        `;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Function to setup chat deletion handlers
    function setupChatDeletionHandlers() {
        document.querySelectorAll('.chat-delete-btn').forEach(button => {
            // Remove existing event listeners to prevent duplicates
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);

            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
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
                                    // Find and remove the specific chat card
                                    const chatCard = newButton.closest('.col-md-6');
                                    if (chatCard) {
                                        chatCard.style.transition = 'all 0.4s ease';
                                        chatCard.style.opacity = '0';
                                        chatCard.style.transform = 'translateY(-15px)';

                                        setTimeout(() => {
                                            chatCard.remove();
                                            updateChatCounter();

                                            // Check if there are no chat cards left
                                            const remainingCards = document.querySelectorAll('.chat-section .col-md-6:not([style*="opacity: 0"])');
                                            // If only the "new chat" card is left (which is always there)
                                            if (remainingCards.length <= 1) {
                                                // Add empty state
                                                const chatSection = document.querySelector('.chat-section .row');
                                                const existingEmptyState = document.querySelector('.chat-section .empty-state');

                                                if (chatSection && !existingEmptyState) {
                                                    // Clear the section
                                                    chatSection.innerHTML = '';

                                                    // Add empty state
                                                    const emptyStateHtml = `
                                                        <div class="col-12">
                                                            <div class="empty-state">
                                                                <i class="fas fa-comments empty-icon"></i>
                                                                <h3 class="empty-title">No conversations yet</h3>
                                                                <p class="empty-description">Start a new conversation to interact with the AI assistant.</p>
                                                                <a href="/new-chat" class="btn btn-primary">
                                                                    <i class="fas fa-plus me-2"></i>Start New Chat
                                                                </a>
                                                            </div>
                                                        </div>
                                                    `;
                                                    chatSection.innerHTML = emptyStateHtml;
                                                }
                                            }
                                        }, 400);
                                    }
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

    // Function to setup document preview handlers
    function setupDocumentPreviewHandlers() {
        document.querySelectorAll('.document-item.document-preview').forEach(item => {
            item.addEventListener('click', function(e) {
                // Don't handle click if it was on the delete button
                if (e.target.closest('.doc-delete-btn')) {
                    return;
                }

                const documentId = this.dataset.documentId;
                const previewArea = document.querySelector(`.document-preview-area[data-document-id="${documentId}"]`);

                if (previewArea) {
                    // Toggle display
                    if (previewArea.style.display === 'none' || !previewArea.style.display) {
                        // Close any other open previews
                        document.querySelectorAll('.document-preview-area').forEach(area => {
                            if (area !== previewArea) {
                                area.style.display = 'none';
                            }
                        });

                        // Show loading in preview area
                        previewArea.style.display = 'block';
                        previewArea.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm text-primary"></div> Loading preview...</div>';

                        // Scroll to make preview visible if needed
                        setTimeout(() => {
                            previewArea.scrollIntoView({behavior: 'smooth', block: 'nearest'});
                        }, 100);

                        // Fetch document content
                        fetch(`/documents/preview/${documentId}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    // Format content based on file type
                                    let formattedContent = data.content;

                                    // Add line breaks for text content
                                    if (data.file_type === 'txt') {
                                        formattedContent = data.content.replace(/\n/g, '<br>');
                                    }

                                    // Update preview area
                                    previewArea.innerHTML = `
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <h6 class="mb-0"><i class="fas fa-file me-2"></i>${data.filename}</h6>
                                            <button class="btn btn-sm btn-outline-secondary close-preview">
                                                <i class="fas fa-times"></i>
                                            </button>
                                        </div>
                                        <div class="small text-muted mb-2">
                                            ${data.file_type.toUpperCase()} · ${Math.round(data.file_size / 1024)} KB
                                        </div>
                                        <div class="preview-content bg-white p-2 rounded border">
                                            ${formattedContent}
                                        </div>
                                    `;

                                    // Add close button functionality
                                    const closeBtn = previewArea.querySelector('.close-preview');
                                    if (closeBtn) {
                                        closeBtn.addEventListener('click', function() {
                                            previewArea.style.display = 'none';
                                        });
                                    }
                                } else {
                                    previewArea.innerHTML = `
                                        <div class="alert alert-danger">
                                            <i class="fas fa-exclamation-triangle me-2"></i>
                                            ${data.message || 'Failed to load document preview.'}
                                        </div>
                                    `;
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                previewArea.innerHTML = `
                                    <div class="alert alert-danger">
                                        <i class="fas fa-exclamation-triangle me-2"></i>
                                        An unexpected error occurred while loading the preview.
                                    </div>
                                `;
                            });
                    } else {
                        // Hide preview
                        previewArea.style.display = 'none';
                    }
                }
            });
        });
    }

    // Function to update the chat counter in the stats
    function updateChatCounter() {
        const statValue = document.querySelector('.welcome-stats .stat-item:nth-child(2) .stat-value');
        if (statValue) {
            const currentCount = parseInt(statValue.textContent, 10);
            if (!isNaN(currentCount) && currentCount > 0) {
                statValue.textContent = (currentCount - 1).toString();

                // Update the last activity date if needed
                const lastActivityStat = document.querySelector('.welcome-stats .stat-item:nth-child(3) .stat-value');
                if (lastActivityStat) {
                    const today = new Date();
                    const formattedDate = formatDate(today);
                    lastActivityStat.textContent = formattedDate;
                }
            }
        }
    }

    // Helper function to format date
    function formatDate(date) {
        const day = date.getDate().toString().padStart(2, '0');
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const month = monthNames[date.getMonth()];
        return `${day} ${month}`;
    }

    // Setup new chat button handler
    const newChatBtn = document.createElement('button');
    newChatBtn.className = 'new-chat-btn';
    newChatBtn.innerHTML = '<i class="fas fa-plus"></i> New Chat';

    const chatSection = document.querySelector('.chat-section .card-body');
    if (chatSection) {
        chatSection.insertBefore(newChatBtn, chatSection.firstChild);
    }

    newChatBtn.addEventListener('click', function() {
        // Create a new session first
        fetch('/chat/new_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear chat container
                const chatContainer = document.getElementById('chat-container');
                chatContainer.innerHTML = '<div class="text-center py-5"><i class="fas fa-comments fa-4x mb-3 text-muted"></i><h4>Start a conversation</h4><p>Ask any question about your documents.</p></div>';

                // Set the new session ID
                document.getElementById('session-id-input').value = data.session_id;

                // Clear any active selection in Recent Conversations
                document.querySelectorAll('.conversation-preview.active').forEach(item => {
                    item.classList.remove('active');
                });

                // Setup message input focus
                const messageInput = document.getElementById('message-input');
                if (messageInput) {
                    messageInput.focus();
                }
            } else {
                console.error('Failed to create new session');
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Failed to create new chat session. Please try again.'
                });
            }
        })
        .catch(err => {
            console.error('Error creating session:', err);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Error creating chat session. Please try again.'
            });
        });
    });


    // Function to setup conversation handlers
    function setupConversationHandlers() {
        document.querySelectorAll('.conversation-preview').forEach(item => {
            item.addEventListener('click', function(e) {
                // Don't handle click if it was on the delete button
                if (e.target.closest('.chat-delete-btn')) {
                    return;
                }

                const sessionId = this.dataset.sessionId;

                // Show loading in chat container
                const chatContainer = document.getElementById('chat-container');
                chatContainer.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm text-primary"></div> Loading messages...</div>';

                // Update hidden session ID input
                document.getElementById('session-id-input').value = sessionId;

                // Fetch conversation messages
                fetch(`/chat/messages/${sessionId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Clear and update chat container
                            chatContainer.innerHTML = '';

                            // Add messages to chat container
                            data.messages.forEach(message => {
                                const messageDiv = document.createElement('div');
                                messageDiv.className = `message ${message.is_user ? 'user-message' : 'ai-message'} animate__animated animate__fadeInUp`;
                                messageDiv.innerHTML = `
                                    <div class="message-content">${message.content}</div>
                                    <div class="message-time">
                                        ${message.timestamp}
                                        <i class="fas ${message.is_user ? 'fa-user' : 'fa-robot'} ms-1"></i>
                                    </div>
                                `;
                                chatContainer.appendChild(messageDiv);
                            });

                            // Scroll to bottom
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                        } else {
                            chatContainer.innerHTML = `
                                <div class="alert alert-danger m-3">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    ${data.message || 'Failed to load conversation messages.'}
                                </div>
                            `;
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        chatContainer.innerHTML = `
                            <div class="alert alert-danger m-3">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                An unexpected error occurred while loading the messages.
                            </div>
                        `;
                    });
            });
        });
    }

// Handle conversation click to load messages
    const conversationItems = document.querySelectorAll('.conversation-preview');
    conversationItems.forEach(item => {
        item.addEventListener('click', function() {
            const sessionId = this.getAttribute('data-session-id');
            if (!sessionId) return;

            // Clear previous messages and set new session ID
            document.getElementById('session-id-input').value = sessionId;
            document.getElementById('chat-container').innerHTML = '';

            // Add loading indicator
            const loadingIndicator = document.createElement('div');
            loadingIndicator.className = 'typing-animation';
            loadingIndicator.innerHTML = `
                <div class="typing-indicator">
                    <div class="plasma-bubble bubble-1"></div>
                    <div class="plasma-bubble bubble-2"></div>
                    <div class="plasma-bubble bubble-3"></div>
                </div>`;
            document.getElementById('chat-container').appendChild(loadingIndicator);

            // Load messages with error handling
            loadChatMessages(sessionId);
        });
    });

// Function to load chat messages
    function loadChatMessages(sessionId) {
        // Remove any loading indicators
        const loadingIndicators = document.querySelectorAll('.typing-animation');
        loadingIndicators.forEach(indicator => indicator.remove());

        fetch(`/chat/messages/${sessionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const chatContainer = document.getElementById('chat-container');
                    chatContainer.innerHTML = '';

                    if (data.messages && data.messages.length > 0) {
                        data.messages.forEach(message => {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = `message ${message.is_user ? 'user-message' : 'ai-message'} animate__animated animate__fadeInUp`;

                            messageDiv.innerHTML = `
                                <div class="message-content">${message.content}</div>
                                <div class="message-time">
                                    ${message.timestamp}
                                    <i class="${message.is_user ? 'fas fa-user' : 'fas fa-robot'} ms-1"></i>
                                </div>
                            `;

                            chatContainer.appendChild(messageDiv);
                        });
                    } else {
                        // If no messages, show welcome message
                        const welcomeDiv = document.createElement('div');
                        welcomeDiv.className = 'message ai-message animate__animated animate__fadeInUp';
                        welcomeDiv.innerHTML = `
                            <div class="message-content">Привет! Я готов помочь с вашими вопросами.</div>
                            <div class="message-time">
                                Сейчас
                                <i class="fas fa-robot ms-1"></i>
                            </div>
                        `;
                        chatContainer.appendChild(welcomeDiv);
                    }

                    // Scroll to the bottom
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                } else {
                    console.error('Error loading messages:', data.message);
                    const chatContainer = document.getElementById('chat-container');
                    chatContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Произошла ошибка при загрузке сообщений. Попробуйте обновить страницу.
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const chatContainer = document.getElementById('chat-container');
                chatContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Произошла ошибка при загрузке сообщений. Попробуйте обновить страницу.
                    </div>
                `;
            });
    }

});