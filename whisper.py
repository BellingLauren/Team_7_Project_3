from transformers import pipeline
import gradio as gr
pipe = pipeline(model="openai/whisper-small")  # change to "your-username/the-name-you-picked"
def transcribe(audio):
    text = pipe(audio)["text"]
    return text
iface = gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(sources=["microphone"], type="filepath"),
    outputs="text",
    title="Whisper English Speech Recognition",
    description="Realtime demo for English speech recognition using a fine-tuned Whisper small model.",
)
iface.launch()