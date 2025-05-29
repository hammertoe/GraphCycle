import os
import datetime
from typing import Dict, Optional
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import asyncio

# Tool for loading text from file
def load_from_file(filename: str, tool_context: ToolContext) -> dict:
    """Loads text content from a file and stores it in the session state.
    
    Args:
        filename: Path to the file to load.
        tool_context: Automatically provided by ADK, provides access to session state.
    
    Returns:
        dict: Status and loaded content or error message.
    """
    try:
        # Check if file exists
        if not os.path.exists(filename):
            return {
                "status": "error",
                "error_message": f"File not found: {filename}"
            }
        
        # Read the file
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Store in session state for other agents to access
        tool_context.state["loaded_text"] = content
        tool_context.state["source_filename"] = filename
        tool_context.state["load_timestamp"] = datetime.datetime.now().isoformat()
        
        # Log the action
        print(f"Tool: Successfully loaded {len(content)} characters from {filename}")
        
        return {
            "status": "success",
            "message": f"Successfully loaded text from {filename}",
            "content_length": len(content),
            "preview": content[:200] + "..." if len(content) > 200 else content
        }
        
    except Exception as e:
        print(f"Tool Error: Failed to load file: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to load file: {str(e)}"
        }

# Tool for storing RDF graph in state
def store_rdf_graph(rdf_content: str, tool_context: ToolContext) -> dict:
    """Stores the RDF graph in the session state.
    
    Args:
        rdf_content: The RDF graph in Turtle format
        tool_context: Automatically provided by ADK
    
    Returns:
        dict: Status of the storage operation
    """
    try:
        # Store the RDF content
        tool_context.state["rdf_graph"] = rdf_content
        
        # Calculate some basic stats
        lines = rdf_content.strip().split('\n')
        prefix_count = sum(1 for line in lines if line.strip().startswith('@prefix'))
        triple_count = rdf_content.count('.')
        
        print(f"Tool: Stored RDF graph with {len(rdf_content)} characters")
        
        return {
            "status": "success",
            "message": "RDF graph stored successfully",
            "size": len(rdf_content),
            "line_count": len(lines),
            "prefix_count": prefix_count,
            "approximate_triples": triple_count
        }
    except Exception as e:
        print(f"Tool Error: Failed to store RDF graph: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to store RDF graph: {str(e)}"
        }

# Tool for saving RDF graph to file
def save_to_file(filename: str, tool_context: ToolContext) -> dict:
    """Saves the RDF knowledge graph from state to a file in Turtle format.
    
    Args:
        filename: Path where the Turtle file should be saved.
        tool_context: Automatically provided by ADK, provides access to session state.
    
    Returns:
        dict: Status of the save operation.
    """
    try:
        # Get the RDF graph from state
        rdf_graph = tool_context.state.get("rdf_graph", None)
        
        if not rdf_graph:
            return {
                "status": "error",
                "error_message": "No RDF graph found in state. Please ensure the conversion was successful."
            }
        
        # Ensure filename has .ttl extension
        if not filename.endswith('.ttl'):
            filename += '.ttl'
        
        # Write the Turtle content to file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(rdf_graph)
        
        # Update state with save information
        tool_context.state["output_filename"] = filename
        tool_context.state["save_timestamp"] = datetime.datetime.now().isoformat()
        
        # Calculate some stats
        triple_count = rdf_graph.count('.')
        
        print(f"Tool: Successfully saved RDF graph to {filename}")
        
        return {
            "status": "success",
            "message": f"Successfully saved RDF graph to {filename}",
            "filename": filename,
            "approximate_triples": triple_count,
            "file_size": os.path.getsize(filename)
        }
        
    except Exception as e:
        print(f"Tool Error: Failed to save file: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to save file: {str(e)}"
        }

# Agent 1: Text Loader
text_loader_agent = Agent(
    name="text_loader",
    model="gemini-2.0-flash",
    description="Loads text content from files into the system for processing.",
    instruction="""
    You are responsible for loading text content from files.
    
    Your tasks:
    1. Use the load_from_file tool to load text from the specified file
    2. Verify the content was loaded successfully
    3. Provide a brief summary of what was loaded
    
    If the user hasn't specified a filename, ask them for it.
    After loading, briefly describe the content (topic, length, type of text).
    """,
    tools=[load_from_file],
    output_key="load_summary"
)

