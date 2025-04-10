from transformers import pipeline
import gradio as gr
pipe = pipeline(model="openai/whisper-small")
latest_transcription = ""
def transcribe(audio):
    global latest_transcription
    # Run pipeline
    text = pipe(audio)["text"]
    # Store result in global variable
    latest_transcription = text
    # Return text for Gradio's display
    return text
def get_latest_transcription():
    return latest_transcription
iface = gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(sources=["microphone"], type="filepath"),
    outputs="text",
    title="Whisper Small Hindi",
    description="Realtime demo for Hindi speech recognition using a fine-tuned Whisper small model.",
)
#    Importing this file from somewhere else will NOT auto-launch Gradio.
if __name__ == "__main__":
    iface.launch()