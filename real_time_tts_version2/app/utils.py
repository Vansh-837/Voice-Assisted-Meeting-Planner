import os
import soundfile as sf

def save_audio_to_temp_file(audio_array, sample_rate):
    """Save NumPy audio array to a temporary WAV file and return the path."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        sf.write(tmpfile.name, audio_array, sample_rate)
        return tmpfile.name

def cleanup_temp_file(path):
    """Delete a file safely."""
    if os.path.exists(path):
        os.remove(path)
