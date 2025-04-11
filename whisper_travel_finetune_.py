#!/usr/bin/env python3
# whisper_travel_finetune.py - Complete script for fine-tuning Whisper on travel data
# Based on Sanchit Gandhi's notebook with modifications for travel-specific use

import os
import torch
import pandas as pd
import numpy as np
from datasets import Dataset, Audio
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer
import evaluate
from huggingface_hub import login, HfApi
import argparse

# Configure argument parser
parser = argparse.ArgumentParser(description="Fine-tune Whisper for travel voice recognition")
parser.add_argument("--audio_dir", type=str, default=None, help="Directory containing audio files")
parser.add_argument("--transcription_file", type=str, default=None, help="File containing transcriptions")
parser.add_argument("--output_dir", type=str, default="./whisper-travel-finetuned", help="Output directory for model")
parser.add_argument("--hf_token", type=str, default=None, help="Hugging Face API token")
parser.add_argument("--hf_model_id", type=str, default=None, help="Hugging Face model ID for upload")
parser.add_argument("--base_model", type=str, default="openai/whisper-small", help="Base Whisper model to fine-tune")
parser.add_argument("--batch_size", type=int, default=4, help="Batch size for training")
parser.add_argument("--learning_rate", type=float, default=1e-5, help="Learning rate")
parser.add_argument("--max_steps", type=int, default=200, help="Maximum training steps")
parser.add_argument("--synthetic", action="store_true", help="Use synthetic data if no audio files available")
parser.add_argument("--upload", action="store_true", help="Upload model to Hugging Face after training")
args = parser.parse_args()

print("Starting Whisper fine-tuning for travel voice recognition...")
print(f"Using base model: {args.base_model}")

# Step 1: Install required packages (uncomment if needed)
# import subprocess
# subprocess.run(["pip", "install", "-q", "transformers", "datasets", "evaluate", "jiwer", "accelerate", "tensorboard", "huggingface_hub"])

# Step 2: Prepare dataset
def prepare_dataset():
    """Prepare the dataset for fine-tuning"""
    print("Preparing dataset...")
    
    # Check for audio files
    has_audio = False
    audio_files = []
    
    if args.audio_dir and os.path.exists(args.audio_dir):
        audio_files = [f for f in os.listdir(args.audio_dir) if f.endswith(('.mp3', '.wav'))]
        if audio_files:
            has_audio = True
            print(f"Found {len(audio_files)} audio files in {args.audio_dir}")
    
    # Load transcription text if available
    transcription_text = ""
    if args.transcription_file and os.path.exists(args.transcription_file):
        with open(args.transcription_file, 'r', encoding='utf-8') as f:
            transcription_text = f.read()
        print(f"Loaded transcription from {args.transcription_file}")
    
    # Option 1: Use real audio files if available
    if has_audio:
        data = []
        for audio_file in audio_files:
            data.append({
                'audio': os.path.join(args.audio_dir, audio_file),
                'sentence': transcription_text  # Using same transcription for all files
            })
        
        df = pd.DataFrame(data)
        dataset = Dataset.from_pandas(df)
        print(f"Created dataset with {len(dataset)} real audio examples")
        
    # Option 2: Use synthetic data
    else:
        if args.synthetic or not has_audio:
            print("No audio files found or --synthetic flag used. Creating synthetic dataset...")
            
            # Default travel queries if no transcription file
            if not transcription_text:
                travel_queries = [
                    "I want to plan a trip to Honolulu, Hawaii from Detroit, Michigan.",
                    "How much are flights from Detroit to Hawaii?",
                    "I would like to take a trip to Honolulu.",
                    "Find me hotels in Hawaii.",
                    "What are the best attractions in Honolulu?",
                    "I need a rental car in Hawaii.",
                    "Are there any direct flights from Detroit to Honolulu?",
                    "What's the weather like in Hawaii in June?",
                    "How much does it cost to travel from Detroit to Honolulu?",
                    "Book a flight from Detroit to Honolulu for next week.",
                    "What's the cheapest time to visit Hawaii?",
                    "Do I need a passport to travel to Hawaii?",
                    "Are there any all-inclusive resorts in Hawaii?",
                    "What's the best island to visit in Hawaii?",
                    "How long is the flight from Detroit to Honolulu?"
                ]
            else:
                # Use the transcription as one query and add variations
                travel_queries = [transcription_text]
                
                # Create variations by adding common phrases
                base_query = transcription_text.strip()
                variations = [
                    f"Can you tell me about {base_query}",
                    f"I need information on {base_query}",
                    f"Please help me with {base_query}",
                    f"I'm looking for {base_query}",
                    f"Could you find {base_query}"
                ]
                travel_queries.extend(variations)
            
            df = pd.DataFrame({'sentence': travel_queries})
            dataset = Dataset.from_pandas(df)
            print(f"Created synthetic dataset with {len(dataset)} examples")
        else:
            raise ValueError("No audio files found and --synthetic flag not used. Please provide audio files or use --synthetic.")
    
    # Split dataset into train/validation
    split_dataset = dataset.train_test_split(test_size=0.2)
    train_dataset = split_dataset['train']
    eval_dataset = split_dataset['test']
    
    print(f"Training set: {len(train_dataset)} examples")
    print(f"Evaluation set: {len(eval_dataset)} examples")
    
    return train_dataset, eval_dataset, has_audio

