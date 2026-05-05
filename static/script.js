// Global state
let currentStep = 1;
let currentContent = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadPipelineStatus();
});

// Load pipeline status (knowledge base info)
async function loadPipelineStatus() {
    try {
        const response = await fetch('/api/pipeline-status');
        const data = await response.json();

        document.getElementById('primary-docs').textContent = data.primary_docs;
        document.getElementById('secondary-docs').textContent = data.secondary_docs;
        document.getElementById('total-tokens').textContent = data.total_tokens.toLocaleString();
    } catch (error) {
        console.error('Error loading pipeline status:', error);
    }
}

// Navigate between steps
function goToStep(stepNumber) {
    // Hide all stages
    document.querySelectorAll('.stage').forEach(stage => {
        stage.classList.add('hidden');
    });

    // Update progress steps
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.toggle('active', index + 1 <= stepNumber);
    });

    // Show selected stage
    currentStep = stepNumber;
    let stageId = `stage-${stepNumber}`;
    if (stepNumber === 5) stageId = 'stage-success';
    const stage = document.getElementById(stageId);
    if (stage) {
        stage.classList.remove('hidden');
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Submit brief and move to publish stage
async function submitBrief() {
    const form = document.getElementById('brief-form');
    const formData = new FormData(form);

    const data = {
        topic: formData.get('topic'),
        format: formData.get('format'),
        template: formData.get('template'),
        key_message: formData.get('key_message'),
        notes: formData.get('notes'),
    };

    // Validate
    if (!data.topic.trim()) {
        alert('Please enter a topic');
        return;
    }

    try {
        // Create brief
        const response = await fetch('/api/brief', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) throw new Error('Failed to create brief');

        // Move to publish stage
        goToStep(3);
        await publishContent();

    } catch (error) {
        console.error('Error:', error);
        alert('Error creating brief. Please try again.');
    }
}

// Publish (generate) content
async function publishContent() {
    const loading = document.getElementById('loading');
    const contentDisplay = document.getElementById('content-display');

    loading.classList.remove('hidden');
    contentDisplay.classList.add('hidden');

    try {
        const response = await fetch('/api/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) throw new Error('Failed to publish');

        const data = await response.json();
        currentContent = data;

        // Display content
        document.getElementById('content-text').innerHTML =
            marked(data.content) || data.content;
        document.getElementById('content-format').textContent =
            data.content.split('\n')[0];
        document.getElementById('content-chars').textContent =
            data.char_count.toLocaleString();

        // Display score if available
        if (data.score) {
            displayScore(data.score);
        }

        loading.classList.add('hidden');
        contentDisplay.classList.remove('hidden');

    } catch (error) {
        console.error('Error:', error);
        loading.innerHTML = '<p style="color: red;">Error generating content. Please try again.</p>';
    }
}

// Display score panel
function displayScore(score) {
    const scorePanel = document.getElementById('score-panel');
    const statusEl = document.getElementById('score-status');
    const overallEl = document.getElementById('score-overall');
    const feedbackEl = document.getElementById('score-feedback');
    const issuesEl = document.getElementById('score-issues');

    // Remove hidden class to show panel
    scorePanel.classList.remove('hidden');

    // Update overall score
    overallEl.textContent = score.overall_score.toFixed(1) + '/10';

    // Update individual metrics
    document.getElementById('score-voice-fill').style.width = (score.voice_authenticity * 10) + '%';
    document.getElementById('score-voice-value').textContent = score.voice_authenticity.toFixed(1);

    document.getElementById('score-constraint-fill').style.width = (score.constraint_compliance * 10) + '%';
    document.getElementById('score-constraint-value').textContent = score.constraint_compliance.toFixed(1);

    document.getElementById('score-identity-fill').style.width = (score.identity_clarity * 10) + '%';
    document.getElementById('score-identity-value').textContent = score.identity_clarity.toFixed(1);

    document.getElementById('score-story-fill').style.width = (score.story_quality * 10) + '%';
    document.getElementById('score-story-value').textContent = score.story_quality.toFixed(1);

    document.getElementById('score-contrast-fill').style.width = (score.competitor_contrast * 10) + '%';
    document.getElementById('score-contrast-value').textContent = score.competitor_contrast.toFixed(1);

    // Update feedback
    feedbackEl.textContent = score.feedback;

    // Threshold logic: 7/10
    if (score.overall_score < 7) {
        scorePanel.classList.add('score-below-threshold');
        scorePanel.classList.remove('score-good');
        statusEl.innerHTML = '<strong style="color: #d9534f;">Score below 7/10 — Consider refining with feedback</strong>';
    } else {
        scorePanel.classList.add('score-good');
        scorePanel.classList.remove('score-below-threshold');
        statusEl.innerHTML = '<strong style="color: var(--success);">Score above 7/10 — Ready to refine or save</strong>';
    }

    // Display issues with suggestions
    if (score.issues && score.issues.length > 0) {
        const issuesList = score.issues.map(issue =>
            `<li><strong>${issue.problem}</strong><br/><em>Suggestion: ${issue.suggestion}</em></li>`
        ).join('');
        issuesEl.innerHTML = `<div style="margin-top: 15px;"><strong>Issues found:</strong><ul style="margin-top: 8px;">${issuesList}</ul></div>`;
    } else {
        issuesEl.innerHTML = '';
    }
}

// Submit feedback and iterate
async function submitFeedback() {
    const feedback = document.getElementById('feedback').value;

    if (!feedback.trim()) {
        alert('Please provide feedback or click "Save & Export" to finish');
        return;
    }

    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.innerHTML = '<div class="spinner"></div><p>Refining...</p>';

    const container = document.querySelector('.refine-container');
    container.appendChild(loading);

    try {
        const response = await fetch('/api/iterate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ feedback }),
        });

        if (!response.ok) throw new Error('Failed to iterate');

        const data = await response.json();
        currentContent = data;

        // Update content display
        document.getElementById('refine-content').innerHTML =
            marked(data.content) || data.content;

        // Update score if available
        if (data.score) {
            const scorePanel = document.querySelector('.refine-container .score-panel') || createScorePanelInRefine();
            displayScoreInRefine(data.score, scorePanel);
        }

        // Clear feedback
        document.getElementById('feedback').value = '';

        // Show success message
        loading.remove();
        showNotification('Content refined! New score displayed above.');

    } catch (error) {
        console.error('Error:', error);
        loading.remove();
        alert('Error refining content. Please try again.');
    }
}

// Display score in refine section
function displayScoreInRefine(score, scorePanel) {
    scorePanel.querySelector('#score-overall').textContent = score.overall_score.toFixed(1) + '/10';
    scorePanel.querySelector('#score-feedback').textContent = score.feedback;

    if (score.overall_score < 7) {
        scorePanel.classList.add('score-below-threshold');
        scorePanel.classList.remove('score-good');
        scorePanel.querySelector('#score-status').innerHTML = '<strong style="color: #d9534f;">Score below 7/10</strong>';
    } else {
        scorePanel.classList.add('score-good');
        scorePanel.classList.remove('score-below-threshold');
        scorePanel.querySelector('#score-status').innerHTML = '<strong style="color: var(--success);">Score above 7/10</strong>';
    }
}

// Save and export
async function saveAndExport() {
    const topic = document.querySelector('#brief-form [name="topic"]').value || 'content';

    try {
        // Save as text
        const saveResponse = await fetch('/api/save-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic }),
        });

        if (!saveResponse.ok) throw new Error('Failed to save');

        // Export as HTML
        const htmlResponse = await fetch('/api/export-html', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!htmlResponse.ok) throw new Error('Failed to export HTML');

        const htmlData = await htmlResponse.json();

        // Show success
        goToStep(5); // success stage

        // Open HTML (optional)
        setTimeout(() => {
            if (confirm('Content saved! Would you like to open the HTML file in your browser?')) {
                // Note: Client-side can't open local files. User must open manually.
                alert(`HTML saved to: ${htmlData.html_path}\n\nOpen it in your browser to view.`);
            }
        }, 500);

    } catch (error) {
        console.error('Error:', error);
        alert('Error saving content. Please try again.');
    }
}

// Export as HTML
async function exportAsHTML() {
    try {
        const response = await fetch('/api/export-html', {
            method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to export');

        const data = await response.json();
        alert(`HTML exported to: ${data.html_path}`);

    } catch (error) {
        console.error('Error:', error);
        alert('Error exporting HTML.');
    }
}

// Start new content
function startNewContent() {
    // Reset form
    document.getElementById('brief-form').reset();
    currentContent = null;

    // Go to step 2 (brief)
    goToStep(2);
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--success);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.remove(), 3000);
}

// Simple markdown support (if needed)
function marked(text) {
    if (!text) return '';
    return text
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/\n/gim, '<br>');
}
