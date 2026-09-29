from agents.youtube_research import youtube_research_agent


state = {
    "niche": "Fitness",
    "platform": "YouTube",
    "goal": "Grow a new channel",
    "plan": [],
    "youtube_results": []
}


result = youtube_research_agent(state)

print("\nNUMBER OF VIDEOS:", len(result["youtube_results"]))