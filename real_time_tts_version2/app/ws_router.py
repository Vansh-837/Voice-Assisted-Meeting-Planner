import os
import uuid
import re
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.tts_engine import synthesize_text

router = APIRouter()

# Configuration
MIN_SENTENCE_LENGTH = 3  # Minimum characters in a sentence to speak
connection_states = {}   # Global state per connection


@router.websocket("/ws/tts")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("📡 WebSocket connection open")

    connection_id = id(websocket)
    connection_states[connection_id] = {
        "current_text": "",
        "last_spoken_position": 0,
        "is_speaking": False
    }

    try:
        while True:
            try:
                data = await websocket.receive_text()
                state = connection_states[connection_id]
                state["current_text"] = data.strip()
                await handle_sentence_speech(connection_id)
            except WebSocketDisconnect:
                print("🔌 WebSocket client disconnected")
                break
            except Exception as e:
                print(f"❌ WebSocket error: {e}")
    finally:
        connection_states.pop(connection_id, None)


async def handle_sentence_speech(connection_id):
    state = connection_states.get(connection_id)
    if not state or state["is_speaking"]:
        return

    full_text = state["current_text"]
    unspoken_text = full_text[state["last_spoken_position"]:]

    if not unspoken_text.strip():
        return

    sentences_to_speak = extract_complete_sentences(unspoken_text)
    if not sentences_to_speak:
        return

    state["is_speaking"] = True

    try:
        for sentence_info in sentences_to_speak:
            sentence_text = sentence_info["text"].strip()
            if len(sentence_text) < MIN_SENTENCE_LENGTH or not any(c.isalnum() for c in sentence_text):
                state["last_spoken_position"] += sentence_info["length"]
                print(f"⏭️ Skipped: '{sentence_text}'")
                continue

            await speak_sentence_terminal(sentence_text)
            state["last_spoken_position"] += sentence_info["length"]
            print(f"🗣️ Spoke: '{sentence_text}'")

    except Exception as e:
        print(f"❌ Error while speaking: {e}")
    finally:
        state["is_speaking"] = False


def extract_complete_sentences(text):
    if not text.strip():
        return []

    pattern = r'([^.!?]*[.!?])(?:\s+|$)'
    matches = re.finditer(pattern, text)
    sentences = []

    for match in matches:
        sentence_text = match.group(1).strip()
        sentence_length = len(match.group(0))
        if sentence_text and len(sentence_text) > 2:
            sentences.append({
                "text": sentence_text,
                "length": sentence_length
            })

    return sentences


async def speak_sentence_terminal(text):
    if not text.strip():
        return

    filename = f"sentence_{uuid.uuid4()}.wav"
    output_path = f"temp_audio/{filename}"  # make sure this folder exists
    speaker_wav = "my/cloning_Male.wav"
    language = "en"

    success = await synthesize_text(text, speaker_wav, language, output_path)

    if success:
        # Play the audio using ffplay in background
        os.system(f"ffplay -nodisp -autoexit {output_path} >/dev/null 2>&1")
    else:
        print(f"❌ Failed to synthesize: {text}")


@router.websocket("/ws/tts/reset")
async def reset_speech_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = id(websocket)
    if connection_id in connection_states:
        connection_states[connection_id].update({
            "last_spoken_position": 0,
            "current_text": ""
        })
        print("🔄 Speech state reset")
    await websocket.close()
