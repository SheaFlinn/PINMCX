// iOS Add to Home Screen popup functionality
const iOSInstallPopup = {
    init() {
        // Only show on iOS devices
        if (!this.isIOS()) return;

        // Create popup element
        const popup = document.createElement('div');
        popup.id = 'ios-install-popup';
        popup.innerHTML = `
            <div class="ios-install-content">
                <h3>Add MCX Points to Home Screen</h3>
                <p>To add MCX Points to your home screen:</p>
                <ol>
                    <li>Tap the <i class="bi bi-share"></i> button</li>
                    <li>Tap "Add to Home Screen"</li>
                </ol>
                <button id="ios-install-close" class="btn btn-primary">Got it!</button>
            </div>
        `;
        document.body.appendChild(popup);

        // Add event listener for close button
        const closeButton = document.getElementById('ios-install-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.hide();
            });
        }

        // Show popup after a delay
        setTimeout(() => this.show(), 2000);
    },

    isIOS() {
        return /iPad|iPhone|iPod/i.test(navigator.userAgent) &&
               !window.MSStream;
    },

    show() {
        const popup = document.getElementById('ios-install-popup');
        if (popup) {
            popup.style.display = 'block';
        }
    },

    hide() {
        const popup = document.getElementById('ios-install-popup');
        if (popup) {
            popup.style.display = 'none';
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    iOSInstallPopup.init();
});
