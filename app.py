from flask import Flask, render_template, request, jsonify, redirect

app = Flask(__name__)

Access_Token= {
    'grant_type': 'client_credentials',
    'client_id': 'RW5x5Bn2aMZYmgyHCyomxPetDteMmM2a',
    'client_secret': 'sKvaa9jS36eO7OCL'
}

# Initialize variables to store user data
user_name = None
origin = 'CLE'
destination = 'NYC'
departure_date = '2025-05-01'
step = 0  # Track the current step in the conversation

# The booking URL for the travel website
booking_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global user_name, origin, destination, departure_date, step

    user_input = request.form['user_input'].lower()
    response = ""

    if step == 0:  # Step 0: Initial greeting
        if "hello" in user_input:
            response = "I can help you find flights! Type 'find flight' to get started!"
            step += 1  # Move to next step
        else:
            response = "Hello! I can assist you in booking a flight. Type 'hello' to get started."
    
    elif step == 1:  # Step 1: Asking for name
        if "find flight" in user_input:
            response = "Great! First, what’s your name?"
            step += 1  # Move to next step
        else:
            response = "To get started, type 'find flight'."

    elif step == 2:  # Step 2: Asking for destination
        user_name = user_input.capitalize()
        response = f"Nice to meet you, {user_name}! Where would you like to go?"
        step += 1  # Move to next step

    elif step == 3:  # Step 3: Asking for departure date
        destination = user_input.capitalize()
        response = f"Got it, you're going to {destination}. When would you like to depart?"
        step += 1  # Move to next step

    elif step == 4:  # Step 4: Asking for departure date
        departure_date = user_input
        response = f"Got it! Let me check flights from {origin} to {destination} on {departure_date}."
        step += 1  # Move to next step

    elif step == 5:  # Step 5: Redirect to booking page
        # Returning a response with the redirect URL
        response = f"Redirecting you to the booking page now..."
        return jsonify({'bot_response': response, 'redirect_url': booking_url})

    else:
        response = "Sorry, I didn’t understand that. Can you tell me where you want to go?"

    return jsonify({'bot_response': response})

if __name__ == '__main__':
    app.run(debug=True)