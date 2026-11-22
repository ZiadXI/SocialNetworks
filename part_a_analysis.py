"""Part A: Comprehensive Social Network Analysis (SNA) Pipeline
Dataset: Human Physical Protein-Protein Interaction Network (STRING v12.5, Score >= 900)
Outputs:
  - output/node_features_for_ml.csv        (Feature table for Cytoscape & Part B ML)
  - output/part_a_summary_report.txt       (All Part A macro/micro/meso metrics & tables)
  - output/top10_hubs_adjacency_matrix.csv (10x10 adjacency submatrix of top hubs)
  - output/top300_core_ppi_cytoscape.csv   (Clean core subgraph for crisp Cytoscape visuals)
  - figures/fig1_degree_distribution.png   (Linear + Log-Log Power-Law fit)
  - figures/fig2_top_centralities.png      (Top 10 proteins across 4 centralities)
  - figures/fig3_community_sizes.png       (Top 15 Louvain communities & Modularity Q)
  - figures/fig4_adjacency_heatmap.png     (Adjacency matrix heatmap of top 15 hubs)
"""

from __future__ import annotations

import logging
import math
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Workspace paths
BASE_DIR = Path("d:/SocialNetworks")
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
FIGURES_DIR = BASE_DIR / "figures"

EDGES_PATH = DATA_DIR / "clean_human_ppi.csv"
META_PATH = DATA_DIR / "clean_protein_metadata.csv"


def load_graph(edges_path: Path) -> Tuple[nx.Graph, pd.DataFrame]:
    """Load clean undirected human PPI graph from CSV."""
    logger.info("Loading edges from %s...", edges_path)
    edges_df = pd.read_csv(edges_path)
    G = nx.Graph()
    for row in edges_df.itertuples(index=False):
        G.add_edge(str(row.source), str(row.target), weight=float(row.confidence_score))
    logger.info("Loaded graph: N=%d nodes, E=%d edges", G.number_of_nodes(), G.number_of_edges())
    return G, edges_df


def compute_exact_distances_and_closeness(
    G: nx.Graph,
    node_list: List[str],
    giant_nodes: Set[str],
    chunk_size: int = 500,
) -> Tuple[int, float, Dict[str, float]]:
    """Compute exact Giant Component diameter, average shortest path length,
    and Wasserman-Faust normalized closeness centrality for all nodes using
    chunked C-level BFS (scipy.sparse.csgraph.shortest_path).
    """
    logger.info("Computing exact shortest paths & closeness via chunked SciPy BFS...")
    t0 = time.time()
    n_total = len(node_list)
    node_to_idx = {node: idx for idx, node in enumerate(node_list)}
    giant_mask = np.array([node in giant_nodes for node in node_list], dtype=bool)
    n_giant = int(giant_mask.sum())

    # Unweighted sparse adjacency matrix (CSR)
    adj: csr_matrix = nx.to_scipy_sparse_array(G, nodelist=node_list, weight=None, format="csr")

    max_dist_giant = 0
    sum_dist_giant = 0.0
    closeness_dict: Dict[str, float] = {}

    for start in range(0, n_total, chunk_size):
        end = min(start + chunk_size, n_total)
        indices = np.arange(start, end)
        # C-level unweighted BFS from each node in chunk
        dist_matrix = shortest_path(adj, directed=False, unweighted=True, indices=indices)

        for local_i, global_i in enumerate(indices):
            dists = dist_matrix[local_i]
            finite_mask = np.isfinite(dists) & (dists > 0)
            reachable_count = int(finite_mask.sum())

            # Wasserman-Faust improved closeness centrality (matches nx.closeness_centrality)
            if reachable_count > 0 and n_total > 1:
                sum_d = float(dists[finite_mask].sum())
                wf_closeness = (reachable_count / sum_d) * (reachable_count / (n_total - 1))
            else:
                wf_closeness = 0.0
            closeness_dict[node_list[global_i]] = wf_closeness

            # Accumulate Giant Component distance stats
            if giant_mask[global_i]:
                gc_dists = dists[giant_mask]
                gc_finite = gc_dists[np.isfinite(gc_dists)]
                if gc_finite.size > 0:
                    local_max = int(gc_finite.max())
                    if local_max > max_dist_giant:
                        max_dist_giant = local_max
                    sum_dist_giant += float(gc_finite.sum())

    avg_path_len_giant = sum_dist_giant / (n_giant * (n_giant - 1))
    logger.info(
        "Exact BFS done in %.1fs | Giant Diameter=%d | Giant Avg Path Length=%.4f",
        time.time() - t0,
        max_dist_giant,
        avg_path_len_giant,
    )
    return max_dist_giant, avg_path_len_giant, closeness_dict


