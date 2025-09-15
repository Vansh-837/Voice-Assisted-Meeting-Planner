import argparse
import os
import sys
import time
from pathlib import Path
import numpy as np
import pyaudio
import threading
import queue
from faster_whisper import WhisperModel

class SpeechToText:
    def __init__(self, model_size="large-v3", device="cuda", compute_type="float16"):
        """
        Initialize the Speech-to-Text model
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v1, large-v2, large-v3)
            device: Device to use (cuda, cpu)
            compute_type: Computation precision (float16, int8_float16, int8)
        """
        print(f"Loading Whisper model: {model_size}")
        print(f"Device: {device}, Compute type: {compute_type}")
        
        try:
            self.model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type,
                # Optimize for RTX 5090
                cpu_threads=0,  # Use GPU acceleration
                num_workers=2   # Use 2 workers for faster GPU utilization
            )
            print("Model loaded successfully!")
            
            # Test GPU inference to catch cuDNN issues early
            if device == "cuda":
                try:
                    # Test with a small dummy audio array
                    import numpy as np
                    test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
                    test_segments, test_info = self.model.transcribe(test_audio, language="en")
                    # Consume the generator to actually run inference
                    list(test_segments)
                    print("GPU inference test passed!")
                except Exception as gpu_test_error:
                    print(f"GPU inference test failed: {gpu_test_error}")
                    if "cudnn" in str(gpu_test_error).lower() or "cuda" in str(gpu_test_error).lower():
                        print("Detected CUDA/cuDNN issue, falling back to CPU...")
                        raise Exception("GPU inference failed due to CUDA/cuDNN")
                    
        except Exception as e:
            print(f"Error loading model with GPU ({device}, {compute_type}): {e}")
            
            # Try different GPU compute types before falling back to CPU
            if device == "cuda" and "cudnn" not in str(e).lower():
                gpu_fallback_types = ["int8_float16", "int8"]
                for fallback_compute in gpu_fallback_types:
                    if fallback_compute != compute_type:  # Don't try the same type again
                        try:
                            print(f"Trying GPU with {fallback_compute} compute type...")
                            self.model = WhisperModel(
                                model_size, 
                                device="cuda", 
                                compute_type=fallback_compute,
                                cpu_threads=0,
                                num_workers=2
                            )
                            
                            # Test inference with this fallback
                            try:
                                import numpy as np
                                test_audio = np.zeros(16000, dtype=np.float32)
                                test_segments, test_info = self.model.transcribe(test_audio, language="en")
                                list(test_segments)
                                print(f"Model loaded successfully with GPU ({fallback_compute})!")
                                return
                            except Exception as gpu_test_error:
                                print(f"GPU inference test failed with {fallback_compute}: {gpu_test_error}")
                                if "cudnn" in str(gpu_test_error).lower():
                                    break  # Stop trying GPU if cuDNN is the issue
                                continue
                                
                        except Exception as e_fallback:
                            print(f"GPU fallback with {fallback_compute} failed: {e_fallback}")
                            continue
            
            # If all GPU attempts failed, fall back to CPU
            print("All GPU attempts failed. Attempting to load with CPU fallback...")
            try:
                self.model = WhisperModel(
                    model_size, 
                    device="cpu", 
                    compute_type="int8",
                    cpu_threads=4
                )
                print("Model loaded successfully with CPU fallback!")
            except Exception as e2:
                print(f"Error loading model with CPU fallback: {e2}")
                sys.exit(1)
    
    def transcribe_file(self, audio_file, language=None, task="transcribe"):
        """
        Transcribe audio file
        
        Args:
            audio_file: Path to audio file
            language: Language code (auto-detect if None)
            task: "transcribe" or "translate"
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        print(f"Transcribing: {audio_file}")
        start_time = time.time()
        
        segments, info = self.model.transcribe(
            audio_file,
            language=language,
            task=task,
            beam_size=7,  # Slightly higher for accuracy, but not too high for speed
            best_of=7,
            temperature=0,
            patience=0.1,  # Lower patience for speed
            condition_on_previous_text=True,
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(min_silence_duration_ms=300),  # Lower silence for faster segmenting
            suppress_tokens=[]  # Allow all symbols to be transcribed
        )
        
        # Collect all segments
        transcription = ""
        segment_list = []
        for segment in segments:
            segment_info = {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text,
                'confidence': getattr(segment, 'avg_logprob', 0)
            }
            segment_list.append(segment_info)
            transcription += segment.text
        # Post-process transcription to fix symbolic words
        def fix_symbols(text):
            import re
            # Replace common symbolic words with their symbols
            symbol_map = {
                r"\\bat the rate\\b": "@",
                r"\\bat the red\\b": "@",
                r"\\bat rate\\b": "@",
                r"\\bdot\\b": ".",
                r"\\bcomma\\b": ",",
                r"\\bslash\\b": "/",
                r"\\bbackslash\\b": "\\",
                r"\\bcolon\\b": ":",
                r"\\bsemicolon\\b": ";",
                r"\\bhyphen\\b": "-",
                r"\\bunderscore\\b": "_",
                r"\\bhash\\b": "#",
                r"\\bdollar\\b": "$",
                r"\\bpercent\\b": "%",
                r"\\bampersand\\b": "&",
                r"\\bstar\\b": "*",
                r"\\bplus\\b": "+",
                r"\\bequal\\b": "=",
                r"\\bquestion mark\\b": "?",
                r"\\bexclamation mark\\b": "!",
                r"\\bopen bracket\\b": "[",
                r"\\bclose bracket\\b": "]",
                r"\\bopen parenthesis\\b": "(",
                r"\\bclose parenthesis\\b": ")",
                r"\\bopen brace\\b": "{",
                r"\\bclose brace\\b": "}",
                r"\\bpipe\\b": "|",
                r"\\bgreater than\\b": ">",
                r"\\bless than\\b": "<",
                r"\\bquote\\b": '"',
                r"\\bapostrophe\\b": "'"
            }
            for word, symbol in symbol_map.items():
                text = re.sub(word, symbol, text, flags=re.IGNORECASE)
            # Fix email patterns like 'name at domain dot com'
            text = re.sub(r"([\w-]+)\s*@\s*([\w-]+)\s*(?:dot|\.)\s*([\w-]+)", r"\1@\2.\3", text, flags=re.IGNORECASE)
            return text
        transcription = fix_symbols(transcription)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Transcription completed in {duration:.2f} seconds")
        print(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")
        
        return {
            'transcription': transcription.strip(),
            'segments': segment_list,
            'language': info.language,
            'language_probability': info.language_probability,
            'duration': duration
        }
    
    def save_transcription(self, result, output_file, format_type="txt"):
        """Save transcription to file"""
        output_path = Path(output_file)
        
        if format_type == "txt":
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['transcription'])
        
        elif format_type == "srt":
            with open(output_path.with_suffix('.srt'), 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result['segments'], 1):
                    start_time = self._seconds_to_srt_time(segment['start'])
                    end_time = self._seconds_to_srt_time(segment['end'])
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text'].strip()}\n\n")
        
        elif format_type == "json":
            import json
            with open(output_path.with_suffix('.json'), 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Transcription saved to: {output_path}")
    
    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


class RealTimeSTT:
    def __init__(self, model_size="large-v3", device="cuda"):
        """Real-time speech-to-text"""
        self.stt = SpeechToText(model_size, device)
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Audio parameters with fallback support
        self.channels = 1
        self.format = pyaudio.paInt16
        self.chunk_size = 1024
        
        # Find a supported sample rate
        self.sample_rate = self._find_supported_sample_rate()
        print(f"Using sample rate: {self.sample_rate} Hz")
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def start_recording(self, duration=None, silence_threshold=None, silence_duration=3.0, auto_calibrate=True):
        """Start real-time recording and transcription with adaptive silence detection"""
        if duration is not None:
            print(f"Starting real-time transcription for {duration} seconds...")
        else:
            print(f"Starting real-time transcription (will stop after {silence_duration} seconds of silence)...")
        
        self.is_recording = True
        
        # Open audio stream
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.audio_callback
        )
        
        stream.start_stream()
        
        # Calibrate noise floor if auto_calibrate is enabled
        noise_floor = 0.0
        if auto_calibrate and silence_threshold is None:
            print("🎯 Calibrating noise floor... (stay quiet for 2 seconds)")
            calibration_samples = []
            calibration_start = time.time()
            
            while time.time() - calibration_start < 2.0:
                try:
                    data = self.audio_queue.get(timeout=0.1)
                    audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    volume = np.sqrt(np.mean(audio_chunk**2))
                    calibration_samples.append(volume)
                    print(".", end="", flush=True)
                except queue.Empty:
                    continue
            
            if calibration_samples:
                noise_floor = np.mean(calibration_samples)
                # Set threshold significantly above noise floor
                adaptive_threshold = noise_floor * 2.5  # 2.5x the noise floor
                # But ensure it's at least 0.05 and at most 0.3
                silence_threshold = max(0.05, min(0.3, adaptive_threshold))
                print(f"\n🎯 Calibrated - Noise floor: {noise_floor:.4f}, Threshold: {silence_threshold:.4f}")
            else:
                silence_threshold = 0.15  # Fallback
                print(f"\n🎯 Calibration failed, using fallback threshold: {silence_threshold}")
        elif silence_threshold is None:
            silence_threshold = 0.15  # Default fallback
            print(f"🎯 Using default threshold: {silence_threshold}")
        else:
            print(f"🎯 Using manual threshold: {silence_threshold}")
        
        print("Speak now...")
        
        # Collect audio data
        audio_data = []
        start_time = time.time()
        voice_detected = False
        voice_chunks = 0
        
        # NEW: Sustained silence detection
        consecutive_silence_chunks = 0
        required_silence_chunks = int((silence_duration * self.sample_rate) / self.chunk_size)
        silence_countdown_active = False
        
        print(f"🎯 Required {required_silence_chunks} consecutive silent chunks to stop")
        
        try:
            while (duration is None or time.time() - start_time < duration) and self.is_recording:
                try:
                    data = self.audio_queue.get(timeout=0.1)
                    audio_data.append(data)
                    
                    # Convert to numpy for volume analysis
                    audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    volume = np.sqrt(np.mean(audio_chunk**2))
                    
                    # Debug: Print volume every 50 chunks (about every 1 second)
                    if len(audio_data) % 50 == 0:
                        print(f"\n[DEBUG] Volume: {volume:.4f}, Threshold: {silence_threshold:.4f}, Silent: {consecutive_silence_chunks}/{required_silence_chunks}")
                    
                    if volume > silence_threshold:
                        # Voice detected - reset sustained silence counter
                        if consecutive_silence_chunks > 0:
                            consecutive_silence_chunks = 0
                            silence_countdown_active = False
                        
                        voice_chunks += 1
                        
                        if not voice_detected and voice_chunks > 3:  # Require confirmation
                            voice_detected = True
                            print(f"\n🎤 Voice detected! Continue speaking...")
                        
                        if voice_detected:
                            print("🟢", end="", flush=True)  # Voice indicator
                    else:
                        # Silence detected - increment sustained silence counter
                        voice_chunks = 0
                        consecutive_silence_chunks += 1
                        
                        if voice_detected:  # Only check silence after voice has been detected
                            # Start countdown message when we first detect sustained silence
                            if not silence_countdown_active and consecutive_silence_chunks >= 10:  # Wait for 10 chunks to avoid false starts
                                silence_countdown_active = True
                                print(f"\n⏸️ Sustained silence detected, will stop after {silence_duration}s...")
                            
                            # Check if we've reached the required silence duration
                            if consecutive_silence_chunks >= required_silence_chunks:
                                print(f"\n🔇 Recording stopped - {silence_duration}s of sustained silence reached")
                                self.is_recording = False
                                break
                            
                            # Show progress during countdown
                            if silence_countdown_active and consecutive_silence_chunks % 15 == 0:
                                progress = (consecutive_silence_chunks / required_silence_chunks) * 100
                                print(f" {progress:.0f}%", end="", flush=True)
                        else:
                            # Still waiting for initial voice
                            if len(audio_data) % 20 == 0:  # Less frequent updates while waiting
                                print("⚪", end="", flush=True)
                            
                except queue.Empty:
                    continue
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
            self.is_recording = False
        
        self.is_recording = False
        stream.stop_stream()
        stream.close()
        
        if not voice_detected:
            print("\n⚠️ No voice detected during recording.")
            return None
        
        # Always process and save if any audio was recorded
        if audio_data:
            # Convert to numpy array
            audio_np = np.frombuffer(b''.join(audio_data), dtype=np.int16)
            audio_float = audio_np.astype(np.float32) / 32768.0
            
            # Resample to 16kHz if needed (Whisper works best with 16kHz)
            audio_float = self._resample_audio_if_needed(audio_float, target_rate=16000)

            # Transcribe using numpy array (if supported)
            segments, info = self.stt.model.transcribe(
                audio_float,
                language=None,
                task="transcribe",
                beam_size=7,
                best_of=7,
                temperature=0,
                patience=0.1,
                condition_on_previous_text=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300),
                suppress_tokens=[]
            )
            # Collect all segments
            transcription = ""
            segment_list = []
            for segment in segments:
                segment_info = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'confidence': getattr(segment, 'avg_logprob', 0)
                }
                segment_list.append(segment_info)
                transcription += segment.text
            result = {
                'transcription': transcription.strip(),
                'segments': segment_list,
                'language': getattr(info, 'language', None),
                'language_probability': getattr(info, 'language_probability', None)
            }
            # Save transcription to transcribe.txt if no output specified
            if not hasattr(self, 'output_file'):
                with open("transcribe.txt", "w", encoding="utf-8") as f:
                    f.write(transcription.strip())
                print("Transcription saved to: transcribe.txt")
            return result
        return None
    
    def start_recording_with_silence_detection(self, silence_threshold=0.05, silence_duration=3.0):
        """Convenience method for recording with custom silence detection parameters"""
        return self.start_recording(duration=None, silence_threshold=silence_threshold, silence_duration=silence_duration)
    
    def start_recording_for_public_environment(self):
        """Optimized settings for noisy public environments with auto-calibration"""
        return self.start_recording(
            duration=None, 
            silence_threshold=None,  # Use auto-calibration for better noise handling
            silence_duration=1.5,    # Shorter duration for public environments
            auto_calibrate=True
        )
    
    def _find_supported_sample_rate(self):
        """Find a supported sample rate for the default input device"""
        # Common sample rates to try (order matters - prefer 16kHz for Whisper)
        sample_rates = [16000, 44100, 48000, 22050, 8000]
        
        try:
            # Get default input device info
            default_device = self.audio.get_default_input_device_info()
            print(f"Default input device: {default_device['name']}")
            
            for rate in sample_rates:
                try:
                    # Test if this sample rate is supported
                    supported = self.audio.is_format_supported(
                        rate=rate,
                        input_device=default_device['index'],
                        input_channels=self.channels,
                        input_format=self.format
                    )
                    if supported:
                        print(f"Found supported sample rate: {rate} Hz")
                        return rate
                except Exception as e:
                    print(f"Sample rate {rate} Hz not supported: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error checking audio device: {e}")
        
        # Fallback to default
        print("Using fallback sample rate: 44100 Hz")
        return 44100
    
    def _resample_audio_if_needed(self, audio_float, target_rate=16000):
        """Resample audio to target rate if needed"""
        if self.sample_rate == target_rate:
            return audio_float
            
        try:
            import librosa
            # Resample to 16kHz for Whisper
            audio_resampled = librosa.resample(
                audio_float, 
                orig_sr=self.sample_rate, 
                target_sr=target_rate
            )
            return audio_resampled
        except ImportError:
            print(f"Warning: librosa not available for resampling. Using original sample rate {self.sample_rate} Hz.")
            # Simple decimation for downsampling (basic approach)
            if self.sample_rate > target_rate and self.sample_rate % target_rate == 0:
                factor = self.sample_rate // target_rate
                return audio_float[::factor]
            return audio_float
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'audio'):
            self.audio.terminate()


def main():
    parser = argparse.ArgumentParser(description="Speech-to-Text using faster-whisper")
    parser.add_argument("--file", "-f", type=str, help="Audio file to transcribe")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--model", "-m", type=str, default="large-v3", 
                       choices=["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"],
                       help="Whisper model size")
    parser.add_argument("--language", "-l", type=str, help="Language code (e.g., 'en', 'es', 'fr')")
    parser.add_argument("--format", type=str, default="txt", choices=["txt", "srt", "json"],
                       help="Output format")
    parser.add_argument("--realtime", "-r", action="store_true", help="Real-time transcription")
    parser.add_argument("--duration", "-d", type=int, help="Recording duration for real-time mode (seconds)")
    parser.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"], help="Device to use")
    parser.add_argument("--compute-type", type=str, default="float16", 
                       choices=["float16", "int8_float16", "int8"], help="Compute precision")
    
    args = parser.parse_args()
    
    if args.realtime:
        # Real-time mode
        rt_stt = RealTimeSTT(args.model, args.device)
        result = rt_stt.start_recording(args.duration)
        
        if result:
            print(f"\nTranscription: {result['transcription']}")
            if args.output:
                stt = SpeechToText(args.model, args.device, args.compute_type)
                stt.save_transcription(result, args.output, args.format)
    
    elif args.file:
        # File mode
        stt = SpeechToText(args.model, args.device, args.compute_type)
        result = stt.transcribe_file(args.file, args.language)
        
        print(f"\nTranscription:\n{result['transcription']}")
        
        if args.output:
            stt.save_transcription(result, args.output, args.format)
        else:
            # Auto-generate output filename
            input_path = Path(args.file)
            output_file = input_path.with_suffix(f'.{args.format}')
            stt.save_transcription(result, output_file, args.format)
    
    else:
        print("Please specify either --file for file transcription or --realtime for real-time transcription")
        parser.print_help()


if __name__ == "__main__":
    main()