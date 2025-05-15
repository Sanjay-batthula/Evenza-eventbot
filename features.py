from datetime import datetime, time
import streamlit as st
from typing import Dict, List
import spacy
import PyPDF2
from pathlib import Path
import json

class EventFeatures:
    def __init__(self):
        # Initialize existing location and schedule data
        self.locations: Dict[str, str] = {
            "main_hall": "Main Workshop Hall (Ground Floor)",
            "washroom": "Washrooms (Floor 1, near elevator)",
            "cafeteria": "Cafeteria (Floor 2)",
            "registration": "Registration Desk (Ground Floor Lobby)",
            "breakout_rooms": "Breakout Rooms (Floor 1, Rooms 101-104)"
        }
        
        self.schedule: Dict[str, Dict] = {
            "registration": {
                "time": time(8, 30),
                "title": "Registration & Welcome Kit",
                "duration": "30min"
            },
            "opening": {
                "time": time(9, 0),
                "title": "Keynote: Future of AI",
                "duration": "1hr"
            },
            "morning_break": {
                "time": time(11, 0),
                "title": "Networking Break",
                "duration": "30min"
            },
            "lunch": {
                "time": time(13, 0),
                "title": "Lunch Break",
                "duration": "1hr"
            },
            "evening_break": {
                "time": time(15, 30),
                "title": "Tea Break",
                "duration": "30min"
            },
            "closing": {
                "time": time(17, 0),
                "title": "Closing Ceremony",
                "duration": "1hr"
            }
        }

        # Initialize new attributes
        self.participants: Dict[str, Dict] = {}
        self.session_feedback: Dict[str, List[Dict]] = {}
        self.nlp = spacy.load("en_core_web_sm")
        self.resume_data: Dict[str, Dict] = {}
        
    def process_resume(self, participant_id: str, resume_file) -> None:
        """Process and store resume information"""
        try:
            pdf_reader = PyPDF2.PdfReader(resume_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

            # Extract key information using spaCy
            doc = self.nlp(text)
            
            # Store processed resume data
            self.resume_data[participant_id] = {
                "skills": self._extract_skills(doc),
                "experience": self._extract_experience(doc),
                "interests": self._extract_interests(doc)
            }
        except Exception as e:
            st.error(f"Error processing resume: {str(e)}")

    def _extract_skills(self, doc) -> List[str]:
        """Extract technical skills from spaCy doc"""
        # Add your skill extraction logic here
        skills = []
        skill_patterns = ["python", "java", "ai", "ml", "deep learning", "tensorflow"]
        for token in doc:
            if token.text.lower() in skill_patterns:
                skills.append(token.text.lower())
        return list(set(skills))

    def find_similar_participants(self, participant_id: str) -> List[Dict]:
        """Find participants with similar technical backgrounds"""
        if participant_id not in self.resume_data:
            return []
        
        user_skills = set(self.resume_data[participant_id]["skills"])
        similar_participants = []
        
        for pid, data in self.resume_data.items():
            if pid != participant_id:
                common_skills = user_skills.intersection(set(data["skills"]))
                if len(common_skills) > 0:
                    similar_participants.append({
                        "participant_id": pid,
                        "common_skills": list(common_skills),
                        "similarity_score": len(common_skills) / len(user_skills)
                    })
        
        return sorted(similar_participants, key=lambda x: x["similarity_score"], reverse=True)

    def recommend_sessions(self, participant_id: str) -> List[Dict]:
        """Recommend workshop sessions based on participant's resume"""
        if participant_id not in self.resume_data:
            return []
        
        user_interests = self.resume_data[participant_id]["interests"]
        user_skills = self.resume_data[participant_id]["skills"]
        
        recommendations = []
        for session, details in self.schedule.items():
            # Add session recommendation logic based on skills and interests
            relevance_score = self._calculate_session_relevance(details, user_skills, user_interests)
            if relevance_score > 0.5:  # Threshold for recommendations
                recommendations.append({
                    "session": session,
                    "details": details,
                    "relevance_score": relevance_score
                })
        
        return sorted(recommendations, key=lambda x: x["relevance_score"], reverse=True)

    def submit_feedback(self, session_id: str, participant_id: str, feedback: Dict) -> None:
        """Store feedback for a session"""
        if session_id not in self.session_feedback:
            self.session_feedback[session_id] = []
        
        feedback["participant_id"] = participant_id
        feedback["timestamp"] = datetime.now()
        self.session_feedback[session_id].append(feedback)

    def get_feedback_summary(self, session_id: str) -> Dict:
        """Get summary of feedback for a session"""
        if session_id not in self.session_feedback:
            return {"total_responses": 0, "average_rating": 0}
        
        feedbacks = self.session_feedback[session_id]
        total = len(feedbacks)
        avg_rating = sum(f.get("rating", 0) for f in feedbacks) / total if total > 0 else 0
        
        return {
            "total_responses": total,
            "average_rating": avg_rating,
            "common_themes": self._analyze_feedback_themes(feedbacks)
        }

    def _analyze_feedback_themes(self, feedbacks: List[Dict]) -> Dict:
        """Analyze common themes in feedback comments"""
        themes = {"positive": [], "negative": []}
        # Add feedback analysis logic here
        return themes

    # Existing methods remain unchanged
    def get_location_info(self, location: str) -> str:
        return self.locations.get(location.lower(), "Location not found")

    def time_until_next_event(self) -> str:
        current_time = datetime.now().time()
        next_event = None
        next_event_time = None

        for event, details in self.schedule.items():
            event_time = details["time"]
            if current_time < event_time:
                if next_event_time is None or event_time < next_event_time:
                    next_event = event
                    next_event_time = event_time

        if next_event and next_event_time:
            time_diff = datetime.combine(datetime.today(), next_event_time) - datetime.combine(datetime.today(), current_time)
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"Next event: {self.schedule[next_event]['title']} in {hours}h {minutes}m"
        return "All events completed for today"

    def get_agenda(self) -> Dict:
        """Get full workshop agenda with details"""
        return {
            event: {
                "time": details["time"].strftime("%H:%M"),
                "title": details["title"],
                "duration": details["duration"]
            }
            for event, details in self.schedule.items()
        }