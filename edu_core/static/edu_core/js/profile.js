// Portfolio\Education_Villa\edu_core\static\edu_core\js\profile.js

document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('.certification img').forEach(image => {
        image.addEventListener('click', () => {
            let modal = document.createElement('div');
            modal.className = 'image-modal';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            modal.style.cursor = 'zoom-out';
            modal.style.zIndex = '1000';
            
            let modalImg = document.createElement('img');
            modalImg.src = image.src;
            modalImg.style.maxWidth = '80%';
            modalImg.style.maxHeight = '80%';
            modalImg.style.margin = 'auto';
            modal.style.animation = 'fadeIn 0.3s';
            
            modal.appendChild(modalImg);
            document.body.appendChild(modal);

            modal.addEventListener('click', () => {
                modal.style.animation = 'fadeOut 0.3s';
                setTimeout(() => modal.remove(), 290);
            });
        });
    });
});

// Optional: Add fadeIn/fadeOut animations in your CSS
