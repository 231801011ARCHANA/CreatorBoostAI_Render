from agents.google_trends import google_trends_agent


state = {
    "niche": "Fitness",
    "platform": "YouTube",
    "goal": "Grow a new channel",
    "plan": [],
    "youtube_results": [],
    "trends_results": {}
}


result = google_trends_agent(state)

print("\nTRENDS RESULT:")
print(result["trends_results"])