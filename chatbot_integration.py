import streamlit as st
from predictive_chatbot import PredictiveChatbot

# Initialize the predictive chatbot
@st.cache_resource
def get_predictive_chatbot():
    """Create or load the predictive chatbot instance (cached for efficiency)"""
    return PredictiveChatbot()

def initialize_chatbot_state():
    """Initialize the chatbot-related state variables if they don't exist"""
    if "predictive_chatbot" not in st.session_state:
        st.session_state.predictive_chatbot = get_predictive_chatbot()
    
    if "suggested_queries" not in st.session_state:
        st.session_state.suggested_queries = []
        
    if "last_destination" not in st.session_state:
        st.session_state.last_destination = None

def update_suggestions(destination=None):
    """Update the suggested queries based on the destination"""
    chatbot = st.session_state.predictive_chatbot
    
    # Only update if destination changed or we don't have suggestions yet
    if (destination != st.session_state.last_destination or 
        not st.session_state.suggested_queries):
        
        # Get suggested queries
        st.session_state.suggested_queries = chatbot.get_suggested_queries(destination)
        st.session_state.last_destination = destination

def record_user_query(query, destination=None):
    """Record a user query to the chatbot model"""
    chatbot = st.session_state.predictive_chatbot
    chatbot.record_query(query, destination)
    
    # Periodically train the model (every 10 queries)
    queries_count = len(chatbot.search_history)
    if queries_count % 10 == 0:
        chatbot.train_model()

def create_chatbot_suggestion_buttons(container):
    """Create buttons for suggested queries in the given container"""
    if st.session_state.suggested_queries:
        container.markdown("#### Suggested Questions:")
        
        # Create a button for each suggested query
        for query in st.session_state.suggested_queries:
            if container.button(query, key=f"suggest_{query}"):
                # When button is clicked, add this query to chat history
                st.session_state.chat_history.append(("You", query))
                
                # Process the query
                try:
                    # Get destination from session state
                    destination = st.session_state.last_destination
                    
                    # Get chatbot response (using your existing chatbot_response function)
                    # This assumes your chatbot_response function is imported here
                    from main import chatbot_response
                    response = chatbot_response(query, destination)
                    
                    # Add response to chat history
                    st.session_state.chat_history.append(("Bot", response))
                    
                    # Record this query for machine learning
                    record_user_query(query, destination)
                except Exception as e:
                    error_message = f"I'm sorry, I encountered an error processing your request: {str(e)}"
                    st.session_state.chat_history.append(("Bot", error_message))
                
                # Force a rerun to update the displayed chat
                st.rerun()

# Function to process user input from chatbot form
def process_user_input(user_input, destination=None):
    """Process user input and record it for machine learning"""
    # Record this query in the ML model
    record_user_query(user_input, destination)
    
    # Update suggestions after processing input
    update_suggestions(destination)

# Function to integrate ML suggestions into the travel search process
def handle_travel_search_completion(origin_city, destination_city, date):
    """Handle the completion of a travel search"""
    # Update chatbot suggestions based on the new destination
    if destination_city:
        initialize_chatbot_state()
        update_suggestions(destination_city)
        
        # Add a welcome message with suggestions to the chat history
        if st.session_state.suggested_queries and len(st.session_state.chat_history) == 0:
            suggestions_text = "\n\nHere are some questions you might want to ask:"
            for i, query in enumerate(st.session_state.suggested_queries, 1):
                suggestions_text += f"\n{i}. {query}"
                
            welcome_msg = (
                f"Welcome to your trip planning for {destination_city}! "
                f"I can help answer questions about your destination.{suggestions_text}"
            )
            st.session_state.chat_history.append(("Bot", welcome_msg))