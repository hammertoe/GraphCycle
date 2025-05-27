"""
Knowledge Graph Pipeline
Converts text documents into RDF knowledge graphs using Google ADK agents.
"""

import os
import random
from pathlib import Path

from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from rdflib import Graph, Namespace

# Configuration
DATA_DIR = Path("graph_data")
DATA_DIR.mkdir(exist_ok=True)

# File paths
NEW_GRAPH_FILE = DATA_DIR / "new_graph.ttl"
MERGED_GRAPH_FILE = DATA_DIR / "merged_graph.ttl"

# State keys
TRIPLES_STATE_KEY = "generated_triples"
RAW_TEXT_STATE_KEY = "raw_text"
SOURCE_FILE_STATE_KEY = "source_file"
WALKED_TRIPLES_STATE_KEY = "walked_triples"

# Constants
MAX_TEXT_PREVIEW_LENGTH = 6000
GRAPH_WALK_SAMPLE_SIZE = 2
REFINEMENT_MAX_ITERATIONS = 3


# ──────────────────────── Tool Functions ────────────────────────

def load_text_file(filename: str, tool_context: ToolContext, **_) -> dict:
    """Load a text file from the data directory into the agent state."""
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        return {
            "status": "error", 
            "message": f"File not found: {filename}"
        }
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    tool_context.state[RAW_TEXT_STATE_KEY] = content
    tool_context.state[SOURCE_FILE_STATE_KEY] = filename
    
    return {
        "status": "success", 
        "message": f"Loaded '{filename}' ({len(content)} characters)"
    }


def get_text_preview(tool_context: ToolContext, **_) -> dict:
    """Return a preview of the loaded text for processing."""
    text = tool_context.state.get(RAW_TEXT_STATE_KEY, "")
    
    if not text:
        return {
            "status": "error", 
            "message": "No text loaded"
        }
    
    preview = text[:MAX_TEXT_PREVIEW_LENGTH]
    truncated = len(text) > MAX_TEXT_PREVIEW_LENGTH
    
    return {
        "status": "success", 
        "text": preview,
        "truncated": truncated,
        "total_length": len(text)
    }


def save_triples_as_graph(tool_context: ToolContext, **_) -> dict:
    """Parse RDF triples from state and save as Turtle format."""
    triples_data = tool_context.state.get(TRIPLES_STATE_KEY)
    
    if not triples_data:
        return {
            "status": "error", 
            "message": "No triples found in state"
        }
    
    # Clean up the data if it has markdown formatting
    if "```turtle" in triples_data:
        # Extract content between ```turtle and ```
        start = triples_data.find("```turtle") + 9
        end = triples_data.find("```", start)
        if end > start:
            triples_data = triples_data[start:end].strip()
    elif "'''turtle" in triples_data:
        # Clean up triple-quote format
        triples_data = triples_data.replace("'''turtle\n", "").replace("'''", "")
    
    # Parse the triples data
    try:
        graph = Graph()
        graph.parse(data=triples_data, format="turtle")
        
        # Save to file
        graph.serialize(destination=str(NEW_GRAPH_FILE), format="turtle")
        
        return {
            "status": "success", 
            "message": f"Saved {len(graph)} triples to {NEW_GRAPH_FILE.name}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to parse triples: {str(e)}"
        }


def merge_graph_files(tool_context: ToolContext, **_) -> dict:
    """Merge the new graph with the existing merged graph."""
    merged_graph = Graph()
    
    # Load existing merged graph if it exists
    if MERGED_GRAPH_FILE.exists():
        merged_graph.parse(str(MERGED_GRAPH_FILE), format="turtle")
        initial_size = len(merged_graph)
    else:
        initial_size = 0
    
    # Add new graph if it exists
    if NEW_GRAPH_FILE.exists():
        merged_graph.parse(str(NEW_GRAPH_FILE), format="turtle")
    
    # Save merged result
    merged_graph.serialize(destination=str(MERGED_GRAPH_FILE), format="turtle")
    
    return {
        "status": "success", 
        "message": f"Merged graphs: {initial_size} → {len(merged_graph)} triples"
    }


