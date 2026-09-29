import os
import json
import re

from dotenv import load_dotenv
from googleapiclient.discovery import build

from workflow.state import CreatorState

load_dotenv()


# --------------------------------------------------
# YOUTUBE RESEARCH AGENT
# --------------------------------------------------

def youtube_research_agent(state: CreatorState):

    niche = state["niche"].lower()
    channel_url = state.get("channel_url", "").strip()

    cache_file = f"data/youtube/{niche}.json"

    cache_used = False
    youtube_api_called = False

    # --------------------------------------------------
    # 1. CHECK GENERAL NICHE CACHE
    # --------------------------------------------------

    if os.path.exists(cache_file):

        try:
            with open(cache_file, "r", encoding="utf-8") as file:
                results = json.load(file)

            if isinstance(results, list) and len(results) > 0:

                cache_used = True

                print("\n========== YOUTUBE RESEARCH ==========")
                print(f"Niche: {state['niche']}")
                print("Using cached YouTube data.")
                print("No YouTube API call made.")
                print("======================================")

                analysis = analyze_youtube_results(results)

                print_youtube_analysis(analysis)

            else:
                results = None

        except (json.JSONDecodeError, OSError):

            print("\nCache is invalid.")
            print("A fresh YouTube API request will be made.")

            results = None

    else:
        results = None


    # --------------------------------------------------
    # 2. CALL YOUTUBE API FOR GENERAL NICHE RESEARCH
    # --------------------------------------------------

    if results is None:

        youtube_api_called = True

        print("\n========== YOUTUBE RESEARCH ==========")
        print(f"Niche: {state['niche']}")
        print("No valid cache found.")
        print("Calling YouTube API...")

        youtube = build(
            "youtube",
            "v3",
            developerKey=os.getenv("YOUTUBE_API_KEY")
        )

        search_response = youtube.search().list(
            part="snippet",
            q=niche,
            type="video",
            maxResults=10,
            order="viewCount",
            regionCode="IN"
        ).execute()

        video_ids = [
            item["id"]["videoId"]
            for item in search_response["items"]
        ]

        # --------------------------------------------------
        # 3. GET VIDEO STATISTICS
        # --------------------------------------------------

        stats_response = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        ).execute()

        results = []

        for video in stats_response["items"]:

            snippet = video["snippet"]
            statistics = video.get("statistics", {})

            data = {
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "published_at": snippet["publishedAt"],
                "views": int(statistics.get("viewCount", 0)),
                "likes": int(statistics.get("likeCount", 0)),
                "comments": int(statistics.get("commentCount", 0)),
                "video_id": video["id"]
            }

            results.append(data)

        # --------------------------------------------------
        # 4. SAVE GENERAL YOUTUBE DATA
        # --------------------------------------------------

        os.makedirs("data/youtube", exist_ok=True)

        with open(cache_file, "w", encoding="utf-8") as file:

            json.dump(
                results,
                file,
                indent=4,
                ensure_ascii=False
            )

        print(f"Saved {len(results)} videos to:")
        print(cache_file)


    # --------------------------------------------------
    # 5. ANALYZE GENERAL YOUTUBE DATA
    # --------------------------------------------------

    analysis = analyze_youtube_results(results)

    # --------------------------------------------------
    # 6. DISPLAY GENERAL YOUTUBE RESULTS
    # --------------------------------------------------

    print("\n========== YOUTUBE VIDEOS ==========")

    for video in results:

        print("\n--------------------------------------")
        print("Title     :", video["title"])
        print("Channel   :", video["channel"])
        print("Published :", video["published_at"])
        print("Views     :", video["views"])
        print("Likes     :", video["likes"])
        print("Comments  :", video["comments"])

    # --------------------------------------------------
    # 7. DISPLAY GENERAL ANALYSIS
    # --------------------------------------------------

    print_youtube_analysis(analysis)


    # ==================================================
    # 8. CREATOR CHANNEL RESEARCH
    # ==================================================

    creator_results = []
    creator_analysis = {}

    if channel_url:

        print("\n========== CREATOR CHANNEL RESEARCH ==========")
        print("Channel URL:", channel_url)
        print("Analyzing creator's public YouTube videos...")

        try:

            youtube = build(
                "youtube",
                "v3",
                developerKey=os.getenv("YOUTUBE_API_KEY")
            )

            channel_id = get_channel_id(
                youtube,
                channel_url
            )

            if channel_id:

                creator_results = get_creator_videos(
                    youtube,
                    channel_id
                )

                creator_analysis = analyze_youtube_results(
                    creator_results
                )

                print_creator_analysis(
                    creator_analysis
                )

            else:

                print("Could not identify the YouTube channel.")
                print("Creator channel research skipped.")

        except Exception as error:

            print("Creator channel research failed.")
            print("Error:", error)

    else:

        print("\n========== CREATOR CHANNEL RESEARCH ==========")
        print("No channel URL provided.")
        print("Skipping creator-specific research.")
        print("==============================================")


    # --------------------------------------------------
    # 9. RETURN STRUCTURED DATA
    # --------------------------------------------------

    return {
        "youtube_results": results,
        "youtube_analysis": analysis,

        "creator_youtube_results": creator_results,
        "creator_youtube_analysis": creator_analysis,

        "youtube_cache_used": cache_used,
        "youtube_api_called": youtube_api_called
    }


