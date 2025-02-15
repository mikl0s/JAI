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
    const confirmedTemplate = document.querySelector('#confirmed-template');
    const undecidedTemplate = document.querySelector('#undecided-template');
    const notCorruptTemplate = document.querySelector('#not-corrupt-template');

  judges.forEach(judge => {
    updatedJudgeIds.add(judge.id);
    let containerId;
    let template;
    if (judge.status === 'corrupt') {
      containerId = 'confirmed-list';
      template = confirmedTemplate;
    } else if (judge.status === 'not_corrupt') {
      containerId = 'not-corrupt-list';
      template = notCorruptTemplate;
    } else {
      containerId = 'undecided-list';
      template = undecidedTemplate;
    }

    const container = document.getElementById(containerId);
    let card = judgeIdToCardMap[judge.id];

  if (!card) {
    // Clone the template
      if (template) {
        const templateContent = template.content.cloneNode(true);
        card = templateContent.querySelector('.card');
        judgeIdToCardMap[judge.id] = card;
        container.appendChild(card);
      } else {
        console.error('Template not found for judge:', judge);
        return;
      }
    } else if (card.parentNode.id !== containerId) {
      // Move card to correct container
      card.parentNode.removeChild(card);
      container.appendChild(card);
    }


    // Update card content
    const totalVotes = judge.corrupt_votes + judge.not_corrupt_votes;
    const ratio = totalVotes > 0 ? Math.round((judge.corrupt_votes / totalVotes) * 100) : 0;

    if (!card) {
      console.log("card is undefined", judgeIdToCardMap, judge.id);
    }

 const ribbon = card.querySelector('.ribbon');
    if (judge.status === 'not_corrupt') {
        const notCorruptRatio = totalVotes > 0 ? Math.round((judge.not_corrupt_votes / totalVotes) * 100) : 0;
     ribbon.textContent = `${notCorruptRatio}% not corrupt votes`;
     ribbon.style.backgroundColor = '#27ae60'; // Green
    } else if (judge.status === 'undecided') {
     ribbon.textContent = 'Undecided';
        ribbon.style.backgroundColor = '#1e3799'; // Blue
    } else {
      ribbon.textContent = `${ratio}% corrupt votes`;
     ribbon.style.backgroundColor = '#c0392b'; // Red
 }

    card.querySelector('.judge-name').textContent = judge.name;
    card.querySelector('.info strong').nextSibling.textContent = ` ${judge.job_position}`;
    card.querySelector('.ruling-text').setAttribute('title', judge.ruling);
    card.querySelector('.ruling-text strong').nextSibling.textContent = ` ${judge.ruling}`;
    card.querySelector('.btn-row a:nth-child(1)').href = judge.link;
    card.querySelector('.btn-row a:nth-child(2)').href = judge.x_link || '#'; // Use '#' if x_link is null
    if (!judge.x_link) {
        card.querySelector('.btn-row a:nth-child(2)').style.display = 'none'; // Hide if no x_link
    }
    card.querySelector('.corrupt-vote-btn').textContent = `Corrupt (${judge.corrupt_votes})`;
    card.querySelector('.not-corrupt-vote-btn').textContent = `Not Corrupt (${judge.not_corrupt_votes})`;
    card.querySelector('.corrupt-vote-btn').dataset.judgeId = judge.id;
    card.querySelector('.not-corrupt-vote-btn').dataset.judgeId = judge.id;
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
  document.querySelectorAll('.corrupt-vote-btn, .not-corrupt-vote-btn').forEach(button => {
    if (!button.hasEventListener) {
      button.addEventListener('click', handleVote);
      button.hasEventListener = true; // Mark as having an event listener
    }
  });
}


  function handleVote(event) {
      const button = event.target;
      const judgeId = button.dataset.judgeId;
      const voteType = button.classList.contains('corrupt-vote-btn') ? 'corrupt' : 'not_corrupt';

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
                 const corruptCountSpan = card.querySelector('.corrupt-vote-btn');
                 const notCorruptCountSpan = card.querySelector('.not-corrupt-vote-btn');
                 const ratioSpan = card.querySelector('.ribbon');

                 corruptCountSpan.textContent = `Corrupt (${updatedJudge.corrupt_votes})`;
                 notCorruptCountSpan.textContent = `Not Corrupt (${updatedJudge.not_corrupt_votes})`;

                 const totalVotes = updatedJudge.corrupt_votes + updatedJudge.not_corrupt_votes;
                 const newRatio = totalVotes > 0 ? Math.round((updatedJudge.corrupt_votes / totalVotes) * 100) : 0;
                 ratioSpan.textContent = `${newRatio}% corrupt votes`;
               }
             });
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