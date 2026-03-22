import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
load_dotenv(dotenv_path="api.env")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DATA_DIR = os.environ.get('DATA_DIR', '.')
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'user_upload')

client = None
if ELEVENLABS_API_KEY:
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    except Exception as e:
        print(f"Error initializing ElevenLabs: {e}")

from gtts import gTTS

def text_to_speech_file(text: str, folder : str) -> str:
    save_file_path = os.path.join(UPLOAD_FOLDER, folder, "audio.mp3")
    
    try:
        if not client:
            raise ValueError("ElevenLabs client not initialized (check API key).")
            
        print(f"Attempting ElevenLabs for {folder}...", flush=True)
        # Calling the text_to_speech conversion API with detailed parameters
        response = client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB", # Adam pre-made voice
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_turbo_v2_5", # use the turbo model for low latency
            voice_settings=VoiceSettings(
                stability=0.0, similarity_boost=1.0, style=0.0, use_speaker_boost=True, speed=1.0,
            ),
        )

        # Writing the audio to a file
        bytes_written = 0
        with open(save_file_path, "wb") as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)

        if bytes_written > 0:
            print(f"Success! ElevenLabs audio saved: {bytes_written} bytes", flush=True)
            return save_file_path
        else:
            raise ValueError("ElevenLabs returned empty data.")

    except Exception as e:
        print(f"Warning: ElevenLabs failed: {e}. Falling back to gTTS...", flush=True)
        try:
            # Fallback to Google Text-to-Speech (Free)
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(save_file_path)
            
            if os.path.exists(save_file_path) and os.path.getsize(save_file_path) > 0:
                print(f"Success! gTTS fallback audio saved!", flush=True)
                return save_file_path
            else:
                raise ValueError("gTTS failed to create file.")
        except Exception as e2:
            print(f"Error: Both TTS engines failed: {e2}", flush=True)
            if os.path.exists(save_file_path):
                os.remove(save_file_path)
            raise e2