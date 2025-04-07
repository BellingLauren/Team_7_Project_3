import requests
from flask import Flask, render_template, request, jsonify
import time

app = Flask(__name__, template_folder='templates')

# Amadeus API Credentials
client_id = 'RW5x5Bn2aMZYmgyHCyomxPetDteMmM2a'
client_secret = 'sKvaa9jS36eO7OCL'

# Global variable to store the access token and its expiry time
access_token = None
token_expiry_time = 0

# Function to get the access token
def get_access_token():
    global access_token, token_expiry_time

    # Check if the token is still valid
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
        token_expiry_time = time.time() + data['expires_in'] - 60  # Subtract 60 seconds to ensure token doesn't expire during use
        return access_token
    else:
        return None

# Function to get flight offers
def get_flight_offers(origin_code, destination_code, departure_date, adults=1, max_results=5):
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to get access token"}

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'originLocationCode': origin_code,
        'destinationLocationCode': destination_code,
        'departureDate': departure_date,
        'adults': adults,
        'currencyCode': 'USD',
        'max': max_results
    }

<<<<<<< HEAD
    flight_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode=CLE&destinationLocationCode=NYC&departureDate=2025-05-01&adults=1&nonStop=false&currencyCode=USD&max=5'

=======
    flight_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers?'
    
    
>>>>>>> e2afbfa6a0337ea551c071e847c359ca035bc2cc
    response = requests.get(flight_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()['data']
    else:
        return {"error": f"API Request failed: {response.status_code}, {response.text}"}

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

# Route for the home page with the flight search form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle flight search and display results
@app.route('/find_flights', methods=['POST'])
def find_flights():
    origin = request.form.get('origin')
    destination = request.form.get('destination')
    departure_date = request.form.get('departure_date')
    return_date = request.form.get('return_date')

    # Get flight results using the Amadeus API
    flight_results = get_flight_offers(origin, destination, departure_date)
    return render_template('flight_results.html', flights=flight_results)

# Route to handle chatbot conversation
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['user_message']
    bot_response = get_bot_response(user_message)
    return jsonify({'bot_message': bot_response})

# Chatbot conversation logic
def get_bot_response(user_message):
    if 'name' in user_message.lower():
        return "Nice to meet you! What is your name?"
    elif 'travel' in user_message.lower():
        return "Great! Where are you looking to travel?"
    elif 'date' in user_message.lower():
        return "What date are you looking to travel?"
    elif 'airport' in user_message.lower():
        return "What airport are you flying from, and to which airport?"
    elif 'flight' in user_message.lower():
        return "I can help you find flights! Please check out this API: <a href='https://test.api.amadeus.com/v2/shopping/flight-offers' target='_blank'>Flight API</a>"
    elif 'hotel' in user_message.lower():
        return "I can help you find hotels! Please check out this API: <a href='https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city' target='_blank'>Hotel API</a>"
    elif 'tour' in user_message.lower() or 'activity' in user_message.lower():
        return "I can help you find tours and activities! Please check out this API: <a href='https://test.api.amadeus.com/v1/shopping/activities' target='_blank'>Tour/Activity API</a>"
    elif 'api' in user_message.lower():
        return "You can find the API documentation here: https://test.api.amadeus.com/"
    else:
        return "I'm here to help! Could you tell me more about your travel plans?"

if __name__ == '__main__':
    app.run(debug=True)