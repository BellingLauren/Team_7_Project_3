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

# Function to get hotel offers
def get_hotels(city_code, radius=5):
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to get access token"}

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'cityCode': city_code,
        'radius': radius,
        'radiusUnit': 'KM',
        'ratings': '3,4,5',  # Optional: filter by star ratings
        'hotelSource': 'ALL'  # ALL, BEDBANK, or DIRECTCHAIN
    }

    hotels_url = 'https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city'
    response = requests.get(hotels_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()['data']
    else:
        return {"error": f"API Request failed: {response.status_code}, {response.text}"}
    
    # Function to get tour activities
def get_tour_activities(latitude, longitude, radius=20):
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to get access token"}

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'radius': radius,
        'currencyCode': 'USD'
    }

    tours_url = 'https://test.api.amadeus.com/v1/shopping/activities'
    response = requests.get(tours_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()['data']
    else:
        return {"error": f"API Request failed: {response.status_code}, {response.text}"}

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
    st.subheader("Find Hotels")
    city_code = st.selectbox("City Code", iata_df['iata_code'].dropna().unique())
    radius = st.slider("Search Radius (KM)", min_value=1, max_value=50, value=5)
    search_hotels = st.button("Search Hotels")

    if search_hotels:
        hotel_results = get_hotels(city_code, radius)
        if isinstance(hotel_results, dict) and "error" in hotel_results:
            st.error(hotel_results["error"])
        elif len(hotel_results) == 0:
            st.info("No hotels found.")
        else:
            for hotel in hotel_results:
                st.markdown(f"**Hotel:** {hotel['name']}")
                st.write(f"Address: {hotel.get('address', {}).get('lines', ['N/A'])[0]}, {hotel.get('address', {}).get('cityName', 'N/A')}")
                st.write(f"Category: {hotel.get('rating', 'N/A')}-star")
                if 'contact' in hotel and 'phone' in hotel['contact']:
                    st.write(f"Phone: {hotel['contact']['phone']}")
                st.markdown("---")

with tab3:
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