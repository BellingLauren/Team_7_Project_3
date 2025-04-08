import streamlit as st
import pandas as pd
import requests
import time

# Load IATA airport codes
@st.cache_data
def load_iata_data():
    return pd.read_csv("IATA_List.csv")

iata_df = load_iata_data()

# Amadeus API credentials
client_id = 'RW5x5Bn2aMZYmgyHCyomxPetDteMmM2a'
client_secret = 'sKvaa9jS36eO7OCL'

access_token = None
token_expiry_time = 0

def get_access_token():
    global access_token, token_expiry_time

    if access_token and time.time() < token_expiry_time:
        return access_token

    auth_url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    response = requests.post(auth_url, data=auth_data)
    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        token_expiry_time = time.time() + data['expires_in'] - 60
        return access_token
    else:
        return None

def get_flight_offers(origin, destination, date, adults=1, max_results=5):
    token = get_access_token()
    if not token:
        return {"error": "Failed to get access token"}

    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': date,
        'adults': adults,
        'currencyCode': 'USD',
        'max': max_results
    }

    url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
    response = requests.get(url, headers=headers, params=params)
    return response.json().get('data', []) if response.status_code == 200 else {"error": response.text}

def get_bot_response(msg):
    msg = msg.lower()
    if 'name' in msg:
        return "Nice to meet you! What is your name?"
    elif 'travel' in msg:
        return "Great! Where are you looking to travel?"
    elif 'date' in msg:
        return "What date are you looking to travel?"
    elif 'airport' in msg:
        return "What airport are you flying from, and to which airport?"
    elif 'flight' in msg:
        return "I can help you find flights! Please provide details above."
    elif 'hotel' in msg:
        return "I can help you find hotels! Hotel search is coming soon!"
    elif 'tour' in msg or 'activity' in msg:
        return "I can help you find tours and activities! Feature coming soon!"
    elif 'api' in msg:
        return "You can find the API documentation here: https://test.api.amadeus.com/"
    else:
        return "I'm here to help! Could you tell me more about your travel plans?"

# UI
st.title("✈️ Travel Planner & Assistant")

tab1, tab2 = st.tabs(["Flight Search", "Chatbot"])

with tab1:
    st.subheader("Find Flights")
   #origin = st.selectbox("From (Origin Airport)", iata_df['IATA Code'].dropna().unique())
    origin = st.selectbox("From (Origin Airport)", iata_df['iata_code'].dropna().unique())
    destination = st.selectbox("To (Destination Airport)", iata_df['iata_code'].dropna().unique())
    date = st.date_input("Departure Date")
    search = st.button("Search Flights")

    if search:
        results = get_flight_offers(origin, destination, date.strftime("%Y-%m-%d"))
        if isinstance(results, dict) and "error" in results:
            st.error(results["error"])
        elif len(results) == 0:
            st.info("No flights found.")
        else:
            for flight in results:
                price = flight['price']['total']
                segments = flight['itineraries'][0]['segments']
                st.markdown(f"**Price:** ${price}")
                for seg in segments:
                    st.write(f"{seg['departure']['iataCode']} → {seg['arrival']['iataCode']}")
                    st.write(f"{seg['departure']['at']} to {seg['arrival']['at']}")
                st.markdown("---")

with tab2:
    st.subheader("Travel Assistant Chatbot")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Say something to the assistant:")
    if user_input:
        response = get_bot_response(user_input)
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", response))

    for sender, message in st.session_state.chat_history:
        st.markdown(f"**{sender}:** {message}")