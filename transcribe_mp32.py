
import subprocess
def convert_mp4_to_mp3(input_mp4: str, output_mp3: str):
    """
    Convert an .mp4 file to .mp3 using ffmpeg via subprocess.
    """
    command = [
        "ffmpeg",
        "-i", input_mp4,      # Input video file
        "-vn",                # Disable video
        "-acodec", "libmp3lame",  # Use the MP3 audio codec
        output_mp3
    ]
    subprocess.run(command, check=True)
    print(f"Converted {input_mp4} to {output_mp3}")

convert_mp4_to_mp3("/mnt/c/Users/degar/OneDrive/Desktop/Team_7_Project_3/Recording.m4a", "/mnt/c/Users/degar/OneDrive/Desktop/Team_7_Project_3/Recording.mp3")

# transcribe_mp3.py
from transformers import pipeline
def transcribe_mp3(mp3_path: str, output_path: str):
    """
    Transcribe the MP3 file at `mp3_path` using a Whisper model
    and save the transcription to `output_path`.
    """
    asr_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-small.en",return_timestamps=True)
    result = asr_pipeline(mp3_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["text"] + "\n")
if __name__ == "__main__":
    #MP3_FILE = "/mnt/c/Users/degar/OneDrive/Desktop/Team_7_Project_3/Emotions.mp3"
    MP3_FILE = "/mnt/c/Users/degar/OneDrive/Desktop/Team_7_Project_3/Recording.m4a"
    OUTPUT_FILE = "/mnt/c/Users/degar/OneDrive/Desktop/Team_7_Project_3/audiototext.txt"
    transcribe_mp3(MP3_FILE, OUTPUT_FILE)
    print("Done! Transcription saved to:", OUTPUT_FILE)
#/mnt/c/Users/tyler/OneDrive/Desktop/whispertest.py
