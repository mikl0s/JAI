import { showNotification, calculateHMAC, calculateProofOfWork, fpPromise, hmacSecretKey } from './utils.js';

// Handle form submission
export function initializeForm(modal, form) {
    form.onsubmit = async (e) => {
        e.preventDefault();

        const formData = {
            name: document.getElementById('name').value,
            position: document.getElementById('position').value,
            ruling: document.getElementById('ruling').value,
            link: document.getElementById('link').value,
            x_link: document.getElementById('x_link').value || null
        };

        // Generate fingerprint
        const fp = await fpPromise;
        const result = await fp.get();
        const fingerprint = result.visitorId;

        // Calculate proof of work
        const difficulty = 4; // Example difficulty
        const { nonce, hash } = await calculateProofOfWork(difficulty);
        formData.proofOfWork = { nonce, hash }; // Add proof of work to form data


        const timestamp = Math.floor(Date.now() / 1000);
        const path = '/submit-judge';
        const body = JSON.stringify(formData);
        const signature = await calculateHMAC(hmacSecretKey, 'POST', path, body, timestamp);


        fetch('/submit-judge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-HMAC-Timestamp': timestamp,
                'X-HMAC-Signature': signature
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                //alert('Judge submission successful! It will be reviewed by an administrator.');
                showNotification('Judge submission successful! It will be reviewed by an administrator.', 5000);
                modal.style.display = 'none';
                form.reset();
            } else {
                alert('Error submitting judge: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error submitting judge. Please try again.');
        });
    };
}
