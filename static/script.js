document.addEventListener('DOMContentLoaded', () => {
    // Fetch and display judges
    fetch('/judges')
        .then(response => response.json())
        .then(data => {
            displayJudges(data.confirmed, 'confirmed-list');
            displayJudges(data.undecided, 'undecided-list');
        })
        .catch(error => console.error('Error fetching data:', error));

    // Modal elements
    const modal = document.getElementById('submit-modal');
    const submitBtn = document.getElementById('submit-judge-btn');
    const closeBtn = document.querySelector('.close');
    const form = document.getElementById('submit-judge-form');

    // Open modal
    submitBtn.onclick = () => {
        modal.style.display = 'block';
    };

    // Close modal
    closeBtn.onclick = () => {
        modal.style.display = 'none';
        form.reset();
    };

    // Close modal when clicking outside
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
            form.reset();
        }
    };

    // Handle form submission
    form.onsubmit = (e) => {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('name').value,
            position: document.getElementById('position').value,
            ruling: document.getElementById('ruling').value,
            link: document.getElementById('link').value,
            x_link: document.getElementById('x_link').value || null
        };

        fetch('/submit-judge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Judge submission successful! It will be reviewed by an administrator.');
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
});

function displayJudges(judges, elementId) {
    const container = document.getElementById(elementId);
    container.innerHTML = ''; // Clear existing content
    judges.forEach(judge => {
        const card = document.createElement('div');
        card.className = 'judge-card';
        
        // Create card content
        card.innerHTML = `
            <div class="card-header">
                <h3>${judge[1]}</h3>
            </div>
            <div class="card-content">
                <p data-position title="${judge[2]}"><strong>Position:</strong> ${judge[2]}</p>
                <p data-ruling title="${judge[3]}"><strong>Ruling:</strong> ${judge[3]}</p>
                <div class="card-links">
                    <a href="${judge[4]}" target="_blank" class="link-button">View Ruling</a>
                    ${judge[5] ? `<a href="${judge[5]}" target="_blank" class="link-button">View on X</a>` : ''}
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}