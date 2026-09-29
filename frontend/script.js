/* =========================================================
   CREATORBOOSTAI FRONTEND
========================================================= */

let selectedNiche = null;


/* =========================================================
   NICHE SELECTION
========================================================= */

function selectNiche(niche) {

    selectedNiche = niche;

    document.getElementById("selected-niche").innerHTML =
        `Selected niche: <strong>${escapeHtml(niche)}</strong>`;

    document.getElementById("generate-btn").disabled = false;

    document
        .querySelectorAll(".niche-card")
        .forEach(card => {

            card.classList.remove("selected");

            if (
                card.dataset.niche &&
                card.dataset.niche.toLowerCase() === niche.toLowerCase()
            ) {
                card.classList.add("selected");
            }

        });

}


/* =========================================================
   GENERATE STRATEGY
========================================================= */

async function generateStrategy() {

    if (!selectedNiche) {

        alert("Please select a niche first.");
        return;

    }


    const generateButton =
        document.getElementById("generate-btn");

    const loading =
        document.getElementById("loading-section");

    const results =
        document.getElementById("results-section");


    const channelUrl =
        document.getElementById("channel-url").value.trim();


    generateButton.disabled = true;

    results.classList.add("hidden");

    document
        .getElementById("youtube-videos-section")
        .classList.add("hidden");

    resetWorkflow();

    loading.classList.remove("hidden");


    /* -----------------------------------------------------
       STEP 1
       Planner Agent
    ----------------------------------------------------- */

    updateWorkflow(
        "agent-planner",
        "running",
        "Planning"
    );

    await delay(400);

    updateWorkflow(
        "agent-planner",
        "completed",
        "Completed"
    );

    await delay(300);


    /* -----------------------------------------------------
       STEP 2
       YouTube Research Agent
    ----------------------------------------------------- */

    updateWorkflow(
        "agent-youtube",
        "running",
        "Researching"
    );


    try {

        const response = await fetch(
            "/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    niche: selectedNiche,

                    platform: "YouTube",

                    goal: "Grow a new channel",

                    channel_url: channelUrl

                })

            }
        );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        /*
         * FastAPI executes the complete
         * LangGraph workflow before returning.
         */

        const data = await response.json();


        /* -------------------------------------------------
           STEP 2 COMPLETE
        ------------------------------------------------- */

        updateWorkflow(
            "agent-youtube",
            "completed",
            "Completed"
        );


        await delay(300);


        /* -------------------------------------------------
           STEP 3
           RAG Retrieval Agent
        ------------------------------------------------- */

        updateWorkflow(
            "agent-rag",
            "running",
            "Retrieving"
        );


        await delay(400);


        updateWorkflow(
            "agent-rag",
            "completed",
            "Completed"
        );


        await delay(300);


        /* -------------------------------------------------
           STEP 4
           Content Strategy Agent
        ------------------------------------------------- */

        updateWorkflow(
            "agent-strategy",
            "running",
            "Generating"
        );


        await delay(400);


        updateWorkflow(
            "agent-strategy",
            "completed",
            "Completed"
        );


        /* -------------------------------------------------
           DISPLAY RESULTS
        ------------------------------------------------- */

        displayResults(data);


        loading.classList.add("hidden");

        results.classList.remove("hidden");

        document
            .getElementById("youtube-videos-section")
            .classList.remove("hidden");


        results.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });


    } catch (error) {

        console.error(
            "Strategy generation failed:",
            error
        );


        loading.classList.add("hidden");

        resetWorkflow();


        alert(
            "Unable to generate the strategy.\n\n" +
            "Please make sure the FastAPI server is running."
        );


    } finally {

        generateButton.disabled = false;

    }

}


/* =========================================================
   WORKFLOW STATUS
========================================================= */