# Step 3: Initialize processor and model
def setup_model():
    """Set up the Whisper processor and model"""
    print(f"Loading processor and model from {args.base_model}...")
    processor = WhisperProcessor.from_pretrained(args.base_model)
    model = WhisperForConditionalGeneration.from_pretrained(args.base_model)
    
    # Set forced decoder IDs for English transcription
    forced_decoder_ids = processor.get_decoder_prompt_ids(language="english", task="transcribe")
    
    return processor, model, forced_decoder_ids

# Step 4: Feature preparation and dataset processing
def process_datasets(train_dataset, eval_dataset, processor, has_audio):
    """Process datasets to prepare for training"""
    print("Processing datasets...")
    
    if has_audio:
        # First cast audio column to Audio type
        train_dataset = train_dataset.cast_column("audio", Audio(sampling_rate=16000))
        eval_dataset = eval_dataset.cast_column("audio", Audio(sampling_rate=16000))
        
        # Define audio processing function
        def prepare_audio_dataset(batch):
            # Load and resample audio data
            audio = batch["audio"]
            
            # Process audio to input features
            batch["input_features"] = processor.feature_extractor(
                audio["array"], sampling_rate=audio["sampling_rate"]
            ).input_features[0]
            
            # Process text to labels
            batch["labels"] = processor.tokenizer(batch["sentence"]).input_ids
            return batch
        
        # Apply processing
        train_dataset = train_dataset.map(prepare_audio_dataset, remove_columns=train_dataset.column_names)
        eval_dataset = eval_dataset.map(prepare_audio_dataset, remove_columns=eval_dataset.column_names)
    else:
        # For synthetic data, create fake audio features
        def prepare_synthetic_dataset(batch):
            # Create synthetic audio features (2 seconds at 16kHz)
            fake_audio = np.random.randn(32000).astype(np.float32)
            
            # Process fake audio to input features
            batch["input_features"] = processor.feature_extractor(
                fake_audio, sampling_rate=16000
            ).input_features[0]
            
            # Process text to labels
            batch["labels"] = processor.tokenizer(batch["sentence"]).input_ids
            return batch
        
        # Apply processing
        train_dataset = train_dataset.map(prepare_synthetic_dataset, remove_columns=train_dataset.column_names)
        eval_dataset = eval_dataset.map(prepare_synthetic_dataset, remove_columns=eval_dataset.column_names)
    
    print("Datasets processed successfully")
    return train_dataset, eval_dataset

# Step 5: Set up trainer
def setup_trainer(train_dataset, eval_dataset, processor, model, forced_decoder_ids):
    """Set up the Seq2SeqTrainer for fine-tuning"""
    print("Setting up trainer...")
    
    # Define compute metrics function using Word Error Rate
    wer_metric = evaluate.load("wer")
    
    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        
        # Replace -100 with the pad_token_id
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        
        # Convert ids to strings
        pred_str = processor.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.batch_decode(label_ids, skip_special_tokens=True)
        
        # Compute WER
        wer_score = 100 * wer_metric.compute(predictions=pred_str, references=label_str)
        
        return {"wer": wer_score}
    
    # Data collator
    def data_collator(features):
        input_features = [feature["input_features"] for feature in features]
        labels = [feature["labels"] for feature in features]
        
        # Pad input_features to max length in batch
        max_length = max([len(x) for x in input_features])
        padded_input_features = []
        
        for feature in input_features:
            padding_length = max_length - len(feature)
            if padding_length > 0:
                padded_feature = torch.cat([feature, torch.zeros(padding_length, dtype=feature.dtype)], dim=0)
            else:
                padded_feature = feature
            padded_input_features.append(padded_feature)
        
        # Stack input features
        batch_input_features = torch.stack(padded_input_features)
        
        return {
            "input_features": batch_input_features,
            "labels": labels,
            "decoder_input_ids": None
        }
    
    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=2,  # To handle GPU memory constraints
        learning_rate=args.learning_rate,
        warmup_steps=50,
        max_steps=args.max_steps,
        gradient_checkpointing=True,
        fp16=torch.cuda.is_available(),  # Use FP16 if GPU is available
        evaluation_strategy="steps",
        eval_steps=50,
        save_steps=50,
        logging_steps=10,
        report_to=["tensorboard"],
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        generation_max_length=225,
        predict_with_generate=True,
        push_to_hub=False,
    )
    
    # Create trainer
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
        tokenizer=processor.feature_extractor,
        data_collator=data_collator,
    )
    
    # Set forced decoder ids
    model.config.forced_decoder_ids = forced_decoder_ids
    
    return trainer

