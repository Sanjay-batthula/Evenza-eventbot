import streamlit as st
import PyPDF2
import requests
import json
import io
import os
from dotenv import load_dotenv
import html
from features import EventFeatures

# Load environment variables
load_dotenv()

class EventAssistantBot:
    def __init__(self, api_key, pdf_path):
        self.api_key = api_key
        self.pdf_text = self.extract_pdf(pdf_path)
        self.system_prompt = """
        You are EVENZA, an advanced AI Event Assistant. Your primary purpose is to enhance the event experience by providing accurate and helpful information. Follow these guidelines:

1. Always identify yourself as "EVENZA" when greeting users
2. Maintain a professional yet friendly tone
3. For event information, only provide details from the context
4. Keep responses concise but engaging
5. Use emojis appropriately to enhance communication
6. If information isn't available, say "I apologize, but I don't have that specific information in my database"
7. Prioritize accuracy while maintaining a helpful demeanor
8. Suggest relevant follow-up questions when appropriate
9. Format responses for easy readability
10. Focus on creating a positive user experience

Remember: You are EVENZA, the next generation of event assistance, focused on making every interaction valuable and informative.
        """

    def extract_pdf(self, pdf_path):
        """Extract text from the provided PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
                
                if not text.strip():
                    st.warning("Warning: Extracted PDF text is empty or contains only whitespace.")
                return text
        except Exception as e:
            st.error(f"Error extracting PDF: {str(e)}")
            return ""

    def post_process_response(self, response, query):
        """Format responses for better readability based on query type."""
        # If it's a lunch-related query, format the response
        if "lunch" in query.lower() or "food" in query.lower() or "eat" in query.lower():
            # Just start with "Regarding lunch:" without the greeting
            formatted = "Regarding lunch:\n\n"
            
            # Split into readable bullet points
            points = []
            
            # Extract key information using common phrases and format as separate points
            if "provided to all" in response:
                points.append("• Lunch will be provided to all participants who have checked in at the venue.")
            if "cafeteria" in response.lower() and "floor" in response.lower():
                # Extract time info if available
                time_info = ""
                if "1:00" in response and "2:00" in response:
                    time_info = "between 1:00 PM and 2:00 PM IST"
                points.append(f"• It will be served in the Cafeteria on the 5th floor {time_info}.")
            if "check-in" in response.lower() or "registration" in response.lower():
                points.append("• Please ensure you've completed the check-in process at the registration desk to be eligible.")
            if "volunteer" in response.lower() or "direction" in response.lower():
                points.append("• Feel free to ask a volunteer if you need directions to the cafeteria.")
                
            # If we couldn't extract structured points, just use the original
            if not points:
                return response
                
            # Combine all points with line breaks
            return formatted + "\n".join(points)
        
        # For other responses, just return the original
        return response

    def answer_question(self, query):
        """Use Google Gemini to answer a question based on PDF context."""
        try:
            # Combine the query with the context for the AI
            combined_prompt = f"Event information: {self.pdf_text}\n\nQuestion: {query}\n\nRemember to follow these guidelines:\n{self.system_prompt}"
            
            # Create the payload for Gemini API
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": combined_prompt}
                        ]
                    }
                ]
            }
            
            # Make request to Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            # Extract the answer from the response
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                # Extract text from the parts in the response
                text_parts = []
                for part in response_data["candidates"][0]["content"]["parts"]:
                    if "text" in part:
                        text_parts.append(part["text"])
                
                raw_response = "\n".join(text_parts)
                return self.post_process_response(raw_response, query)
            else:
                if "error" in response_data:
                    return f"Error: {response_data['error']['message']}"
                return "Sorry, I couldn't process your question. Please try again."
                
        except Exception as e:
            return f"An error occurred: {str(e)}"

# Set page configuration
st.set_page_config(
    page_title="EVENZA - Your AI Event Guide",
    page_icon="✨",
    layout="centered"
)

# Load the CSS from the external file
def load_css(css_file):
    with open(css_file, 'r') as f:
        css = f.read()
    return css

# Load and apply CSS
css = load_css("styles.css")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Main app title with styling
st.markdown("""
    <h1 style='text-align: center; color: #1E88E5; margin-bottom: 30px;'>
        ✨ EVENZA - Your AI Event Guide
    </h1>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Get API key from environment variables
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API key not found in .env file. Please add GEMINI_API_KEY to your .env file.")
    st.stop()

