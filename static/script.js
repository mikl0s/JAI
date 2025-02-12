document.addEventListener('DOMContentLoaded', () => {
    // Fetch and display judges
    fetch('/judges')
        .then(response => response.json())
        .then(data => {
            // Display all judges
            displayJudges(data.judges, 'undecided-list');
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
                <h3>${judge.name}</h3>
                <div class="vote-counts">
                    <span class="corrupt-count">${judge.corrupt_votes} Corrupt</span>
                    <span class="not-corrupt-count">${judge.not_corrupt_votes} Not Corrupt</span>
                </div>
            </div>
            <div class="card-content">
                <p data-position title="${judge.job_position}"><strong>Position:</strong> ${judge.job_position}</p>
                <p data-ruling title="${judge.ruling}"><strong>Ruling:</strong> ${judge.ruling}</p>
                <div class="card-links">
                    <a href="${judge.link}" target="_blank" class="link-button">View Ruling</a>
                    ${judge.x_link ? `<a href="${judge.x_link}" target="_blank" class="link-button">View on X</a>` : ''}
                </div>
                <div class="vote-buttons">
                    <button class="vote-button corrupt" data-judge-id="${judge.id}">Corrupt</button>
                    <button class="vote-button not-corrupt" data-judge-id="${judge.id}">Not Corrupt</button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });

    // Add event listeners to vote buttons
    document.querySelectorAll('.vote-button').forEach(button => {
        button.addEventListener('click', handleVote);
    });
}

function handleVote(event) {
    const button = event.target;
    const judgeId = button.dataset.judgeId;
    const voteType = button.classList.contains('corrupt') ? 'corrupt' : 'not_corrupt';
    
    // Generate basic fingerprint (for demo purposes)
    const fingerprint = Math.random().toString(36).substring(2, 15);
    
    fetch(`/vote/${judgeId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            vote_type: voteType,
            fingerprint: fingerprint
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI with new vote counts
            fetch('/judges')
                .then(response => response.json())
                .then(data => {
                    displayJudges(data.judges, 'undecided-list');
                });
        } else {
            alert(data.error || 'Error submitting vote');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error submitting vote. Please try again.');
    });
}