# ==================================================
# GET CHANNEL ID
# ==================================================

def get_channel_id(youtube, channel_url):

    # --------------------------------------------------
    # Handle @username URLs
    # Example:
    # https://youtube.com/@example
    # --------------------------------------------------

    match = re.search(
        r"youtube\.com/@([^/?]+)",
        channel_url
    )

    if match:

        handle = match.group(1)

        response = youtube.channels().list(
            part="id",
            forHandle=handle
        ).execute()

        items = response.get("items", [])

        if items:

            return items[0]["id"]


    # --------------------------------------------------
    # Handle channel ID URLs
    # Example:
    # https://youtube.com/channel/UCxxxx
    # --------------------------------------------------

    match = re.search(
        r"youtube\.com/channel/([^/?]+)",
        channel_url
    )

    if match:

        return match.group(1)


    # --------------------------------------------------
    # Handle custom URLs
    # Example:
    # https://youtube.com/c/example
    # --------------------------------------------------

    match = re.search(
        r"youtube\.com/c/([^/?]+)",
        channel_url
    )

    if match:

        custom_name = match.group(1)

        response = youtube.search().list(
            part="snippet",
            q=custom_name,
            type="channel",
            maxResults=1
        ).execute()

        items = response.get("items", [])

        if items:

            return items[0]["snippet"]["channelId"]


    return None


# ==================================================
# GET CREATOR VIDEOS
# ==================================================

def get_creator_videos(youtube, channel_id):

    # --------------------------------------------------
    # Get creator's uploaded videos
    # --------------------------------------------------

    search_response = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        type="video",
        maxResults=10,
        order="viewCount"
    ).execute()

    video_ids = [
        item["id"]["videoId"]
        for item in search_response.get("items", [])
    ]

    if not video_ids:

        return []


    # --------------------------------------------------
    # Get video statistics
    # --------------------------------------------------

    stats_response = youtube.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids)
    ).execute()


    creator_results = []

    for video in stats_response.get("items", []):

        snippet = video["snippet"]
        statistics = video.get("statistics", {})

        creator_results.append({

            "title": snippet["title"],

            "channel": snippet["channelTitle"],

            "published_at": snippet["publishedAt"],

            "views": int(
                statistics.get("viewCount", 0)
            ),

            "likes": int(
                statistics.get("likeCount", 0)
            ),

            "comments": int(
                statistics.get("commentCount", 0)
            ),

            "video_id": video["id"]

        })


    print(
        f"Found {len(creator_results)} public creator videos."
    )

    return creator_results


# ==================================================
# YOUTUBE ANALYSIS
# ==================================================

