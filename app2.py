import streamlit as st
import pandas as pd
import requests
import time
import os
import logging
import traceback
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import urllib.parse
#from whispertest import get_latest_transcription
from transcribe_mp3 import TRANSCRIPT_TEXT
from chatbot_integration import (
    initialize_chatbot_state,
    update_suggestions,
    create_chatbot_suggestion_buttons,
    process_user_input,
    handle_travel_search_completion
)

# Initialize session state variables for storing search results
if "flight_results" not in st.session_state:
    st.session_state.flight_results = None
if "hotel_results" not in st.session_state:
    st.session_state.hotel_results = None
if "has_searched" not in st.session_state:
    st.session_state.has_searched = False
if "chat_history" not in st.session_state: 
    st.session_state.chat_history = []

# Initialize ML chatbot state
initialize_chatbot_state()

# Amadeus API credentials
load_dotenv()
client_id = os.getenv("api_key")
client_secret = os.getenv("api_secret")
google_api = os.getenv("GOOGLE_PLACES_API_KEY")
access_token = None
token_expiry_time = 0

# Amadeus Token Request
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
    if response.status_code == 200:
        data = response.json().get('data', [])
        
        # Extract flight numbers for each offer
        for offer in data:
            for itinerary in offer.get('itineraries', []):
                for segment in itinerary.get('segments', []):
                    # Extract the carrier code and flight number
                    carrier_code = segment.get('carrierCode', '')
                    flight_number = segment.get('number', '')
                    
                    # Add complete flight number to the segment
                    segment['flightNumber'] = f"{carrier_code}{flight_number}"
        
        return data
    else:
        return {"error": response.text}

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
    
# Attractions by City   
def get_attractions_by_city(city_name, google_api):
    
    # Ensure city name is properly URL encoded
    encoded_city = urllib.parse.quote(city_name)
    
    # Construct the Places API URL for text search
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    search_query = f"top attractions in {encoded_city}"
    url = f"{base_url}?query={urllib.parse.quote(search_query)}&key={google_api}"
    try:
        # Make the API request
        response = requests.get(url)
        data = response.json()
        
        # Check if the request was successful
        if response.status_code != 200 or data.get('status') != 'OK':
            print(f"API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
            return []
        
        # Extract and format attraction information
        attractions = []
        for place in data.get('results', [])[:5]:  # Get top 5 attractions
            attraction = {
                "name": place.get('name', 'Unnamed Attraction'),
                "rating": place.get('rating', 'No rating'),
                "address": place.get('formatted_address', 'No address available'),
                "place_id": place.get('place_id', '')  # Store the place_id for potential detail requests
            }
            attractions.append(attraction)  
        return attractions    
    except Exception as e:
        print(f"Error fetching attractions data: {str(e)}")
        return []

# Google Search
def web_search(query, num_results=3):
    results = []
    try:
        # Get search URLs
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"       
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        }
        try:
            from googlesearch import search as google_search           
            urls = []
            if callable(google_search):
                for url in google_search(query, num_results=num_results):
                    urls.append(url)           
            if not urls:
                raise Exception("No results from googlesearch-python")              
        except Exception as e:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            urls = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.startswith('/url?q='):
                    url = href.split('/url?q=')[1].split('&')[0]
                    if url.startswith('http') and not url.startswith('https://accounts.google.com'):
                        urls.append(url)
                        if len(urls) >= num_results:
                            break
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=5)               
                if response.status_code != 200:
                    results.append({
                        'title': "Could not fetch page",
                        'link': url,
                        'snippet': "Unable to access this page."
                    })
                    continue
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')               
                # Extract title
                title = soup.title.string if soup.title else "No title available"               
                # Extract content
                content = ""               
                # Try paragraphs first
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text() for p in paragraphs[:3]])               
                # Try content areas if needed
                if not content or len(content) < 50:
                    for tag in ['article', 'main', 'div', 'section']:
                        if content and len(content) >= 50:
                            break                       
                        main_elements = soup.find_all(tag)
                        for element in main_elements:
                            element_text = element.get_text().strip()
                            if len(element_text) > 100:
                                content = element_text
                                break               
                # Last resort: body content
                if not content or len(content) < 50:
                    body = soup.find('body')
                    if body:
                        content = body.get_text()               
                # Clean up content
                content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                while '  ' in content:
                    content = content.replace('  ', ' ')               
                # Truncate if too long
                snippet = content[:300] + "..." if len(content) > 300 else content               
                results.append({
                    'title': title,
                    'link': url,
                    'snippet': snippet
                })                
            except Exception as e:
                results.append({
                    'title': "Unable to process page",
                    'link': url,
                    'snippet': "Could not extract content from this page."
                })       
        return results        
    except Exception as e:
        return []
    
