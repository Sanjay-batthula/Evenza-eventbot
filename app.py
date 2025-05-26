import streamlit as st
import PyPDF2
import requests
import json
import io
import os
from dotenv import load_dotenv
import html
from datetime import datetime, time
import pytz
from googletrans import Translator
import streamlit as st
import uuid
from time import sleep

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
        self.lunch_time = time(13, 0)  # 1:00 PM
        self.lunch_end_time = time(14, 0)  # 2:00 PM
        self.event_date = datetime(2025, 5, 18).date()  # Event date
        self.india_tz = pytz.timezone('Asia/Kolkata')
        self.translator = Translator()
        self.telugu_slang_dict = {
            "Hello": "Ela unnaru",
            "How are you": "Baunnara",
            "Welcome": "Suswaagatham",
            "Thank you": "Dhanyavaadalu",
            "Food": "Tindhi",
            "Time": "Samayam",
            "Event": "Karyakramam",
            "Where": "Ekkada",
            "When": "Eppudu",
            # Add more slang translations as needed
        }

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

    def answer_question(self, query, target_lang="en"):
        """Modified answer_question method with translation support."""
        # Translate query to English for processing
        if target_lang != "en" and target_lang != "tenglish":
            eng_query = self.translator.translate(query, dest="en").text
        else:
            eng_query = query

        # Get response in English
        response = self._answer_question(eng_query)

        # Translate response to target language
        return self.translate_text(response, target_lang)

    def _answer_question(self, query):
        """Handle questions and generate responses."""
        # Check for lunch time related queries
        lunch_keywords = ["lunch", "food", "eat", "meal", "time until lunch", "when is lunch"]
        if any(keyword in query.lower() for keyword in lunch_keywords):
            time_info = self.get_time_until_lunch()
            current_time = datetime.now(self.india_tz)
            
            if current_time.date() == self.event_date:
                current_hour = current_time.hour
                current_min = current_time.minute
                
                # Create a visual progress bar for time until lunch
                if current_hour < 13:
                    total_mins = (13 - current_hour) * 60 - current_min
                    progress = "🕐 Time until lunch:\n"
                    progress += "\n⏳ Progress: "
                    blocks = "█" * (12 - current_hour) + "░" * (current_hour)
                    progress += f"{blocks} {time_info}\n"
                elif 13 <= current_hour < 14:
                    progress = "🍽️ Lunch is happening now!\n"
                    progress += "\n⌛ Status: "
                    mins_left = 60 - current_min
                    blocks = "█" * (60 - mins_left) + "░" * mins_left
                    progress += f"{blocks}\n"
                else:
                    progress = "Lunch time has ended for today!"

                lunch_details = f"""
{progress}

📍 Lunch Details:
• Location: Cafeteria (5th floor)
• Time: 1:00 PM - 2:00 PM IST
• Status: {time_info}
• Note: Remember to check-in at registration!

Need directions? Just ask! 🗺️
"""
            else:
                lunch_details = f"""
🗓️ Event Date: May 18, 2025

Lunch will be served:
• Time: 1:00 PM - 2:00 PM IST
• Location: Cafeteria (5th floor)
• Duration: 1 hour
• Note: Don't forget to check-in first!

{time_info}
"""
            return lunch_details

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

    def get_time_until_lunch(self):
        """Calculate time remaining until lunch."""
        current_time = datetime.now(self.india_tz)
        
        # Check if today is event day
        if current_time.date() != self.event_date:
            return "The event is scheduled for May 18, 2025. Lunch will be served from 1:00 PM to 2:00 PM."
            
        current_time = current_time.time()
        
        # If before lunch
        if current_time < self.lunch_time:
            time_diff = datetime.combine(datetime.today(), self.lunch_time) - datetime.combine(datetime.today(), current_time)
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"🕐 {hours} hours and {minutes} minutes until lunch (1:00 PM - 2:00 PM)"
            
        # If during lunch
        elif self.lunch_time <= current_time <= self.lunch_end_time:
            time_diff = datetime.combine(datetime.today(), self.lunch_end_time) - datetime.combine(datetime.today(), current_time)
            minutes = time_diff.seconds // 60
            return f"🍽️ Lunch is currently being served! {minutes} minutes remaining until lunch ends."
            
        # If after lunch
        else:
            return "⏰ Lunch time (1:00 PM - 2:00 PM) has ended for today."

    def translate_text(self, text, target_lang):
        """Translate text to target language."""
        try:
            if target_lang == "tenglish":
                # Handle Telugu slang in English
                for eng, slang in self.telugu_slang_dict.items():
                    text = text.replace(eng, slang)
                return text
            elif target_lang != "en":
                translation = self.translator.translate(text, dest=target_lang)
                return translation.text
            return text
        except Exception as e:
            st.error(f"Translation error: {str(e)}")
            return text

