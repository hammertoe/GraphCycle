from rdflib import Graph, URIRef, Literal
import networkx as nx
from pyvis.network import Network
from collections import defaultdict

def get_label(node):
    """Extract readable labels from URIs and literals"""
    if isinstance(node, URIRef):
        return str(node).split('#')[-1].split('/')[-1].replace('_', ' ')
    elif isinstance(node, Literal):
        return str(node)
    else:
        return str(node)

def get_node_color(degree):
    """Assign colors based on node connections"""
    if degree > 10:
        return '#ff6b6b'  # Red for highly connected nodes
    elif degree > 5:
        return '#4ecdc4'  # Teal for moderately connected
    elif degree > 2:
        return '#45b7d1'  # Blue for somewhat connected
    else:
        return '#96ceb4'  # Green for less connected

print("Loading RDF data...")
g = Graph()

# Check if file exists first
import os
file_path = "ancient_greece.ttl" 
print(f"Checking if file exists: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

if not os.path.exists(file_path):
    print("\nFile not found! Trying alternative paths...")
    # Try some common alternative locations
    alternative_paths = [
        "./ancient_greece.ttl",
        "ancient_greece.ttl",
    ]
    
    found_file = None
    for alt_path in alternative_paths:
        if os.path.exists(alt_path):
            found_file = alt_path
            print(f"Found file at: {alt_path}")
            break
    
    if found_file:
        file_path = found_file
    else:
        print("Could not find ancient_greece.ttl in any common locations.")
        print("Please check your file path or place the file in the same directory as this script.")
        exit(1)

try:
    g.parse(file_path, format="turtle")
    print(f"Successfully loaded {len(g)} triples from {file_path}")
except Exception as e:
    print(f"Error loading RDF file: {e}")
    print(f"File path attempted: {file_path}")
    exit(1)

print("Building NetworkX graph...")
G = nx.DiGraph()

# Build the graph
for s, p, o in g:
    subject_label = get_label(s)
    predicate_label = get_label(p)
    object_label = get_label(o)
    
    G.add_edge(subject_label, object_label, label=predicate_label)

print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

print("Creating interactive visualization...")
net = Network(height="800px", width="100%", directed=True)

# Set physics options for better layout
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

# Add nodes with styling
for node in G.nodes():
    degree = G.degree(node)
    size = max(10, min(30, degree * 3))  # Size based on connections
    color = get_node_color(degree)
    
    # Create simple hover info
    hover_info = f"{node}\\nConnections: {degree}"
    
    net.add_node(node, 
                 label=node,
                 size=size,
                 color=color,
                 title=hover_info)

# Add edges
for src, dst, data in G.edges(data=True):
    net.add_edge(src, dst, 
                 label=data['label'],
                 title=f"{data['label']}: {src} → {dst}")

# Save the file
output_file = "interactive_knowledge_graph.html"
print(f"Attempting to save HTML file as: {output_file}")

try:
    net.show(output_file)
    print(f"HTML file generation completed")
    
    # Check if file was actually created
    import os
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"Success! File created: {output_file} (Size: {file_size} bytes)")
    else:
        print(f"Warning: HTML file was not created at {output_file}")
        
except Exception as e:
    print(f"Error creating HTML file: {e}")
    print("Trying alternative method...")
    
    # Try using write_html instead
    try:
        net.write_html(output_file)
        print(f"Success with alternative method! File saved as: {output_file}")
    except Exception as e2:
        print(f"Alternative method also failed: {e2}")
        print("Saving to current directory...")
        net.save_graph("kg_output.html")
        print("Saved as: kg_output.html")

print(f"Success! Interactive knowledge graph saved as: {output_file}")
print("\nNode colors indicate connection levels:")
print("🔴 Red: Highly connected (>10 connections)")
print("🔵 Teal: Moderately connected (6-10 connections)")  
print("🔵 Blue: Somewhat connected (3-5 connections)")
print("🟢 Green: Less connected (≤2 connections)")
print("\nOpen the HTML file in your browser to explore!")