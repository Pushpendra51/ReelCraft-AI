<<<<<<< HEAD
import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
load_dotenv(dotenv_path="api.env")
# from config import ELEVENLABS_API_KEY

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)


from gtts import gTTS

def text_to_speech_file(text: str, folder : str) -> str:
    save_file_path = os.path.join("user_upload", folder, "audio.mp3")
    
    try:
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

=======
import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
load_dotenv(dotenv_path="api.env")
# from config import ELEVENLABS_API_KEY

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)


def text_to_speech_file(text: str, folder : str) -> str:
    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB", # Adam pre-made voice
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5", # use the turbo model for low latency
        # Optional voice settings that allow you to customize the output
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )


    # uncomment the line below to play the audio back
    # play(response)

    # Generating a unique file name for the output MP3 file
    save_file_path = os.path.join(f"user_upload/{folder}","audio.mp3")

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return save_file_path

>>>>>>> d2843ecda691aedf049b50668aadd628c4843c0b
# text_to_speech_file("Hi, I'm Pushpendra, and I'm currently working on a Python-based project.","bba58def-4e69-11f0-8324-f4c88aafc124")