# Step 6: Train the model
def train_model(trainer):
    """Train the fine-tuned model"""
    print("\nStarting training... This will take some time.")
    print("Watch progress in the training metrics below.")
    
    # Start training
    trainer.train()
    
    print("\nTraining complete!")
    
    # Evaluate model
    print("Evaluating model...")
    eval_results = trainer.evaluate()
    print(f"Evaluation results: {eval_results}")
    
    return eval_results

# Step 7: Save and upload model
def save_and_upload_model(processor, eval_results):
    """Save and optionally upload the model to Hugging Face Hub"""
    # Create model card
    print(f"Saving model to {args.output_dir}...")
    wer_score = eval_results.get("eval_wer", "N/A")
    
    # Default model ID if not provided
    model_id = args.hf_model_id or "your-username/whisper-travel-finetuned"
    
    model_card = f"""---
language: en
license: apache-2.0
tags:
- whisper
- audio
- speech-recognition
- transcription
- travel
metrics:
- wer: {wer_score}
---

# Whisper Fine-Tuned for Travel Applications

This model is fine-tuned from {args.base_model} specifically for travel-related voice queries and commands. It's designed to improve speech recognition accuracy for travel planning applications.

## Use Cases

- Travel voice assistants
- Flight and hotel booking systems
- Travel planning applications
- Tourist information systems

## Performance

- Word Error Rate (WER): {wer_score}

## Training

This model was fine-tuned on a custom dataset of travel-related queries and commands.

## Usage

```python
from transformers import pipeline

# Load the model
asr = pipeline("automatic-speech-recognition", model="{model_id}")

# Transcribe audio
transcription = asr("path/to/audio.mp3")
print(transcription["text"])
```

## Integration with Travel Applications

This model can be integrated with travel planning applications to provide accurate voice recognition for travel queries.
"""
    
    # Save model card
    with open(os.path.join(args.output_dir, "README.md"), "w") as f:
        f.write(model_card)
    
    # Upload to Hugging Face if requested
    if args.upload:
        if not args.hf_token:
            print("Warning: No Hugging Face token provided. Skipping upload.")
            return
        
        print(f"Uploading model to Hugging Face as {model_id}...")
        
        # Login to Hugging Face
        login(token=args.hf_token)
        
        # Upload model
        api = HfApi()
        api.upload_folder(
            folder_path=args.output_dir,
            repo_id=model_id,
            repo_type="model"
        )
        
        print(f"Model uploaded successfully to: https://huggingface.co/{model_id}")
    else:
        print("Model upload skipped. Use --upload to upload to Hugging Face.")

# Step 8: Main execution
def main():
    """Main execution function"""
    print("\n===== Whisper Fine-Tuning for Travel Voice Recognition =====\n")
    
    # Prepare datasets
    train_dataset, eval_dataset, has_audio = prepare_dataset()
    
    # Set up model and processor
    processor, model, forced_decoder_ids = setup_model()
    
    # Process datasets
    processed_train_dataset, processed_eval_dataset = process_datasets(
        train_dataset, eval_dataset, processor, has_audio
    )
    
    # Set up trainer
    trainer = setup_trainer(
        processed_train_dataset, processed_eval_dataset, 
        processor, model, forced_decoder_ids
    )
    
    # Train model
    eval_results = train_model(trainer)
    
    # Save processor for inference
    processor.save_pretrained(args.output_dir)
    
    # Save and upload model
    save_and_upload_model(processor, eval_results)

if __name__ == "__main__":
    main()