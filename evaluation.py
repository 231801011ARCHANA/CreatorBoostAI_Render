"""Runtime evaluation metrics for CreatorBoostAI.

The live /generate endpoint uses evaluate_generation() after every LangGraph run.

RAG retrieval benchmark metrics such as Precision@3, Recall@3, MRR and nDCG@3
are calculated separately using evaluation/metrics.py and saved to:

    evaluation/rag_benchmark_summary.json

This file loads those precomputed benchmark results during live evaluation.

Metrics that require a dedicated evaluator or human judges, such as
Faithfulness, Answer Relevance and Human Evaluation, are reported as
Not Measured instead of inventing a score.
"""

import json
import time
from pathlib import Path
from typing import Any

from workflow.state import SUPPORTED_NICHES
from workflow.creatorboost_graph import creatorboost_graph


def load_rag_benchmark():
    """Load the separately computed RAG retrieval benchmark."""

    benchmark_path = (
        Path(__file__).resolve().parent
        / "evaluation"
        / "rag_benchmark_summary.json"
    )

    if not benchmark_path.exists():
        return {
            "status": "Not measured",
            "reason": "Run python evaluation\\metrics.py first.",
            "evaluation_queries": 0,
            "precision_at_3": None,
            "recall_at_3": None,
            "mrr": None,
            "ndcg_at_3": None,
        }

    try:
        with open(benchmark_path, "r", encoding="utf-8") as file:
            benchmark = json.load(file)

        return {
            "status": "Measured",
            "evaluation_queries": benchmark.get(
                "evaluation_queries",
                0,
            ),
            "precision_at_3": benchmark.get(
                "average_precision_at_3",
            ),
            "recall_at_3": benchmark.get(
                "average_recall_at_3",
            ),
            "mrr": benchmark.get(
                "average_mrr",
            ),
            "ndcg_at_3": benchmark.get(
                "average_ndcg_at_3",
            ),
        }

    except Exception as error:
        return {
            "status": "Not measured",
            "reason": f"Could not read benchmark file: {error}",
            "evaluation_queries": 0,
            "precision_at_3": None,
            "recall_at_3": None,
            "mrr": None,
            "ndcg_at_3": None,
        }


def _success(value: Any) -> bool:
    return bool(value)


def _percentage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2,
    )