def chatbot_response(query, destination=None):
    # Prepare search query
    search_query = query
    if destination and destination.lower() not in query.lower():
        search_query = f"{query} {destination}"
    
    # Perform web search
    search_results = web_search(search_query)
    
    if search_results:
        # Create response from search results
        response = f"Here's what I found about your question:\n\n"
        
        for i, result in enumerate(search_results, 1):
            title = result['title']
            snippet = result['snippet']
            link = result['link']
            
            response += f"{i}. **{title}**\n"
            response += f"   {snippet}\n"
            response += f"   [Read more]({link})\n\n"
        
        return response
    else:
        # Simple fallback response if search fails
        dest_text = f" about {destination}" if destination else ""
        return f"I couldn't find specific information for your query{dest_text}. Could you try asking a more specific question?"
    
def get_google_flights_url(origin, destination, date):

    # Format date as YYYY-MM-DD for Google Flights
    if isinstance(date, str):
        formatted_date = date
    else:
        try:
            formatted_date = date.strftime("%Y-%m-%d")
        except AttributeError:
            raise ValueError("Date must be a string in 'YYYY-MM-DD' format or a datetime.date object.")

    # Create Google Flights URL
    url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{formatted_date}"

    return url

def ask_about_flight(flight_info):
    query = f"Tell me more about flight {flight_info['flightNumber']} from {flight_info['departure']} to {flight_info['arrival']} on {flight_info['date']}"
    # Add user query to chat history
    st.session_state.chat_history.append(("You", query))
    # Get chatbot response
    response = chatbot_response(query, flight_info['destination_city'])
    # Add bot response to chat history
    st.session_state.chat_history.append(("Bot", response))
    # Record query for ML
    process_user_input(query, flight_info['destination_city'])

# Function to add a chatbot query when hotel button is clicked
def ask_about_hotel(hotel_name, destination_city):
    query = f"Tell me more about {hotel_name} in {destination_city}"
    st.session_state.chat_history.append(("You", query))
    response = chatbot_response(query, destination_city)
    st.session_state.chat_history.append(("Bot", response))
    # Record query for ML
    process_user_input(query, destination_city)


def get_transcript_text(
    file_path = "C:\Users\Bryan\Desktop\Final_Project\Team_7_Project_3\audiototext.txt"
):
    with open(file_path, "r", encoding="utf-8") as f:
        transcript_text2 = f.read()
    return transcript_text2
TRANSCRIPT_TEXT2 = get_transcript_text()
# Initialize session state variables for storing search results
if "flight_results" not in st.session_state:
    st.session_state.flight_results = None
if "hotel_results" not in st.session_state:
    st.session_state.hotel_results = None
if "has_searched" not in st.session_state:
    st.session_state.has_searched = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


st.title(":airplane: Travel Planner & Assistant")

# Create a container for the input fields at the top
top_container = st.container()

# Create two columns for the left and right sections
left_column, right_column = st.columns([3, 2])

# Input fields at the top
with top_container:
    st.subheader("Travel Search")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        origin_city = st.text_input("From (Origin City)", key="origin_city_input")
    with col2:
        destination_city = st.text_input("To (Destination City)", key="destination_city_input")
    with col3:
        date = st.date_input("Departure Date")
    
    # Convert city names to IATA codes
    origin = city_to_iata(origin_city) if origin_city else None
    destination = city_to_iata(destination_city) if destination_city else None
    
    # Handle search button click and store results in session state
if st.button("Search Flights and Hotels"):
    if origin and destination:
        # Get flight results
        flight_data = get_flight_offers(origin, destination, date.strftime("%Y-%m-%d"))
        st.session_state.flight_results = flight_data
    else:
        st.session_state.flight_results = None
        
    # Get hotel results
    if destination:
        hotel_data = get_hotels(destination)
        st.session_state.hotel_results = hotel_data
    else:
        st.session_state.hotel_results = None
        
    st.session_state.has_searched = True
    
    # Update ML chatbot with the new destination
    handle_travel_search_completion(origin_city, destination_city, date)
    
    st.rerun()  # Rerun to refresh the data display

