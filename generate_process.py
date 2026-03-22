import os
from text_to_audio import text_to_speech_file
import time
import subprocess
import shutil

# Configuration: Use Render's persistent disk if available
DATA_DIR = os.environ.get('DATA_DIR', '.')
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'user_upload')
REELS_DIR = os.path.join(DATA_DIR, 'reels')
DONE_FILE = os.path.join(DATA_DIR, 'done.txt')

def generate_audio_for_folder(folder):
    print("TTA - ", folder)
    desc_path = os.path.join(UPLOAD_FOLDER, folder, "desc.txt")
    with open(desc_path, encoding="utf-8") as f:
        raw_text = f.read()
    
    import re
    # Collapse multiple newlines and spaces to prevent AI from inserting long 3-second silences
    text = re.sub(r'\s+', ' ', raw_text).strip()
    
    print(text, folder)
    text_to_speech_file(text, folder)


def create_reel(folder):
    folder_path = os.path.join(UPLOAD_FOLDER, folder)
    input_txt = os.path.join(folder_path, "input.txt")
    audio_path = os.path.join(folder_path, "audio.mp3")
    out_path = os.path.join(REELS_DIR, f"{folder}.mp4")
    
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


def run_worker(app=None, db=None, Reel=None):
    """Main worker loop that can be run in a background thread."""
    # Ensure required directories exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(REELS_DIR, exist_ok=True)

    if not os.path.exists(DONE_FILE):
        open(DONE_FILE, "w").close()

    while True:
        try:
            if not os.path.exists(DONE_FILE):
                open(DONE_FILE, "w").close()
                
            with open(DONE_FILE, "r", encoding="utf-8") as f:
                done_folders = [line.strip() for line in f.readlines() if line.strip()]

            done_set = set(done_folders)
            
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
            folders = os.listdir(UPLOAD_FOLDER)

            for folder in folders:
                if folder in done_set:
                    continue
                
                folder_path = os.path.join(UPLOAD_FOLDER, folder)
                if not os.path.isdir(folder_path):
                    continue
                    
                input_txt = os.path.join(folder_path, "input.txt")
                if not os.path.exists(input_txt):
                    continue
                    
                print(f"[START] Starting reel generation: {folder}", flush=True)
                try:
                    audio_path = os.path.join(folder_path, "audio.mp3")
                    desc_path = os.path.join(folder_path, "desc.txt")
                    
                    if os.path.exists(desc_path) and not os.path.exists(audio_path):
                        print(f"[TTS] Generating TTS for {folder}", flush=True)
                        generate_audio_for_folder(folder)
                    elif os.path.exists(audio_path):
                        print(f"[MUSIC] Using uploaded music for {folder}", flush=True)
                    else:
                        print(f"[SILENT] No audio provided for {folder}. Creating silent reel.", flush=True)
                        
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) == 0:
                        print(f"[WARN] Audio file was empty for {folder}. Deleting.", flush=True)
                        os.remove(audio_path)

                    if os.path.exists(audio_path) and os.path.getsize(audio_path) == 0:
                        print(f"[CRITICAL] 0-byte audio detected before ffmpeg. Deleting it.", flush=True)
                        os.remove(audio_path)

                    create_reel(folder)
                    
                    with open(DONE_FILE, "a") as f:
                        f.write(folder + "\n")
                        
                    if app and db and Reel:
                        with app.app_context():
                            reel_record = Reel.query.filter_by(job_id=folder).first()
                            if reel_record:
                                reel_record.status = 'completed'
                                db.session.commit()
                            
                    print(f"[SUCCESS] Reel created successfully: {folder}", flush=True)
                    shutil.rmtree(folder_path, ignore_errors=True)
                    print(f"[CLEANUP] Cleaned up folder: {folder_path}", flush=True)
                except Exception as e:
                    print(f"[ERROR] Critical Error: create_reel failed for {folder}: {e}", flush=True)

            time.sleep(3)
        except Exception as outer_e:
            print(f"[ERROR] Outer worker loop error: {outer_e}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    from main import app, db, Reel
    run_worker(app, db, Reel)
