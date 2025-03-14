import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List, Any, Tuple
from knowledge_graph import KnowledgeGraph

def create_graph_visualization(kg: KnowledgeGraph, highlight_entities: List[str] = None) -> str:
    """Create a visualization of the knowledge graph and return as base64 encoded image"""
    # Create a NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes (entities)
    for entity in kg.entities:
        G.add_node(entity.id, label=entity.name, type=entity.type)
    
    # Add edges (relationships)
    for rel in kg.relationships:
        G.add_edge(rel.source, rel.target, label=rel.type)
    
    # Create node colors based on entity type
    entity_types = set(entity.type for entity in kg.entities)
    color_map = {}
    colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899']
    
    for i, entity_type in enumerate(entity_types):
        color_map[entity_type] = colors[i % len(colors)]
    
    node_colors = [color_map[G.nodes[node]['type']] for node in G.nodes]
    
    # Highlight specific entities if provided
    if highlight_entities:
        for i, node in enumerate(G.nodes):
            if node in highlight_entities:
                node_colors[i] = '#ff0000'  # Highlight in red
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)  # Positions for all nodes
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=700, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, arrows=True)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, labels={node: G.nodes[node]['label'] for node in G.nodes}, font_size=8)
    
    # Draw edge labels
    edge_labels = {(u, v): G.edges[u, v]['label'] for u, v in G.edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
    
    # Add a legend for entity types
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                 label=entity_type,
                                 markerfacecolor=color_map[entity_type], markersize=10)
                      for entity_type in color_map]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.axis('off')  # Turn off axis
    plt.tight_layout()
    
    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    
    # Encode the image as base64
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_str}"

def create_entity_network(kg: KnowledgeGraph, entity_id: str, depth: int = 1) -> str:
    """Create a visualization of the network around a specific entity"""
    # Create a NetworkX graph
    G = nx.DiGraph()
    
    # Get the central entity
    central_entity = kg.get_entity(entity_id)
    if not central_entity:
        return None
    
    # Add the central entity
    G.add_node(central_entity.id, label=central_entity.name, type=central_entity.type)
    
    # Add connected entities up to the specified depth
    entities_to_process = [(central_entity.id, 0)]  # (entity_id, current_depth)
    processed_entities = set([central_entity.id])
    
    while entities_to_process:
        current_id, current_depth = entities_to_process.pop(0)
        
        if current_depth >= depth:
            continue
        
        # Get relationships for this entity
        relationships = kg.get_relationships_for_entity(current_id)
        
        for rel in relationships:
            # Add the relationship
            G.add_edge(rel.source, rel.target, label=rel.type)
            
            # Process the other entity in the relationship
            other_id = rel.target if rel.source == current_id else rel.source
            
            if other_id not in processed_entities:
                other_entity = kg.get_entity(other_id)
                if other_entity:
                    G.add_node(other_id, label=other_entity.name, type=other_entity.type)
                    processed_entities.add(other_id)
                    
                    if current_depth + 1 < depth:
                        entities_to_process.append((other_id, current_depth + 1))
    
    # Create node colors based on entity type
    entity_types = set(G.nodes[node]['type'] for node in G.nodes)
    color_map = {}
    colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899']
    
    for i, entity_type in enumerate(entity_types):
        color_map[entity_type] = colors[i % len(colors)]
    
    node_colors = [color_map[G.nodes[node]['type']] for node in G.nodes]
    
    # Highlight the central entity
    for i, node in enumerate(G.nodes):
        if node == central_entity.id:
            node_colors[i] = '#ff0000'  # Highlight in red
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)  # Positions for all nodes
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=700, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, arrows=True)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, labels={node: G.nodes[node]['label'] for node in G.nodes}, font_size=8)
    
    # Draw edge labels
    edge_labels = {(u, v): G.edges[u, v]['label'] for u, v in G.edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
    
    plt.axis('off')  # Turn off axis
    plt.tight_layout()
    
    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    
    # Encode the image as base64
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_str}"

