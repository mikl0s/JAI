// Modal functionality
export function initializeModals() {
    // Modal elements
    const submitModal = document.getElementById('submit-modal');
    const aboutModal = document.getElementById('about-modal');
    const donateModal = document.getElementById('donate-modal');
    
    const submitBtn = document.getElementById('submit-judge-btn');
    const aboutBtn = document.getElementById('about-jai-btn');
    const donateBtn = document.getElementById('donate-jai-btn');
    
    const closeButtons = document.querySelectorAll('.close');
    const form = document.getElementById('submit-judge-form');

    // Open submit modal
    submitBtn.onclick = () => {
        submitModal.style.display = 'block';
    };

    // Open about modal
    aboutBtn.onclick = () => {
        aboutModal.style.display = 'block';
    };

    // Open donate modal
    donateBtn.onclick = () => {
        donateModal.style.display = 'block';
    };

    // Close modals
    closeButtons.forEach(closeBtn => {
        closeBtn.onclick = () => {
            submitModal.style.display = 'none';
            aboutModal.style.display = 'none';
            donateModal.style.display = 'none';
            if (form) form.reset();
        };
    });

    // Close modals when clicking outside
    window.onclick = (event) => {
        if (event.target === submitModal) {
            submitModal.style.display = 'none';
            if (form) form.reset();
        } else if (event.target === aboutModal) {
            aboutModal.style.display = 'none';
        } else if (event.target === donateModal) {
            donateModal.style.display = 'none';
        }
    };

    // Set up donation option click handlers
    const donationOptions = document.querySelectorAll('.donation-option');
    donationOptions.forEach(option => {
        option.addEventListener('click', () => {
            // For now, these do nothing as mentioned in the requirements
            console.log('Donation option clicked');
        });
    });

    return { modal: submitModal, form };
}
