#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Building ReelCraft AI ---"

# Install Python dependencies
pip install -r requirements.txt

# Create ffmpeg directory if it doesn't exist
mkdir -p ffmpeg_bin

# Install ffmpeg if not already present
if [ ! -f "ffmpeg_bin/ffmpeg" ]; then
  echo "Downloading ffmpeg..."
  # Using a reliable static build source
  wget -q https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz
  tar xf ffmpeg-master-latest-linux64-gpl.tar.xz --strip-components=2 -C ffmpeg_bin "ffmpeg-master-latest-linux64-gpl/bin/ffmpeg" "ffmpeg-master-latest-linux64-gpl/bin/ffprobe"
  rm ffmpeg-master-latest-linux64-gpl.tar.xz
  echo "ffmpeg installed in ffmpeg_bin/"
fi

# Ensure binaries are executable
chmod +x ffmpeg_bin/ffmpeg
chmod +x ffmpeg_bin/ffprobe

echo "--- Build Complete ---"