def get_graph_statistics(tool_context: ToolContext, **_) -> dict:
    """Return statistics about the merged graph."""
    if not MERGED_GRAPH_FILE.exists():
        return {
            "status": "error", 
            "message": "No merged graph found"
        }
    
    graph = Graph()
    graph.parse(str(MERGED_GRAPH_FILE), format="turtle")
    
    # Collect statistics
    subjects = set(s for s, _, _ in graph)
    predicates = set(p for _, p, _ in graph)
    objects = set(o for _, _, o in graph)
    
    return {
        "status": "success",
        "total_triples": len(graph),
        "unique_subjects": len(subjects),
        "unique_predicates": len(predicates),
        "unique_objects": len(objects)
    }


def sample_graph_nodes(tool_context: ToolContext, **_) -> dict:
    """Sample random nodes from the graph for inspection."""
    if not MERGED_GRAPH_FILE.exists():
        return {
            "status": "error", 
            "message": "No merged graph found"
        }
    
    graph = Graph()
    graph.parse(str(MERGED_GRAPH_FILE), format="turtle")
    
    # Get all subjects
    subjects = list({s for s, _, _ in graph})
    if not subjects:
        return {
            "status": "success", 
            "message": "Graph is empty"
        }
    
    # Sample nodes
    sample_size = min(GRAPH_WALK_SAMPLE_SIZE, len(subjects))
    sampled_nodes = random.sample(subjects, sample_size)
    
    # Collect triples for sampled nodes
    sampled_triples = []
    for node in sampled_nodes:
        for s, p, o in graph.triples((node, None, None)):
            sampled_triples.append((str(s), str(p), str(o)))
    
    tool_context.state[WALKED_TRIPLES_STATE_KEY] = sampled_triples
    
    return {
        "status": "success",
        "sampled_nodes": sample_size,
        "triples_found": len(sampled_triples)
    }


def store_rdf_triples(triples: str, tool_context: ToolContext, **_) -> dict:
    """Store generated RDF triples in the agent state."""
    if not triples:
        return {
            "status": "error",
            "message": "No triples provided to store"
        }
    
    tool_context.state[TRIPLES_STATE_KEY] = triples
    
    return {
        "status": "success",
        "message": f"Stored RDF triples in state (length: {len(triples)} characters)"
    }


# ──────────────────────── Agent Definitions ────────────────────────

# Agent for loading text files
text_loader_agent = Agent(
    name="text_loader",
    model="gemini-2.0-flash",
    description=(
        "Loads text files from the data directory. Use this agent when you need to "
        "read a text file that will be converted into a knowledge graph. It handles "
        "file reading and stores the content in the agent state for further processing."
    ),
    instruction=(
        "Load the text file specified by the user (e.g., 'file=recipe.txt'). "
        "Use the load_text_file tool with the filename. "
        "If no filename is provided, ask the user to specify one."
    ),
    tools=[load_text_file]
)

# Agent for converting text to RDF triples
text_to_rdf_agent = Agent(
    name="text_to_rdf_converter",
    model="gemini-2.0-flash",
    description=(
        "Converts loaded text into RDF triples in Turtle format. Use this agent after "
        "loading text to extract entities and relationships and transform them into a "
        "knowledge graph structure. It requires text to be already loaded in the state."
    ),
    instruction=(
        "First, call get_text_preview to retrieve the loaded text. "
        "Then convert the text into a knowledge graph in Turtle RDF format. "
        "Focus on extracting entities and their relationships. "
        "Generate valid Turtle syntax with appropriate namespaces. "
        "After generating the triples, use store_rdf_triples to save them to the state. "
        "The triples should be plain Turtle format without markdown code blocks."
    ),
    tools=[get_text_preview, store_rdf_triples]
)

