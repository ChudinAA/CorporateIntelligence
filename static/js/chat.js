// Chat functionality implementation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO with configuration
    const socket = io(window.location.origin, socketIOConfig);
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const chatContainer = document.getElementById('chat-container');
    const typingIndicator = document.getElementById('typing-indicator');
    const sessionId = document.getElementById('session-id-input') ? 
                     document.getElementById('session-id-input').value : 
                     window.sessionId; // Fallback to global variable if input not found

    // Scroll to bottom of chat container
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Initially scroll to bottom
    scrollToBottom();

    // Connect to Socket.IO
    socket.on('connect', function() {
        console.log('Connected to Socket.IO server');
        // Remove any error messages about connection when connected
        const errorElements = document.querySelectorAll('.message.ai-message .text-danger');
        errorElements.forEach(element => {
            if (element.textContent.includes('Unable to connect')) {
                element.closest('.message.ai-message').remove();
            }
        });
    });

    // Handle connection error
    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        addErrorMessage('Unable to connect to the server. Please refresh the page.');
    });

    // Handle incoming messages
    socket.on('receive_message', function(data) {
        // Hide typing indicator
        typingIndicator.style.display = 'none';

        // Add AI message to chat
        const message = data.message;
        const sources = data.sources || [];

        addAIMessage(message, sources);
        scrollToBottom();
    });

    // Handle errors
    socket.on('error', function(data) {
        typingIndicator.style.display = 'none';
        addErrorMessage(data.message || 'An error occurred.');
        scrollToBottom();
    });

    // Send message on form submit
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addUserMessage(message);

        // Clear input
        messageInput.value = '';

        // Show typing indicator
        typingIndicator.style.display = 'block';
        scrollToBottom();

        // Send message to server
        socket.emit('send_message', {
            message: message,
            session_id: sessionId
        });
    });

    // Add user message to chat
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message new-message';

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

    // Add AI message to chat
    function addAIMessage(message, sources = []) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message ai-message new-message';

        const now = new Date();
        const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');
        
        // Remove sources section as requested

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

    // Add error message to chat
    function addErrorMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message ai-message new-message';

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
    
    // Add some interactivity to the message input
    messageInput.addEventListener('focus', function() {
        this.parentElement.classList.add('shadow-sm');
    });
    
    messageInput.addEventListener('blur', function() {
        this.parentElement.classList.remove('shadow-sm');
    });
});
