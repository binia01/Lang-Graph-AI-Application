import os
from typing import Dict, Any
import requests

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from dotenv import load_dotenv

# 1. Load the .env file immediately
load_dotenv()


if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

class TravelAgentNodes:
    """
    Encapsulates the logic for individual nodes in the graph.
    """
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

    def node_planner(self, state: AgentState) -> Dict[str, Any]:
        """Node 1: Generates the initial itinerary."""
        print(f"\n[NODE: Planner] Generating itinerary for {state['location']}")
        prompt = f"Create a 1-day travel itinerary for {state['location']}"

        response = self.llm.invoke([HumanMessage(content=prompt)])

        return {
            "itinerary": response.content,
            "messages": [response],
            "revision_count": state.get("revision_count", 0)
        }
    
    def _get_weather(self, city: str) -> str:
        geo_resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1}
        ).json()

        if "results" not in geo_resp:
            return "Unknown (location not found)"

        lat = geo_resp["results"][0]["latitude"]
        lon = geo_resp["results"][0]["longitude"]

        weather_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "timezone": "auto"
            }
        ).json()

        daily = weather_resp["daily"]

        precipitation = daily["precipitation_sum"][0]
        max_temp = daily["temperature_2m_max"][0]

        if precipitation > 1:
            weather_report = "Rainy and Cold" if max_temp < 15 else "Rainy"
        else:
            weather_report = "Sunny and Warm" if max_temp > 20 else "Sunny"

        return weather_report
    

    def node_weather_tool(self, state: AgentState) -> Dict[str, Any]:
        """Node 2: (Tool) Checks weather"""
        print(f"\n[NODE: Weather Tool] Checking weather for {state['location']}...")

        city = state["location"]
        weather_report = self._get_weather(city)

        print(f"   > Weather detected: {weather_report}")
        return {"weather": weather_report}

    def node_adjuster(self, state: AgentState) -> Dict[str, Any]:
        """Node 3: Adjusts itinerary based on weather or feedback."""
        print(f"\n[NODE: Adjuster] Modifying plan...")

        current_plan = state["itinerary"]
        weather = state["weather"]
        feedback = state.get('human_feedback', 'No feedback')

        prompt = (
            f"Original Plan: {current_plan}\n"
            f"Weather Condition: {weather}\n"
            f"User Feedback: {feedback}\n"
            "please rewrite the itinerary to account for the weather (indoor activities if rainy)"
            "and address any specific user feedback."
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])

        return {
            "itinerary": response.content,
            "messages": [response],
            "revision_count": state["revision_count"] + 1
        }     
    def node_human_review(self, state: AgentState) -> Dict[str, Any]:
        """Node 4: Placeholder node for the Human-in-the-Loop interrupt."""
        print(f"\n[NODE: Human Review] Waiting for user approval...")
        return {}
