import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
SPEAKER_WAV_PATH = "my/cloning_Male.wav"
LANGUAGE = "en"
