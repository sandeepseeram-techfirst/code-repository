from google.adk.agents.llm_agent import Agent


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    mock_times = {
        "Hyderabad": "5:20 PM IST",
        "Bengaluru": "5:20 PM IST",
        "London": "12:50 PM BST",
        "New York": "7:50 AM EDT",
    }

    time = mock_times.get(city)

    if not time:
        return {
            "status": "error",
            "city": city,
            "message": "City not supported by this demo tool.",
        }

    return {
        "status": "success",
        "city": city,
        "time": time,
    }


root_agent = Agent(
    model="gemini-flash-latest",
    name="time_agent",
    description="Tells the current time in supported cities.",
    instruction=(
        "You are a helpful assistant that tells the current time in cities. "
        "Always use the get_current_time tool. "
        "If the tool returns an error, tell the user which cities are supported."
    ),
    tools=[get_current_time],
)