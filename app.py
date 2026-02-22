"""Flask web application for KittenTTS text-to-speech synthesis."""

import os
import io
import json
import re
import unicodedata
from flask import Flask, render_template, request, jsonify, send_file
from kittentts import KittenTTS
import soundfile as sf
import numpy as np
from pathlib import Path

app = Flask(__name__)

# Initialize KittenTTS model (using nano version for speed)
MODEL_NAME = "KittenML/kitten-tts-nano-0.8-fp32"
tts = None

# Available voices based on the model
AVAILABLE_VOICES = [
    'Bella', 'Jasper', 'Luna', 'Bruno', 
    'Rosie', 'Hugo', 'Kiki', 'Leo'
]

# Create output directory for audio files
OUTPUT_DIR = Path(__file__).parent / "generated_audio"
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_TEXT_LEN = 1000
SAFE_CHUNK_LEN = 180


def _normalize_input_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _sanitize_text_for_model(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.replace("\n", " ")
    ascii_text = re.sub(r"[^A-Za-z0-9 .,!?;:'\"()\-]", " ", ascii_text)
    ascii_text = re.sub(r"\s+", " ", ascii_text).strip()
    return ascii_text


def _split_safe_chunks(text: str, max_len: int = SAFE_CHUNK_LEN) -> list[str]:
    if len(text) <= max_len:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_len:
            words = sentence.split()
            temp = ""
            for word in words:
                candidate = f"{temp} {word}".strip()
                if len(candidate) <= max_len:
                    temp = candidate
                else:
                    if temp:
                        chunks.append(temp)
                    temp = word
            if temp:
                chunks.append(temp)
            continue

        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks or [text[:max_len]]


def _synthesize_audio_safe(model: KittenTTS, text: str, voice: str, speed: float) -> np.ndarray:
    try:
        return model.generate(text, voice=voice, speed=speed)
    except Exception as first_error:
        sanitized = _sanitize_text_for_model(text)
        if not sanitized:
            raise ValueError("Text contains unsupported characters for this model.") from first_error

        if sanitized != text:
            try:
                return model.generate(sanitized, voice=voice, speed=speed)
            except Exception:
                pass

        chunk_audios = []
        for chunk in _split_safe_chunks(sanitized):
            try:
                chunk_audio = model.generate(chunk, voice=voice, speed=speed)
                if chunk_audio is not None and getattr(chunk_audio, "size", 0) > 0:
                    chunk_audios.append(chunk_audio)
            except Exception:
                continue

        if chunk_audios:
            return np.concatenate(chunk_audios, axis=-1)

        raise ValueError(
            "Model could not synthesize this text. Try shorter text or English-only phrasing."
        ) from first_error


def get_model():
    """Lazy load the TTS model."""
    global tts
    if tts is None:
        print(f"Loading KittenTTS model: {MODEL_NAME}")
        cache_dir = os.getenv("HF_HOME", str(Path(__file__).parent / ".cache" / "huggingface"))
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        tts = KittenTTS(MODEL_NAME, cache_dir=cache_dir)
    return tts


@app.route('/')
def index():
    """Render the main web interface."""
    return render_template('index.html', voices=AVAILABLE_VOICES)


@app.route('/api/voices')
def get_voices():
    """Return list of available voices."""
    return jsonify({'voices': AVAILABLE_VOICES})


@app.route('/api/generate', methods=['POST'])
def generate_audio():
    """Generate audio from the provided text."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON payload'}), 400

        text = _normalize_input_text(data.get('text', ''))
        voice = data.get('voice', 'Jasper')
        try:
            speed = float(data.get('speed', 1.0))
        except (TypeError, ValueError):
            return jsonify({'error': 'Speed must be a number'}), 400

        if not text:
            return jsonify({'error': 'Text is required'}), 400

        if len(text) > MAX_TEXT_LEN:
            return jsonify({'error': f'Text is too long (max {MAX_TEXT_LEN} characters)'}), 400

        if voice not in AVAILABLE_VOICES:
            return jsonify({'error': f'Invalid voice: {voice}'}), 400

        if speed < 0.5 or speed > 2.0:
            return jsonify({'error': 'Speed must be between 0.5 and 2.0'}), 400

        # Generate audio
        print(f"Generating audio: text='{text[:50]}...', voice={voice}, speed={speed}")
        model = get_model()
        audio = _synthesize_audio_safe(model, text, voice, speed)

        # Convert audio to WAV format in memory
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, 24000, format='WAV')
        audio_buffer.seek(0)

        # Return audio file
        return send_file(
            audio_buffer,
            mimetype='audio/wav',
            as_attachment=True,
            download_name=f'kitten_tts_{voice}.wav'
        )

    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-stream', methods=['POST'])
def generate_audio_stream():
    """Generate audio and return as base64 for inline playback."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON payload'}), 400

        text = _normalize_input_text(data.get('text', ''))
        voice = data.get('voice', 'Jasper')
        try:
            speed = float(data.get('speed', 1.0))
        except (TypeError, ValueError):
            return jsonify({'error': 'Speed must be a number'}), 400

        if not text:
            return jsonify({'error': 'Text is required'}), 400

        if len(text) > MAX_TEXT_LEN:
            return jsonify({'error': f'Text is too long (max {MAX_TEXT_LEN} characters)'}), 400

        if voice not in AVAILABLE_VOICES:
            return jsonify({'error': f'Invalid voice: {voice}'}), 400

        if speed < 0.5 or speed > 2.0:
            return jsonify({'error': 'Speed must be between 0.5 and 2.0'}), 400

        # Generate audio
        print(f"Generating audio stream: text='{text[:50]}...', voice={voice}, speed={speed}")
        model = get_model()
        audio = _synthesize_audio_safe(model, text, voice, speed)

        # Convert audio to WAV format in memory
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, 24000, format='WAV')
        audio_buffer.seek(0)

        # Convert to base64 for embedding in HTML
        import base64
        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode('utf-8')

        return jsonify({
            'success': True,
            'audio': f'data:audio/wav;base64,{audio_base64}',
            'text': text,
            'voice': voice
        })

    except Exception as e:
        print(f"Error generating audio stream: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Check if Flask is installed
    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    except ModuleNotFoundError:
        print("Error: Flask is not installed.")
        print("Install it with: pip install flask")
