from transformers import pipeline
import gradio as gr
   
# Use your fine-tuned model
pipe = pipeline(model="{args.hf_model_id or 'path/to/local/model'}")
   
def transcribe(audio):
    text = pipe(audio)["text"]
    return text
   
iface = gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(sources=["microphone"], type="filepath"),
    outputs="text",
    title="Travel Voice Assistant",
    description="Voice recognition for travel planning.",
)
   
if __name__ == "__main__":
    iface.launch()