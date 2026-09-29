def evaluate_result(result, execution_time_seconds=None):
    """
    Evaluate whether each CreatorBoostAI agent completed its expected task.
    """

    plan = result.get("plan") or []
    research_sources = result.get("research_sources") or []

    youtube_results = result.get("youtube_results") or []
    youtube_analysis = result.get("youtube_analysis") or {}

    rag_context = result.get("rag_context") or []

    strategy = result.get("strategy") or {}
    video_ideas = strategy.get("video_ideas") or []

    # -----------------------------
    # 1. PLANNER AGENT
    # -----------------------------

    planner_ok = (
        len(plan) > 0
        and "youtube" in [str(x).lower() for x in research_sources]
        and bool(result.get("research_required"))
        and bool(result.get("strategy_required"))
    )

    # -----------------------------
    # 2. YOUTUBE RESEARCH AGENT
    # -----------------------------

    youtube_ok = (
        len(youtube_results) > 0
        and int(youtube_analysis.get("total_videos", 0) or 0) > 0
    )

    # -----------------------------
    # 3. RAG RETRIEVAL AGENT
    # -----------------------------

    rag_ok = len(rag_context) > 0

    # -----------------------------
    # 4. CONTENT STRATEGY AGENT
    # -----------------------------

    strategy_ok = (
        isinstance(strategy, dict)
        and bool(strategy.get("content_patterns"))
        and bool(strategy.get("recommended_topics"))
        and len(video_ideas) > 0
        and bool(strategy.get("content_direction"))
    )

    # -----------------------------
    # AGENT CHECKS
    # -----------------------------

    agent_checks = {
        "Planner Agent": planner_ok,
        "YouTube Research Agent": youtube_ok,
        "RAG Retrieval Agent": rag_ok,
        "Content Strategy Agent": strategy_ok
    }

    agents_passed = sum(agent_checks.values())
    agents_total = len(agent_checks)

    # -----------------------------
    # EVALUATION
    # -----------------------------

    evaluation = {
        "evaluation_type": "Functional pipeline evaluation",

        "overall_success": agents_passed == agents_total,

        "score_percent": round(
            (agents_passed / agents_total) * 100,
            1
        ),

        "agents_passed": agents_passed,
        "agents_total": agents_total,

        "agent_checks": agent_checks,

        "metrics": {
            "youtube_videos_retrieved": len(youtube_results),
            "rag_documents_retrieved": len(rag_context),
            "video_ideas_generated": len(video_ideas)
        }
    }

    # -----------------------------
    # EXECUTION TIME
    # -----------------------------

    if execution_time_seconds is not None:
        evaluation["execution_time_seconds"] = round(
            execution_time_seconds,
            2
        )

    # -----------------------------
    # CREATOR-SPECIFIC NOVELTY
    # -----------------------------

    creator_results = result.get("creator_youtube_results") or []

    if creator_results:

        novelty_metrics = strategy.get("novelty_metrics") or {}

        evaluation["novelty_evaluation"] = {
            "applicable": True,
            "candidate_ideas": novelty_metrics.get(
                "candidate_ideas"
            ),
            "accepted_ideas": novelty_metrics.get(
                "accepted_ideas"
            ),
            "rejected_ideas": novelty_metrics.get(
                "rejected_ideas"
            ),
            "novelty_rate": novelty_metrics.get(
                "novelty_rate"
            ),
            "creator_videos_checked": novelty_metrics.get(
                "creator_videos_checked"
            ),
            "niche_videos_checked": novelty_metrics.get(
                "niche_videos_checked"
            )
        }

    else:

        evaluation["novelty_evaluation"] = {
            "applicable": False,
            "note": "No creator channel was supplied."
        }

    return evaluation