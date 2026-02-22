/**
 * KittenTTS Web Interface - JavaScript
 */

// DOM Elements
const textInput = document.getElementById('textInput');
const voiceSelect = document.getElementById('voiceSelect');
const speedSlider = document.getElementById('speedSlider');
const speedValue = document.getElementById('speedValue');
const playBtn = document.getElementById('playBtn');
const downloadBtn = document.getElementById('downloadBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const playerSection = document.getElementById('playerSection');
const audioPlayer = document.getElementById('audioPlayer');
const playerVoice = document.getElementById('playerVoice');
const playerText = document.getElementById('playerText');
const charCount = document.getElementById('charCount');

// State
let isGenerating = false;
let currentAudioUrl = null;

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    playBtn.addEventListener('click', handlePlay);
    downloadBtn.addEventListener('click', handleDownload);
    speedSlider.addEventListener('input', updateSpeedDisplay);
    textInput.addEventListener('input', updateCharCounter);
}

/**
 * Update character count display
 */
function updateCharCounter() {
    charCount.textContent = textInput.value.length;
}

/**
 * Update speed display
 */
function updateSpeedDisplay() {
    const speed = parseFloat(speedSlider.value);
    speedValue.textContent = speed.toFixed(1) + 'x';
}

/**
 * Show loading indicator
 */
function showLoading() {
    loadingIndicator.classList.remove('hidden');
    hideError();
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

/**
 * Show error message
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

/**
 * Hide error message
 */
function hideError() {
    errorMessage.classList.add('hidden');
}

/**
 * Disable controls during generation
 */
function disableControls(disabled) {
    textInput.disabled = disabled;
    voiceSelect.disabled = disabled;
    speedSlider.disabled = disabled;
    playBtn.disabled = disabled;
    downloadBtn.disabled = disabled;
}

/**
 * Validate form inputs
 */
function validateInputs() {
    const text = textInput.value.trim();
    
    if (!text) {
        showError('Please enter some text');
        return false;
    }
    
    if (text.length > 1000) {
        showError('Text is too long (max 1000 characters)');
        return false;
    }
    
    return true;
}

/**
 * Generate audio - Play version (using streaming)
 */
async function handlePlay() {
    if (isGenerating) return;
    if (!validateInputs()) return;

    isGenerating = true;
    disableControls(true);
    showLoading();

    try {
        const text = textInput.value.trim();
        const voice = voiceSelect.value;
        const speed = parseFloat(speedSlider.value);

        const response = await fetch('/api/generate-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                voice: voice,
                speed: speed
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate audio');
        }

        const data = await response.json();
        
        if (data.success) {
            // Set audio source and show player
            audioPlayer.src = data.audio;
            playerVoice.textContent = data.voice;
            playerText.textContent = data.text;
            currentAudioUrl = data.audio;
            
            playerSection.classList.remove('hidden');
            hideError();
            
            // Play audio automatically
            audioPlayer.play().catch(err => {
                console.log('Autoplay prevented or failed:', err);
            });
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Error: ' + error.message);
    } finally {
        isGenerating = false;
        disableControls(false);
        hideLoading();
    }
}

/**
 * Generate and download audio
 */
async function handleDownload() {
    if (isGenerating) return;
    if (!validateInputs()) return;

    isGenerating = true;
    disableControls(true);
    showLoading();

    try {
        const text = textInput.value.trim();
        const voice = voiceSelect.value;
        const speed = parseFloat(speedSlider.value);

        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                voice: voice,
                speed: speed
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate audio');
        }

        // Get the audio blob
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `kitten_tts_${voice}.wav`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        hideError();
    } catch (error) {
        console.error('Error:', error);
        showError('Error: ' + error.message);
    } finally {
        isGenerating = false;
        disableControls(false);
        hideLoading();
    }
}

/**
 * Handle keyboard shortcuts
 */
document.addEventListener('keydown', function(event) {
    // Ctrl+Enter or Cmd+Enter to play
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        handlePlay();
    }
});

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateSpeedDisplay();
});
