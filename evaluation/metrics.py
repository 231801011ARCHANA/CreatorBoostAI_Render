import json
import math
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# ============================================================
# METRIC FUNCTIONS
# ============================================================

def precision_at_k(retrieved_documents, relevant_documents, k):
    retrieved_at_k = retrieved_documents[:k]

    if not retrieved_at_k:
        return 0.0

    relevant_count = sum(
        1
        for document_id in retrieved_at_k
        if document_id in relevant_documents
    )

    return relevant_count / len(retrieved_at_k)


def recall_at_k(retrieved_documents, relevant_documents, k):
    if not relevant_documents:
        return 0.0

    retrieved_at_k = retrieved_documents[:k]

    relevant_count = sum(
        1
        for document_id in retrieved_at_k
        if document_id in relevant_documents
    )

    return relevant_count / len(relevant_documents)


def reciprocal_rank(retrieved_documents, relevant_documents):
    for rank, document_id in enumerate(
        retrieved_documents,
        start=1
    ):
        if document_id in relevant_documents:
            return 1 / rank

    return 0.0


def ndcg_at_k(retrieved_documents, graded_relevance, k):
    retrieved_at_k = retrieved_documents[:k]

    if not retrieved_at_k:
        return 0.0

    # --------------------------------------------------------
    # DCG
    # --------------------------------------------------------

    dcg = 0.0

    for rank, document_id in enumerate(
        retrieved_at_k,
        start=1
    ):
        relevance = graded_relevance.get(
            document_id,
            0
        )

        dcg += (
            (2 ** relevance - 1)
            / math.log2(rank + 1)
        )

    # --------------------------------------------------------
    # IDEAL DCG
    # --------------------------------------------------------

    ideal_relevances = sorted(
        graded_relevance.values(),
        reverse=True
    )[:k]

    idcg = 0.0

    for rank, relevance in enumerate(
        ideal_relevances,
        start=1
    ):
        idcg += (
            (2 ** relevance - 1)
            / math.log2(rank + 1)
        )

    if idcg == 0:
        return 0.0

    return dcg / idcg


# ============================================================
# LOAD EVALUATION DATASET
# ============================================================