# Agent for saving RDF triples
graph_writer_agent = Agent(
    name="graph_writer",
    model="gemini-2.0-flash",
    description=(
        "Saves generated RDF triples to a graph file. Use this agent after converting "
        "text to RDF to persist the knowledge graph. It takes the triples from the "
        "agent state and saves them in Turtle format."
    ),
    instruction="Save the generated RDF triples to a graph file using save_triples_as_graph.",
    tools=[save_triples_as_graph]
)

# Agent for merging graphs
graph_merger_agent = Agent(
    name="graph_merger",
    model="gemini-2.0-flash",
    description=(
        "Merges newly created graphs with the existing knowledge base. Use this agent "
        "to combine multiple knowledge graphs into a single, comprehensive graph. It "
        "preserves all existing knowledge while adding new information."
    ),
    instruction="Merge the new graph with the existing knowledge base using merge_graph_files.",
    tools=[merge_graph_files]
)

# Agent for graph analysis
graph_analyzer_agent = Agent(
    name="graph_analyzer",
    model="gemini-2.0-flash",
    description=(
        "Analyzes the knowledge graph and provides statistics. Use this agent to get "
        "insights about the graph such as total triples, unique entities, and relationships. "
        "Useful for understanding the size and structure of your knowledge base."
    ),
    instruction="Analyze the merged graph and report statistics using get_graph_statistics.",
    tools=[get_graph_statistics]
)

# Agent for graph sampling
graph_sampler_agent = Agent(
    name="graph_sampler",
    model="gemini-2.0-flash",
    description=(
        "Samples random nodes from the knowledge graph for inspection. Use this agent "
        "to explore specific parts of the graph and understand the types of relationships "
        "and entities that have been extracted."
    ),
    instruction="Sample nodes from the graph for inspection using sample_graph_nodes.",
    tools=[sample_graph_nodes]
)

# Refinement loop - iteratively samples and examines the graph
refinement_loop = LoopAgent(
    name="graph_refinement_loop",
    description=(
        "Iteratively samples and examines the knowledge graph. Use this agent to "
        "perform multiple rounds of graph inspection, which can help identify patterns "
        "or areas that might need improvement in the knowledge extraction process."
    ),
    sub_agents=[graph_sampler_agent],
    max_iterations=REFINEMENT_MAX_ITERATIONS
)

# Main orchestrator with subagents
knowledge_graph_pipeline = Agent(
    name="knowledge_graph_orchestrator",
    model="gemini-2.0-flash",
    instruction=(
        "You are a knowledge graph pipeline orchestrator. Your role is to manage the "
        "conversion of text documents into RDF knowledge graphs. Based on the user's "
        "request, intelligently decide which subagents to use and in what order.\n\n"
        "Available subagents:\n"
        "- text_loader: Loads text files from the data directory\n"
        "- text_to_rdf_converter: Converts loaded text into RDF triples\n"
        "- graph_writer: Saves generated RDF triples to a file\n"
        "- graph_merger: Merges new graphs with existing knowledge base\n"
        "- graph_analyzer: Provides statistics about the graph\n"
        "- graph_refinement_loop: Iteratively samples the graph for inspection\n\n"
        "Common workflows:\n"
        "1. To process a new file: text_loader → text_to_rdf_converter → graph_writer → graph_merger\n"
        "2. To analyze the existing graph: graph_analyzer\n"
        "3. To explore graph content: graph_refinement_loop\n\n"
        "Consider the current state and what has already been done. If a file "
        "is already loaded, you don't need to load it again. If triples are already "
        "generated, you can skip directly to saving or merging."
    ),
    sub_agents=[
        text_loader_agent,
        text_to_rdf_agent,
        graph_writer_agent,
        graph_merger_agent,
        graph_analyzer_agent,
        refinement_loop
    ]
)

# Entry point
root_agent = knowledge_graph_pipeline