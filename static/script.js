document.addEventListener('DOMContentLoaded', () => {
    const judgeIdToCardMap = {};

    // Fetch and display judges
    function fetchAndDisplayJudges() {
        fetch('/judges')
            .then(response => response.json())
            .then(data => {
                // Clear existing lists
                document.getElementById('confirmed-list').innerHTML = '';
                document.getElementById('undecided-list').innerHTML = '';
                document.getElementById('not-corrupt-list').innerHTML = '';

                // Display judges in appropriate sections
                displayJudges(data.judges);
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    // Initial fetch
    fetchAndDisplayJudges();


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

  function displayJudges(judges) {
    const updatedJudgeIds = new Set();

    judges.forEach(judge => {
      updatedJudgeIds.add(judge.id);
      let containerId;
      if (judge.status === 'corrupt') {
        containerId = 'confirmed-list';
      } else if (judge.status === 'not_corrupt') {
        containerId = 'not-corrupt-list';
      } else {
        containerId = 'undecided-list';
      }

      const container = document.getElementById(containerId);
      let card = judgeIdToCardMap[judge.id];

      if (!card) {
        card = document.createElement('div');
        card.className = 'judge-card';
        judgeIdToCardMap[judge.id] = card;
        container.appendChild(card);
      } else if (card.parentNode.id !== containerId) {
        // Move card to correct container
        card.parentNode.removeChild(card);
        container.appendChild(card);
      }

      const totalVotes = judge.corrupt_votes + judge.not_corrupt_votes;
      const ratio = totalVotes > 0 ? (judge.corrupt_votes / totalVotes).toFixed(2) : 'N/A';

      // Update card content
      card.innerHTML = `
        <div class="card-header">
          <h3>${judge.name}</h3>
          <div class="vote-ratio">${ratio}</div>
        </div>
        <div class="card-content">
          <p data-position title="${judge.job_position}"><strong>Position:</strong> ${judge.job_position}</p>
          <p data-ruling title="${judge.ruling}"><strong>Ruling:</strong> ${judge.ruling}</p>
          <div class="card-grid">
            <a href="${judge.link}" target="_blank" class="link-button">View Ruling</a>
            <button class="vote-button corrupt" data-judge-id="${judge.id}">Corrupt</button>
            ${judge.x_link ? `<a href="${judge.x_link}" target="_blank" class="link-button">View on X</a>` : ''}
            <button class="vote-button not-corrupt" data-judge-id="${judge.id}">Not Corrupt</button>
          </div>
        </div>
      `;
    });

    // Remove old cards
    for (const judgeId in judgeIdToCardMap) {
      if (!updatedJudgeIds.has(parseInt(judgeId))) {
        const cardToRemove = judgeIdToCardMap[judgeId];
        cardToRemove.parentNode.removeChild(cardToRemove);
        delete judgeIdToCardMap[judgeId];
      }
    }

    // Add event listeners to vote buttons (only for new buttons)
    document.querySelectorAll('.vote-button').forEach(button => {
      if (!button.hasEventListener) {
        button.addEventListener('click', handleVote);
        button.hasEventListener = true; // Mark as having an event listener
      }
    });
  }


  function handleVote(event) {
        const button = event.target;
        const judgeId = button.dataset.judgeId;
        const voteType = button.classList.contains('corrupt-vote') ? 'corrupt' : 'not_corrupt';

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
                // Find the judge in the judgeIdToCardMap and update its vote counts
                const card = judgeIdToCardMap[judgeId];
                if (card) {
                   fetch('/judges')
                     .then(response => response.json())
                     .then(updatedData => {
                         const updatedJudge = updatedData.judges.find(j => j.id === parseInt(judgeId));
                         if (updatedJudge) {
                             const corruptCountSpan = card.querySelector('.corrupt-count');
                             const notCorruptCountSpan = card.querySelector('.not-corrupt-count');
                             const ratioSpan = card.querySelector('.vote-ratio')

                             corruptCountSpan.textContent = updatedJudge.corrupt_votes;
                             notCorruptCountSpan.textContent = updatedJudge.not_corrupt_votes;

                             const totalVotes = updatedJudge.corrupt_votes + updatedJudge.not_corrupt_votes;
                             ratioSpan.textContent = totalVotes > 0 ? (updatedJudge.corrupt_votes / totalVotes).toFixed(2) : 'N/A';


                         }
                     })
                }
            } else {
                alert(data.error || 'Error submitting vote');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error submitting vote. Please try again.');
        });
    }
});