


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
    MP3_FILE = "C:\Users\Bryan\Desktop\Final_Project\Team_7_Project_3\Recording.mp3"
    OUTPUT_FILE = "C:\Users\Bryan\Desktop\Final_Project\Team_7_Project_3\audiototext.txt"
    transcribe_mp3(MP3_FILE, OUTPUT_FILE)
    print("Done! Transcription saved to:", OUTPUT_FILE)
#/mnt/c/Users/tyler/OneDrive/Desktop/whispertest.py

with open("/mnt/c/Users/degar/OneDrive/Desktop/Team_7_Project_3/audiototext.txt", "r", encoding="utf-8") as f:
    TRANSCRIPT_TEXT = f.read()
