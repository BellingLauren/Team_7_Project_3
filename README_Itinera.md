
# ✈️ Itinera: Smart Travel Planner & Chatbot Assistant

**Team 7 - Project 3**  
Contributors: Bryan Paul, Lauren Belling, George Racolta, John DeGarmo, Josh Rahman

---

## 🎥 Project Presentation

- [View Slideshow (Editable)](https://docs.google.com/presentation/d/1blsT5YexcNUG13J-qSFze73j6cf1fgh-WKNKphfgRdU/view)
- [Watch Slideshow (Presentation Mode)](https://docs.google.com/presentation/d/1blsT5YexcNUG13J-qSFze73j6cf1fgh-WKNKphfgRdU/present)

---

## 🎯 Overview

**Itinera** is an AI-powered, web-based travel assistant that streamlines the trip planning experience by integrating real-time flight and hotel data, a predictive chatbot, and voice-based input using Whisper. Built with Streamlit and powered by Amadeus and Google APIs, Itinera offers intuitive tools to explore destinations and plan trips interactively.

---

## 🌐 Features

### Data Sources
- The project uses multiple external and internal data sources:

- Amadeus API for real-time flight and hotel data (credentials and calls are handled in app2.py)​app2.

- Google Places API is used to get local attractions​app2.

- IATA_List.csv is used to interpret and match airport codes with user input​README.

- Search history from search_history.csv is used to train the predictive model​predictive_chatbot.

### 🚀 Travel Search
- **Real-time flight and hotel data** via Amadeus API.
- **Google Flights integration** for direct booking.
- Dynamic suggestions powered by machine learning.

### 🤖 Smart Chatbot
- Predictive, learning-based assistant for:
  - Travel tips
  - Destination info
  - Search assistance
- Personalized query suggestions using a TF-IDF + K-Means/Near Neighbors ML model【29†source】.
- Learns and adapts from user queries over time【28†source】.

### 🗣️ Voice-to-Text Support
- Powered by **OpenAI's Whisper** via Gradio interface【21†source】【23†source】.
- Converts voice commands into travel queries.

### Data Cleanup and Analysis
- The predictive_chatbot.py file manages the core of the cleanup and analysis:

- Cleans and aggregates queries from search_history.csv.

- Trains on query frequency using TfidfVectorizer, KMeans clustering for frequent intent grouping, and NearestNeighbors for real-time suggestions​predictive_chatbot.

- It includes logic to update counts, avoid duplicates, and save updated model data, ensuring consistent ML behavior.

---

## 🛠️ Tech Stack

| Area            | Technologies                              |
|-----------------|-------------------------------------------|
| UI              | Streamlit, Gradio, HTML/CSS               |
| ML & Chatbot    | Scikit-learn, Pandas, TF-IDF, KMeans, NearestNeighbors, Hugging Face |
| APIs            | Amadeus, Google Places, Google Flights    |
| Audio Handling  | Whisper (Gradio)                          |
| Data            | IATA Codes (CSV)                          |
| Others          | BeautifulSoup, Requests, ffmpeg (for MP3 conversion) |

---

## 🧠 Predictive Chatbot

- Learns from past queries saved in `search_history.csv`.
- Trained on TF-IDF vectorized query data with KMeans for common topic clustering.
- Provides adaptive suggestions based on destination【28†source】.

---

## 📁 Key Files & Structure

```
├── app2.py                    # Main Streamlit app
├── chatbot_integration.py     # Chatbot state/suggestion handler
├── predictive_chatbot.py      # Core ML chatbot class
├── text_var.py                # Shared variables (e.g., transcript text)
├── transcribe_mp32.py         # Whisper audio transcription w/ file conversion
├── speaktotext.py             # Whisper-based Gradio voice app
├── whisper.py                 # Alternative Whisper demo (Hindi)
├── IATA_List.csv              # IATA airport code reference
├── search_history.csv         # CSV tracking user queries
├── chatbot_model.pkl          # Pickled ML model and vectorizer
├── styles.css                 # Custom styles
├── audiototext.txt            # Output from voice transcription
├── Project_3_Pipeline.ipynb   # Development notebook
```

---

## 📦 Installation

### Clone & Set Up

```bash
git clone https://github.com/your-username/itinera-travel-assistant.git
cd itinera-travel-assistant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Sample `requirements.txt`

```
streamlit
pandas
scikit-learn
requests
transformers
gradio
python-dotenv
beautifulsoup4
```

---

## 🔐 API Keys (Environment Variables)

Create a `.env` file and add the following:

```bash
api_key=YOUR_AMADEUS_CLIENT_ID
api_secret=YOUR_AMADEUS_CLIENT_SECRET
GOOGLE_PLACES_API_KEY=YOUR_GOOGLE_PLACES_KEY
```

---

## 🚀 Run the App

```bash
streamlit run app2.py
```

---

## 🔊 Launch Voice Assistant

```bash
python speaktotext.py
```

This opens a Gradio interface for real-time voice recognition using Whisper.

---

## 🔮 Future Enhancements

- LLM-based contextual chatbot (GPT).
- Enhanced hotel/tour recommendations.
- Save and manage itineraries.
- Natural language understanding for broader queries.

---

## 📄 License

This project is licensed under the MIT License.