def evaluate_generation(
    result: dict,
    execution_time_seconds: float,
) -> dict:
    """Evaluate one normal CreatorBoostAI generation.

    This evaluates the actual pipeline execution.

    RAG retrieval benchmark metrics are loaded from the separately generated
    benchmark file instead of running the 15 benchmark queries again.

    This means a normal /generate request does not perform additional
    benchmark retrievals and does not make additional YouTube or Groq calls
    just for evaluation.
    """

    plan = result.get("plan") or []

    research_sources = (
        result.get("research_sources") or []
    )

    youtube_results = (
        result.get("youtube_results") or []
    )

    youtube_analysis = (
        result.get("youtube_analysis") or {}
    )

    rag_context = (
        result.get("rag_context") or []
    )

    strategy = (
        result.get("strategy") or {}
    )

    video_ideas = (
        strategy.get("video_ideas") or []
    )

    creator_results = (
        result.get("creator_youtube_results") or []
    )

    # ---------------------------------------------------------
    # Planner Agent evaluation
    # ---------------------------------------------------------

    planner_success = (
        isinstance(plan, list)
        and len(plan) > 0
        and bool(result.get("research_required"))
        and "youtube" in [
            str(source).lower()
            for source in research_sources
        ]
        and bool(result.get("strategy_required"))
    )

    # ---------------------------------------------------------
    # YouTube Research Agent evaluation
    # ---------------------------------------------------------

    youtube_success = (
        len(youtube_results) > 0
        and int(
            youtube_analysis.get(
                "total_videos",
                0,
            )
            or 0
        ) > 0
    )

    # ---------------------------------------------------------
    # RAG Retrieval Agent evaluation
    # ---------------------------------------------------------

    rag_success = len(rag_context) > 0

    # ---------------------------------------------------------
    # Content Strategy Agent evaluation
    # ---------------------------------------------------------

    required_strategy_fields = [
        bool(
            strategy.get(
                "content_patterns"
            )
        ),
        bool(
            strategy.get(
                "recommended_topics"
            )
        ),
        bool(video_ideas),
        bool(
            strategy.get(
                "content_direction"
            )
        ),
    ]

    strategy_completeness = _percentage(
        sum(required_strategy_fields),
        len(required_strategy_fields),
    )

    strategy_success = (
        strategy_completeness == 100.0
    )

    # ---------------------------------------------------------
    # Agent-level evaluation
    # ---------------------------------------------------------

    agent_checks = {
        "Planner Agent": planner_success,
        "YouTube Research Agent": youtube_success,
        "RAG Retrieval Agent": rag_success,
        "Content Strategy Agent": strategy_success,
    }

    passed_agents = sum(
        1
        for passed in agent_checks.values()
        if passed
    )

    agent_success_rate = _percentage(
        passed_agents,
        len(agent_checks),
    )

    end_to_end_success = (
        passed_agents == len(agent_checks)
    )

    # ---------------------------------------------------------
    # RAG niche-filter precision
    # ---------------------------------------------------------

    # This is a pipeline-specific metric.
    #
    # Because the retrieval query uses a niche metadata filter,
    # we can verify whether retrieved documents belong to the
    # requested niche.
    #
    # This should NOT be described as research-paper Context
    # Precision.
    # ---------------------------------------------------------

    correct_niche_documents = sum(
        1
        for document in rag_context
        if str(
            document.get(
                "niche",
                "",
            )
        ).lower()
        == str(
            result.get(
                "niche",
                "",
            )
        ).lower()
    )

    rag_niche_precision = _percentage(
        correct_niche_documents,
        len(rag_context),
    )

    # ---------------------------------------------------------
    # Novelty evaluation
    # ---------------------------------------------------------

    novelty = strategy.get(
        "novelty_metrics"
    )

    if isinstance(
        novelty,
        dict,
    ) and novelty:

        novelty_metric = {
            "status": "Measured",
            "candidate_ideas": novelty.get(
                "candidate_ideas",
                0,
            ),
            "accepted_ideas": novelty.get(
                "accepted_ideas",
                0,
            ),
            "rejected_ideas": novelty.get(
                "rejected_ideas",
                0,
            ),
            "novelty_rate_percent": novelty.get(
                "novelty_rate",
                0,
            ),
        }

    else:

        novelty_metric = {
            "status": "Not applicable",
            "reason": (
                "Creator-specific novelty filtering runs only "
                "when a YouTube channel URL is supplied."
            ),
            "candidate_ideas": 0,
            "accepted_ideas": 0,
            "rejected_ideas": 0,
            "novelty_rate_percent": None,
        }

    # ---------------------------------------------------------
    # YouTube cache/API information
    # ---------------------------------------------------------

    youtube_cache_used = bool(
        result.get(
            "youtube_cache_used",
            False,
        )
    )

    youtube_api_called = bool(
        result.get(
            "youtube_api_called",
            False,
        )
    )

    # ---------------------------------------------------------
    # Load separately calculated RAG benchmark
    # ---------------------------------------------------------

    rag_benchmark = load_rag_benchmark()

    # ---------------------------------------------------------
    # Research-paper evaluation metrics
    # ---------------------------------------------------------

    research_metrics = {

        # Complete benchmark summary
        "rag_retrieval_benchmark": rag_benchmark,

        # Precision@3
        "precision_at_k": {
            "value": rag_benchmark.get(
                "precision_at_3"
            ),
            "status": rag_benchmark.get(
                "status",
                "Not measured",
            ),
            "k": 3,
            "reason": (
                "Measured using the 15-query "
                "labelled RAG benchmark."
                if rag_benchmark.get(
                    "status"
                ) == "Measured"
                else rag_benchmark.get(
                    "reason",
                    "",
                )
            ),
        },

        # Recall@3
        "recall_at_k": {
            "value": rag_benchmark.get(
                "recall_at_3"
            ),
            "status": rag_benchmark.get(
                "status",
                "Not measured",
            ),
            "k": 3,
            "reason": (
                "Measured using the 15-query "
                "labelled RAG benchmark."
                if rag_benchmark.get(
                    "status"
                ) == "Measured"
                else rag_benchmark.get(
                    "reason",
                    "",
                )
            ),
        },

        # Mean Reciprocal Rank
        "mrr": {
            "value": rag_benchmark.get(
                "mrr"
            ),
            "status": rag_benchmark.get(
                "status",
                "Not measured",
            ),
            "reason": (
                "Measured using the 15-query "
                "labelled RAG benchmark."
                if rag_benchmark.get(
                    "status"
                ) == "Measured"
                else rag_benchmark.get(
                    "reason",
                    "",
                )
            ),
        },

        # Normalized Discounted Cumulative Gain@3
        "ndcg_at_k": {
            "value": rag_benchmark.get(
                "ndcg_at_3"
            ),
            "status": rag_benchmark.get(
                "status",
                "Not measured",
            ),
            "k": 3,
            "reason": (
                "Measured using the 15-query "
                "labelled RAG benchmark."
                if rag_benchmark.get(
                    "status"
                ) == "Measured"
                else rag_benchmark.get(
                    "reason",
                    "",
                )
            ),
        },

        # -----------------------------------------------------
        # Metrics that still require dedicated evaluation
        # -----------------------------------------------------

        "faithfulness": {
            "value": None,
            "status": "Not measured",
            "reason": (
                "Requires a groundedness evaluator "
                "or human/LLM judge."
            ),
        },

        "answer_relevance": {
            "value": None,
            "status": "Not measured",
            "reason": (
                "Requires a reference/judge-based "
                "relevance evaluation."
            ),
        },

        "human_evaluation": {
            "value": None,
            "status": "Not measured",
            "reason": (
                "Requires ratings from human evaluators."
            ),
        },
    }

    # ---------------------------------------------------------
    # Final evaluation response
    # ---------------------------------------------------------

    return {
        "evaluation_type": (
            "Live functional + literature-metric "
            "readiness evaluation"
        ),

        "overall_success": end_to_end_success,

        "agent_success_rate_percent": (
            agent_success_rate
        ),

        "end_to_end_success": (
            end_to_end_success
        ),

        "execution_time_seconds": round(
            execution_time_seconds,
            3,
        ),

        "agent_checks": agent_checks,

        "agent_metrics": {
            "agents_passed": passed_agents,
            "agents_total": len(agent_checks),

            "planner_success": (
                planner_success
            ),

            "youtube_research_success": (
                youtube_success
            ),

            "rag_retrieval_success": (
                rag_success
            ),

            "content_strategy_success": (
                strategy_success
            ),
        },

        # -----------------------------------------------------
        # YouTube metrics
        # -----------------------------------------------------

        "youtube_metrics": {
            "videos_retrieved": len(
                youtube_results
            ),

            "analysis_available": bool(
                youtube_analysis
            ),

            "cache_used": (
                youtube_cache_used
            ),

            "api_called": (
                youtube_api_called
            ),

            "creator_videos_retrieved": len(
                creator_results
            ),
        },

        # -----------------------------------------------------
        # RAG live-generation metrics
        # -----------------------------------------------------

        "rag_metrics": {
            "documents_retrieved": len(
                rag_context
            ),

            "correct_niche_documents": (
                correct_niche_documents
            ),

            "niche_filter_precision_percent": (
                rag_niche_precision
            ),
        },

        # -----------------------------------------------------
        # Output metrics
        # -----------------------------------------------------

        "output_metrics": {
            "video_ideas": len(
                video_ideas
            ),

            "content_patterns": len(
                strategy.get(
                    "content_patterns"
                )
                or []
            ),

            "recommended_topics": len(
                strategy.get(
                    "recommended_topics"
                )
                or []
            ),

            "strategy_completeness_percent": (
                strategy_completeness
            ),
        },

        # -----------------------------------------------------
        # Novelty
        # -----------------------------------------------------

        "novelty": novelty_metric,

        # -----------------------------------------------------
        # Research metrics
        # -----------------------------------------------------

        "research_metrics": research_metrics,

        # -----------------------------------------------------
        # Notes
        # -----------------------------------------------------

        "metric_notes": [
            (
                "Precision@3, Recall@3, MRR and nDCG@3 "
                "are measured using the separate 15-query "
                "RAG retrieval benchmark."
            ),

            (
                "The RAG benchmark is loaded from "
                "evaluation/rag_benchmark_summary.json "
                "and is not rerun during /generate."
            ),

            (
                "Faithfulness and answer relevance require "
                "a dedicated evaluator or human/LLM judge."
            ),

            (
                "Human evaluation requires ratings from "
                "people using the generated strategy."
            ),

            (
                "CTR, watch time and subscriber growth are "
                "not measured because this prototype does "
                "not have private YouTube Analytics or "
                "deployed user-behaviour data."
            ),
        ],
    }