function updateWorkflow(
    elementId,
    state,
    statusText
) {

    const card =
        document.getElementById(elementId);


    if (!card) {
        return;
    }


    card.classList.remove(
        "running",
        "completed"
    );


    if (state) {

        card.classList.add(state);

    }


    const status =
        card.querySelector(".agent-status");


    if (status) {

        status.textContent = statusText;

        status.classList.remove(
            "waiting",
            "running",
            "completed"
        );

        status.classList.add(
            state || "waiting"
        );

    }

}


/* =========================================================
   RESET WORKFLOW
========================================================= */

function resetWorkflow() {

    updateWorkflow(
        "agent-planner",
        "waiting",
        "Waiting"
    );

    updateWorkflow(
        "agent-youtube",
        "waiting",
        "Waiting"
    );

    updateWorkflow(
        "agent-rag",
        "waiting",
        "Waiting"
    );

    updateWorkflow(
        "agent-strategy",
        "waiting",
        "Waiting"
    );
}

/* =========================================================
   DELAY
========================================================= */

function delay(milliseconds) {

    return new Promise(
        resolve => setTimeout(resolve, milliseconds)
    );

}


/* =========================================================
   DISPLAY RESULTS
========================================================= */

function displayResults(data) {

    const analysis =
        data.youtube_analysis || {};

    const strategy =
        data.strategy || {};

    const youtubeResults =
        data.youtube_results || [];

    const creatorResults =
        data.creator_youtube_results || [];

    const creatorAnalysis =
        data.creator_youtube_analysis || {};

    const ragContext =
        data.rag_context || [];


    /* =====================================================
       YOUTUBE ANALYSIS
    ====================================================== */

    const analysisContainer =
        document.getElementById("youtube-analysis");


    analysisContainer.innerHTML = `

        <div class="stat-card">

            <span>Videos Analyzed</span>

            <strong>
                ${formatNumber(analysis.total_videos)}
            </strong>

        </div>


        <div class="stat-card">

            <span>Total Views</span>

            <strong>
                ${formatNumber(analysis.total_views)}
            </strong>

        </div>


        <div class="stat-card">

            <span>Average Views</span>

            <strong>
                ${formatNumber(analysis.average_views)}
            </strong>

        </div>


        <div class="stat-card">

            <span>Engagement Rate</span>

            <strong>
                ${analysis.average_engagement_rate || 0}%
            </strong>

        </div>

    `;


    /* =====================================================
       CONTENT PATTERNS
    ====================================================== */

    const patternsList =
        document.getElementById("patterns-list");


    patternsList.innerHTML = "";


    if (
        strategy.content_patterns &&
        strategy.content_patterns.length > 0
    ) {

        strategy.content_patterns.forEach(pattern => {

            patternsList.innerHTML += `

                <div class="result-item">

                    ${escapeHtml(pattern)}

                </div>

            `;

        });

    } else {

        patternsList.innerHTML =
            "<p>No content patterns available.</p>";

    }


    /* =====================================================
       RECOMMENDED TOPICS
    ====================================================== */

    const topicsList =
        document.getElementById("topics-list");


    topicsList.innerHTML = "";


    if (
        strategy.recommended_topics &&
        strategy.recommended_topics.length > 0
    ) {

        strategy.recommended_topics.forEach(topic => {

            topicsList.innerHTML += `

                <div class="result-item">

                    ${escapeHtml(topic)}

                </div>

            `;

        });

    } else {

        topicsList.innerHTML =
            "<p>No recommended topics available.</p>";

    }


    /* =====================================================
       VIDEO IDEAS
    ====================================================== */

    const ideasList =
        document.getElementById("ideas-list");


    ideasList.innerHTML = "";


    if (
        strategy.video_ideas &&
        strategy.video_ideas.length > 0
    ) {

        strategy.video_ideas.forEach(idea => {

            ideasList.innerHTML += `

                <div class="idea-card">

                    <h4>
                        ${escapeHtml(
                            idea.title || ""
                        )}
                    </h4>

                    <p>
                        ${escapeHtml(
                            idea.reason || ""
                        )}
                    </p>

                </div>

            `;

        });

    } else {

        ideasList.innerHTML =
            "<p>No video ideas available.</p>";

    }


    /* =====================================================
       CONTENT DIRECTION
    ====================================================== */

    const directionText =
        document.getElementById("direction-text");


    directionText.textContent =
        strategy.content_direction ||
        "No content direction available.";


    /* =====================================================
       TOP YOUTUBE VIDEOS
    ====================================================== */

    const youtubeVideosContainer =
        document.getElementById("youtube-videos");


    youtubeVideosContainer.innerHTML = "";


    youtubeResults
        .slice(0, 10)
        .forEach(video => {

            youtubeVideosContainer.innerHTML += `

                <div class="youtube-video-card">

                    <div class="youtube-video-title">

                        ${escapeHtml(
                            video.title || ""
                        )}

                    </div>


                    <div class="youtube-video-channel">

                        ${escapeHtml(
                            video.channel || ""
                        )}

                    </div>


                    <div class="youtube-video-stats">

                        <span>
                            👁 ${formatNumber(video.views)}
                        </span>

                        <span>
                            👍 ${formatNumber(video.likes)}
                        </span>

                        <span>
                            💬 ${formatNumber(video.comments)}
                        </span>

                    </div>

                </div>

            `;

        });


    /* =====================================================
       CREATOR RESEARCH
    ====================================================== */

    displayCreatorResearch(
        creatorResults,
        creatorAnalysis
    );


    /* =====================================================
    RAG KNOWLEDGE
    ====================================================== */

    const ragList =
        document.getElementById("rag-list");


    if (ragList) {

        ragList.innerHTML = "";


        if (ragContext.length > 0) {

            ragContext.forEach(item => {

                ragList.innerHTML += `

                    <div class="result-item">

                        <strong>
                            Source:
                            ${escapeHtml(
                                item.niche || "Knowledge Base"
                            )}
                        </strong>

                        <div class="rag-content">

                            ${escapeHtml(
                                item.content || ""
                            )}

                        </div>

                    </div>

                `;

            });

        } else {

            ragList.innerHTML = `

                <div class="result-item">

                    No knowledge retrieved.

                </div>

            `;

        }

    }


    console.log(
        "Creator YouTube Research:",
        creatorResults
    );

    /* =====================================================
       EVALUATION METRICS
    ====================================================== */

    displayEvaluation(
        data.evaluation || {}
    );

}

