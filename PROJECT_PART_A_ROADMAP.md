# Part A: Social Network Analysis (SNA) — Roadmap & Execution Checklist

**Course:** Introduction to Social Networks (Dr. Reem Essameldin)  
**Project Role:** Part A Owners (Network Analysis & Feature Engineering)  
**Target Delivery:** End of Week 10 (Handoff to Part B)

---

## 1. The Big Picture in 30 Seconds

* **What Part A is:** An exploratory structural audit of a real-world graph. You load the network, compute its global/local mathematical metrics (degrees, paths, clustering, centralities, communities), and generate visual plots.
* **What Part B is:** Your teammates train Machine Learning models twice:
  1. *Before SNA:* Baseline features only.
  2. *After SNA:* Baseline features + **the network metrics that YOU computed in Part A**.
* **Why You Go First:** Part B literally cannot start until you export the **`node_features_for_ml.csv`** table. You are the data provider for the team.

---

## 2. Dataset Selection Guide (Pick ONE within 24 hours)

Coordinate with the Part B team immediately to pick one of these pre-vetted datasets:

| Dataset Name | Domain | Nodes / Edges | Why It’s Great | Recommended Part B Task |
|---|---|---|---|---|
| **SNAP: GitHub Developers** | Tech / Social | ~37K nodes, ~289K edges *(or sub-sample to 5K)* | Real developers, mutual stars/follows, rich attributes | **Node Classification:** Predict ML dev vs. Web dev |
| **Cora / Citeseer** | Academic Citation | ~2.7K nodes, ~5.4K edges | Fast to compute, clean, zero RAM issues | **Node Classification:** Predict paper subject category |
| **SNAP: Twitch Gamers** | Social Media | ~7K nodes, ~35K edges | Clean size, explicit communities and ego networks | **Link Prediction** or **Community Clustering** |

> **Pro-Tip:** Keep the node count between **1,500 and 10,000 nodes**. Large enough to look like real research, but small enough that betweenness centrality computes in seconds.

---

## 3. The Step-by-Step Execution Checklist

### Phase 1: Team Alignment & Data Setup (Day 1)
- [ ] **Lock the Dataset:** Agree with the 8 members of Part B on the dataset (e.g. GitHub Developers or Cora).
- [ ] **Lock the Part B ML Task:** Confirm whether Part B is doing **Node Classification** (predicting a node label) or **Link Prediction** (predicting whether an edge exists).
- [ ] **Download Data:** Download raw `.csv`, `.txt`, or `.edges` into a `data/` folder.
- [ ] **Create GitHub Repo / Shared Drive:** Keep scripts and files version-controlled.

---

### Phase 2: Python Metrics Extraction Pipeline (Days 2–3)
*Build a single Python script (`src/analyze_network.py`) using `networkx` to calculate everything in one run.*

#### A. Graph Topology & Global Measurements (Macro-Level)
- [ ] **Network Dimensions:** Total node count ($N$) and edge count ($E$).
- [ ] **Type Classification:** Directed vs. Undirected, Weighted vs. Unweighted.
- [ ] **Density ($D$):** Calculate network edge saturation ($D = \frac{2E}{N(N-1)}$).
- [ ] **Node Degrees:** Minimum, maximum, and average degree ($\langle k \rangle = \frac{2E}{N}$).
- [ ] **Degree Distribution $P(k)$:** Plot histogram of node degrees (verify power-law / heavy-tail skewness).
- [ ] **Connectivity & Components:**
  - Count connected components (or Weakly / Strongly Connected Components if directed).
  - Report the size and percentage of the **Giant Component**.
- [ ] **Distances & Paths (on Giant Component):**
  - Average Shortest Path Length ($\bar{h}$).
  - Network Diameter ($D_{\max}$) and Radius.
- [ ] **Clustering & Triangles:**
  - Average Clustering Coefficient ($C$).
  - Total triangle count and transitivity.

#### B. Node Centralities (Micro-Level — Who is influential?)
- [ ] Calculate **Degree Centrality** (`nx.degree_centrality`).
- [ ] Calculate **Closeness Centrality** (`nx.closeness_centrality`).
- [ ] Calculate **Betweenness Centrality** (`nx.betweenness_centrality`).
- [ ] Calculate **PageRank** or **Eigenvector Centrality** (`nx.pagerank`).
- [ ] Build a **Top-10 Nodes Summary Table** comparing which nodes dominate each centrality.

#### C. Community Detection (Meso-Level — Natural clusters)
- [ ] Run the **Louvain Algorithm** (`nx.community.louvain_communities`).
- [ ] Calculate the **Modularity Score ($Q$)** (`nx.community.modularity`).
- [ ] Record the number of detected communities and the size of the top 3 largest clusters.

---

### Phase 3: The Part B Feature Export Contract (Day 3)
*This is the bridge between Part A and Part B.*

