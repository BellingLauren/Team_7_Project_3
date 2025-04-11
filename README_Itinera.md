# ✈️Itinera Smart Travel Planner & Assistant

## 👥 Contributors  
**Bryan Paul, Lauren Belling, George Racolta, John DeGarmo, Josh Rahman**

## 📽️ Project Presentation
View the full slideshow presentation [here](https://docs.google.com/presentation/d/1blsT5YexcNUG13J-qSFze73j6cf1fgh-WKNKphfgRdU/view).

Or watch it in slideshow mode [here](https://docs.google.com/presentation/d/1blsT5YexcNUG13J-qSFze73j6cf1fgh-WKNKphfgRdU/present).



This project is a web-based travel planning application that integrates real-time flight data and provides a chatbot assistant using the **Amadeus Travel APIs**. It features a **Streamlit interface**, enhanced by a built-in **chatbot assistant** to guide users through their travel search process.

---

## 🌐 Project Features

### Data Sources
- The project uses multiple external and internal data sources:

- Amadeus API for real-time flight and hotel data (credentials and calls are handled in app2.py)​app2.

- Google Places API is used to get local attractions​app2.

- IATA_List.csv is used to interpret and match airport codes with user input​README.

- Search history from search_history.csv is used to train the predictive model​predictive_chatbot.

### ✅ Streamlit App
- Interactive UI using tabs for:
  - **Flight Search**: Users select origin, destination, and departure date to get live flight options.
  - **Chatbot Assistant**: Offers conversational assistance for trip planning.
- Reads and utilizes IATA airport codes (`IATA_List.csv`).

### ✅ Chatbot Features
- Provides friendly, dynamic responses for:
  - Travel locations
  - Dates
  - Airports
  - APIs (Flights, Hotels, Tours)
- Helps guide users in formulating search queries.

---### 🗣️ Voice-to-Text Support
- Powered by **OpenAI's Whisper** via Gradio interface【21†source】【23†source】.
- Converts voice commands into travel queries.

### Data Cleanup and Analysis
- The predictive_chatbot.py file manages the core of the cleanup and analysis:

- Cleans and aggregates queries from search_history.csv.

- Trains on query frequency using TfidfVectorizer, KMeans clustering for frequent intent grouping, and NearestNeighbors for real-time suggestions​predictive_chatbot.

- It includes logic to update counts, avoid duplicates, and save updated model data, ensuring consistent ML behavior.

## 📁 Project Structure

```
├── app.py                  # Streamlit app
├── IATA_List.csv           # List of IATA airport codes (used by Streamlit app)
├── USA_Airports_IATA.csv   # Additional airport data (not directly used in app logic)
├── Project_3_Pipeline.ipynb# Development notebook (Jupyter)
├──
```

---

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/smart-travel-assistant.git
cd smart-travel-assistant
```

### 2. Install Dependencies
Create a virtual environment and install packages:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install -r requirements.txt
```

Sample `requirements.txt`:
```
streamlit
requests
pandas
```

---

## 🚀 Running the Application

```bash
streamlit run app.py
```

---

## 🔐 API Configuration

The app uses Amadeus APIs:
- Flight Offers

Replace the following credentials with your own in `app.py`:
```python
client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'
```

Sign up and get credentials here: [Amadeus for Developers](https://developers.amadeus.com/)

---

## 💬 Chatbot Logic

The chatbot is rule-based and responds to specific keywords like:
- `travel`, `flight`, `hotel`, `tour`, `api`, `name`, `date`, `airport`
- Responses are tailored for user engagement and guidance.

Fine tuning for the chatbot is located within the 'whisper_travel_fintune.py' file:
---

## 📌 Future Enhancements

- Add hotel and tour search in Streamlit.
- Upgrade chatbot with NLP/LLM capabilities.
- Persist conversation history and booking preferences.

---


## 🎥 Demo Video

Watch a screen recording of our Streamlit travel planner app in action:

➡️ [Click here to download or view the demo video](20250410-2205-11.2667297.mp4)

This video walks through how a user can search for flights and hotels, interact with the chatbot assistant, and use machine learning–powered suggestions for a smoother travel planning experience.


## 📄 License

This project is licensed under the MIT License. See `LICENSE` file for more details.