import os
import datetime
from typing import Dict, Optional
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import asyncio

# Import visualisation libraries
from rdflib import Graph, URIRef, Literal
import networkx as nx
from pyvis.network import Network

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
        
        # Use the requested filename if provided
        requested_filename = tool_context.state.get("requested_output_filename")
        if requested_filename:
            filename = requested_filename

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

# Tool for visualising RDF graph
def visualize_rdf_graph(tool_context: ToolContext) -> dict:
    """Visualizes the RDF graph stored in session state using NetworkX and Pyvis."""

    try:
        rdf_content = tool_context.state.get("rdf_graph", None)
        if not rdf_content:
            return {"status": "error", "error_message": "No RDF graph found in state"}
        
        # Helper functions
        def get_label(node):
            if isinstance(node, URIRef):
                return str(node).split('#')[-1].split('/')[-1].replace('_', ' ')
            elif isinstance(node, Literal):
                return str(node)
            else:
                return str(node)

        def get_node_color(degree):
            if degree > 10:
                return '#ff6b6b'  # Red for highly connected nodes
            elif degree > 5:
                return "#fceb02"  # Yellow for moderately connected
            elif degree > 2:
                return '#45b7d1'  # Blue for somewhat connected
            else:
                return '#96ceb4'  # Green for less connected 

        print("Loading RDF data...")
        g = Graph()

        # debug attempt
        try:
            g.parse(data=rdf_content, format="turtle")
            print(f"Successfully loaded {len(g)} triples")
        except Exception as parse_error:
            print(f"Parse error: {parse_error}")
            return {"status": "error", "error_message": f"Failed to parse RDF: {parse_error}"}
            
        if len(g) == 0:
            return {"status": "error", "error_message": "No triples found in RDF graph"}
            
        
        print("Building NetworkX graph...")
        G = nx.DiGraph()

        # Build the graph
        for s, p, o in g:
            subject_label = get_label(s)
            predicate_label = get_label(p)
            object_label = get_label(o)
            G.add_edge(subject_label, object_label, label=predicate_label)

        print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
      #debug attempt

        if G.number_of_nodes() == 0:
            return {"status": "error", "error_message": "No nodes created from RDF graph"}


        print("Creating interactive visualization...")
        net = Network(height="800px", width="100%", directed=True)

        net.set_options("""
        var options = {
             "physics": {
             "enabled": true,
             "barnesHut": {
             "gravitationalConstant": -8000,
             "centralGravity": 0.3,
             "springLength": 95,
             "springConstant": 0.04,
             "damping": 0.09
             }
        }
        }
        """)

        # Add nodes
        for node in G.nodes():
            degree = G.degree(node)
            size = max(10, min(30, degree * 3))
            color = get_node_color(degree)
            hover_info = f"{node}\\nConnections: {degree}"

            net.add_node(node, label=node, size=size, color=color, title=hover_info)

        # Add edges
        for src, dst, data in G.edges(data=True):
            net.add_edge(src, dst, label=data['label'],
                         title=f"{data['label']}: {src} → {dst}")

        # Generate filename
        source_filename = tool_context.state.get("source_filename", "knowledge_graph")
        base_name = os.path.splitext(os.path.basename(source_filename))[0]
        output_file = f"interactive_{base_name}_graph.html"

        # Save the file 
        net.show(output_file)

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            tool_context.state["visualization_filename"] = output_file
            print(f"Successfully created HTML file: {output_file} ({file_size} bytes)")
            return {
                "status": "success",
                "message": f"Interactive visualization saved as: {output_file}",
                "filename": output_file,
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "file_size": file_size
            }
        else:
            return {"status": "error", "error_message": f"HTML file was not created {output_file}"}

    except Exception as e:
        print(f"Visualization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error_message": f"Failed to create visualization: {str(e)}"}



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

     IMPORTANT: You MUST call the load_from_file tool. Extract the filename from the user's message.
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
    
     CRITICAL: You MUST call the store_rdf_graph tool with your complete RDF graph as a string.
    Do not just describe what you would do - actually call the tool!
    
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
    1. MUST call the save_to_file tool to save the RDF graph from state["rdf_graph"]
    2. Use the requested filename from state if available, or generate a default name
    3. Verify the save was successful
    4. Provide a summary of what was saved
    
    CRITICAL: You MUST actually call the save_to_file tool. Do not just describe what you would do!
    
    For the filename parameter, use a simple name like the base filename with .ttl extension.
    """,
    tools=[save_to_file],
    output_key="archive_summary"
)

#Agent 4: RDF Visualizer
visualization_agent = Agent(
    name="visualizer",
    model="gemini-2.0-flash",
    description="Creates interactive HTML visualization from RDF graph.",
    instruction="""
    You are responsible for creating an interactive HTML visualization of the RDF graph.
    
    Your task:
    1. MUST call the visualize_rdf_graph tool (it takes no parameters)
    2. The tool will read the RDF graph from state["rdf_graph"] automatically
    3. Verify the HTML file was created successfully
    4. Report the visualization details
    
    CRITICAL: You MUST actually call the visualize_rdf_graph tool. Do not just describe what you would do!
    The tool handles everything automatically - just call it.
    """,
    tools=[visualize_rdf_graph],
    output_key="visualization_summary"
)

# Create the sequential multi-agent system
text_to_rdf_system = SequentialAgent(
    name="text_to_rdf_knowledge_graph_system",
    sub_agents=[
        text_loader_agent,
        knowledge_graph_converter,
        rdf_archiver_agent,
        visualization_agent
    ]
)

# Define required constants for session creation
APP_NAME = "TextToRDFApp"
USER_ID = "default_user"
SESSION_ID = "default_session"

# Helper function to run the system (changed the functio to match the new system)
async def convert_and_visualize(input_filename: str, output_ttl: Optional[str] = None):
    """Convert text to RDF and create visualization."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    
    )
    
    # Store filenames in initial state
    if output_ttl:
        session.state["requested_output_filename"] = output_ttl
    
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
    if output_ttl:
        print(f"Output file: {output_ttl}")
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
    print("\nFinal State Summary:")
    print(f"- Loaded text: {'Yes' if 'loaded_text' in final_state else 'No'}")
    print(f"- RDF graph stored: {'Yes' if 'rdf_graph' in final_state else 'No'}")
    
    if "output_filename" in final_state:
        ttl_file = final_state['output_filename']
        print(f"- TTL file saved: {ttl_file}")
        if os.path.exists(ttl_file):
            print(f"  ✓ File exists ({os.path.getsize(ttl_file)} bytes)")
        else:
            print(f"  ✗ File not found!")
    else:
        print("- TTL file saved: No")
        
    if "visualization_filename" in final_state:
        html_file = final_state['visualization_filename']
        print(f"- HTML visualization: {html_file}")
        if os.path.exists(html_file):
            print(f"  ✓ File exists ({os.path.getsize(html_file)} bytes)")
            print(f"  → Open {html_file} in your browser to view the interactive graph!")
        else:
            print(f"  ✗ File not found!")
    else:
        print("- HTML visualization: No")
    
    # Debug: Show what's in the state
    print(f"\nState keys: {list(final_state.keys())}")

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
    
    asyncio.run(convert_and_visualize('sample_google.txt', 'google_knowledge_graph.ttl'))