/* =========================================================
   AGENT EVALUATION
========================================================= */

function displayEvaluation(evaluation) {

    if (!evaluation) {
        console.warn("No evaluation data returned.");
        return;
    }

    const resultsSection =
        document.getElementById("results-section");

    if (!resultsSection) {
        return;
    }

    const existingEvaluation =
        document.getElementById("evaluation-section");

    if (existingEvaluation) {
        existingEvaluation.remove();
    }

    const agents = evaluation.agent_metrics || {};
    const youtube = evaluation.youtube_metrics || {};
    const rag = evaluation.rag_metrics || {};
    const output = evaluation.output_metrics || {};
    const novelty = evaluation.novelty || {};
    const research = evaluation.research_metrics || {};

    const overallSuccess =
        evaluation.end_to_end_success === true;

    const statusBadge = (success) => `
        <span class="evaluation-status ${success ? "passed" : "failed"}">
            ${success ? "✓ PASS" : "✗ CHECK"}
        </span>
    `;

    const valueOrNA = (value, suffix = "") =>
        value === null || value === undefined
            ? "N/A"
            : `${value}${suffix}`;

    const researchMetric = (key, label) => {
        const item = research[key] || {};
        return `
            <div class="evaluation-metric">
                <div>
                    <strong>${label}</strong>
                    <span>${escapeHtml(item.reason || "Requires evaluation data")}</span>
                </div>
                <b class="metric-na">${valueOrNA(item.value)}</b>
            </div>
        `;
    };

    const evaluationHTML = `
        <section id="evaluation-section" class="evaluation-section">

            <div class="evaluation-header">
                <div>
                    <div class="step-label">STEP 04</div>
                    <h2>📈 System Evaluation</h2>
                    <p>
                        Metrics calculated for this exact generation.
                        No additional YouTube or Groq request is made for evaluation.
                    </p>
                </div>

                <div class="evaluation-overall ${overallSuccess ? "evaluation-success" : "evaluation-failed"}">
                    ${overallSuccess ? "✓ End-to-End Success" : "⚠ Incomplete Run"}
                </div>
            </div>

            <!-- LIVE SYSTEM METRICS -->
            <div class="evaluation-summary-grid">

                <div class="evaluation-summary-card">
                    <span>Agent Task Success Rate</span>
                    <strong>${valueOrNA(evaluation.agent_success_rate_percent, "%")}</strong>
                    <small>${agents.agents_passed || 0} / ${agents.agents_total || 4} agents passed</small>
                </div>

                <div class="evaluation-summary-card">
                    <span>End-to-End Success</span>
                    <strong>${overallSuccess ? "100%" : "0%"}</strong>
                    <small>All required pipeline stages completed</small>
                </div>

                <div class="evaluation-summary-card">
                    <span>Execution Time</span>
                    <strong>${valueOrNA(evaluation.execution_time_seconds, " s")}</strong>
                    <small>Measured for this generation</small>
                </div>

                <div class="evaluation-summary-card">
                    <span>Strategy Completeness</span>
                    <strong>${valueOrNA(output.strategy_completeness_percent, "%")}</strong>
                    <small>Patterns + topics + ideas + direction</small>
                </div>

            </div>

            <!-- AGENT-LEVEL METRICS -->
            <h3 class="evaluation-subtitle">Agent-Level Evaluation</h3>

            <div class="evaluation-grid">

                <div class="evaluation-card">
                    <div class="evaluation-card-header">
                        <h3>🧭 Planner Agent</h3>
                        ${statusBadge(agents.planner_success)}
                    </div>
                    <div class="evaluation-stat">
                        <span>Task Success</span>
                        <strong>${agents.planner_success ? "100%" : "0%"}</strong>
                    </div>
                </div>

                <div class="evaluation-card">
                    <div class="evaluation-card-header">
                        <h3>▶ YouTube Research Agent</h3>
                        ${statusBadge(agents.youtube_research_success)}
                    </div>
                    <div class="evaluation-stat">
                        <span>Task Success</span>
                        <strong>${agents.youtube_research_success ? "100%" : "0%"}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>Videos Retrieved</span>
                        <strong>${formatNumber(youtube.videos_retrieved || 0)}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>YouTube API Call</span>
                        <strong>${youtube.api_called ? "Yes" : "No (cache)"}</strong>
                    </div>
                </div>

                <div class="evaluation-card">
                    <div class="evaluation-card-header">
                        <h3>🧠 RAG Retrieval Agent</h3>
                        ${statusBadge(agents.rag_retrieval_success)}
                    </div>
                    <div class="evaluation-stat">
                        <span>Task Success</span>
                        <strong>${agents.rag_retrieval_success ? "100%" : "0%"}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>Documents Retrieved</span>
                        <strong>${formatNumber(rag.documents_retrieved || 0)}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>Niche-Filter Precision</span>
                        <strong>${valueOrNA(rag.niche_filter_precision_percent, "%")}</strong>
                    </div>
                </div>

                <div class="evaluation-card">
                    <div class="evaluation-card-header">
                        <h3>✨ Content Strategy Agent</h3>
                        ${statusBadge(agents.content_strategy_success)}
                    </div>
                    <div class="evaluation-stat">
                        <span>Task Success</span>
                        <strong>${agents.content_strategy_success ? "100%" : "0%"}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>Video Ideas</span>
                        <strong>${formatNumber(output.video_ideas || 0)}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>Recommended Topics</span>
                        <strong>${formatNumber(output.recommended_topics || 0)}</strong>
                    </div>
                </div>

            </div>

            <!-- NOVELTY -->
            <div class="evaluation-card novelty-card">
                <div class="evaluation-card-header">
                    <h3>💡 Novelty Evaluation</h3>
                    <span class="evaluation-badge">
                        ${novelty.status === "Measured"
                            ? valueOrNA(novelty.novelty_rate_percent, "%") + " Novelty Rate"
                            : "N/A"}
                    </span>
                </div>

                <div class="evaluation-grid novelty-grid">
                    <div class="evaluation-stat">
                        <span>Candidate Ideas</span>
                        <strong>${formatNumber(novelty.candidate_ideas || 0)}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>Accepted Ideas</span>
                        <strong>${formatNumber(novelty.accepted_ideas || 0)}</strong>
                    </div>
                    <div class="evaluation-stat">
                        <span>Rejected as Duplicate</span>
                        <strong>${formatNumber(novelty.rejected_ideas || 0)}</strong>
                    </div>
                </div>

                <p class="evaluation-note">
                    ${escapeHtml(
                        novelty.status === "Measured"
                            ? "Calculated by comparing generated ideas with the analyzed creator and niche video titles."
                            : (novelty.reason || "Creator-specific novelty is not applicable for this run.")
                    )}
                </p>
            </div>

            <!-- RESEARCH-PAPER METRICS -->
                        <!-- RAG RETRIEVAL BENCHMARK -->
            <div class="evaluation-card research-metrics-card">

                <div class="evaluation-card-header">
                    <div>
                        <h3>📚 RAG Retrieval Benchmark</h3>

                        <p class="evaluation-card-description">
                            Retrieval quality measured using the
                            15-query labelled RAG benchmark.
                        </p>
                    </div>
                </div>

                <div class="research-metrics-grid">

                    <div class="evaluation-metric">
                        <div>
                            <strong>Precision@3</strong>
                            <span>
                                Average precision across the benchmark queries.
                            </span>
                        </div>

                        <b class="metric-value">
                            ${
                                research.rag_retrieval_benchmark &&
                                research.rag_retrieval_benchmark.precision_at_3 !== null
                                    ? (
                                        research.rag_retrieval_benchmark.precision_at_3 * 100
                                    ).toFixed(2) + "%"
                                    : "N/A"
                            }
                        </b>
                    </div>


                    <div class="evaluation-metric">
                        <div>
                            <strong>Recall@3</strong>
                            <span>
                                Whether the relevant document was retrieved within the top 3.
                            </span>
                        </div>

                        <b class="metric-value">
                            ${
                                research.rag_retrieval_benchmark &&
                                research.rag_retrieval_benchmark.recall_at_3 !== null
                                    ? (
                                        research.rag_retrieval_benchmark.recall_at_3 * 100
                                    ).toFixed(2) + "%"
                                    : "N/A"
                            }
                        </b>
                    </div>


                    <div class="evaluation-metric">
                        <div>
                            <strong>MRR</strong>
                            <span>
                                Mean Reciprocal Rank of the relevant document.
                            </span>
                        </div>

                        <b class="metric-value">
                            ${
                                research.rag_retrieval_benchmark &&
                                research.rag_retrieval_benchmark.mrr !== null
                                    ? (
                                        research.rag_retrieval_benchmark.mrr * 100
                                    ).toFixed(2) + "%"
                                    : "N/A"
                            }
                        </b>
                    </div>


                    <div class="evaluation-metric">
                        <div>
                            <strong>nDCG@3</strong>
                            <span>
                                Ranking quality of the retrieved documents.
                            </span>
                        </div>

                        <b class="metric-value">
                            ${
                                research.rag_retrieval_benchmark &&
                                research.rag_retrieval_benchmark.ndcg_at_3 !== null
                                    ? (
                                        research.rag_retrieval_benchmark.ndcg_at_3 * 100
                                    ).toFixed(2) + "%"
                                    : "N/A"
                            }
                        </b>
                    </div>


                    <div class="evaluation-metric">
                        <div>
                            <strong>Evaluation Queries</strong>
                            <span>
                                Labelled queries used for the benchmark.
                            </span>
                        </div>

                        <b class="metric-value">
                            ${
                                research.rag_retrieval_benchmark
                                    ? research.rag_retrieval_benchmark.evaluation_queries || 0
                                    : 0
                            }
                        </b>
                    </div>

                </div>


                <div class="evaluation-note">

                    <strong>Benchmark Status:</strong>

                    ${
                        research.rag_retrieval_benchmark &&
                        research.rag_retrieval_benchmark.status === "Measured"
                            ? "Measured using the saved 15-query RAG benchmark. These values are loaded from the benchmark file and are not recalculated during each generation."
                            : (
                                research.rag_retrieval_benchmark?.reason ||
                                "RAG benchmark has not been measured yet."
                            )
                    }

                </div>

            </div>



        </section>
    `;

    resultsSection.insertAdjacentHTML("beforeend", evaluationHTML);
}


