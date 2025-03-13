document.addEventListener('DOMContentLoaded', () => {
    const judgeIdToCardMap = {};

    // USA Only Toggle
    const usaOnlyToggle = document.getElementById('usa-only-toggle');

    // Fetch and display judges
    function fetchAndDisplayJudges(usaOnly = false) {
        console.log('Fetching judges, USA only:', usaOnly);
        
        // Clear existing lists first
        document.getElementById('confirmed-list').innerHTML = '';
        document.getElementById('undecided-list').innerHTML = '';
        document.getElementById('not-corrupt-list').innerHTML = '';
        
        // Reset the judge card map completely
        for (const key in judgeIdToCardMap) {
            delete judgeIdToCardMap[key];
        }
        
        fetch('/judges')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received judges data:', data);
                if (!data.judges || !Array.isArray(data.judges)) {
                    console.error('Invalid judges data received:', data);
                    return;
                }
                
                // Apply USA filter in the frontend if needed
                const judges = data.judges.map(judge => {
                    // Create a copy of the judge object to avoid modifying the original
                    const judgeWithFiltered = { ...judge };
                    
                    // Ensure all vote counts are numbers, not undefined
                    judgeWithFiltered.corrupt_votes = Number(judge.corrupt_votes || 0);
                    judgeWithFiltered.not_corrupt_votes = Number(judge.not_corrupt_votes || 0);
                    judgeWithFiltered.us_corrupt_votes = Number(judge.us_corrupt_votes || 0);
                    judgeWithFiltered.us_not_corrupt_votes = Number(judge.us_not_corrupt_votes || 0);
                    
                    if (usaOnly) {
                        // Use US-specific vote counts
                        judgeWithFiltered.corrupt_votes_filtered = judgeWithFiltered.us_corrupt_votes;
                        judgeWithFiltered.not_corrupt_votes_filtered = judgeWithFiltered.us_not_corrupt_votes;
                        
                        // Recalculate status based on filtered votes
                        const totalVotes = judgeWithFiltered.corrupt_votes_filtered + judgeWithFiltered.not_corrupt_votes_filtered;
                        judgeWithFiltered.status_filtered = 'undecided';
                        
                        if (totalVotes >= 5) {
                            const corruptRatio = judgeWithFiltered.corrupt_votes_filtered / totalVotes;
                            const notCorruptRatio = judgeWithFiltered.not_corrupt_votes_filtered / totalVotes;
                            
                            if (corruptRatio >= 0.8333) {
                                judgeWithFiltered.status_filtered = 'corrupt';
                            } else if (notCorruptRatio >= 0.8333) {
                                judgeWithFiltered.status_filtered = 'not_corrupt';
                            }
                        }
                    } else {
                        // Use regular vote counts
                        judgeWithFiltered.corrupt_votes_filtered = judgeWithFiltered.corrupt_votes;
                        judgeWithFiltered.not_corrupt_votes_filtered = judgeWithFiltered.not_corrupt_votes;
                        judgeWithFiltered.status_filtered = judge.status;
                    }
                    
                    return judgeWithFiltered;
                });
                
                // Log vote counts for debugging
                const totalVotesAll = judges.reduce((sum, judge) => sum + judge.corrupt_votes + judge.not_corrupt_votes, 0);
                const totalVotesUS = judges.reduce((sum, judge) => sum + judge.us_corrupt_votes + judge.us_not_corrupt_votes, 0);
                const totalVotesFiltered = judges.reduce((sum, judge) => sum + judge.corrupt_votes_filtered + judge.not_corrupt_votes_filtered, 0);
                
                console.log(`Total votes (all): ${totalVotesAll}, Total votes (US only): ${totalVotesUS}, Total votes (filtered): ${totalVotesFiltered}`);
                console.log(`Judges count: ${judges.length}`);
                
                // Display judges in appropriate sections
                displayJudges(judges, usaOnly);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });
    }

    // Initial fetch
    fetchAndDisplayJudges();

    // Add event listener for the toggle
    usaOnlyToggle.addEventListener('change', () => {
        fetchAndDisplayJudges(usaOnlyToggle.checked);
    });

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
  // Function to show a temporary notification
    function showNotification(message, duration = 3000) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        // Show the notification
        setTimeout(() => {
            notification.style.opacity = '1';
        }, 100);

        // Hide the notification after the specified duration
        setTimeout(() => {
            notification.style.opacity = '0';
            // Remove the notification from the DOM after the fade-out transition
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500); // Match the CSS transition time
        }, duration);
    }

  // Include the FingerprintJS library
  var fpPromise = import('https://openfpcdn.io/fingerprintjs/v4')
    .then(FingerprintJS => FingerprintJS.load())

  // TODO: Fetch this key from the server securely.  DO NOT leave it hardcoded in production.
  const hmacSecretKey = "d174ab988d3b9b65597e98957e02b355d174ab988d3b9b65597e98957e02b355";  // Replace with your actual secret key

    async function calculateHMAC(secretKey, method, path, body, timestamp) {
      const encoder = new TextEncoder();
      const keyData = encoder.encode(secretKey);
      const key = await crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign"]
      );

      let message = method + path;
      if (body) {
          message += body;
      }
      message += timestamp;
      const messageData = encoder.encode(message);

      const signature = await crypto.subtle.sign("HMAC", key, messageData);
      const hexSignature = Array.from(new Uint8Array(signature))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
      return hexSignature;
    }

  async function calculateProofOfWork(difficulty) {
    let nonce = 0;
    let hash;
    const targetPrefix = '0'.repeat(difficulty);
    do {
        nonce++;
        const data = `nonce:${nonce}`;
        const messageData = new TextEncoder().encode(data);
        hash = await crypto.subtle.digest('SHA-256', messageData);
        const hexHash = Array.from(new Uint8Array(hash))
            .map((b) => b.toString(16).padStart(2, "0"))
            .join("");
    } while (!hexHash.startsWith(targetPrefix));
    return { nonce, hash: Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('') };
  }


    // Handle form submission
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

  function displayJudges(judges, usaOnly = false) {
    console.log('Starting to display judges, count:', judges ? judges.length : 0, 'USA only:', usaOnly);
    // Create a new map each time instead of reusing the old one
    // This avoids issues with stale references
    const currentJudgeIdToCardMap = {};
    
    const confirmedTemplate = document.querySelector('#confirmed-template');
    const undecidedTemplate = document.querySelector('#undecided-template');
    const notCorruptTemplate = document.querySelector('#not-corrupt-template');

    if (!judges || !Array.isArray(judges) || judges.length === 0) {
      console.warn('No judges to display or judges is not an array');
      return;
    }

    // Check if any judge has votes when filtered
    const hasFilteredVotes = judges.some(judge => (judge.corrupt_votes_filtered + judge.not_corrupt_votes_filtered) > 0);
    console.log(`Has filtered votes: ${hasFilteredVotes}`);

    judges.forEach(judge => {
        // Skip judges without an id
        if (!judge || judge.id === undefined || judge.id === null) {
            console.warn('Skipping judge with missing id:', judge);
            return;
        }
        
        let containerId;
        let template;
        
        // Use the filtered status to determine container
        if (judge.status_filtered === 'corrupt') {
            containerId = 'confirmed-list';
            template = confirmedTemplate;
        } else if (judge.status_filtered === 'not_corrupt') {
            containerId = 'not-corrupt-list';
            template = notCorruptTemplate;
        } else {
            containerId = 'undecided-list';
            template = undecidedTemplate;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container not found:', containerId);
            return;
        }

        // Always create a new card for each judge
        if (template) {
            const templateContent = template.content.cloneNode(true);
            const card = templateContent.querySelector('.card');
            if (!card) {
                console.error('Card element not found in template');
                return;
            }
            
            // Store in our new map
            currentJudgeIdToCardMap[judge.id] = card;
            container.appendChild(card);
            
            // Update card content
            const totalVotes = judge.corrupt_votes_filtered + judge.not_corrupt_votes_filtered;
            const ratio = totalVotes > 0 ? Math.round((judge.corrupt_votes_filtered / totalVotes) * 100) : 0;

            const ribbon = card.querySelector('.ribbon');
            if (ribbon) {
                if (judge.status_filtered === 'not_corrupt') {
                    const notCorruptRatio = totalVotes > 0 ? Math.round((judge.not_corrupt_votes_filtered / totalVotes) * 100) : 0;
                    ribbon.textContent = `${notCorruptRatio}% not corrupt votes`;
                    ribbon.style.backgroundColor = '#27ae60'; // Green
                } else if (judge.status_filtered === 'undecided') {
                    ribbon.textContent = 'Undecided';
                    ribbon.style.backgroundColor = '#1e3799'; // Blue
                } else {
                    ribbon.textContent = `${ratio}% corrupt votes`;
                    ribbon.style.backgroundColor = '#c0392b'; // Red
                }
            }

            const nameElement = card.querySelector('.judge-name');
            if (nameElement) nameElement.textContent = judge.name;
            
            const infoElement = card.querySelector('.info strong');
            if (infoElement && infoElement.nextSibling) infoElement.nextSibling.textContent = ` ${judge.job_position}`;
            
            const rulingTextElement = card.querySelector('.ruling-text');
            if (rulingTextElement) {
                rulingTextElement.setAttribute('title', judge.ruling);
                const rulingStrong = rulingTextElement.querySelector('strong');
                if (rulingStrong && rulingStrong.nextSibling) rulingStrong.nextSibling.textContent = ` ${judge.ruling}`;
            }
            
            const linkElements = card.querySelectorAll('.btn-row a');
            if (linkElements && linkElements.length > 0) {
                if (linkElements[0]) linkElements[0].href = judge.link;
                if (linkElements[1]) {
                    linkElements[1].href = judge.x_link || '#'; // Use '#' if x_link is null
                    linkElements[1].style.display = judge.x_link ? '' : 'none'; // Hide if no x_link
                }
            }
            
            const corruptBtn = card.querySelector('.corrupt-vote-btn');
            if (corruptBtn) {
                // Ensure vote count is a number and not undefined
                const voteCount = typeof judge.corrupt_votes_filtered === 'number' ? judge.corrupt_votes_filtered : 0;
                corruptBtn.textContent = `Corrupt (${voteCount})`;
                corruptBtn.dataset.judgeId = judge.id;
            }
            
            const notCorruptBtn = card.querySelector('.not-corrupt-vote-btn');
            if (notCorruptBtn) {
                // Ensure vote count is a number and not undefined
                const voteCount = typeof judge.not_corrupt_votes_filtered === 'number' ? judge.not_corrupt_votes_filtered : 0;
                notCorruptBtn.textContent = `Not Corrupt (${voteCount})`;
                notCorruptBtn.dataset.judgeId = judge.id;
            }
        } else {
            console.error('Template not found for judge:', judge);
        }
    });

    // Update the global map with our new one
    Object.keys(judgeIdToCardMap).forEach(key => delete judgeIdToCardMap[key]);
    Object.assign(judgeIdToCardMap, currentJudgeIdToCardMap);

    // Add event listeners to vote buttons (only for new buttons)
    document.querySelectorAll('.corrupt-vote-btn, .not-corrupt-vote-btn').forEach(button => {
        if (!button.hasEventListener) {
            button.addEventListener('click', handleVote);
            button.hasEventListener = true; // Mark as having an event listener
        }
    });
}

