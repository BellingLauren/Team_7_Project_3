import streamlit as st
import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv
   
# Amadeus API credentials
load_dotenv()
client_id = os.getenv("api_key")
client_secret = os.getenv("api_secret")
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
    
#Function to convert city name to destination IATA code
def city_to_iata(city_name):
    token = get_access_token()
    if not token:
        return {"error": "Failed to get access token"}
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'keyword': city_name,
        'subType': 'CITY' 
    }
    url = 'https://test.api.amadeus.com/v1/reference-data/locations'
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json().get('data', [])
        if data:
            return data[0].get('iataCode')
        else:
            return None
    else:
        return {"error": response.text}
    
# Function to get flight offers
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

# Chatbot Function
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

# Streamlit Interface
st.title(":airplane: Travel Planner & Assistant")
tab1, tab2, tab3, tab4 = st.tabs(["Flight Search", "Find Hotels","Tour Activities Search","Chatbot"])
with tab1:
    st.subheader("Find Flights")
    origin = city_to_iata(st.text_input("From (Origin City)", key="origin_city_input"))
    destination = city_to_iata(st.text_input("To (Destination City)", key="destination_city_input"))
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
    st.subheader("Hotel Search")
    city = st.text_input("Enter a city for hotel recommendations:", key="hotel_input")
    search_hotels = st.button("Search Hotels")
    if search_hotels and city:
        hotels = get_hotels(city)
        if isinstance(hotels, dict) and "error" in hotels:
            st.error(hotels["error"])
        elif len(hotels) == 0:
            st.info("No hotels found.")
        else:
            for hotel in hotels:
                st.markdown(f"**Hotel Name:** {hotel['name']}")
                st.write(f"**Address:** {hotel['address']['lines'][0]}")
                st.write(f"**Distance from city center:** {hotel['distance']['value']} {hotel['distance']['unit']}")
                st.write(f"**Rating:** {hotel.get('rating', 'N/A')}")
                st.markdown("---")
with tab3:
    st.subheader("Tour Activities Search")
    location = st.text_input("Enter a location for activities (city or latitude, longitude):", key="activities")
    search_tours = st.button("Search Tours and Activities")
    if search_tours and location:
        if ',' in location:
            latitude, longitude = map(float, location.split(','))
            tours = get_tour_activities(latitude, longitude)
        else:
            # In a real app, you'd need a function to convert city name to lat, lon
            st.info("For now, please use latitude,longitude format.")
            tours = []
        if isinstance(tours, dict) and "error" in tours:
            st.error(tours["error"])
        elif len(tours) == 0:
            st.info("No activities found.")
        else:
            for tour in tours:
                st.markdown(f"**Activity Name:** {tour['name']}")
                st.write(f"**Category:** {tour['category']}")
                st.write(f"**Price:** ${tour.get('price', {}).get('total', 'N/A')}")
                st.markdown("---")
with tab4:
    st.subheader("Travel Assistant Chatbot")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    user_input = st.text_input("Say something to the assistant:", key="user_input")
    if user_input:
        response = get_bot_response(user_input)
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", response))
    for sender, message in st.session_state.chat_history:
        st.markdown(f"**{sender}:** {message}")