from datetime import datetime, time
import streamlit as st
from typing import Dict, List

class EventFeatures:
    def __init__(self):
        self.locations: Dict[str, str] = {
            "main_hall": "Main Workshop Hall (Ground Floor)",
            "washroom": "Washrooms (Floor 1, near elevator)",
            "cafeteria": "Cafeteria (Floor 2)",
            "registration": "Registration Desk (Ground Floor Lobby)",
            "breakout_rooms": "Breakout Rooms (Floor 1, Rooms 101-104)"
        }
        
        self.schedule: Dict[str, time] = {
            "registration": time(8, 30),
            "opening": time(9, 0),
            "morning_break": time(11, 0),
            "lunch": time(13, 0),
            "evening_break": time(15, 30),
            "closing": time(17, 0)
        }
        
        self.active_participants: Dict[str, Dict] = {}

    def get_location_info(self, location: str) -> str:
        """Get information about a specific location"""
        return self.locations.get(location.lower(), "Location not found")

    def time_until_next_event(self) -> str:
        """Calculate time until the next scheduled event"""
        current_time = datetime.now().time()
        next_event = None
        next_event_time = None

        for event, event_time in self.schedule.items():
            if current_time < event_time:
                if next_event_time is None or event_time < next_event_time:
                    next_event = event
                    next_event_time = event_time

        if next_event and next_event_time:
            time_diff = datetime.combine(datetime.today(), next_event_time) - datetime.combine(datetime.today(), current_time)
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"Next event: {next_event} in {hours}h {minutes}m"
        return "All events completed for today"

    def track_participant(self, participant_id: str, location: str) -> None:
        """Update participant's current location"""
        self.active_participants[participant_id] = {
            "location": location,
            "last_updated": datetime.now()
        }

    def get_nearby_participants(self, location: str) -> List[str]:
        """Get list of participants in the same location"""
        return [
            pid for pid, data in self.active_participants.items()
            if data["location"] == location
        ]