def evaluate_single_niche(niche: str):
    """Run one benchmark evaluation without a creator channel."""

    start_time = time.perf_counter()

    initial_state = {
        "niche": niche,
        "platform": "YouTube",
        "goal": "Grow a new channel",

        "plan": [],

        "research_required": False,
        "research_sources": [],

        "strategy_required": False,

        "channel_url": "",

        "youtube_results": [],
        "youtube_analysis": {},

        "creator_youtube_results": [],
        "creator_youtube_analysis": {},

        "rag_context": [],

        "strategy": {},

        "evaluation_mode": True,
        "evaluation": {},
    }

    try:

        state = creatorboost_graph.invoke(
            initial_state
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        evaluation = evaluate_generation(
            state,
            elapsed,
        )

        return {
            "niche": niche,

            "success": evaluation[
                "overall_success"
            ],

            "evaluation": evaluation,

            "execution_time_seconds": round(
                elapsed,
                3,
            ),
        }

    except Exception as error:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        return {
            "niche": niche,

            "success": False,

            "error": str(error),

            "execution_time_seconds": round(
                elapsed,
                3,
            ),
        }


def evaluate_all_niches():

    results = [
        evaluate_single_niche(niche)
        for niche in SUPPORTED_NICHES
    ]

    successful_runs = sum(
        1
        for item in results
        if item.get("success")
    )

    overall_score = _percentage(
        successful_runs,
        len(results),
    )

    total_execution_time = round(
        sum(
            item.get(
                "execution_time_seconds",
                0,
            )
            for item in results
        ),
        3,
    )

    return {
        "overall_score": overall_score,

        "summary": {
            "niches_evaluated": len(
                results
            ),

            "successful_niches": (
                successful_runs
            ),

            "failed_niches": (
                len(results)
                - successful_runs
            ),

            "total_execution_time_seconds": (
                total_execution_time
            ),
        },

        "results": results,
    }