# Agent 2: Text to Knowledge Graph Converter
knowledge_graph_converter = Agent(
    name="kg_converter",
    model="gemini-2.0-flash",
    description="Converts text content into RDF knowledge graphs in Turtle format.",
    instruction="""
    You are an expert at converting text into RDF knowledge graphs using the Turtle format.
    
    Your task is to:
    1. Analyze the text that was loaded by the previous agent
    2. Extract entities, relationships, and properties from the text
    3. Create a well-structured RDF graph in Turtle format
    4. Use the store_rdf_graph tool to save your RDF graph
    
    Guidelines for creating the RDF graph:
    - Use meaningful URIs for resources (e.g., :Person1, :Organization1)
    - Define appropriate prefixes at the beginning
    - Use standard vocabularies where applicable (foaf:, dc:, schema:)
    - Include rdf:type statements for all entities
    - Extract relationships between entities
    - Add literal properties (names, dates, descriptions)
    
    Example Turtle format:
    ```
    @prefix : <http://example.org/> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix schema: <http://schema.org/> .
    
    :Person1 a foaf:Person ;
        foaf:name "John Doe" ;
        schema:worksFor :Organization1 .
    
    :Organization1 a schema:Organization ;
        schema:name "Example Corp" .
    ```
    
    IMPORTANT: You must use the store_rdf_graph tool to save your RDF graph.
    First create the complete RDF graph as a string, then call the tool with that string.
    
    Also provide a summary of the entities and relationships extracted.
    """,
    tools=[store_rdf_graph],
    output_key="conversion_summary"
)

# Agent 3: RDF Archiver
rdf_archiver_agent = Agent(
    name="rdf_archiver",
    model="gemini-2.0-flash",
    description="Archives the generated RDF knowledge graph to a Turtle format file.",
    instruction="""
    You are responsible for saving the RDF knowledge graph to a file.
    
    Your tasks:
    1. Use the save_to_file tool to save the RDF graph from state["rdf_graph"]
    2. If no output filename is specified, generate one based on:
       - The source filename (if available in state["source_filename"])
       - Or use a timestamp-based name like "knowledge_graph_YYYYMMDD_HHMMSS.ttl"
    3. Actually call the tool.
    4. Verify the save was successful
    5. Provide a summary of what was saved
    
    Report the filename, file size, and approximate number of triples saved.
    """,
    tools=[save_to_file],
    output_key="archive_summary"
)

# Create the sequential multi-agent system
text_to_rdf_system = SequentialAgent(
    name="text_to_rdf_knowledge_graph_system",
    sub_agents=[
        text_loader_agent,
        knowledge_graph_converter,
        rdf_archiver_agent
    ]
)

# Helper function to run the system
async def convert_text_to_rdf(input_filename: str, output_filename: Optional[str] = None):
    """
    Converts a text file to an RDF knowledge graph in Turtle format.
    
    Args:
        input_filename: Path to the input text file
        output_filename: Optional path for the output Turtle file
    """
    # Set up session and runner
    session_service = InMemorySessionService()
    APP_NAME = "text_to_rdf_app"
    USER_ID = "user_001"
    SESSION_ID = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    # Store filenames in initial state
    if output_filename:
        session.state["requested_output_filename"] = output_filename
    
    runner = Runner(
        agent=text_to_rdf_system,
        app_name=APP_NAME,
        session_service=session_service
    )
    
    # Create the user message
    message = f"Process {input_filename}"
    
    content = types.Content(role='user', parts=[types.Part(text=message)])
    
    print(f"Starting text to RDF conversion...")
    print(f"Input file: {input_filename}")
    if output_filename:
        print(f"Output file: {output_filename}")
    print("-" * 50)
    
    # Process the request
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        # Print agent responses as they come
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"\n{event.author}: {part.text}")
    
    print("\n" + "-" * 50)
    print("Conversion complete!")
    
    # Print final state summary
    final_state = session.state
    if "output_filename" in final_state:
        print(f"Output saved to: {final_state['output_filename']}")
    if "rdf_graph" in final_state:
        print(f"Graph preview:\n{final_state['rdf_graph'][:500]}...")

# Example usage
if __name__ == "__main__":
    # Example 1: Convert a text file with auto-generated output filename
    # asyncio.run(convert_text_to_rdf("example.txt"))
    
    # Example 2: Convert with specific output filename
    # asyncio.run(convert_text_to_rdf("example.txt", "my_knowledge_graph.ttl"))
    
    # For demonstration, create a sample text file
    sample_text = """
    Google was founded in 1998 by Larry Page and Sergey Brin while they were Ph.D. students 
    at Stanford University in California. The company's rapid growth since incorporation has 
    triggered a chain of products, acquisitions, and partnerships beyond Google's core search engine.
    Google is now a subsidiary of Alphabet Inc., which was created in 2015 as part of a corporate 
    restructuring. Sundar Pichai became the CEO of Google in 2015.
    """
    
    with open("sample_google.txt", "w") as f:
        f.write(sample_text)
    
    print("Created sample_google.txt for demonstration")
    print("\nTo run the conversion:")
    
    asyncio.run(convert_text_to_rdf('sample_google.txt', 'google_knowledge_graph.ttl'))
