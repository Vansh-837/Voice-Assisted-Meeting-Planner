import torch
from torch.serialization import add_safe_globals
import asyncio
import os
import time
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

# Allow unpickling for secure globals
add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
DEVICE = "cpu"  # Use CPU for TTS to avoid cuDNN issues while STT uses GPU

print("🔄 Loading TTS model...")
tts = TTS(MODEL_NAME).to(DEVICE)
print(f"✅ TTS model loaded on {DEVICE}!")

# Cache for speaker embeddings to speed up processing
speaker_cache = {}

def clean_text_for_tts(text):
    """Clean and normalize text for better TTS processing"""
    import re
    
    # Remove or replace problematic patterns
    text = text.strip()
    
    # Skip if too short or just punctuation
    if len(text) < 3 or text.strip() in [".", "!", "?", ",", ";", ":"]:
        return None
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Ensure sentences end properly
    if text and text[-1] not in '.!?':
        text += '.'
    
    # Remove standalone punctuation at the beginning
    text = re.sub(r'^\s*[.!?]+\s*', '', text)
    
    # Handle common abbreviations
    text = text.replace('i am', 'I am')
    text = text.replace('i\'m', 'I\'m')
    text = text.replace('i ', 'I ')
    
    return text.strip() if text.strip() else None

async def synthesize_text(text, speaker_wav, language, output_path):
    """
    Async TTS synthesis optimized for chunked processing with text cleaning
    """
    try:
        # Clean and validate text
        cleaned_text = clean_text_for_tts(text)
        if not cleaned_text:
            print(f"⚠️ Skipping problematic text: '{text}'")
            return False
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        start_time = time.time()
        
        # Use cached speaker embedding if available
        if speaker_wav not in speaker_cache:
            print(f"🎭 Caching speaker embedding for {speaker_wav}")
            speaker_cache[speaker_wav] = True
        
        # Run synthesis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        def sync_synthesis():
            try:
                # Generate audio with cleaned text
                wav = tts.tts(
                    text=cleaned_text,
                    speaker_wav=speaker_wav,
                    language=language
                )
                
                # Save to file
                tts.synthesizer.save_wav(wav, output_path)
                return True
                
            except Exception as e:
                print(f"❌ Synthesis error for '{cleaned_text}': {e}")
                return False
        
        # Run in executor to prevent blocking
        success = await loop.run_in_executor(None, sync_synthesis)
        
        if success:
            generation_time = time.time() - start_time
            print(f"⚡ Generated chunk in {generation_time:.2f}s: '{cleaned_text[:30]}...'")
        else:
            print(f"❌ Failed to generate: {cleaned_text[:30]}...")
            
        return success
        
    except Exception as e:
        print(f"❌ TTS synthesis error: {e}")
        return False

# Optional: Preload speaker for faster first synthesis
async def preload_speaker(speaker_wav, language="en"):
    """
    Preload speaker embedding for faster chunk processing
    """
    try:
        print(f"🔄 Preloading speaker: {speaker_wav}")
        dummy_path = "temp_preload.wav"
        await synthesize_text("Hello", speaker_wav, language, dummy_path)
        
        # Clean up temp file
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
            
        print(f"✅ Speaker preloaded: {speaker_wav}")
        
    except Exception as e:
        print(f"⚠️ Speaker preload failed: {e}")

# Optional: Batch synthesis for multiple chunks (if needed)
async def synthesize_batch(text_chunks, speaker_wav, language, output_dir):
    """
    Synthesize multiple text chunks in parallel (use with caution - may consume lots of VRAM)
    """
    tasks = []
    
    for i, text in enumerate(text_chunks):
        output_path = os.path.join(output_dir, f"chunk_{i}.wav")
        task = synthesize_text(text, speaker_wav, language, output_path)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if r is True)
    print(f"✅ Batch synthesis complete: {successful}/{len(text_chunks)} successful")
    
    return results

# Utility function to clean up old audio files
def cleanup_old_audio_files(audio_dir="static/audio", max_age_minutes=30):
    """
    Clean up audio files older than specified age
    """
    try:
        if not os.path.exists(audio_dir):
            return
            
        current_time = time.time()
        max_age_seconds = max_age_minutes * 60
        
        for filename in os.listdir(audio_dir):
            if filename.endswith('.wav'):
                file_path = os.path.join(audio_dir, filename)
                file_age = current_time - os.path.getctime(file_path)
                
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    print(f"🗑️ Cleaned up old audio file: {filename}")
                    
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

# Run cleanup periodically (you can call this from your main app)
async def periodic_cleanup():
    """
    Run periodic cleanup of old audio files
    """
    while True:
        await asyncio.sleep(600)  # Clean up every 10 minutes
        cleanup_old_audio_files()