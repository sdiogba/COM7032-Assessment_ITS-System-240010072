// Global variables
let problemStartTime = null;
let timerInterval = null;
let hasAnsweredCurrentProblem = false;

// Utility Functions
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function showLoader() {
    return `<div class="d-flex justify-content-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>`;
}

// Timer Functions
function startTimer() {
    problemStartTime = Date.now();
    if (timerInterval) clearInterval(timerInterval);
    
    timerInterval = setInterval(() => {
        const elapsedTime = Math.floor((Date.now() - problemStartTime) / 1000);
        const timerDisplay = document.getElementById('timer');
        if (timerDisplay) {
            timerDisplay.textContent = formatTime(elapsedTime);
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        return Math.floor((Date.now() - problemStartTime) / 1000);
    }
    return 0;
}

// Stats Update Functions
function updateStats() {
    fetch('/get_stats')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const stats = data.stats;
                // Update level and score badges
                const levelBadge = document.querySelector('.badge.bg-primary');
                const scoreBadge = document.querySelector('.badge.bg-info');
                
                if (levelBadge) levelBadge.textContent = `Level ${stats.level}`;
                if (scoreBadge) scoreBadge.textContent = `Score: ${stats.score}/50`;
                
                // Update progress bar 
                const progressBar = document.querySelector('.progress-bar');
                if (progressBar) {
                    const percentage = (stats.score / 50) * 100;
                    progressBar.style.width = `${percentage}%`;
                    progressBar.setAttribute('aria-valuenow', stats.score);
                }
            }
        })
        .catch(error => console.error('Error updating stats:', error));
}

// Practice Page Functionality
const Practice = {
    init: function() {
        if (document.getElementById('equation')) {
            this.bindEvents();
            hasAnsweredCurrentProblem = true; 
            this.generateProblem();
        }
    },

    bindEvents: function() {
        const submitBtn = document.getElementById('submitBtn');
        const nextBtn = document.getElementById('nextBtn');
        const answerInput = document.getElementById('answer');

        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitAnswer());
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.generateProblem());
        }
        if (answerInput) {
            answerInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.submitAnswer();
                }
            });
        }
    },

    generateProblem: function() {
        if (!hasAnsweredCurrentProblem) {
            this.showFeedback('Please solve the current problem first!', 'warning');
            return;
        }
    
        const equationElement = document.getElementById('equation');
        equationElement.innerHTML = showLoader();
    
        fetch('/generate_problem')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    handleError(data.error);
                    return;
                }
                equationElement.textContent = data.equation;
                startTimer();
                document.getElementById('answer').value = '';
                document.getElementById('feedback-area').classList.add('d-none');
                hasAnsweredCurrentProblem = false;
                
                // Update stats after generating new problem
                updateStats();
            })
            .catch(error => handleError(error));
    },

    submitAnswer: function() {
        const answer = document.getElementById('answer').value;
        if (!answer) {
            this.showFeedback('Please enter an answer', 'warning');
            return;
        }
    
        const timeTaken = stopTimer();
        
        fetch('/check_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                answer: answer,
                time_taken: timeTaken
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                this.showFeedback(data.error, 'danger');
                return;
            }
    
            // Mark problem as answered
            hasAnsweredCurrentProblem = true;
    
            // Handle level up
  
if (data.levelUp) {
    // Remove  existing level up alerts
    const existingAlert = document.querySelector('.level-up-alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    // Create new level up alert
    const levelUpAlert = document.createElement('div');
    levelUpAlert.className = 'alert alert-success text-center level-up-alert';
    levelUpAlert.textContent = data.levelUp;
    document.querySelector('.container').insertBefore(levelUpAlert, document.querySelector('.card'));

    // Update stats
    updateStats();

    // Update equation for new problem is provided
    if (data.newProblem) {
        const equationElement = document.getElementById('equation');
        equationElement.textContent = data.newProblem;
        
        // Reset input and feedback
        document.getElementById('answer').value = '';
        document.getElementById('feedback-area').classList.add('d-none');
        
        // Reset timer
        startTimer();
        
        // Allow answering the new problem
        hasAnsweredCurrentProblem = false;
    }

    // Remove level up alert after delay
    setTimeout(() => {
        if (levelUpAlert && levelUpAlert.parentNode) {
            levelUpAlert.remove();
        }
    }, 3000);
} else {
                // Show feedback
                const feedbackType = data.status === 'correct' ? 'success' : 'danger';
                this.showFeedback(data.feedback, feedbackType);
                
                // Update stats
                updateStats();
    
                // For correct answers, clear input and generate new problem after delay
                if (data.status === 'correct') {
                    document.getElementById('answer').value = '';
                    setTimeout(() => {
                        this.generateProblem();
                    }, 1500);
                }
            }
        })
        .catch(error => handleError(error));
    },
    
    showFeedback: function(feedback, type) {
        const feedbackArea = document.getElementById('feedback-area');
        const feedbackMessage = document.getElementById('feedback-message');
        
        if (!feedbackArea || !feedbackMessage) return;
        
        feedbackArea.classList.remove('d-none');
        feedbackMessage.className = `alert alert-${type}`;
        
        if (typeof feedback === 'object' && feedback.message) {
            let content = `<p><strong>${feedback.message}</strong></p>`;
            if (feedback.steps && Array.isArray(feedback.steps)) {
                content += '<ol class="mb-3">';
                feedback.steps.forEach(step => {
                    content += `<li class="mb-2">${step}</li>`;
                });
                content += '</ol>';
            }
            if (feedback.explanation) {
                content += `<p class="mt-3"><strong>Tip:</strong> ${feedback.explanation}</p>`;
            }
            feedbackMessage.innerHTML = content;
        } else {
            feedbackMessage.textContent = feedback;
        }
    }
};

// Error Handling
function handleError(error, message = 'Something went wrong. Please try again.') {
    console.error('Error:', error);
    const feedbackArea = document.getElementById('feedback-area');
    if (feedbackArea) {
        feedbackArea.classList.remove('d-none');
        feedbackArea.innerHTML = `
            <div class="alert alert-danger">
                ${message}
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof bootstrap !== 'undefined') {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    Practice.init();
});