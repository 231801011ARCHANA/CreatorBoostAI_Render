from pytrends.request import TrendReq

from workflow.state import CreatorState


def google_trends_agent(state: CreatorState):

    niche = state["niche"]

    pytrends = TrendReq(hl="en-US", tz=330)

    print("\n========== GOOGLE TRENDS RESEARCH ==========")

    # Search the niche
    pytrends.build_payload(
        [niche],
        timeframe="today 12-m",
        geo="IN",
        gprop=""
    )

    # Interest over time
    interest = pytrends.interest_over_time()

    if interest.empty:
        print("No Google Trends data found.")
        return {
            "trends_results": []
        }

    print("\nInterest over time:")

    # Display recent values
    print(interest.tail(10))

    # Related topics
    try:
        related_topics = pytrends.related_topics()

        print("\nRelated Topics:")

        if niche in related_topics and related_topics[niche] is not None:
            print(
                related_topics[niche]["top"]
                .head(10)
                [["topic_title", "value"]]
                .to_string(index=False)
            )
        else:
            print("No related topics found.")

    except Exception as e:
        print("Could not retrieve related topics:", e)

    print("\n============================================")

    return {
        "trends_results": interest.tail(10).to_dict()
    }