/* =========================================================
   CREATOR RESEARCH DISPLAY
========================================================= */

function displayCreatorResearch(
    creatorResults,
    creatorAnalysis
) {

    const section =
        document.getElementById("creator-videos-section");

    const analysisContainer =
        document.getElementById("creator-analysis");

    const videosContainer =
        document.getElementById("creator-videos");


    /*
     * No creator channel data
     */

    if (!creatorResults || creatorResults.length === 0) {

        section.classList.add("hidden");

        console.log(
            "No creator-specific YouTube research."
        );

        return;

    }


    /*
     * Show creator section
     */

    section.classList.remove("hidden");


    /* =====================================================
       CREATOR STATISTICS
    ====================================================== */

    analysisContainer.innerHTML = `

        <div class="stat-card">

            <span>
                Videos Analyzed
            </span>

            <strong>
                ${formatNumber(
                    creatorAnalysis.total_videos
                )}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Total Views
            </span>

            <strong>
                ${formatNumber(
                    creatorAnalysis.total_views
                )}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Average Views
            </span>

            <strong>
                ${formatNumber(
                    creatorAnalysis.average_views
                )}
            </strong>

        </div>


        <div class="stat-card">

            <span>
                Engagement Rate
            </span>

            <strong>
                ${creatorAnalysis.average_engagement_rate || 0}%
            </strong>

        </div>

    `;


    /* =====================================================
       CREATOR VIDEOS
    ====================================================== */

    videosContainer.innerHTML = "";


    creatorResults
        .slice(0, 10)
        .forEach(video => {

            videosContainer.innerHTML += `

                <div class="youtube-video-card">

                    <div class="youtube-video-title">

                        ${escapeHtml(
                            video.title || ""
                        )}

                    </div>


                    <div class="youtube-video-channel">

                        ${escapeHtml(
                            video.channel || ""
                        )}

                    </div>


                    <div class="youtube-video-stats">

                        <span>
                            👁 ${formatNumber(
                                video.views
                            )}
                        </span>

                        <span>
                            👍 ${formatNumber(
                                video.likes
                            )}
                        </span>

                        <span>
                            💬 ${formatNumber(
                                video.comments
                            )}
                        </span>

                    </div>

                </div>

            `;

        });


    /* =====================================================
       CONSOLE DEBUG
    ====================================================== */

    console.log(
        "========== CREATOR CHANNEL RESEARCH =========="
    );

    console.log(
        "Videos analyzed:",
        creatorAnalysis.total_videos
    );

    console.log(
        "Total views:",
        creatorAnalysis.total_views
    );

    console.log(
        "Average views:",
        creatorAnalysis.average_views
    );

    console.log(
        "Engagement rate:",
        creatorAnalysis.average_engagement_rate
    );

    console.table(creatorResults);

    console.log(
        "=============================================="
    );

}

/* =========================================================
   FORMAT NUMBERS
========================================================= */

function formatNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "0";

    }


    const number = Number(value);


    if (Number.isNaN(number)) {

        return value;

    }


    return new Intl.NumberFormat(
        "en-IN"
    ).format(number);

}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}