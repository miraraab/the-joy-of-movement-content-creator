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

        loading.classList.add('hidden');
        contentDisplay.classList.remove('hidden');

    } catch (error) {
        console.error('Error:', error);
        loading.innerHTML = '<p style="color: red;">Error generating content. Please try again.</p>';
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

        // Clear feedback
        document.getElementById('feedback').value = '';

        // Show success message
        loading.remove();
        showNotification('Content refined! Ready to save or refine again.');

    } catch (error) {
        console.error('Error:', error);
        loading.remove();
        alert('Error refining content. Please try again.');
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