def load_evaluation_dataset():
    dataset_path = Path(
        "evaluation/eval_dataset.json"
    )

    with open(
        dataset_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# LOAD RAG VECTOR DATABASE
# ============================================================

def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = Chroma(
        persist_directory="data/chroma",
        embedding_function=embeddings
    )

    return vectorstore


# ============================================================
# EVALUATE ACTUAL RAG RETRIEVAL
# ============================================================

def evaluate_rag_retrieval():

    dataset = load_evaluation_dataset()
    vectorstore = load_vectorstore()

    results = []

    # ========================================================
    # RUN ALL EVALUATION QUERIES
    # ========================================================

    for test_case in dataset:

        query = test_case["query"]

        niche = test_case["niche"]

        relevant_documents = test_case[
            "relevant_documents"
        ]

        graded_relevance = test_case[
            "graded_relevance"
        ]

        print("\n========================================")
        print("EVALUATION QUERY")
        print("========================================")

        print(
            "Query:",
            query
        )

        print(
            "Niche:",
            niche
        )

        # ----------------------------------------------------
        # RETRIEVE ACTUAL DOCUMENTS
        # ----------------------------------------------------

        documents_with_scores = (
            vectorstore.similarity_search_with_score(
                query,
                k=3,
                filter={
                    "niche": niche
                }
            )
        )

        retrieved_documents = []

        for document, score in documents_with_scores:

            document_id = document.metadata.get(
                "document_id"
            )

            if document_id:

                retrieved_documents.append(
                    document_id
                )

        print("\nRetrieved documents:")

        for rank, document_id in enumerate(
            retrieved_documents,
            start=1
        ):

            print(
                f"{rank}. {document_id}"
            )

        # ----------------------------------------------------
        # CALCULATE PRECISION@3
        # ----------------------------------------------------

        precision = precision_at_k(
            retrieved_documents,
            relevant_documents,
            k=3
        )

        # ----------------------------------------------------
        # CALCULATE RECALL@3
        # ----------------------------------------------------

        recall = recall_at_k(
            retrieved_documents,
            relevant_documents,
            k=3
        )

        # ----------------------------------------------------
        # CALCULATE MRR
        # ----------------------------------------------------

        mrr = reciprocal_rank(
            retrieved_documents,
            relevant_documents
        )

        # ----------------------------------------------------
        # CALCULATE nDCG@3
        # ----------------------------------------------------

        ndcg = ndcg_at_k(
            retrieved_documents,
            graded_relevance,
            k=3
        )

        # ----------------------------------------------------
        # STORE QUERY RESULT
        # ----------------------------------------------------

        evaluation_result = {

            "query": query,

            "niche": niche,

            "retrieved_documents":
                retrieved_documents,

            "precision_at_3":
                round(
                    precision,
                    4
                ),

            "recall_at_3":
                round(
                    recall,
                    4
                ),

            "mrr":
                round(
                    mrr,
                    4
                ),

            "ndcg_at_3":
                round(
                    ndcg,
                    4
                )
        }

        results.append(
            evaluation_result
        )

        # ----------------------------------------------------
        # DISPLAY QUERY METRICS
        # ----------------------------------------------------

        print("\nMetrics:")

        print(
            "Precision@3:",
            evaluation_result[
                "precision_at_3"
            ]
        )

        print(
            "Recall@3:",
            evaluation_result[
                "recall_at_3"
            ]
        )

        print(
            "MRR:",
            evaluation_result[
                "mrr"
            ]
        )

        print(
            "nDCG@3:",
            evaluation_result[
                "ndcg_at_3"
            ]
        )

        print(
            "========================================"
        )

    # ========================================================
    # OVERALL RAG BENCHMARK
    # ========================================================

    total_cases = len(results)

    if total_cases > 0:

        average_precision = (
            sum(
                item["precision_at_3"]
                for item in results
            )
            / total_cases
        )

        average_recall = (
            sum(
                item["recall_at_3"]
                for item in results
            )
            / total_cases
        )

        average_mrr = (
            sum(
                item["mrr"]
                for item in results
            )
            / total_cases
        )

        average_ndcg = (
            sum(
                item["ndcg_at_3"]
                for item in results
            )
            / total_cases
        )

    else:

        average_precision = 0.0
        average_recall = 0.0
        average_mrr = 0.0
        average_ndcg = 0.0

    # ========================================================
    # DISPLAY OVERALL RESULTS
    # ========================================================

    print("\n")

    print(
        "========================================"
    )

    print(
        "       OVERALL RAG BENCHMARK"
    )

    print(
        "========================================"
    )

    print(
        "Evaluation queries:",
        total_cases
    )

    print(
        "Average Precision@3:",
        round(
            average_precision,
            4
        )
    )

    print(
        "Average Recall@3:",
        round(
            average_recall,
            4
        )
    )

    print(
        "Average MRR:",
        round(
            average_mrr,
            4
        )
    )

    print(
        "Average nDCG@3:",
        round(
            average_ndcg,
            4
        )
    )

    print(
        "========================================"
    )

    # ========================================================
    # CREATE REUSABLE BENCHMARK SUMMARY
    # ========================================================

    benchmark_summary = {

        "evaluation_queries":
            total_cases,

        "average_precision_at_3":
            round(
                average_precision,
                4
            ),

        "average_recall_at_3":
            round(
                average_recall,
                4
            ),

        "average_mrr":
            round(
                average_mrr,
                4
            ),

        "average_ndcg_at_3":
            round(
                average_ndcg,
                4
            )
    }

    # ========================================================
    # SAVE BENCHMARK SUMMARY
    # ========================================================

    benchmark_path = Path(
        "evaluation/rag_benchmark_summary.json"
    )

    with open(
        benchmark_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            benchmark_summary,
            file,
            indent=4
        )

    print("\nBenchmark summary saved to:")

    print(
        benchmark_path
    )

    # ========================================================
    # RETURN REUSABLE BENCHMARK SUMMARY
    # ========================================================

    return {
        "query_results": results,
        **benchmark_summary
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n")

    print(
        "========================================"
    )

    print(
        "RAG RETRIEVAL EVALUATION"
    )

    print(
        "========================================"
    )

    benchmark = evaluate_rag_retrieval()

    print("\n")

    print(
        "Evaluation completed successfully."
    )

    print(
        "\nReturned benchmark summary:"
    )

    print(
        "Evaluation queries:",
        benchmark[
            "evaluation_queries"
        ]
    )

    print(
        "Average Precision@3:",
        benchmark[
            "average_precision_at_3"
        ]
    )

    print(
        "Average Recall@3:",
        benchmark[
            "average_recall_at_3"
        ]
    )

    print(
        "Average MRR:",
        benchmark[
            "average_mrr"
        ]
    )

    print(
        "Average nDCG@3:",
        benchmark[
            "average_ndcg_at_3"
        ]
    )