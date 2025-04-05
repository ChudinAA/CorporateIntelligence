
document.addEventListener('DOMContentLoaded', function() {
    const socket = io(window.location.origin, socketIOConfig);
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const chatContainer = document.getElementById('chat-container');
    const typingIndicator = document.getElementById('typing-indicator');
    const sessionId = document.getElementById('session-id-input')?.value || window.sessionId;
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('document');
    const uploadForm = document.getElementById('upload-form');

    // Drag and drop functionality
    if (dropZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, function() {
                dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, function() {
                dropZone.classList.remove('dragover');
            });
        });

        dropZone.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            if (files.length) {
                fileInput.files = files;
                uploadForm.submit();
            }
        });

        dropZone.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                uploadForm.submit();
            }
        });
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    scrollToBottom();

    socket.on('connect', function() {
        console.log('Connected to Socket.IO server');
        const errorElements = document.querySelectorAll('.message.ai-message .text-danger');
        errorElements.forEach(element => {
            if (element.textContent.includes('Unable to connect')) {
                element.closest('.message.ai-message').remove();
            }
        });
    });

    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        addErrorMessage('Unable to connect to the server. Please refresh the page.');
    });

    socket.on('receive_message', function(data) {
        typingIndicator.style.display = 'none';
        addAIMessage(data.message);
        scrollToBottom();
    });

    socket.on('error', function(data) {
        typingIndicator.style.display = 'none';
        addErrorMessage(data.message || 'An error occurred.');
        scrollToBottom();
    });

    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        const currentSessionId = document.getElementById('session-id-input').value;

        // Create a new session if one doesn't exist
        if (!currentSessionId) {
            // Create a new session first, then send the message
            fetch('/chat/new_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('session-id-input').value = data.session_id;
                    
                    // Now send the message with the new session ID
                    sendMessageToServer(message, data.session_id);
                } else {
                    console.error('Failed to create new session');
                    addErrorMessage('Failed to create new chat session. Please refresh the page and try again.');
                }
            })
            .catch(err => {
                console.error('Error creating session:', err);
                addErrorMessage('Error creating chat session. Please try again.');
            });
        } else {
            // Send message with existing session ID
            sendMessageToServer(message, currentSessionId);
        }
    });
    
    function sendMessageToServer(message, sessionId) {
        addUserMessage(message);
        messageInput.value = '';
        typingIndicator.style.display = 'block';
        scrollToBottom();

        socket.emit('send_message', {
            message: message,
            session_id: sessionId
        });
    }

    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message animate__animated animate__fadeInUp';

        const now = new Date();
        const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');

        messageElement.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">
                ${timeString}
                <i class="fas fa-user ms-1"></i>
            </div>
        `;

        chatContainer.appendChild(messageElement);
        scrollToBottom();
    }

    function addAIMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message ai-message animate__animated animate__fadeInUp';

        const now = new Date();
        const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');

        messageElement.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">
                ${timeString}
                <i class="fas fa-robot ms-1"></i>
            </div>
        `;

        chatContainer.appendChild(messageElement);
        scrollToBottom();
    }

    function addErrorMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message ai-message animate__animated animate__fadeInUp';

        const now = new Date();
        const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');

        messageElement.innerHTML = `
            <div class="message-content text-danger">
                <i class="fas fa-exclamation-triangle me-1"></i> ${message}
            </div>
            <div class="message-time">
                ${timeString}
                <i class="fas fa-robot ms-1"></i>
            </div>
        `;

        chatContainer.appendChild(messageElement);
    }

    messageInput.addEventListener('focus', function() {
        this.parentElement.classList.add('shadow-sm');
    });
    
    messageInput.addEventListener('blur', function() {
        this.parentElement.classList.remove('shadow-sm');
    });
});
