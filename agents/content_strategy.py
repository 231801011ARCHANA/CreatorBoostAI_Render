import os
import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from workflow.state import CreatorState

load_dotenv()


# --------------------------------------------------
# GROQ MODEL
# --------------------------------------------------

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)



# --------------------------------------------------
# IDEA NOVELTY CHECK
# --------------------------------------------------

# Uses the same local embedding model as RAG.
# No YouTube or Groq API call is made here.
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def cosine_similarity(a, b):
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = sum(x * x for x in a) ** 0.5
    magnitude_b = sum(y * y for y in b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def filter_duplicate_ideas(video_ideas, creator_results, niche_results):
    """
    Remove ideas that are too semantically similar to either:
    1. the creator's existing videos, or
    2. videos already found in the broader niche research.

    This uses the local embedding model only. No YouTube or Groq
    API call is made during the novelty check.
    """

    creator_titles = [
        video.get("title", "").strip()
        for video in creator_results
        if video.get("title")
    ]

    niche_titles = [
        video.get("title", "").strip()
        for video in niche_results
        if video.get("title")
    ]

    # Remove duplicate titles while preserving order.
    creator_titles = list(dict.fromkeys(creator_titles))
    niche_titles = list(dict.fromkeys(niche_titles))

    creator_embeddings = (
        embeddings.embed_documents(creator_titles)
        if creator_titles
        else []
    )

    niche_embeddings = (
        embeddings.embed_documents(niche_titles)
        if niche_titles
        else []
    )

    accepted = []
    rejected = []

    # Creator matches use a slightly lower threshold because
    # rewording the creator's own topic should be rejected.
    creator_threshold = 0.78

    # Niche matches use a slightly higher threshold so a related
    # topic can still survive when it has a genuinely different angle.
    niche_threshold = 0.82

    for idea in video_ideas:
        title = idea.get("title", "").strip()

        if not title:
            continue

        idea_embedding = embeddings.embed_query(title)

        best_creator_similarity = 0.0
        best_creator_title = ""

        if creator_embeddings:
            creator_similarities = [
                cosine_similarity(idea_embedding, existing_embedding)
                for existing_embedding in creator_embeddings
            ]

            best_creator_similarity = max(creator_similarities)
            best_creator_index = creator_similarities.index(
                best_creator_similarity
            )
            best_creator_title = creator_titles[best_creator_index]

        best_niche_similarity = 0.0
        best_niche_title = ""

        if niche_embeddings:
            niche_similarities = [
                cosine_similarity(idea_embedding, existing_embedding)
                for existing_embedding in niche_embeddings
            ]

            best_niche_similarity = max(niche_similarities)
            best_niche_index = niche_similarities.index(
                best_niche_similarity
            )
            best_niche_title = niche_titles[best_niche_index]

        if best_creator_similarity >= creator_threshold:
            rejected.append({
                "title": title,
                "source": "creator",
                "matched_video": best_creator_title,
                "similarity": round(best_creator_similarity, 3)
            })

        elif best_niche_similarity >= niche_threshold:
            rejected.append({
                "title": title,
                "source": "niche",
                "matched_video": best_niche_title,
                "similarity": round(best_niche_similarity, 3)
            })

        else:
            accepted.append(idea)

    return accepted, rejected


# --------------------------------------------------
# CONTENT STRATEGY AGENT
# --------------------------------------------------

def content_strategy_agent(state: CreatorState):

    niche = state["niche"].lower()

    channel_url = state.get(
        "channel_url",
        ""
    ).strip()

    cache_file = f"data/strategy/{niche}.json"


    # --------------------------------------------------
    # 1. CHECK CACHE
    # --------------------------------------------------
    # Generic strategy cache is used ONLY when
    # there is no creator channel.
    #
    # If a channel is provided, we must generate
    # a personalized strategy using creator data.
    # --------------------------------------------------

    if (
        not channel_url
        and not state.get("evaluation_mode", False)
        and os.path.exists(cache_file)
    ):

        try:

            with open(
                cache_file,
                "r",
                encoding="utf-8"
            ) as file:

                strategy = json.load(file)

            if isinstance(strategy, dict) and strategy:

                print("\n========== CONTENT STRATEGY ==========")

                print(
                    f"Niche: {state['niche']}"
                )

                print(
                    "Using cached strategy."
                )

                print(
                    "No Groq API call made."
                )

                print(
                    "======================================"
                )

                return {
                    "strategy": strategy
                }

        except (json.JSONDecodeError, OSError):

            print(
                "\nStrategy cache is invalid."
            )

            print(
                "Generating a new strategy."
            )


    # --------------------------------------------------
    # 2. GET GENERAL YOUTUBE DATA
    # --------------------------------------------------

    youtube_results = state.get(
        "youtube_results",
        []
    )

    youtube_analysis = state.get(
        "youtube_analysis",
        {}
    )


    # --------------------------------------------------
    # 3. GET CREATOR YOUTUBE DATA
    # --------------------------------------------------

    creator_results = state.get(
        "creator_youtube_results",
        []
    )

    creator_analysis = state.get(
        "creator_youtube_analysis",
        {}
    )


    # --------------------------------------------------
    # 4. GET RAG DATA
    # --------------------------------------------------

    rag_context = state.get(
        "rag_context",
        []
    )


    # --------------------------------------------------
    # 5. PREPARE GENERAL YOUTUBE VIDEO DATA
    # --------------------------------------------------

    research_text = ""


    for video in youtube_results:

        research_text += f"""
Title: {video["title"]}
Channel: {video["channel"]}
Views: {video["views"]}
Likes: {video["likes"]}
Comments: {video["comments"]}
Published: {video["published_at"]}
---
"""


    # --------------------------------------------------
    # 6. PREPARE GENERAL YOUTUBE ANALYSIS
    # --------------------------------------------------

    analysis_text = f"""
Total videos: {youtube_analysis.get("total_videos", 0)}
Total views: {youtube_analysis.get("total_views", 0)}
Average views: {youtube_analysis.get("average_views", 0)}
Average likes: {youtube_analysis.get("average_likes", 0)}
Average comments: {youtube_analysis.get("average_comments", 0)}
Average engagement rate: {youtube_analysis.get("average_engagement_rate", 0)}%

Top channels:
"""


    for channel in youtube_analysis.get(
        "top_channels",
        []
    ):

        analysis_text += f"""
- {channel["channel"]}: {channel["total_views"]} views
"""


    # --------------------------------------------------
    # 7. PREPARE CREATOR VIDEO DATA
    # --------------------------------------------------

    creator_research_text = ""


    for video in creator_results:

        creator_research_text += f"""
Title: {video["title"]}
Channel: {video["channel"]}
Views: {video["views"]}
Likes: {video["likes"]}
Comments: {video["comments"]}
Published: {video["published_at"]}
---
"""


    # --------------------------------------------------
    # 8. PREPARE CREATOR ANALYSIS
    # --------------------------------------------------

    creator_analysis_text = f"""
Creator videos: {creator_analysis.get("total_videos", 0)}
Creator total views: {creator_analysis.get("total_views", 0)}
Creator average views: {creator_analysis.get("average_views", 0)}
Creator average likes: {creator_analysis.get("average_likes", 0)}
Creator average comments: {creator_analysis.get("average_comments", 0)}
Creator average engagement rate: {creator_analysis.get("average_engagement_rate", 0)}%
"""


    # --------------------------------------------------
    # 9. PREPARE RAG KNOWLEDGE
    # --------------------------------------------------

    rag_text = ""


    for item in rag_context:

        rag_text += f"""
Niche: {item["niche"]}

{item["content"]}

---
"""


    # --------------------------------------------------
    # 10. CREATE PROMPT
    # --------------------------------------------------

    prompt = f"""
You are the Content Strategy Agent for CreatorBoostAI.

Your job is to create a practical and personalized
YouTube content strategy.

==================================================
CREATOR INFORMATION
==================================================

Niche: {state["niche"]}

Platform: {state["platform"]}

Goal: {state["goal"]}

Creator Channel:
{channel_url if channel_url else "No creator channel provided"}


==================================================
SOURCE 1: GENERAL YOUTUBE RESEARCH
==================================================

This data represents successful videos found
in the selected niche.

========== YOUTUBE ANALYSIS ==========

{analysis_text}


========== RAW YOUTUBE VIDEOS ==========

{research_text}


==================================================
SOURCE 2: CREATOR'S OWN YOUTUBE RESEARCH
==================================================

This data represents the creator's own
public YouTube videos and their available
performance statistics.

========== CREATOR ANALYSIS ==========

{creator_analysis_text}


========== CREATOR'S RAW VIDEOS ==========

{creator_research_text}


==================================================
SOURCE 3: RAG KNOWLEDGE
==================================================

{rag_text}


==================================================
ANALYSIS TASK
==================================================

Use ALL available sources.

1. Analyze successful patterns in the broader
   {state["niche"]} YouTube niche.

2. Analyze the creator's own public videos.

3. Identify which topics appear strongest
   on the creator's channel.

4. Identify patterns shared between successful
   niche videos and the creator's own videos.

5. Identify opportunities where the creator
   could improve or expand their content.

6. Use the RAG knowledge to make recommendations
   practical and relevant to the niche.

7. Create original video ideas around relevant topics
   observed among the analyzed successful niche videos,
   while also considering patterns demonstrated by the
   creator's analyzed videos.

8. If creator video data is available, generate at least
   6 candidate video ideas so that ideas rejected by the
   novelty check can be replaced.

9. For every new video title, avoid unsupported
   numerical promises, timelines, growth claims,
   yield claims, or performance guarantees.

10. Do not simply copy existing YouTube videos.

11. If creator video data is available, do not propose an
    idea that is merely a rewording of an existing creator
    video title. Prefer genuinely new topics or clearly
    different content angles.

==================================================
PERSONALIZATION RULE
==================================================

If creator data is available, the strategy MUST
be personalized using the creator's actual videos.

Do not generate a generic niche strategy when
creator data is available.

For example, if the creator's strongest videos
focus on specific plants, seed germination,
harvesting, or step-by-step growing methods,
consider those patterns when generating new ideas.

However, do not assume that every successful
niche video will work equally well for this creator.

==================================================
IMPORTANT DATA RULES
==================================================

1. Use YouTube research only for observable information present in the supplied data.
2. Do not invent YouTube statistics.
3. Do not claim watch time.
4. Do not claim click-through rate (CTR).
5. Do not claim revenue.
6. Do not claim subscriber conversion.
7. Do not perform sentiment analysis.
8. Comment text is not available.
9. Do not assume thumbnail performance.
10. Do not assume description performance.
11. Do not assume tag performance.
12. Do not assume video duration.
13. Do not mention Google Trends.
14. If creator YouTube data is available, use it to personalize the strategy.
15. Identify which topics appear strongest among the creator videos that were actually provided in the research data.
16. Compare the creator's observed successful topics with successful topics in the broader niche research.
17. Do not claim that the creator has no Shorts, long-form videos, or any other content type unless that information is explicitly present in the supplied data.
18. Do not infer video duration because video duration is not available in the research data.
19. Do not claim that a video is a Short based only on assumptions. Only identify it as a Short if the supplied data explicitly supports it.
20. Do not assume thumbnail style, editing style, audience demographics, watch time, CTR, retention, or other unavailable metrics.
21. Do not claim that a topic "dominates" the niche unless the supplied research clearly supports that conclusion.
22. When comparing creator performance with niche performance, describe the comparison as an observation from the available sample rather than a definitive statement about the entire channel or niche.
23. Do not assume that a high-performing niche video will automatically perform equally well for this creator.
24. New video ideas should combine relevant opportunities from the niche with patterns already demonstrated by the creator where appropriate.
25. Every factual claim about YouTube performance must be traceable to the supplied YouTube research or creator research.
26. If the available data is insufficient to make a claim, do not make that claim.

27. Treat the creator research as a sample of the videos returned by the research system, not as a complete representation of the entire channel.

28. Treat the general YouTube research as a sample of the videos returned by the research system, not as a complete representation of the entire niche.

29. Do not use words such as "causes", "drives", "guarantees", "leads to", or "results in" unless the supplied data directly establishes causation. Prefer phrases such as "is associated with", "appears in", "was observed in", or "is present among".

30. Do not invent time-based claims such as "30 days", "60 days", "90 days", "in 4 days", or similar timelines unless that exact timeline is present in the supplied research data or RAG knowledge.

31. Do not invent expected performance, growth, views, engagement, or viral potential for new video ideas.

32. When generating a new video idea, keep the topic grounded in the observed data, but do not copy unsupported claims or timelines from a source title.

33. When a source video title contains a numerical claim or promise, treat it as part of that video's title, not as verified factual evidence that the claim is true.

34. Do not infer that a title element caused a video's performance. You may describe title patterns that are observed among the supplied sample.

35. If a topic is not present among the analyzed creator videos, say "not present among the analyzed videos" rather than "absent from the creator's library."

36. For new video titles, do not invent durations, days-to-harvest, growth rates, yields, percentages, view counts, engagement rates, or other numerical promises unless they are supported by the supplied data.

37. Do not turn an observation from a source video's title into a factual promise for a new video.

38. New video ideas should be practical and specific, but their titles must remain evidence-grounded and should avoid unsupported numerical claims.
39. Do not mention a creator video topic unless that topic is explicitly present in the supplied creator video titles or creator research data.

40. Do not mention lemon, guava, coconut, or any other creator topic unless it appears in the supplied creator video data.

41. When describing patterns in the general YouTube research, use cautious wording such as "appears among the analyzed videos" or "is observed in the sample" instead of "frequently", "commonly", "dominates", or similar broad claims.

42. Do not make recommendations about thumbnails, thumbnail design, thumbnail performance, or thumbnail effectiveness because thumbnail data is not available.

43. Do not recommend hashtags based on performance unless the supplied data directly supports that conclusion. You may mention that hashtags appear in video titles as an observable title characteristic.

44. Do not claim that emojis, hashtags, Shorts, harvesting formats, or any other title/content characteristic improves performance unless the supplied data directly establishes that relationship.

45. Do not describe a video as visually appealing, satisfying, engaging, attractive, or similar unless the supplied data explicitly supports that description.
46. Every generated idea must be checked against the supplied creator video titles and broader niche video titles for semantic similarity.
47. If an idea is too semantically similar to an existing creator video, reject it because the creator has already covered that topic.
48. If an idea is too semantically similar to a broader niche research video, reject it when it essentially copies the researched topic or concept.
49. A rejected idea must not be returned as a final video idea.
50. Do not treat a different wording of the same creator or researched niche topic as a new idea.
51. A related topic may be accepted when it has a clearly different content angle or purpose.
52. Prefer genuinely new topics or clearly differentiated angles over reworded copies.
53. The novelty check must use the supplied research only; do not fetch additional videos just for novelty checking.
54. If both creator and niche matches are available, creator similarity takes priority in the rejection reason.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "creator_insights": [
        "insight 1",
        "insight 2",
        "insight 3"
    ],

    "content_patterns": [
        "pattern 1",
        "pattern 2",
        "pattern 3"
    ],

    "recommended_topics": [
        "topic 1",
        "topic 2",
        "topic 3",
        "topic 4",
        "topic 5"
    ],

    "video_ideas": [
        {{
            "title": "video title",
            "reason": "reason based on the available research and RAG knowledge"
        }},
        {{
            "title": "video title",
            "reason": "reason based on the available research and RAG knowledge"
        }},
        {{
            "title": "video title",
            "reason": "reason based on the available research and RAG knowledge"
        }},
        {{
            "title": "video title",
            "reason": "reason based on the available research and RAG knowledge"
        }},
        {{
            "title": "video title",
            "reason": "reason based on the available research and RAG knowledge"
        }},
        {{
            "title": "video title",
            "reason": "reason based on the available research and RAG knowledge"
        }}
    ],

    "content_direction": "overall recommendation for the creator"
}}
"""


    # --------------------------------------------------
    # 11. CALL GROQ
    # --------------------------------------------------

    print(
        "\n========== CONTENT STRATEGY =========="
    )

    print(
        f"Niche: {state['niche']}"
    )


    if channel_url:

        print(
            "Creator channel provided."
        )

        print(
            "Using creator-specific research."
        )

    else:

        print(
            "No creator channel provided."
        )

        print(
            "Using general niche research."
        )


    print(
        "Calling Groq API..."
    )


    response = llm.invoke(
        prompt
    )

    content = response.content.strip()


    # --------------------------------------------------
    # 12. CLEAN RESPONSE
    # --------------------------------------------------

    if content.startswith("```"):

        content = content.replace(
            "```json",
            ""
        )

        content = content.replace(
            "```",
            ""
        )

        content = content.strip()


    # --------------------------------------------------
    # 13. PARSE JSON
    # --------------------------------------------------

    try:

        strategy = json.loads(
            content
        )


    except json.JSONDecodeError:

        print(
            "\nERROR: Groq returned invalid JSON."
        )

        print(
            "Raw response:"
        )

        print(
            content
        )

        raise


    # --------------------------------------------------
    # 14. CHECK IDEAS AGAINST CREATOR VIDEOS
    # --------------------------------------------------

    if creator_results or youtube_results:

        original_ideas = strategy.get("video_ideas", [])

        accepted_ideas, rejected_ideas = filter_duplicate_ideas(
            original_ideas,
            creator_results,
            youtube_results
        )

        strategy["video_ideas"] = accepted_ideas[:3]

        candidate_count = len(original_ideas)
        accepted_count = len(accepted_ideas)
        rejected_count = len(rejected_ideas)

        novelty_rate = (
            round(
                (accepted_count / candidate_count) * 100,2)
                if candidate_count > 0
                else 0
            )

        strategy["novelty_metrics"] = {
                "candidate_ideas": candidate_count,
                "accepted_ideas": accepted_count,
                "rejected_ideas": rejected_count,
                "novelty_rate": novelty_rate,
                "creator_videos_checked": len(creator_results),
                "niche_videos_checked": len(youtube_results)
        }

        print("\n========== IDEA NOVELTY CHECK ==========")
        print("Creator videos checked:", len(creator_results))
        print("Niche videos checked:", len(youtube_results))
        print("Candidate ideas generated:", len(original_ideas))
        print("Ideas rejected as duplicates:", len(rejected_ideas))

        for rejected in rejected_ideas:
            print("- REJECTED:", rejected["title"])
            print("  Matched source:", rejected["source"])
            print("  Matched video:", rejected["matched_video"])
            print("  Similarity:", rejected["similarity"])

        print("Final unique ideas:", len(strategy["video_ideas"]))

        for idea in strategy["video_ideas"]:
            print("- ACCEPTED:", idea.get("title", ""))

        print("========================================")

    else:

        print("\n========== IDEA NOVELTY CHECK ==========")
        print("No creator channel data available.")
        print("Creator-video duplicate checking skipped.")
        print("========================================")


    # --------------------------------------------------
    # 15. SAVE GENERIC STRATEGY CACHE
    # --------------------------------------------------
    #
    # IMPORTANT:
    #
    # Creator-specific strategies are NOT saved
    # into the generic niche cache.
    #
    # Otherwise one creator's personalized
    # strategy could be reused for another creator.
    # --------------------------------------------------

    if not channel_url:

        os.makedirs(
            "data/strategy",
            exist_ok=True
        )


        with open(
            cache_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                strategy,
                file,
                indent=4,
                ensure_ascii=False
            )


        print(
            "\nStrategy saved to:"
        )

        print(
            cache_file
        )

    else:

        print(
            "\nPersonalized creator strategy generated."
        )

        print(
            "Generic strategy cache was not modified."
        )


    # --------------------------------------------------
    # 16. DISPLAY STRATEGY
    # --------------------------------------------------

    print(
        "\n========== GENERATED STRATEGY =========="
    )


    # --------------------------------------------------
    # CREATOR INSIGHTS
    # --------------------------------------------------

    if strategy.get(
        "creator_insights"
    ):

        print(
            "\nCREATOR INSIGHTS:"
        )


        for insight in strategy.get(
            "creator_insights",
            []
        ):

            print(
                "-",
                insight
            )


    # --------------------------------------------------
    # CONTENT PATTERNS
    # --------------------------------------------------

    print(
        "\nCONTENT PATTERNS:"
    )


    for pattern in strategy.get(
        "content_patterns",
        []
    ):

        print(
            "-",
            pattern
        )


    # --------------------------------------------------
    # RECOMMENDED TOPICS
    # --------------------------------------------------

    print(
        "\nRECOMMENDED TOPICS:"
    )


    for topic in strategy.get(
        "recommended_topics",
        []
    ):

        print(
            "-",
            topic
        )


    # --------------------------------------------------
    # VIDEO IDEAS
    # --------------------------------------------------

    print(
        "\nVIDEO IDEAS:"
    )


    for idea in strategy.get(
        "video_ideas",
        []
    ):

        print(
            "\nTitle :",
            idea.get(
                "title"
            )
        )

        print(
            "Reason:",
            idea.get(
                "reason"
            )
        )


    # --------------------------------------------------
    # CONTENT DIRECTION
    # --------------------------------------------------

    print(
        "\nCONTENT DIRECTION:"
    )


    print(
        strategy.get(
            "content_direction",
            ""
        )
    )


    print(
        "\n========================================"
    )


    # --------------------------------------------------
    # 17. RETURN STRUCTURED STRATEGY
    # --------------------------------------------------

    return {
        "strategy": strategy
    }