async function handleVote(event) {
    const button = event.target;
    const judgeId = button.dataset.judgeId;
    const voteType = button.classList.contains('corrupt-vote-btn') ? 'corrupt' : 'not_corrupt';

    // Generate fingerprint
      const fp = await fpPromise;
      const result = await fp.get();
      const fingerprint = result.visitorId;

    // Calculate proof of work
    const difficulty = 4; // Example difficulty.  Could be adjusted.
    const { nonce, hash } = await calculateProofOfWork(difficulty);

    const timestamp = Math.floor(Date.now() / 1000);
    const path = `/vote/${judgeId}`;
    const body = JSON.stringify({ vote_type: voteType, fingerprint: fingerprint, proofOfWork: { nonce, hash } });
    const signature = await calculateHMAC(hmacSecretKey, 'POST', path, body, timestamp);

      fetch(`/vote/${judgeId}`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-HMAC-Timestamp': timestamp,
              'X-HMAC-Signature': signature
          },
          body: JSON.stringify({
              vote_type: voteType,
              fingerprint: fingerprint,
              proofOfWork: { nonce, hash }
          })
      })
      .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        } else {
            return response.json();
        }
      })
      .then(data => {
          if (data.success) {
              // Find the judge in the judgeIdToCardMap and update its vote counts
              const card = judgeIdToCardMap[judgeId];
              if (card) {
                 fetch('/judges')
                   .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    } else {
                        return response.json();
                    }
                   })
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