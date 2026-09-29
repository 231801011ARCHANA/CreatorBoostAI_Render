from agents.planner import planner_agent


state = {
    "niche": "Fitness",
    "platform": "YouTube",
    "goal": "Grow a new channel",
    "plan": []
}


result = planner_agent(state)

print("\nFINAL PLAN:")
print(result["plan"])