# Left column for flight and hotel results
with left_column:
    # Display flight results from session state
    if st.session_state.has_searched:
        st.markdown("### Flight Results")
        if origin and destination and st.session_state.flight_results:
            results = st.session_state.flight_results
            if isinstance(results, dict) and "error" in results:
                st.error(results["error"])
            elif len(results) == 0:
                st.info("No flights found.")
            else:
                for i, flight in enumerate(results):
                    # Create a container for each flight
                    flight_container = st.container()
                    with flight_container:
                        price = flight['price']['total']
                        segments = flight['itineraries'][0]['segments']
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Price:** ${price}")
                            for seg in segments:
                                flight_num = seg['flightNumber']
                                departure = seg['departure']['iataCode']
                                arrival = seg['arrival']['iataCode']
                                dep_time = seg['departure']['at']
                                arr_time = seg['arrival']['at']
                                
                                # Make the flight number a clickable link for Google search
                                st.write(f"**Flight:** {flight_num}")
                                st.write(f"{departure} → {arrival}")
                                st.write(f"{dep_time} to {arr_time}")
                                
                                # Store flight info for the chat button
                                flight_info = {
                                    'flightNumber': flight_num,
                                    'departure': departure,
                                    'arrival': arrival,
                                    'date': date.strftime("%Y-%m-%d"),
                                    'destination_city': destination_city
                                }
                                
                        with col2:
                            # Add button to search on Google Flights
                            if st.button("Search on Google", key=f"flight_btn_{i}"):
                                # Generate Google Flights URL
                                google_flights_url = get_google_flights_url(departure, arrival, flight_info['date'])
                                # Open URL in new tab
                                st.markdown(f'<script>window.open("{google_flights_url}", "_blank");</script>', unsafe_allow_html=True)
                                # Alternative fallback approach using a link
                                st.markdown(f"[Click here if a new tab doesn't open automatically]({google_flights_url})")
                                
                    st.markdown("---")
        else:
            if not origin:
                st.error("Please enter a valid origin city")
            if not destination:
                st.error("Please enter a valid destination city")
        
        # Display hotel results from session state
        st.markdown("### Hotel Results")
        if destination and st.session_state.hotel_results:
            hotels = st.session_state.hotel_results
            if isinstance(hotels, dict) and "error" in hotels:
                st.error(hotels["error"])
            elif len(hotels) == 0:
                st.info("No hotels found.")
            else:
                for i, hotel in enumerate(hotels):
                    # Create a container for each hotel
                    hotel_container = st.container()
                    with hotel_container:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Hotel Name:** {hotel['name']}")
                            st.write(f"**Distance from city center:** {hotel['distance']['value']} {hotel['distance']['unit']}")
                            st.write(f"**Rating:** {hotel.get('rating', 'N/A')}")
                        
                        with col2:
                            # Add button to ask chatbot about this hotel
                            if st.button("Ask About This Hotel", key=f"hotel_btn_{i}"):
                                ask_about_hotel(hotel['name'], destination_city)
                                st.rerun()
                    
                    st.markdown("---")
        elif st.session_state.has_searched:  # Only show this error if search was performed
            st.error("Please enter a valid destination city to find hotels")


# Right column for chatbot
with right_column:
    st.markdown("### Travel Assistant Chatbot")
    
    # Use the destination from the travel search automatically
    destination_for_chat = destination_city if destination_city else None
    
    if destination_for_chat:
        st.info(f"Using destination: {destination_for_chat}")
    
    # Button to clear chat history
    if st.button("Clear Chat", key="clear_chat_button"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Display chat history
    chat_display = st.container()
    with chat_display:
        for sender, message in st.session_state.chat_history:
            if sender == "You":
                st.markdown(f"**{sender}:** {message}")
            else:
                st.markdown(f"**AI Travel Assistant:** {message}")
    
    # Create a container for suggestion buttons
    suggestion_container = st.container()
    with suggestion_container:
        # Display ML-generated suggestion buttons
        create_chatbot_suggestion_buttons(suggestion_container)
    
    # Create a form for the chat input
    with st.form(key="chat_form"):
        user_input = TRANSCRIPT_TEXT2
        submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input:
            # Add to chat history immediately
            st.session_state.chat_history.append(("You", user_input))
            
            # Get response
            with st.spinner("Thinking..."):
                try:
                    response = chatbot_response(user_input, destination_for_chat)
                    # Add bot response to chat history
                    st.session_state.chat_history.append(("Bot", response))
                    
                    # Process input with ML chatbot
                    process_user_input(user_input, destination_for_chat)
                except Exception as e:
                    error_message = "I'm sorry, I encountered an error processing your request. Please try again."
                    st.session_state.chat_history.append(("Bot", error_message))
                                   
            # Force a rerun to update the displayed chat
            st.rerun()

st.write(TRANSCRIPT_TEXT)