# Initialize the bot
if "bot" not in st.session_state:
    pdf_path = "context.pdf"
    if not os.path.exists(pdf_path):
        st.error(f"PDF file '{pdf_path}' not found in the current directory.")
        st.stop()
    
    with st.spinner("Initializing assistant..."):
        st.session_state.bot = EventAssistantBot(api_key, pdf_path)
    

    #this si welcome
    # Add welcome message with options
    if not st.session_state.messages:
        welcome_message = """✨ Hello! I'm your personal AI Event Assistant, here to make your workshop experience amazing!\n"""
        what_to_know = """🎯 What would you like to know about:\n"""
        welcome_options = """1. 🎓 Workshop Agenda & Schedule
2. 📅 Important Dates & Deadlines
3. 🏆 AI Hackathon Challenge Details
4. 🚀 Featured AI/ML Projects
5. 🗺️ Venue Navigation & Facilities
6. 🍽️ Dining & Refreshments\n"""
        footer = """💬 Feel free to ask me anything about the event!"""
        
        st.session_state.messages.append(
            {"role": "assistant", "content": welcome_message + what_to_know + welcome_options + footer}
        )

# Add additional CSS to fix spacing issues
st.markdown("""
<style>
.bot-message {
    white-space: pre-line !important;
    line-height: 1.2 !important;
    margin-bottom: 0 !important;
    padding: 5px !important;
}
.message-container {
    margin: 5px 0 !important;
    padding: 5px !important;
}
.bot-message ol {
    margin: 5px 0 !important;
    padding-left: 20px !important;
}
.bot-message li {
    margin: 2px 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}
</style>
""", unsafe_allow_html=True)

# Custom Chat UI Implementation - Completely bypassing Streamlit's chat components
# Open a container div for the chat
chat_html = '<div class="custom-chat-container">'

# Add all messages to the custom chat HTML
for message in st.session_state.messages:
    if message["role"] == "user":
        avatar = '<div class="avatar-icon user-avatar-icon">👤</div>'
        chat_html += f'<div class="message-container user">'
        chat_html += avatar
        chat_html += f'<div class="user-message">{html.escape(message["content"])}</div>'
        chat_html += '</div>'
    else:  # assistant
        avatar = '<div class="avatar-icon">🤖</div>'
        chat_html += f'<div class="message-container">'
        chat_html += avatar
        # Format the welcome message to be more compact
        formatted_content = message["content"]
        if "I can help you with the following:" in formatted_content:
            # Replace the original formatting with HTML formatting
            formatted_content = formatted_content.replace("Hello! I'm Event bot.\nI can help you with the following:", 
                                                          "Hello! I'm Event bot.<br><br>I can help you with the following:")
            formatted_content = formatted_content.replace("\n1. ", "<ol style='margin-top:8px;margin-bottom:8px;padding-left:25px;'><li style='margin-bottom:4px;'>")
            formatted_content = formatted_content.replace("\n2. ", "</li><li style='margin-bottom:4px;'>")
            formatted_content = formatted_content.replace("\n3. ", "</li><li style='margin-bottom:4px;'>")
            formatted_content = formatted_content.replace("\n4. ", "</li><li style='margin-bottom:4px;'>")
            formatted_content = formatted_content.replace("\n5. ", "</li><li style='margin-bottom:4px;'>")
            formatted_content = formatted_content.replace("\n6. ", "</li><li style='margin-bottom:4px;'>")
            formatted_content = formatted_content.replace("\n\nHow can I help you", "</li></ol><br>How can I help you")
            chat_html += f'<div class="bot-message">{formatted_content}</div>'
        else:
            chat_html += f'<div class="bot-message">{html.escape(message["content"])}</div>'
        chat_html += '</div>'

# Close the container div
chat_html += '</div>'

# Render the custom chat container
st.markdown(chat_html, unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Ask a question about the event...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate response
    with st.spinner("Thinking..."):
        response = st.session_state.bot.answer_question(user_input)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Rerun to update the UI
    st.rerun()

# Initialize features in session state
if 'features' not in st.session_state:
    st.session_state.features = EventFeatures()

# Add to your sidebar or main interface
with st.sidebar:
    st.subheader("📍 Quick Navigation")
    location = st.selectbox(
        "Find Location:",
        options=list(st.session_state.features.locations.keys())
    )
    if location:
        st.info(st.session_state.features.get_location_info(location))
    
    st.subheader("⏰ Next Event")
    st.write(st.session_state.features.time_until_next_event())

# Add participant tracking (optional)
if st.session_state.get("user_id"):
    current_location = st.selectbox(
        "Update your location:",
        options=list(st.session_state.features.locations.keys())
    )
    if current_location:
        st.session_state.features.track_participant(
            st.session_state.user_id,
            current_location
        )
        nearby = st.session_state.features.get_nearby_participants(current_location)
        if nearby:
            st.write(f"Participants in same location: {len(nearby)}")