def analyze_youtube_results(results):

    if not results:

        return {
            "total_videos": 0,
            "total_views": 0,
            "average_views": 0,
            "average_likes": 0,
            "average_comments": 0,
            "top_videos": [],
            "top_channels": [],
            "average_engagement_rate": 0
        }

    total_videos = len(results)

    total_views = sum(
        video["views"]
        for video in results
    )

    total_likes = sum(
        video["likes"]
        for video in results
    )

    total_comments = sum(
        video["comments"]
        for video in results
    )

    average_views = total_views / total_videos

    average_likes = total_likes / total_videos

    average_comments = total_comments / total_videos


    # --------------------------------------------------
    # ENGAGEMENT RATE
    # --------------------------------------------------

    engagement_rates = []

    for video in results:

        views = video["views"]

        if views > 0:

            engagement_rate = (
                video["likes"] + video["comments"]
            ) / views * 100

            engagement_rates.append(
                engagement_rate
            )


    if engagement_rates:

        average_engagement_rate = (
            sum(engagement_rates)
            / len(engagement_rates)
        )

    else:

        average_engagement_rate = 0


    # --------------------------------------------------
    # TOP VIDEOS
    # --------------------------------------------------

    top_videos = sorted(
        results,
        key=lambda video: video["views"],
        reverse=True
    )[:5]


    top_videos = [

        {
            "title": video["title"],
            "channel": video["channel"],
            "views": video["views"],
            "likes": video["likes"],
            "comments": video["comments"]
        }

        for video in top_videos

    ]


    # --------------------------------------------------
    # TOP CHANNELS
    # --------------------------------------------------

    channel_views = {}

    for video in results:

        channel = video["channel"]

        channel_views[channel] = (
            channel_views.get(channel, 0)
            + video["views"]
        )


    top_channels = sorted(
        channel_views.items(),
        key=lambda item: item[1],
        reverse=True
    )[:5]


    top_channels = [

        {
            "channel": channel,
            "total_views": views
        }

        for channel, views in top_channels

    ]


    # --------------------------------------------------
    # RETURN ANALYSIS
    # --------------------------------------------------

    return {

        "total_videos": total_videos,

        "total_views": total_views,

        "average_views": round(
            average_views,
            2
        ),

        "average_likes": round(
            average_likes,
            2
        ),

        "average_comments": round(
            average_comments,
            2
        ),

        "average_engagement_rate": round(
            average_engagement_rate,
            2
        ),

        "top_videos": top_videos,

        "top_channels": top_channels

    }


# ==================================================
# PRINT YOUTUBE ANALYSIS
# ==================================================

def print_youtube_analysis(analysis):

    print("\n========== YOUTUBE ANALYSIS ==========")

    print(
        "Total videos:",
        analysis["total_videos"]
    )

    print(
        "Total views:",
        analysis["total_views"]
    )

    print(
        "Average views:",
        analysis["average_views"]
    )

    print(
        "Average likes:",
        analysis["average_likes"]
    )

    print(
        "Average comments:",
        analysis["average_comments"]
    )

    print(
        "Average engagement rate:",
        f"{analysis['average_engagement_rate']}%"
    )


    print("\nTOP VIDEOS:")

    for video in analysis["top_videos"]:

        print("\nTitle   :", video["title"])
        print("Channel :", video["channel"])
        print("Views   :", video["views"])
        print("Likes   :", video["likes"])
        print("Comments:", video["comments"])


    print("\nTOP CHANNELS:")

    for channel in analysis["top_channels"]:

        print(
            channel["channel"],
            "→",
            channel["total_views"],
            "views"
        )


    print("\n======================================")


# ==================================================
# PRINT CREATOR ANALYSIS
# ==================================================

def print_creator_analysis(analysis):

    print("\n========== CREATOR ANALYSIS ==========")

    print(
        "Creator videos:",
        analysis["total_videos"]
    )

    print(
        "Creator total views:",
        analysis["total_views"]
    )

    print(
        "Creator average views:",
        analysis["average_views"]
    )

    print(
        "Creator average likes:",
        analysis["average_likes"]
    )

    print(
        "Creator average comments:",
        analysis["average_comments"]
    )

    print(
        "Creator average engagement:",
        f"{analysis['average_engagement_rate']}%"
    )


    print("\nTOP CREATOR VIDEOS:")

    for video in analysis["top_videos"]:

        print("\nTitle   :", video["title"])
        print("Views   :", video["views"])
        print("Likes   :", video["likes"])
        print("Comments:", video["comments"])


    print("\n======================================")