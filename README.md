```md
# GraphCycle

GraphCycle is an experimental autonomous agent built using the Google Agent Development Kit (ADK). It is designed to extract, refine, and organize knowledge from unstructured data (text files or YouTube video transcripts) into RDF knowledge graphs in Turtle format. The agent employs an iterative, parallel processing approach to build and review knowledge graphs, culminating in a merged, comprehensive graph.

## Features

*   **Autonomous Knowledge Extraction:** Leverages the Google ADK for autonomous operation.
*   **Versatile Input:** Processes unstructured text from local files or YouTube video transcripts.
*   **RDF Knowledge Graph Generation:** Outputs knowledge graphs in the Turtle RDF format.
*   **Iterative Refinement:** Employs a loop of generation and review to improve graph quality.
*   **Parallel Processing:** Runs two independent knowledge graph refinement loops concurrently for enhanced coverage and robustness.
*   **Knowledge Fusion:** Merges the outputs of the parallel refinement loops into a single knowledge graph.
*   **Integrated Tools:**
    *   `read_file_content`: Reads text from specified file paths.
    *   `download_youtube_transcript`: Fetches and formats transcripts from YouTube videos.
    *   `validate_turtle`: Checks the syntax of generated Turtle RDF.
    *   `store_knowledge_graph` / `load_knowledge_graph`: Manages knowledge graph data within the agent's state.

## Prerequisites

*   Python 3.10+
*   Git
*   Google ADK installed via pip

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/hammertoe/GraphCycle.git
cd GraphCycle
```

### 2. Set up a virtual environment

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Google ADK CLI (if not already installed)

```bash
pip install google-adk
```

### 5. Set up Google Gemini API Key

1.  Generate an API key for Google Gemini at [Google AI Studio](https://aistudio.google.com/app/apikey)
2.  Set the API key as an environment variable:

**macOS / Linux**

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

**Windows**

```bash
set GOOGLE_API_KEY=your_api_key_here
```

Alternatively, you can add it to your `.bashrc`, `.zshrc`, or create a `.env` file in the project root.

## Running the Agent

To run the main knowledge graph extraction agent:

```bash
adk run graphcycle
```

This command launches the `KnowledgeGraphPipeline` defined in `graphcycle/agent.py`. The agent will then prompt for input:
`[user]: `

You can provide:
*   A path to a local text file (e.g., `scratch/graph_data/a.txt`).
*   A URL to a YouTube video (e.g., `https://www.youtube.com/watch?v=your_video_id`).

The agent will process the input through its pipeline and output logs of its operations, including the refined knowledge graphs. An example of the agent's interaction and output can be found in `graphcycle/example_output.txt`.

## Project Structure

```
GraphCycle/
├── graphcycle/
│   ├── __init__.py         # Initializes the graphcycle package
│   └── agent.py          # Core logic for the knowledge graph extraction agent
│   └── example_output.txt# Example run output of the agent
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── scratch/              # Directory for earlier experiments, utility scripts, and sample data.
                          # These are not part of the main agent execution flow but demonstrate
                          # various ADK capabilities and development steps.
```

## Agent Workflow Overview

The `KnowledgeGraphPipeline` orchestrates the following sequence of operations:

1.  **Text Loading (`TextLoader`)**:
    *   Prompts the user for a file path or YouTube URL.
    *   Uses tools to load the raw text content into the agent's state (`raw_text`).

2.  **Parallel Knowledge Graph Refinement (`KGRefinementLoopParallel`)**:
    *   Two identical refinement loops (`KGRefinementLoop1` and `KGRefinementLoop2`) run in parallel, each operating on the same `raw_text`.
    *   Each loop iteratively performs the following (up to a maximum of 5 iterations):
        *   **Graph Building (`GraphBuilder1`/`GraphBuilder2`)**: An LLM agent generates or refines a knowledge graph in Turtle format based on `raw_text` and any `missing_items` identified by the reviewer in the previous iteration. The generated graph is stored in the agent's state (e.g., `knowledge_graph1`).
        *   **Graph Reviewing (`GraphReviewer1`/`GraphReviewer2`)**: Another LLM agent accesses the `raw_text` and the generated knowledge graph. It validates the graph's Turtle syntax and compares its content against the `raw_text`.
            *   If the graph is complete and syntactically valid, it outputs `pass`.
            *   If the graph is incomplete, contains errors, or requires improvements, it outputs `fail` along with a list of missing items or suggestions. This feedback is stored (e.g., as `missing_items`) for the next iteration of the `GraphBuilder`.
        *   **Stopping Condition (`StopChecker1`/`StopChecker2`)**: The loop terminates if the `GraphReviewer` outputs `pass` or if the maximum number of iterations is reached.

3.  **Knowledge Graph Merging (`SynthesisAgent`)**:
    *   An LLM agent takes the two (potentially different) knowledge graphs produced by `KGRefinementLoop1` and `KGRefinementLoop2`.
    *   It merges them into a single, more comprehensive Turtle RDF graph, resolving conflicts and removing duplicates.
    *   The final merged graph is outputted.

## Key Components

The agent system is composed of several specialized ADK agents:

*   **`TextLoader`**: Loads input text from files or YouTube transcripts.
*   **`GraphBuilder1`, `GraphBuilder2`**: LLM agents responsible for generating/refining Turtle knowledge graphs from text. They are instructed to consider feedback from reviewers.
*   **`GraphReviewer1`, `GraphReviewer2`**: LLM agents that validate the generated graphs against the source text and Turtle syntax, providing feedback for improvement.
*   **`StopIfComplete`**: A simple agent that checks the output of a `GraphReviewer` and signals whether its refinement loop should stop.
*   **`KGRefinementLoop1`, `KGRefinementLoop2`**: `LoopAgent`s that encapsulate the iterative build-review-stop cycle.
*   **`KGRefinementLoopParallel`**: A `ParallelAgent` that executes `KGRefinementLoop1` and `KGRefinementLoop2` concurrently.
*   **`SynthesisAgent`**: An LLM agent that merges the two knowledge graphs from the parallel loops.
*   **`KnowledgeGraphPipeline`**: The main `SequentialAgent` that defines the overall workflow: Load -> Parallel Refine -> Merge.

## Scratch Directory

The `scratch/` directory contains various files related to earlier experiments, utility scripts (e.g., for visualizing RDF graphs directly with `pyvis`), sample data (text files, Turtle files), and simpler ADK agent examples. These files are not part of the main `graphcycle` agent's execution flow but serve as a log of development efforts and demonstrations of different ADK features.
```