from graphviz import Digraph
import sys

def parse_blockchain_file(file_path):
    """Parse the blockchain data file into a dictionary"""
    blocks = {}
    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]
        for line in lines:
            if line.strip():
                block_id, parent_id, creator_id, time = map(str.strip, line.split(','))
                blocks[block_id] = {
                    'parent': parent_id if parent_id != 'None' else None,
                    'creator': creator_id,
                    'time': time
                }
    return blocks

def visualize_blockchain(blocks, output_file='blockchain_tree'):
    """Create and render blockchain visualization"""
    dot = Digraph(comment='Blockchain Structure', format='png')
    dot.attr(rankdir='TB', ordering='out')  # Top to Bottom layout
    
    # Create nodes with timestamp labels
    for block_id, data in blocks.items():
        dot.node(
            block_id,
            label=f"{block_id}: {data['creator']}\nArrival: {data['time']}",
            shape='circle',
            style='filled',
            fillcolor='lightblue'
        )
    
    # Create parent-child relationships
    for block_id, data in blocks.items():
        if data['parent'] and data['parent'] in blocks:
            dot.edge(data['parent'], block_id)
    
    # Render and save
    dot.render(output_file, cleanup=True)
    print(f"Visualization saved as {output_file}.png")

if __name__ == "__main__":
    # Input and output configuration
    input_file = sys.argv[1]
    output_file = sys.argv[1].split('.')[0]

    # Process and visualize
    blockchain_data = parse_blockchain_file(input_file)
    visualize_blockchain(blockchain_data, output_file)