- [ ] Combine all node-level metrics into a single Pandas DataFrame:
  * Columns: `node_id`, `degree`, `degree_centrality`, `betweenness`, `closeness`, `pagerank`, `clustering_coeff`, `community_id`.
- [ ] If Part B is doing **Link Prediction**, also compute pairwise features for edge pairs:
  * Common Neighbors count, Jaccard Coefficient, Adamic-Adar Index, Preferential Attachment score.
- [ ] Export and send **`node_features_for_ml.csv`** to the Part B group.

---

### Phase 4: Visualizations in Cytoscape & Python (Days 4–5)
- [ ] **Plot 1: Degree Distribution Histogram:** Plot $P(k)$ vs $k$ (using Matplotlib / Seaborn).
- [ ] **Plot 2: Complete Network Visualization:**
  * Import graph into **Cytoscape** (or Gephi).
  * Apply a Force-Directed layout (ForceAtlas2 or Prefuse layout).
- [ ] **Plot 3: Community Structure Visualization:**
  * In Cytoscape, color nodes according to their **`community_id`**.
- [ ] **Plot 4: Centrality Highlights:**
  * Scale node size proportionally to **Betweenness** or **Degree** to visually showcase network hubs.
- [ ] Export high-resolution PNGs (300 DPI) for the report.

---

### Phase 5: Writing the Part A Report Section (Days 6–7)
- [ ] **Dataset Description:** Explain domain, nodes meaning, edges meaning, source link.
- [ ] **Graph Statistics Table:** Clean summary table displaying $N, E, \langle k \rangle, D, \bar{h}, \text{Diameter}, C, Q$.
- [ ] **Plot Descriptions:** 2–3 sentences under every figure explaining what the viewer is seeing.
- [ ] **Centrality Interpretation:** Brief discussion on why certain nodes have high betweenness vs. high degree.
- [ ] **Code & Tool Screenshots:** Screenshots of Cytoscape and documented Python code.

---

## 4. Division of Labor (You vs. Your Friend)

| Task | Lead | Co-Lead |
|---|---|---|
| Dataset Selection & Team Coordination | You & Friend | Shared |
| Python Pipeline (`networkx` metrics & export) | **You** | Review |
| Top-10 Centrality Table & Statistics Analysis | **You** | Friend |
| Cytoscape Network Visualizations (Plots 2, 3, 4) | **Your Friend** | You |
| Degree Distribution Plot (Plot 1) | **Your Friend** | You |
| Writing Part A Draft for Final PDF Report | **Your Friend** | You (Tech review) |

---

## 5. Timeline & Milestones

```
Week 9 (Now):
  ├── Day 1: Lock dataset with the 10-person team.
  ├── Days 2–3: Python pipeline generates all stats & exports CSV.
  ├── Days 4–5: Cytoscape visual plots generated.
  └── Days 6–7: Part A section written & handed off to Part B.

Week 10:
  └── Part B builds ML models (Before vs. After SNA) using YOUR feature CSV.

Week 11:
  └── Assemble the complete 10-person PDF report & rehearse presentation.

Week 12+:
  └── Project Discussion / Defense (starts Saturday 5/12).
```

---

## 6. Minimal Python Starter Blueprint

You can run this skeleton to compute 80% of Part A in under 30 lines:

```python
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

# 1. Load Graph
G = nx.read_edgelist("data/edges.csv", delimiter=",", create_using=nx.Graph())
print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

# 2. Global Metrics
giant = G.subgraph(max(nx.connected_components(G), key=len))
density = nx.density(G)
avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
avg_clustering = nx.average_clustering(G)
diameter = nx.diameter(giant)
avg_path_len = nx.average_shortest_path_length(giant)

# 3. Node Centralities
deg_cent = nx.degree_centrality(G)
bet_cent = nx.betweenness_centrality(G)
close_cent = nx.closeness_centrality(G)
pagerank = nx.pagerank(G)

# 4. Communities & Modularity
communities = nx.community.louvain_communities(G)
modularity = nx.community.modularity(G, communities)

node_community = {}
for comm_id, comm_nodes in enumerate(communities):
    for node in comm_nodes:
        node_community[node] = comm_id

# 5. Export Features for Part B
df = pd.DataFrame({
    "node_id": list(G.nodes()),
    "degree": [G.degree(n) for n in G.nodes()],
    "degree_centrality": [deg_cent[n] for n in G.nodes()],
    "betweenness": [bet_cent[n] for n in G.nodes()],
    "closeness": [close_cent[n] for n in G.nodes()],
    "pagerank": [pagerank[n] for n in G.nodes()],
    "clustering_coeff": [nx.clustering(G, n) for n in G.nodes()],
    "community_id": [node_community.get(n, -1) for n in G.nodes()]
})
df.to_csv("output/node_features_for_ml.csv", index=False)
print("Part A feature export complete!")
```