def initialize_languages():
    return {
        "English": "en",
        "Telugu": "te",
        "Hindi": "hi",
        "French": "fr",
        "Spanish": "es",
        "Italian": "it",
        "Telugu Slang (English)": "tenglish"  # Custom code for Telugu slang in English
    }

# Set page configuration
st.set_page_config(
    page_title="EVENZA - Your AI Event Guide",
    page_icon="✨",
    layout="centered"
)

# Language selector sidebar
st.sidebar.header("🌐 Language Settings")
languages = initialize_languages()
selected_language = st.sidebar.selectbox(
    "Choose your preferred language",
    list(languages.keys()),
    index=0
)

# Add TTS controls to sidebar
st.sidebar.markdown("---")
st.sidebar.header("🔊 Text-to-Speech")
auto_tts = st.sidebar.toggle("Auto-read responses", value=False)

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
        welcome_messages = {
            "en": """✨ Hello! I'm your personal AI Event Assistant, here to make your workshop experience amazing!""",
            "te": """✨ నమస్కారం! నేను మీ వ్యక్తిగత AI ఈవెంట్ అసిస్టెంట్ని, మీ వర్క్‌షాప్ అనుభవాన్ని అద్భుతంగా మార్చడానికి ఇక్కడ ఉన్నాను!""",
            "hi": """✨ नमस्ते! मैं आपका पर्सनल AI इवेंट असिस्टेंट हूं, आपके वर्कशॉप अनुभव को शानदार बनाने के लिए यहां हूं!""",
            "fr": """✨ Bonjour! Je suis votre assistant AI personnel pour l'événement, ici pour rendre votre expérience d'atelier incroyable!""",
            "es": """✨ ¡Hola! Soy tu asistente personal de eventos AI, ¡aquí para hacer tu experiencia del taller increíble!""",
            "it": """✨ Ciao! Sono il tuo assistente personale AI per l'evento, qui per rendere incredibile la tua esperienza del workshop!""",
            "tenglish": """✨ Namaskaram! Nenu mee personal AI Event Assistant ni, mee workshop experience ni amazing ga marchadaniki ikkada unna!"""
        }

        target_lang = languages[selected_language]
        welcome_message = welcome_messages.get(target_lang, welcome_messages["en"])
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

# Add to initialize session state section
if "feedback_clicks" not in st.session_state:
    st.session_state.feedback_clicks = set()

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
        message_id = str(uuid.uuid4())  # Generate unique ID for message
        avatar = '<div class="avatar-icon">🤖</div>'
        chat_html += f'<div class="message-container">'
        chat_html += avatar
        formatted_content = message["content"]
        
        if "I can help you with the following:" in formatted_content:
            # Your existing welcome message formatting
            chat_html += f'<div class="bot-message">{formatted_content}</div>'
        else:
            chat_html += f'<div class="bot-message">{html.escape(message["content"])}</div>'
        
        # Add feedback buttons
        if message_id not in st.session_state.feedback_clicks:
            chat_html += f'''
                <div class="feedback-container">
                    <button class="feedback-button" onclick="giveFeedback('{message_id}', 'positive')" title="This was helpful">
                        <span style="font-size: 1.2em;">👍</span>
                    </button>
                    <button class="feedback-button" onclick="giveFeedback('{message_id}', 'negative')" title="This needs improvement">
                        <span style="font-size: 1.2em;">👎</span>
                    </button>
                </div>
            '''
        chat_html += '</div>'

# Close the container div
chat_html += '</div>'

# Render the custom chat container
st.markdown(chat_html, unsafe_allow_html=True)

# Add JavaScript for handling feedback
st.markdown("""
<script>
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'feedback-notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Fade out and remove after 3 seconds
    setTimeout(() => {
        notification.style.transition = 'opacity 0.5s ease-out';
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 2500);
}

function giveFeedback(messageId, type) {
    // Send feedback to backend
    const data = {
        message_id: messageId,
        feedback_type: type
    };
    
    // Use Streamlit's components API to communicate
    window.parent.postMessage({
        type: "streamlit:setComponentValue",
        data: data
    }, "*");
    
    // Show thank you message
    const message = type === 'positive' 
        ? 'Thank you for your positive feedback! 😊'
        : 'Thank you for your feedback. We\'ll work on improving! 🙏';
    
    showNotification(message);
    
    // Disable feedback buttons for this message
    const buttons = event.target.parentElement.querySelectorAll('.feedback-button');
    buttons.forEach(btn => {
        btn.style.opacity = '0.3';
        btn.style.cursor = 'default';
        btn.disabled = true;
    });
}
</script>
""", unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Ask a question about the event...")

# Modify the chat input section

if user_input:
    target_lang = languages[selected_language]
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate response with translation
    with st.spinner("Thinking..."):
        response = st.session_state.bot.answer_question(user_input, target_lang)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Rerun to update the UI
    st.rerun()