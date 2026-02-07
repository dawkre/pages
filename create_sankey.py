#!/usr/bin/env python3
"""
Create a Sankey diagram from budget.json data
"""
import json
import plotly.graph_objects as go

# Read the budget data
with open('budget.json', 'r') as f:
    data = json.load(f)

# Create mappings
node_ids = [node['id'] for node in data['nodes']]
node_labels = [node['name'] for node in data['nodes']]
node_id_to_index = {node_id: idx for idx, node_id in enumerate(node_ids)}

# Build all links first to identify leaf nodes
all_sources = []
all_targets = []
all_values = []

for link in data['links']:
    source_id = link['source']
    target_id = link['target']
    value = link['value']

    if source_id not in node_id_to_index or target_id not in node_id_to_index:
        print(f"Warning: Skipping link {source_id} -> {target_id} (missing node)")
        continue

    source_idx = node_id_to_index[source_id]
    target_idx = node_id_to_index[target_id]

    all_sources.append(source_idx)
    all_targets.append(target_idx)
    all_values.append(value)

# Identify leaf nodes (leftmost sources and rightmost sinks)
has_incoming = set(all_targets)
has_outgoing = set(all_sources)

# Leftmost nodes: have outgoing but no incoming
leftmost_nodes = set(range(len(node_ids))) - has_incoming
# Rightmost nodes: have incoming but no outgoing
rightmost_nodes = set(range(len(node_ids))) - has_outgoing

# Nodes to hide (leaf nodes on both ends)
hidden_nodes = leftmost_nodes | rightmost_nodes

print(f"Removing {len(hidden_nodes)} leaf nodes from diagram:")
print(f"  Leftmost (sources): {len(leftmost_nodes)} nodes")
print(f"  Rightmost (sinks): {len(rightmost_nodes)} nodes")

# Create new node list without hidden nodes
visible_node_ids = []
visible_node_labels = []
old_to_new_index = {}
new_index = 0

for i, (node_id, label) in enumerate(zip(node_ids, node_labels)):
    if i not in hidden_nodes:
        visible_node_ids.append(node_id)
        visible_node_labels.append(label)
        old_to_new_index[i] = new_index
        new_index += 1

# Filter links to only include those between visible nodes
sources = []
targets = []
values = []

for source_idx, target_idx, value in zip(all_sources, all_targets, all_values):
    # Only keep links where both source and target are visible
    if source_idx not in hidden_nodes and target_idx not in hidden_nodes:
        sources.append(old_to_new_index[source_idx])
        targets.append(old_to_new_index[target_idx])
        values.append(value)

# Create custom hover text for links
hover_labels = []
for source_idx, target_idx, value in zip(sources, targets, values):
    source_name = visible_node_labels[source_idx]
    target_name = visible_node_labels[target_idx]
    hover_text = f"Z: {source_name}<br>Do: {target_name}<br>Kwota: {value:,.2f} zł"
    hover_labels.append(hover_text)

# Create custom hover text for visible nodes (including hidden node details)
node_hover_labels = []
for node_idx in range(len(visible_node_ids)):
    node_name = visible_node_labels[node_idx]

    # Find the original node index
    original_idx = None
    for orig_idx, new_idx in old_to_new_index.items():
        if new_idx == node_idx:
            original_idx = orig_idx
            break

    # Find all incoming flows (including from hidden nodes)
    incoming = []
    total_incoming = 0
    for i, target_idx in enumerate(all_targets):
        if target_idx == original_idx:
            source_name = node_labels[all_sources[i]]
            value = all_values[i]
            incoming.append(f"  • {source_name}: {value:,.2f} zł")
            total_incoming += value

    # Find all outgoing flows (including to hidden nodes)
    outgoing = []
    total_outgoing = 0
    for i, source_idx in enumerate(all_sources):
        if source_idx == original_idx:
            target_name = node_labels[all_targets[i]]
            value = all_values[i]
            outgoing.append(f"  • {target_name}: {value:,.2f} zł")
            total_outgoing += value

    # Use the larger of incoming or outgoing as the total
    total = max(total_incoming, total_outgoing)

    # Build hover text
    hover_parts = [f"<b>{node_name}: {total:,.2f} zł</b>"]
    if incoming:
        hover_parts.append("<br><br>Wpływy:")
        hover_parts.extend([f"<br>{line}" for line in incoming])
    if outgoing:
        hover_parts.append("<br><br>Wypływy:")
        hover_parts.extend([f"<br>{line}" for line in outgoing])

    node_hover_labels.append("".join(hover_parts))

# Create the Sankey diagram
base_colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
    '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',
    '#5254a3', '#8ca252', '#bd9e39', '#ad494a', '#a55194',
    '#6b6ecf', '#b5cf6b', '#e7ba52', '#d6616b', '#ce6dbd',
    '#9c9ede', '#cedb9c', '#e7cb94', '#e7969c', '#de9ed6',
    '#3182bd', '#e6550d', '#31a354', '#756bb1', '#636363'
]

fig = go.Figure(data=[go.Sankey(
    arrangement='snap',
    node=dict(
        pad=50,  # More space between nodes
        thickness=20,  # Thicker nodes for easier hovering
        line=dict(color="black", width=0.5),
        label=visible_node_labels,
        color=[base_colors[i % len(base_colors)] for i in range(len(visible_node_labels))],
        customdata=node_hover_labels,
        hovertemplate='%{customdata}<extra></extra>'
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color='rgba(0,0,0,0.2)',
        customdata=hover_labels,
        hovertemplate='%{customdata}<extra></extra>'
    )
)])

fig.update_layout(
    title={
        'text': "Budget Flow Diagram",
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 24}
    },
    font=dict(size=10),
    height=800,
    width=1400
)

# Save as HTML
output_file = 'budget_sankey.html'
fig.write_html(output_file)
print(f"Sankey diagram saved to {output_file}")
print("Open this file in your web browser to view the interactive diagram.")
