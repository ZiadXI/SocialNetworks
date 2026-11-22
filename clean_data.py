import pandas as pd

print("1. Loading protein names and annotations dictionary...")
# Load protein info (uncompressed .txt file)
info_path = "d:/SocialNetworks/data/9606.protein.info.v12.0.txt"
info_df = pd.read_csv(info_path, sep="\t")

# Create lookup dictionary: ENSP ID -> Human Gene Symbol (e.g. TP53)
id_to_name = dict(zip(info_df["#string_protein_id"], info_df["preferred_name"]))
id_to_desc = dict(zip(info_df["#string_protein_id"], info_df["annotation"]))
id_to_size = dict(zip(info_df["#string_protein_id"], info_df["protein_size"]))
print(f"   Loaded {len(id_to_name)} protein definitions.")

print("2. Loading physical interactions...")
links_path = "d:/SocialNetworks/data/9606.protein.physical.links.v12.5.txt"
links_df = pd.read_csv(links_path, sep=" ")

# Filter for Highest Confidence physical binding (Score >= 900 / 1000)
# (In STRING, score >= 900 is the gold-standard 'Highest Confidence' tier)
print("3. Filtering for Highest Confidence physical interactions (Score >= 900)...")
filtered_df = links_df[links_df["combined_score"] >= 900].copy()

# Map to real gene names
filtered_df["source"] = filtered_df["protein1"].map(id_to_name)
filtered_df["target"] = filtered_df["protein2"].map(id_to_name)

# Drop any unmapped proteins or self-loops
clean_edges = filtered_df.dropna(subset=["source", "target"]).copy()
clean_edges = clean_edges[clean_edges["source"] != clean_edges["target"]]

# Keep unique undirected edges (avoid duplicates where (A, B) and (B, A) are both listed)
clean_edges["u"] = clean_edges[["source", "target"]].min(axis=1)
clean_edges["v"] = clean_edges[["source", "target"]].max(axis=1)
final_edges = clean_edges.drop_duplicates(subset=["u", "v"])[["u", "v", "combined_score"]]
final_edges.columns = ["source", "target", "confidence_score"]

# Save Clean Edges CSV for Cytoscape and NetworkX
edges_out = "d:/SocialNetworks/data/clean_human_ppi.csv"
final_edges.to_csv(edges_out, index=False)

# Collect all unique proteins present in the network
network_proteins = set(final_edges["source"]).union(set(final_edges["target"]))

# Save Node Metadata CSV
node_meta = []
for p_id, name in id_to_name.items():
    if name in network_proteins:
        node_meta.append({
            "gene_name": name,
            "string_id": p_id,
            "protein_size": id_to_size.get(p_id, 0),
            "description": id_to_desc.get(p_id, "")
        })

nodes_df = pd.DataFrame(node_meta).drop_duplicates(subset=["gene_name"])
nodes_out = "d:/SocialNetworks/data/clean_protein_metadata.csv"
nodes_df.to_csv(nodes_out, index=False)

print("\n" + "="*50)
print("SUCCESS!")
print(f"Network has: {len(nodes_df)} proteins (nodes) and {len(final_edges)} physical interactions (edges)")
print(f"Saved clean edges to: {edges_out}")
print(f"Saved node metadata to: {nodes_out}")
print("="*50)
