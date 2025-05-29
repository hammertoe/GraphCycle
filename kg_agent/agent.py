"""
Iterative knowledge-graph extractor with ADK
Run with:  adk run kg_agent          # CLI
           adk web                   # Dev UI in the browser
"""

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent, BaseAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator

from rdflib import Graph

import sys
import os

import logging
logger = logging.getLogger(__name__)

import json

def read_file_content(file_path: str) -> dict:
    """
    Read the content of a file and return it as a string.
    If the file does not exist, return an empty string.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return {"status": "error", "error_message": "File not found"}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    return {"status": "success", 
            "file_path": file_path,
            "length": len(content),
            "raw_text": content}

def validate_turtle(turtle_string: str) -> dict:
    """
    Validates if a string is valid Turtle RDF syntax.
    
    Args:
        turtle_string: String containing potential Turtle RDF
        
    Returns:
        A dictionary with the following keys:
        - "status": "success" or "error"
        - "error_message": Description of the result
        - "triple_count": Number of triples parsed (if successful)
    """
    try:
        g = Graph()
        # Remove the fence prefix if it exists
        if turtle_string.startswith("```turtle"):
            turtle_string = turtle_string.replace("```turtle", "").replace
        g.parse(data=turtle_string, format='turtle')
        output = g.serialize(format='turtle')
        
        # Return success with triple count
        return {"status": "success", 
                "output": output,
                "triple_count": len(g)}
    except Exception as e:
        # Return the error message
        return {"status": "error", 
                "error_message": str(e)}
    
# ───────────────────────── 1. LLM agents ──────────────────────────
file_loader = LlmAgent(
    name="TextLoader",
    model="gemini-2.0-flash",  # or any model ID you've configured
    instruction=(
        "You are a text loader."
        "Use the read_file_content tool to read the content of a file. "
        "store the content in state['raw_text']."
        "Report the length of the text and the file path in the output."
    ),
    output_key="raw_text",
    tools=[read_file_content],
)

graph_builder = LlmAgent(
    name="GraphBuilder",
    model="gemini-2.0-flash",          # or any model ID you've configured
    instruction=(
        "You are an RDF engineer. "
        "Read state['raw_text'] and create **or refine** a Turtle knowledge "
        "graph covering every entity and relationship mentioned. "
        "If state['missing_items'] exists, be sure to add them. "
        "Output ONLY the Turtle RDF graph, nothing else."
    ),
    output_key="knowledge_graph",
)

graph_reviewer = LlmAgent(
    name="GraphReviewer",
    model="gemini-2.0-flash",
    instruction="""
        Compare state['raw_text'] with state['knowledge_graph'].
        Check if every entity and relationship from the raw_text is present in the knowledge graph.
        If everything is captured, output the single word 'pass'.
        If something is missing, output 'fail', followed by a list of missing items.
        If everything is captured then use the validate_turtle tool to check the Turtle syntax.
        If the Turtle syntax is invalid put the error message in the output.
        If the Turtle syntax is valid put the output from the validate_turtle tool in state['knowledge_graph'].
    """,
    tools=[validate_turtle],
    output_key="graph_status",
)

# ──────────────────────── 2. Stop checker ─────────────────────────
class StopIfComplete(BaseAgent):
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("graph_status", "fail").strip().lower()
        should_stop = status.startswith("pass")
        
        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_stop),  # stop loop when pass
        )

# ──────────────────────── 3. Loop agent ───────────────────────────
kg_refinement_loop = LoopAgent(
    name="KGRefinementLoop",
    max_iterations=5,  # bump if your text is huge
    sub_agents=[
        graph_builder,
        graph_reviewer,
        StopIfComplete(name="StopChecker"),
    ],
)

# ──────────────────────── 4. Root pipeline ────────────────────────
kg_pipeline = SequentialAgent(
    name="KnowledgeGraphPipeline",
    sub_agents=[file_loader, kg_refinement_loop],
)

# ADK discovers this when you run `adk run kg_agent`
root_agent = kg_pipeline