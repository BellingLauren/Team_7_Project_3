from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Replace with your Amadeus API credentials
AMADEUS_API_KEY = "Amadeus_API"
AMADEUS_API_SECRET = "Secret"

# Function to get authentication token
def get_amadeus_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(url, data=payload, headers=headers)
    return response.json().get("access_token")

# Endpoint to fetch flight offers
@app.route("/flights", methods=["GET"])
def get_flights():
    origin = request.args.get("origin")
    destination = request.args.get("destination")
    departure_date = request.args.get("departure_date")
    adults = request.args.get("adults", 1)

    if not origin or not destination or not departure_date:
        return jsonify({"error": "Missing required parameters"}), 400

    token = get_amadeus_token()
    if not token:
        return jsonify({"error": "Authentication failed"}), 401

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": adults,
        "max": 5  # Fetch up to 5 flight offers
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch flight offers", "details": response.json()}), response.status_code

    return jsonify(response.json())

# Run the app
if __name__ == "__main__":
    app.run(debug=True)