def fit_power_law_tail(degrees: np.ndarray, k_min: int = 5) -> Tuple[float, float]:
    """Fit linear regression to log10(P(k)) vs log10(k) for k >= k_min."""
    unique_k, counts = np.unique(degrees, return_counts=True)
    probs = counts / degrees.size
    mask = (unique_k >= k_min) & (probs > 0)
    log_k = np.log10(unique_k[mask])
    log_p = np.log10(probs[mask])
    slope, intercept = np.polyfit(log_k, log_p, 1)
    y_pred = slope * log_k + intercept
    ss_res = float(np.sum((log_p - y_pred) ** 2))
    ss_tot = float(np.sum((log_p - np.mean(log_p)) ** 2))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    gamma = -float(slope)
    return gamma, r2


def plot_degree_distribution(degrees: np.ndarray, gamma: float, r2: float, out_path: Path) -> None:
    """Plot Linear and Log-Log degree distributions side by side."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

    # Panel 1: Linear histogram (capped at 99th percentile for readability)
    p99 = int(np.percentile(degrees, 99))
    axes[0].hist(degrees[degrees <= p99], bins=40, color="#2B6CB0", edgecolor="white", alpha=0.88)
    axes[0].axvline(np.mean(degrees), color="#E53E3E", linestyle="--", linewidth=1.8, label=f"Mean = {np.mean(degrees):.2f}")
    axes[0].axvline(np.median(degrees), color="#38A169", linestyle=":", linewidth=1.8, label=f"Median = {np.median(degrees):.1f}")
    axes[0].set_title("Degree Distribution P(k) — Linear Scale (up to 99th pct)", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Node Degree (k)")
    axes[0].set_ylabel("Number of Proteins")
    axes[0].legend()

    # Panel 2: Log-Log Scale-Free check
    unique_k, counts = np.unique(degrees, return_counts=True)
    probs = counts / degrees.size
    axes[1].scatter(unique_k, probs, s=18, color="#2B6CB0", alpha=0.75, label="Observed P(k)")

    # Overlay fitted line for k >= 5
    k_fit = unique_k[unique_k >= 5]
    mask = unique_k >= 5
    slope, intercept = np.polyfit(np.log10(unique_k[mask]), np.log10(probs[mask]), 1)
    p_fit = 10 ** (slope * np.log10(k_fit) + intercept)
    axes[1].plot(k_fit, p_fit, color="#E53E3E", linewidth=2.0, linestyle="--", label=f"Power-Law Fit: gamma = {gamma:.2f} (R² = {r2:.2f})")

    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_title("Degree Distribution — Log-Log Scale (Scale-Free Verification)", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Degree k (log scale)")
    axes[1].set_ylabel("Probability P(k) (log scale)")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved %s", out_path)


def plot_top_centralities(features_df: pd.DataFrame, out_path: Path) -> None:
    """Create a 2x2 figure showing Top 10 proteins for each of the 4 centralities."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), dpi=300)

    metrics = [
        ("degree", "Top 10 Proteins by Degree (Hubs)", "#2B6CB0"),
        ("betweenness", "Top 10 Proteins by Betweenness (Bridges)", "#DD6B20"),
        ("closeness", "Top 10 Proteins by Closeness (Fastest Spreaders)", "#38A169"),
        ("pagerank", "Top 10 Proteins by PageRank (Influence)", "#805AD5"),
    ]

    for ax, (col, title, color) in zip(axes.flat, metrics):
        top10 = features_df.nlargest(10, col).sort_values(col, ascending=True)
        ax.barh(top10["gene_name"], top10[col], color=color, alpha=0.88)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel(col.replace("_", " ").title())
        for i, v in enumerate(top10[col]):
            fmt = f"{int(v)}" if col == "degree" else f"{v:.4f}"
            ax.text(v, i, f" {fmt}", va="center", fontsize=8.5, fontweight="bold")
        ax.margins(x=0.18)

    plt.suptitle("Human Physical PPI Network — Centrality Leaders (Part A)", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved %s", out_path)


def plot_community_sizes(comm_sizes: List[int], modularity: float, out_path: Path) -> None:
    """Plot Top 15 Louvain community sizes."""
    sns.set_theme(style="whitegrid")
    top15 = comm_sizes[:15]
    labels = [f"C{i}" for i in range(len(top15))]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    bars = ax.bar(labels, top15, color="#3182CE", edgecolor="white", alpha=0.9)
    for bar, val in zip(bars, top15):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 15, str(val), ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_title(
        f"Top 15 Louvain Communities (Total Communities: {len(comm_sizes)} | Modularity Q = {modularity:.4f})",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Community ID (Sorted by Size)")
    ax.set_ylabel("Number of Proteins")
    ax.margins(y=0.12)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved %s", out_path)


def plot_adjacency_heatmap(G: nx.Graph, top_nodes: List[str], out_path: Path) -> pd.DataFrame:
    """Plot & return the binary adjacency matrix for the top hub proteins."""
    sub_G = G.subgraph(top_nodes)
    mat = nx.to_pandas_adjacency(sub_G, nodelist=top_nodes, weight=None).astype(int)

    fig, ax = plt.subplots(figsize=(8, 6.8), dpi=300)
    sns.heatmap(
        mat,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        linewidths=0.6,
        linecolor="#CBD5E0",
        square=True,
        ax=ax,
    )
    ax.set_title("Binary Adjacency Submatrix A (Top 15 Hub Proteins)", fontsize=12, fontweight="bold", pad=12)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved %s", out_path)
    return mat


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    G, edges_df = load_graph(EDGES_PATH)
    meta_df = pd.read_csv(META_PATH)
    meta_df = meta_df.drop_duplicates(subset=["gene_name"]).set_index("gene_name")

    node_list = list(G.nodes())
    N = G.number_of_nodes()
    E = G.number_of_edges()

    # 1. Basic Degree & Density Statistics
    degrees_dict = dict(G.degree())
    degrees_arr = np.array(list(degrees_dict.values()), dtype=int)
    sum_degrees = int(degrees_arr.sum())
    avg_degree = float(degrees_arr.mean())
    median_degree = float(np.median(degrees_arr))
    max_degree = int(degrees_arr.max())
    min_degree = int(degrees_arr.min())
    density = nx.density(G)
    e_max = N * (N - 1) // 2
    sparsity_pct = (1.0 - (2 * E) / (N * N)) * 100.0

    # 2. Connectivity & Components
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    num_components = len(components)
    giant_nodes = components[0]
    n_giant = len(giant_nodes)
    giant_G = G.subgraph(giant_nodes)
    e_giant = giant_G.number_of_edges()
    giant_pct = (n_giant / N) * 100.0

    # Component size breakdown (special small structures)
    comp_sizes = [len(c) for c in components]
    num_dyads = sum(1 for s in comp_sizes if s == 2)
    num_triads_comp = sum(1 for s in comp_sizes if s == 3)
    num_small_comp = sum(1 for s in comp_sizes if 2 <= s <= 10)

    # Bridges & Articulation Points
    logger.info("Finding bridges and articulation points...")
    bridges_list = list(nx.bridges(G))
    articulation_set = set(nx.articulation_points(G))

    # 3. Quantifying Structure: Clustering, Transitivity, Power-Law
    logger.info("Computing clustering coefficients and transitivity...")
    clustering_dict = nx.clustering(G)
    avg_clustering = float(np.mean(list(clustering_dict.values())))
    transitivity = nx.transitivity(G)
    gamma, r2_pl = fit_power_law_tail(degrees_arr, k_min=5)

    # 4. Exact Distances & Closeness Centrality
    diameter_giant, avg_path_giant, closeness_dict = compute_exact_distances_and_closeness(
        G, node_list, giant_nodes, chunk_size=500
    )

    # Small-world comparison against equivalent Erdos-Renyi random graph G(N_giant, avg_k_giant)
    avg_k_giant = (2.0 * e_giant) / n_giant
    c_random = avg_k_giant / n_giant
    l_random = math.log(n_giant) / math.log(avg_k_giant)

    # 5. Centralities: Degree, PageRank, Betweenness (k=500 Brandes pivot approximation)
    logger.info("Computing Degree Centrality & PageRank...")
    deg_cent_dict = nx.degree_centrality(G)
    pagerank_dict = nx.pagerank(G, weight=None)

    logger.info("Computing Betweenness Centrality (Brandes k=500 pivot sampling, seed=42)...")
    t_bet = time.time()
    betweenness_dict = nx.betweenness_centrality(G, k=500, normalized=True, seed=42)
    logger.info("Betweenness completed in %.1fs", time.time() - t_bet)

    # 6. Community Detection (Louvain) + Modularity Q
    logger.info("Running Louvain Community Detection...")
    raw_communities = nx.community.louvain_communities(G, weight=None, seed=42)
    communities = sorted(raw_communities, key=len, reverse=True)
    modularity_q = nx.community.modularity(G, communities, weight=None)
    comm_sizes = [len(c) for c in communities]

    node_comm_map: Dict[str, int] = {}
    for cid, cnodes in enumerate(communities):
        for node in cnodes:
            node_comm_map[node] = cid
    logger.info("Louvain found %d communities | Modularity Q = %.4f", len(communities), modularity_q)

    # 7. Assemble Master Feature Table (for Cytoscape & Part B ML)
    rows = []
    for node in node_list:
        p_size = int(meta_df.at[node, "protein_size"]) if node in meta_df.index else 0
        p_desc = str(meta_df.at[node, "description"]) if node in meta_df.index else ""
        rows.append(
            {
                "gene_name": node,
                "protein_size": p_size,
                "degree": degrees_dict[node],
                "degree_centrality": round(deg_cent_dict[node], 6),
                "betweenness": round(betweenness_dict[node], 6),
                "closeness": round(closeness_dict[node], 6),
                "pagerank": round(pagerank_dict[node], 6),
                "clustering_coeff": round(clustering_dict[node], 6),
                "community_id": node_comm_map[node],
                "in_giant_component": int(node in giant_nodes),
                "is_articulation_point": int(node in articulation_set),
                "description": p_desc,
            }
        )

    features_df = pd.DataFrame(rows).sort_values("degree", ascending=False).reset_index(drop=True)
    features_out = OUTPUT_DIR / "node_features_for_ml.csv"
    features_df.to_csv(features_out, index=False)
    logger.info("Exported master feature table to %s (%d rows)", features_out, len(features_df))

    # 8. Export Clean Core Subgraph (Top 300 Hubs) for crisp Cytoscape rendering
    top300_nodes = set(features_df.head(300)["gene_name"])
    core_edges = edges_df[edges_df["source"].isin(top300_nodes) & edges_df["target"].isin(top300_nodes)]
    core_out = OUTPUT_DIR / "top300_core_ppi_cytoscape.csv"
    core_edges.to_csv(core_out, index=False)
    logger.info("Exported Top-300 Core Subgraph to %s (%d edges)", core_out, len(core_edges))

    # 9. Generate Publication-Ready Plots
    plot_degree_distribution(degrees_arr, gamma, r2_pl, FIGURES_DIR / "fig1_degree_distribution.png")
    plot_top_centralities(features_df, FIGURES_DIR / "fig2_top_centralities.png")
    plot_community_sizes(comm_sizes, modularity_q, FIGURES_DIR / "fig3_community_sizes.png")
    top15_hubs = features_df.head(15)["gene_name"].tolist()
    adj_sub_df = plot_adjacency_heatmap(G, top15_hubs, FIGURES_DIR / "fig4_adjacency_heatmap.png")
    adj_sub_df.iloc[:10, :10].to_csv(OUTPUT_DIR / "top10_hubs_adjacency_matrix.csv")

    # 10. Write Complete Part A Summary Report
    report_lines: List[str] = []
    report_lines.append("=" * 75)
    report_lines.append("PART A: SOCIAL NETWORK ANALYSIS — HUMAN PHYSICAL PPI NETWORK (STRING v12.5)")
    report_lines.append("=" * 75)
    report_lines.append("\n1. GRAPH & MATRIX REPRESENTATIONS")
    report_lines.append("-" * 50)
    report_lines.append(f"Graph Type             : Simple, Undirected, Weighted (Confidence >= 900)")
    report_lines.append(f"Total Nodes (N)        : {N:,}")
    report_lines.append(f"Total Edges (E)        : {E:,}")
    report_lines.append(f"Max Possible Edges     : {e_max:,}  [N(N-1)/2]")
    report_lines.append(f"Adjacency Matrix Shape : {N:,} x {N:,} (Symmetric, Binary/Weighted)")
    report_lines.append(f"Matrix Sparsity        : {sparsity_pct:.4f}% zeros (Network Density D = {density:.6f})")

    report_lines.append("\nSample Adjacency List (Top 5 Hub Proteins — first 8 neighbors shown):")
    for hub in features_df.head(5)["gene_name"]:
        nbrs = sorted(list(G.neighbors(hub)))[:8]
        report_lines.append(f"  {hub} (k={degrees_dict[hub]}): {', '.join(nbrs)}, ...")

    report_lines.append("\n2. NODE DEGREES & QUANTIFYING STRUCTURE")
    report_lines.append("-" * 50)
    report_lines.append(f"Sum of Degrees (Sum k) : {sum_degrees:,} (Handshaking Check: 2E = {2*E:,})")
    report_lines.append(f"Average Degree <k>     : {avg_degree:.4f}")
    report_lines.append(f"Median Degree          : {median_degree:.1f}")
    report_lines.append(f"Min / Max Degree       : {min_degree} / {max_degree}")
    report_lines.append(f"Power-Law Exponent     : gamma = {gamma:.3f} (Log-Log R^2 = {r2_pl:.3f}, k >= 5)")
    report_lines.append(f"Avg Clustering (C)     : {avg_clustering:.4f}")
    report_lines.append(f"Global Transitivity    : {transitivity:.4f}")

    report_lines.append("\n3. CONNECTIVITY, SPECIAL STRUCTURES & SMALL-WORLD CHECK")
    report_lines.append("-" * 50)
    report_lines.append(f"Connected Components   : {num_components:,}")
    report_lines.append(f"Giant Component (GCC)  : {n_giant:,} nodes ({giant_pct:.2f}%), {e_giant:,} edges")
    report_lines.append(f"Small Isolated Modules : {num_dyads} dyads (size 2), {num_triads_comp} triads (size 3), {num_small_comp} total (size 2-10)")
    report_lines.append(f"Bridge Edges           : {len(bridges_list):,}")
    report_lines.append(f"Articulation Points    : {len(articulation_set):,} cut-vertices")
    report_lines.append(f"Diameter (Giant Comp.) : {diameter_giant} hops (Exact)")
    report_lines.append(f"Avg Path Length (GCC)  : {avg_path_giant:.4f} hops (Exact)")
    report_lines.append(f"Small-World Verification (vs Random G({n_giant}, <k>={avg_k_giant:.2f})):")
    report_lines.append(f"  - Clustering : C_actual = {avg_clustering:.4f}  >>  C_random = {c_random:.5f} ({avg_clustering/c_random:.0f}x higher!)")
    report_lines.append(f"  - Path Length: L_actual = {avg_path_giant:.4f}  ~   L_random = {l_random:.4f}")

    report_lines.append("\n4. CENTRALITY MEASURES — TOP 10 PROTEINS")
    report_lines.append("-" * 50)
    for metric_col, label in [
        ("degree", "DEGREE CENTRALITY (Super-Hubs)"),
        ("betweenness", "BETWEENNESS CENTRALITY (Pathway Bridges, k=500 pivots)"),
        ("closeness", "CLOSENESS CENTRALITY (Global Reach / Fast Signalers)"),
        ("pagerank", "PAGERANK (Prestigious / Core Regulators)"),
    ]:
        report_lines.append(f"\n  [{label}]")
        top10 = features_df.nlargest(10, metric_col)
        for rank, r in enumerate(top10.itertuples(index=False), start=1):
            val = getattr(r, metric_col)
            val_str = f"{val:d}" if metric_col == "degree" else f"{val:.5f}"
            short_desc = r.description.split(";")[0][:65]
            report_lines.append(f"   {rank:2d}. {r.gene_name:<12} | {val_str:<9} | Comm C{r.community_id:<3} | {short_desc}")

    report_lines.append("\n5. COMMUNITY DETECTION (LOUVAIN) & MODULARITY")
    report_lines.append("-" * 50)
    report_lines.append(f"Total Communities      : {len(communities):,}")
    report_lines.append(f"Modularity Score (Q)   : {modularity_q:.4f}  (Strong community structure > 0.30)")
    report_lines.append("\nTop 5 Largest Biological Communities:")
    for cid in range(min(5, len(communities))):
        c_sub = features_df[features_df["community_id"] == cid].nlargest(5, "degree")
        hub_names = ", ".join(c_sub["gene_name"].tolist())
        top_desc = c_sub.iloc[0]["description"].split(";")[0][:70]
        report_lines.append(f"  Community C{cid} ({comm_sizes[cid]:,} proteins) | Top Hubs: {hub_names}")
        report_lines.append(f"      Lead Protein Role: {top_desc}")

    report_text = "\n".join(report_lines)
    report_out = OUTPUT_DIR / "part_a_summary_report.txt"
    report_out.write_text(report_text, encoding="utf-8")
    logger.info("Saved complete report to %s", report_out)
    logger.info("TOTAL PIPELINE RUNTIME: %.1f seconds", time.time() - t_start)


if __name__ == "__main__":
    main()
