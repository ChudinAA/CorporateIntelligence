document.addEventListener('DOMContentLoaded', function() {
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
