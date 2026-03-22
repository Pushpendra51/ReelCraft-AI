import os
from text_to_audio import text_to_speech_file
import time
import subprocess
import shutil
from main import app, db, Reel

def generate_audio_for_folder(folder):
    print("TTA - ", folder)
    with open(os.path.join("user_upload", folder, "desc.txt"), encoding="utf-8") as f:
        raw_text = f.read()
    
    import re
    # Collapse multiple newlines and spaces to prevent AI from inserting long 3-second silences
    text = re.sub(r'\s+', ' ', raw_text).strip()
    
    print(text, folder)
    text_to_speech_file(text, folder)  # Fixed: was commented out before


def create_reel(folder):
    input_txt = os.path.join("user_upload", folder, "input.txt")
    audio_path = os.path.join("user_upload", folder, "audio.mp3")
    out_path = os.path.join("static", "reels", f"{folder}.mp4")
    
    # Cinematic vertical scaling + padding
    vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p,fps=30"
    
    if os.path.exists(audio_path):
        # Audio exists: Map video from input 0 and audio from input 1
        args = [
            "ffmpeg", "-y", 
            "-f", "concat", "-safe", "0", "-i", input_txt,
            "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", vf,
            "-c:v", "libx264", "-r", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "192k", "-af", "aresample=async=1", "-shortest",
            out_path
        ]
    else:
        # No audio: Just process video
        args = [
            "ffmpeg", "-y", 
            "-f", "concat", "-safe", "0", "-i", input_txt,
            "-vf", vf,
            "-c:v", "libx264", "-r", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            out_path
        ]
        
    subprocess.run(args, check=True)
    print("CR - ", folder)


if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("user_upload", exist_ok=True)
    os.makedirs(os.path.join("static", "reels"), exist_ok=True)

    if not os.path.exists("done.txt"):
        open("done.txt", "w").close()

    while True:
        print("Processing queue...", flush=True)
        if not os.path.exists("done.txt"):
            open("done.txt", "w").close()
            
        with open("done.txt", "r", encoding="utf-8") as f:
            done_folders = [line.strip() for line in f.readlines() if line.strip()]

        # Unique set for faster lookup
        done_set = set(done_folders)
        
        if not os.path.exists("user_upload"):
            os.makedirs("user_upload", exist_ok=True)
            
        folders = os.listdir("user_upload")

        for folder in folders:
            if folder in done_set:
                continue
            
            # Check if it's a valid folder with our input.txt
            folder_path = os.path.join("user_upload", folder)
            if not os.path.isdir(folder_path):
                continue
                
            input_txt = os.path.join(folder_path, "input.txt")
            if not os.path.exists(input_txt):
                continue
                
            print(f"[START] Starting reel generation: {folder}", flush=True)
            try:
                # Try to generate AI audio if desc.txt exists and audio.mp3 doesn't
                audio_path = os.path.join(folder_path, "audio.mp3")
                desc_path = os.path.join(folder_path, "desc.txt")
                
                try:
                    if os.path.exists(desc_path) and not os.path.exists(audio_path):
                        print(f"[TTS] Generating TTS for {folder}", flush=True)
                        generate_audio_for_folder(folder)
                    elif os.path.exists(audio_path):
                        print(f"[MUSIC] Using uploaded music for {folder}", flush=True)
                    else:
                        print(f"[SILENT] No audio provided for {folder}. Creating silent reel.", flush=True)
                        
                    # Verify audio was actually created/exists and is not empty
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) == 0:
                        print(f"[WARN] Audio file was empty for {folder}. Deleting.", flush=True)
                        os.remove(audio_path)
                except Exception as tts_error:
                    print(f"[WARN] Audio generation failed for {folder}: {tts_error}. Proceeding as-is.", flush=True)

                # Final safety check: if audio.mp3 exists but is 0-bytes, it will crash ffmpeg. Delete it.
                if os.path.exists(audio_path) and os.path.getsize(audio_path) == 0:
                    print(f"[CRITICAL] 0-byte audio detected before ffmpeg. Deleting it.", flush=True)
                    os.remove(audio_path)

                create_reel(folder)     # Stitch images + audio into mp4
                
                with open("done.txt", "a") as f:
                    f.write(folder + "\n")
                    
                # Update DB status
                with app.app_context():
                    reel_record = Reel.query.filter_by(job_id=folder).first()
                    if reel_record:
                        reel_record.status = 'completed'
                        db.session.commit()
                        
                print(f"[SUCCESS] Reel created successfully: {folder}", flush=True)
                
                # Cleanup the raw files to save disk space
                shutil.rmtree(folder_path, ignore_errors=True)
                print(f"[CLEANUP] Cleaned up folder: {folder_path}", flush=True)
            except Exception as e:
                print(f"[ERROR] Critical Error: create_reel failed for {folder}: {e}", flush=True)

        time.sleep(3)
