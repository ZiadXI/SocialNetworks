"""Build polished, submission-ready Part A Project Report PDF.
Output: d:/SocialNetworks/Project_Report_PartA_Human_PPI_Network.pdf
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageChops
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path("d:/SocialNetworks")
FIG_DIR = BASE_DIR / "figures"
OUT_PDF = BASE_DIR / "Project_Report_PartA_Human_PPI_Network.pdf"

# Brand palette (Clean academic navy & teal)
NAVY = colors.HexColor("#1A365D")
TEAL = colors.HexColor("#2B6CB0")
ACCENT_BG = colors.HexColor("#EBF8FF")
WARN_BG = colors.HexColor("#FFFBEB")
WARN_BORDER = colors.HexColor("#D69E2E")
CODE_BG = colors.HexColor("#F7FAFC")
GRID_GRAY = colors.HexColor("#CBD5E0")
HEADER_BG = colors.HexColor("#E2E8F0")
ALT_ROW = colors.HexColor("#F8FAFC")
TEXT_DARK = colors.HexColor("#1A202C")
TEXT_MUTED = colors.HexColor("#4A5568")


def trim_whitespace(img_path: Path, out_path: Path, pad: int = 24) -> Path:
    """Trim excess white margins around Cytoscape export for sharper full-width rendering."""
    im = PILImage.open(img_path).convert("RGB")
    bg = PILImage.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        x0 = max(0, bbox[0] - pad)
        y0 = max(0, bbox[1] - pad)
        x1 = min(im.width, bbox[2] + pad)
        y1 = min(im.height, bbox[3] + pad)
        im = im.crop((x0, y0, x1, y1))
    im.save(out_path, format="PNG")
    return out_path


def scaled_image(img_path: Path, max_w: float, max_h: float) -> Image:
    """Return a ReportLab Image preserving exact aspect ratio within (max_w, max_h)."""
    with PILImage.open(img_path) as im:
        w, h = im.size
    ratio = min(max_w / w, max_h / h)
    return Image(str(img_path), width=w * ratio, height=h * ratio)


class NumberedCanvas(canvas.Canvas):
    """Canvas with clean header and Page X of Y footer (skipping header on Page 1)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count: int):
        page_num = self._pageNumber
        width, height = A4
        self.saveState()

        # Subtle header on pages >= 2
        if page_num > 1:
            self.setStrokeColor(GRID_GRAY)
            self.setLineWidth(0.5)
            self.line(42, height - 38, width - 42, height - 38)
            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawString(42, height - 32, "FCDS — Introduction to Social Networks | Final Project Report (Part A)")
            self.drawRightString(width - 42, height - 32, "Human Physical PPI Network (STRING v12.5)")

        # Footer on all pages
        self.setStrokeColor(GRID_GRAY)
        self.setLineWidth(0.5)
        self.line(42, 38, width - 42, 38)
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(42, 26, "Alexandria University — Faculty of Computers & Data Science (Fall 2026-2027)")
        self.drawRightString(width - 42, 26, f"Page {page_num} of {page_count}")
        self.restoreState()


def build_report() -> None:
    # Crop Cytoscape figure cleanly
    cyto_cropped = trim_whitespace(
        FIG_DIR / "fig5_cytoscape_communities.png",
        FIG_DIR / "fig5_cytoscape_communities_cropped.png",
        pad=25,
    )

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=50,
        bottomMargin=50,
        title="Project Report - Human Physical PPI Network (Part A)",
        author="Ziad Kassem",
    )

    styles = getSampleStyleSheet()
    content_w = A4[0] - 84  # ~511 pt

    # Typography styles
    banner_uni = ParagraphStyle(
        "BannerUni", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9, textColor=colors.HexColor("#BEE3F8"), alignment=TA_LEFT, spaceAfter=3
    )
    banner_title = ParagraphStyle(
        "BannerTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=15.5, leading=19.5, textColor=colors.white, alignment=TA_LEFT, spaceAfter=4
    )
    banner_sub = ParagraphStyle(
        "BannerSub", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9.5, leading=13, textColor=colors.HexColor("#E2E8F0"), alignment=TA_LEFT
    )
    h1 = ParagraphStyle(
        "H1", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=8, spaceAfter=4
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10.2, leading=13.5, textColor=TEAL, spaceBefore=6, spaceAfter=3
    )
    body = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9.2, leading=13.2, textColor=TEXT_DARK, alignment=TA_JUSTIFY, spaceAfter=4.5
    )
    bullet = ParagraphStyle(
        "Bullet", parent=body, leftIndent=14, firstLineIndent=-8, spaceAfter=3
    )
    caption = ParagraphStyle(
        "Caption", parent=styles["Normal"], fontName="Helvetica-Oblique",
        fontSize=8.3, leading=11.5, textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=6
    )
    tbl_hdr = ParagraphStyle(
        "TblHdr", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8.4, leading=10.5, textColor=NAVY
    )
    tbl_cell = ParagraphStyle(
        "TblCell", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8.2, leading=10.8, textColor=TEXT_DARK
    )
    callout_text = ParagraphStyle(
        "Callout", parent=styles["Normal"], fontName="Helvetica",
        fontSize=8.7, leading=12.4, textColor=TEXT_DARK, alignment=TA_JUSTIFY
    )
    code_style = ParagraphStyle(
        "CodeBlock", parent=styles["Code"], fontName="Courier",
        fontSize=7.4, leading=9.6, textColor=colors.HexColor("#1A202C"),
        backColor=CODE_BG, leftIndent=6, rightIndent=6
    )

    def make_callout(html_text: str, bg=ACCENT_BG, border=TEAL) -> Table:
        t = Table([[Paragraph(html_text, callout_text)]], colWidths=[content_w])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LINEBEFORE", (0, 0), (0, -1), 3.0, border),
            ("BOX", (0, 0), (-1, -1), 0.4, GRID_GRAY),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return t

    def styled_table(data, col_widths) -> Table:
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("GRID", (0, 0), (-1, -1), 0.45, GRID_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_ROW]),
        ]))
        return t

    story = []

    # =========================================================================
    # PAGE 1: COVER BANNER, TEAM METADATA, PROBLEM STATEMENT & DATASET
    # =========================================================================
    banner = Table(
        [[
            Paragraph("ALEXANDRIA UNIVERSITY  |  FACULTY OF COMPUTERS & DATA SCIENCE (FCDS)", banner_uni),
        ], [
            Paragraph("Introduction to Social Networks — Final Project Report (Part A)", banner_title),
        ], [
            Paragraph("Social Network Analysis of the Human Physical Protein-Protein Interaction Network (STRING v12.5)", banner_sub),
        ]],
        colWidths=[content_w],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("TOPPADDING", (0, 1), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 1),
    ]))
    story.append(banner)
    story.append(Spacer(1, 8))

    # Student / Group Info Table
    meta_rows = [
        [Paragraph("<b>Role / Section</b>", tbl_hdr), Paragraph("<b>Student Name</b>", tbl_hdr), Paragraph("<b>Student ID</b>", tbl_hdr), Paragraph("<b>Group / Track</b>", tbl_hdr)],
        [Paragraph("Part A — SNA Pipeline & Metrics", tbl_cell), Paragraph("Ziad Kassem", tbl_cell), Paragraph("[Enter ID]", tbl_cell), Paragraph("[Enter Group]", tbl_cell)],
        [Paragraph("Part A — Visualization & Report", tbl_cell), Paragraph("[Teammate Name]", tbl_cell), Paragraph("[Enter ID]", tbl_cell), Paragraph("[Enter Group]", tbl_cell)],
        [Paragraph("Course Instructor", tbl_cell), Paragraph("Dr. Reem Essameldin Ebrahim", tbl_cell), Paragraph("Term: Fall 2026-2027", tbl_cell), Paragraph("Dataset: Human PPI", tbl_cell)],
    ]
    story.append(styled_table(meta_rows, [145, 145, 110, 111]))
    story.append(Spacer(1, 8))

    # Section 1: Problem Statement
    story.append(Paragraph("1. Problem Statement: Purpose, Inputs & Outputs", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "<b>Program Objective:</b> This project applies formal Social Network Analysis (SNA) to a real-world biological "
        "system—the <b>Human Physical Protein-Protein Interaction (PPI) Network</b>—to uncover its macro-level topology, "
        "identify essential hub and bridge proteins via centrality analysis, detect functional molecular machines via "
        "modularity-based community detection, and export a clean topological feature set that empowers downstream "
        "Machine Learning models (Part B).",
        body,
    ))
    io_rows = [
        [Paragraph("<b>Component</b>", tbl_hdr), Paragraph("<b>Specification</b>", tbl_hdr)],
        [Paragraph("<b>Inputs</b>", tbl_cell), Paragraph(
            "1. <font name='Courier'>9606.protein.physical.links.v12.5.txt</font> (1,296,490 raw scored physical interactions between human Ensembl protein IDs).<br/>"
            "2. <font name='Courier'>9606.protein.info.v12.0.txt</font> (19,699 human protein records mapping Ensembl IDs to HGNC gene symbols, amino acid sizes, and biological annotations).", tbl_cell)],
        [Paragraph("<b>Outputs</b>", tbl_cell), Paragraph(
            "1. <font name='Courier'>clean_human_ppi.csv</font> — Undirected simple edge list (11,442 proteins, 70,797 highest-confidence links).<br/>"
            "2. <font name='Courier'>node_features_for_ml.csv</font> — Master feature matrix (baseline metadata + 9 SNA features) handed off to Part B.<br/>"
            "3. <font name='Courier'>top300_core_ppi.graphml</font> &amp; <font name='Courier'>full_human_ppi.graphml</font> — Native Cytoscape graphs with embedded attributes.<br/>"
            "4. Five publication-resolution analytical figures (degree distribution, centralities, communities, adjacency heatmap, Cytoscape cluster visual).", tbl_cell)],
    ]
    story.append(styled_table(io_rows, [85, content_w - 85]))
    story.append(Spacer(1, 6))

    # Section 2: Dataset Description & Preprocessing
    story.append(Paragraph("2. Dataset Description & Data Engineering Pipeline", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "<b>Source &amp; Biological Context:</b> Data were obtained from the <b>STRING Database v12.5</b> "
        "(Swiss Institute of Bioinformatics / EMBL) for <i>Homo sapiens</i> (NCBI Taxonomy ID: <b>9606</b>). "
        "Unlike noisy text-mining associations, we specifically selected the <b>physical subnetwork</b>, where an edge "
        "represents experimentally verified physical binding between two proteins inside human cells (e.g., TP53 binding "
        "MDM2 to regulate cell division and tumor suppression). Each edge carries an experimental confidence score from "
        "0 to 1,000.",
        body,
    ))
    story.append(Paragraph("<b>Four-Stage Preprocessing Performed in <font name='Courier'>clean_data.py</font>:</b>", h2))
    story.append(Paragraph("&#8226; <b>1. Highest-Confidence Noise Filtering (Score &gt;= 900):</b> Raw STRING data contain 1,296,490 links including low-confidence experimental noise. Filtering to STRING's official <i>Highest Confidence</i> tier (score &gt;= 900) removes ~94.5% of noise while retaining the rock-solid biological core.", bullet))
    story.append(Paragraph("&#8226; <b>2. Human-Readable Gene Symbol Mapping:</b> Replaced internal Ensembl codes (e.g., <font name='Courier'>9606.ENSP00000269305</font>) with standard HGNC gene symbols (e.g., <b>TP53</b>, <b>EGFR</b>, <b>MAPT</b>) using <font name='Courier'>protein.info</font>, enabling biological interpretation of every hub and community.", bullet))
    story.append(Paragraph("&#8226; <b>3. Undirected Reverse-Edge Deduplication:</b> Raw STRING logs symmetric physical handshakes twice—both <font name='Courier'>(A, B)</font> and <font name='Courier'>(B, A)</font>. Retaining both turns the network into an artificial <i>multigraph</i>, doubling the edge count (E), inflating density (D) by 2x, falsifying node degrees, and allowing mathematically illegal clustering coefficients (C_i &gt; 1). Canonical alphabetical sorting <font name='Courier'>(min(u,v), max(u,v))</font> reduced edges to <b>70,797 unique undirected physical links</b>.", bullet))
    story.append(Paragraph("&#8226; <b>4. Self-Loop Pruning (Simple Graph Enforcement):</b> Filtered out edges where <font name='Courier'>source == target</font> (detailed biological rationale provided in the methodological note at the top of Page 2).", bullet))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: SELF-LOOPS NOTE, TOOLS, LIBRARIES & CODE ARCHITECTURE
    # =========================================================================
    story.append(make_callout(
        "<b>Methodological Note on Self-Loops (Biology vs. SNA Math):</b> In human biochemistry, self-loops represent "
        "<b>homodimerization</b> (e.g., four identical TP53 proteins binding into an active tetramer). However, classical "
        "network science metrics taught in Lectures 1–5—specifically Local Clustering Coefficient C_i = 2e_i / [k_i(k_i-1)], "
        "shortest paths (d(u,u) = 0), and Euler's Handshaking Lemma—require a strict <b>Simple Graph</b> (no self-loops, "
        "no parallel edges). Pruning self-loops prevents self-referential neighbor distortion while preserving full "
        "inter-protein structural fidelity.",
        bg=WARN_BG, border=WARN_BORDER,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("3. Tools, Libraries & Code Implementation", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "To achieve both high-precision mathematical computation on all 11,442 nodes and publication-quality visual "
        "exploration, we combined a reproducible <b>Python analytical pipeline</b> with <b>Cytoscape</b> via native "
        "GraphML data exchange.",
        body,
    ))

    tools_rows = [
        [Paragraph("<b>Tool / Library</b>", tbl_hdr), Paragraph("<b>Version / Role</b>", tbl_hdr), Paragraph("<b>Key Functions &amp; Attributes Used</b>", tbl_hdr)],
        [Paragraph("<b>Cytoscape</b>", tbl_cell), Paragraph("Desktop GUI (SNA Visuals)", tbl_cell), Paragraph("Native GraphML import (<font name='Courier'>top300_core_ppi.graphml</font>), Prefuse Force-Directed Layout, Style mapping (Discrete Rainbow on <font name='Courier'>community_id</font>, Continuous Size on <font name='Courier'>degree</font>, Edge Transparency = 60).", tbl_cell)],
        [Paragraph("<b>NetworkX</b>", tbl_cell), Paragraph("Python v3.3 (Graph Engine)", tbl_cell), Paragraph("<font name='Courier'>nx.Graph()</font>, <font name='Courier'>density</font>, <font name='Courier'>clustering</font>, <font name='Courier'>transitivity</font>, <font name='Courier'>connected_components</font>, <font name='Courier'>bridges</font>, <font name='Courier'>articulation_points</font>, <font name='Courier'>degree_centrality</font>, <font name='Courier'>betweenness_centrality(k=500)</font>, <font name='Courier'>pagerank</font>, <font name='Courier'>louvain_communities</font>, <font name='Courier'>modularity</font>, <font name='Courier'>write_graphml</font>.", tbl_cell)],
        [Paragraph("<b>SciPy Sparse</b>", tbl_cell), Paragraph("C-Level Exact BFS", tbl_cell), Paragraph("<font name='Courier'>scipy.sparse.csgraph.shortest_path(adj, directed=False, unweighted=True)</font> executed in 500-node chunks to compute <b>exact</b> Giant Component Diameter, exact Average Path Length, and exact Wasserman-Faust Closeness Centrality in 17.2s.", tbl_cell)],
        [Paragraph("<b>Pandas / NumPy</b>", tbl_cell), Paragraph("Data &amp; Numerical Math", tbl_cell), Paragraph("Edge deduplication, gene-symbol mapping, log-log OLS Power-Law regression (<font name='Courier'>np.polyfit</font>), and exporting <font name='Courier'>node_features_for_ml.csv</font>.", tbl_cell)],
        [Paragraph("<b>Matplotlib / Seaborn</b>", tbl_cell), Paragraph("300 DPI Statistical Plots", tbl_cell), Paragraph("Linear/Log-Log degree distributions, 4-panel centrality bar charts, Louvain community size distribution, and binary adjacency matrix heatmap.", tbl_cell)],
    ]
    story.append(styled_table(tools_rows, [90, 115, content_w - 205]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.1 Algorithmic Efficiency Notes (Scaling to 11,442 Nodes)", h2))
    story.append(Paragraph(
        "Computing exact all-pairs shortest paths (APSP) in pure Python loops scales as O(N(N + E)) and takes 20+ minutes "
        "on 11,442 nodes. By converting the NetworkX graph to a compressed sparse row matrix (<font name='Courier'>csr_matrix</font>) "
        "and running chunked C-level BFS via <font name='Courier'>scipy.sparse.csgraph.shortest_path</font>, our pipeline "
        "computed <b>exact Diameter (16)</b>, <b>exact Average Shortest Path Length (4.9764)</b>, and <b>exact Wasserman-Faust "
        "Closeness Centrality</b> for all 11,442 proteins in <b>17.2 seconds</b> using under 50 MB of RAM. For Betweenness "
        "Centrality (O(VE)), we applied Brandes' standard pivot approximation (<font name='Courier'>k=500, seed=42</font>, "
        "22.0 seconds), yielding reproducible global rankings (total runtime: <b>52.3 seconds</b>).",
        body,
    ))

    story.append(Paragraph("3.2 Core Pipeline Code Excerpts (<font name='Courier'>clean_data.py</font> &amp; <font name='Courier'>part_a_analysis.py</font>)", h2))
    code_excerpt = """# 1. Data Cleaning & Undirected Simple-Graph Construction (clean_data.py)
info_df  = pd.read_csv("data/9606.protein.info.v12.0.txt", sep="\\t")
id_map   = dict(zip(info_df["#string_protein_id"], info_df["preferred_name"]))
links_df = pd.read_csv("data/9606.protein.physical.links.v12.5.txt", sep=" ")
clean    = links_df[links_df["combined_score"] >= 900].copy()
clean["source"], clean["target"] = clean["protein1"].map(id_map), clean["protein2"].map(id_map)
clean    = clean.dropna(subset=["source", "target"])
clean    = clean[clean["source"] != clean["target"]]                   # Remove self-loops
clean["u"], clean["v"] = clean[["source","target"]].min(axis=1), clean[["source","target"]].max(axis=1)
edges    = clean.drop_duplicates(subset=["u", "v"])[["u", "v", "combined_score"]]

# 2. Fast Exact Shortest Paths, Centralities & Louvain Communities (part_a_analysis.py)
adj = nx.to_scipy_sparse_array(G, nodelist=node_list, weight=None, format="csr")
dist_chunk  = shortest_path(adj, directed=False, unweighted=True, indices=chunk)  # Exact C-level BFS
betweenness = nx.betweenness_centrality(G, k=500, normalized=True, seed=42)
pagerank    = nx.pagerank(G, weight=None)
communities = sorted(nx.community.louvain_communities(G, weight=None, seed=42), key=len, reverse=True)
modularity  = nx.community.modularity(G, communities, weight=None)     # Q = 0.8146
nx.write_graphml(G_top300, "output/top300_core_ppi.graphml")           # 1-Click Cytoscape export"""
    code_box = Table([[Preformatted(code_excerpt, code_style)]], colWidths=[content_w])
    code_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(code_box)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: GRAPH & MATRIX REPRESENTATIONS
    # =========================================================================
    story.append(Paragraph("4. Part A Results — Graph & Matrix Representations", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "The cleaned Human Physical PPI network is formally represented as a simple, undirected, weighted graph "
        "<b>G = (V, E)</b> with <b>N = 11,442</b> protein vertices and <b>E = 70,797</b> physical interaction edges.",
        body,
    ))

    rep_rows = [
        [Paragraph("<b>Representation Property</b>", tbl_hdr), Paragraph("<b>Measured Value</b>", tbl_hdr), Paragraph("<b>Course Formula / Interpretation</b>", tbl_hdr)],
        [Paragraph("Nodes (N) / Edges (E)", tbl_cell), Paragraph("11,442 / 70,797", tbl_cell), Paragraph("Undirected simple graph (no self-loops, no multi-edges)", tbl_cell)],
        [Paragraph("Max Possible Edges (E_max)", tbl_cell), Paragraph("65,453,961", tbl_cell), Paragraph("N(N - 1) / 2 = 11,442 x 11,441 / 2", tbl_cell)],
        [Paragraph("Network Density (D)", tbl_cell), Paragraph("0.001082 (0.108%)", tbl_cell), Paragraph("D = 2E / [N(N - 1)] — Extremely sparse biological wiring", tbl_cell)],
        [Paragraph("Adjacency Matrix Shape", tbl_cell), Paragraph("11,442 x 11,442", tbl_cell), Paragraph("Symmetric (A_ij = A_ji); 99.8918% zero entries (sparse CSR)", tbl_cell)],
    ]
    story.append(styled_table(rep_rows, [140, 125, content_w - 265]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Sample Edge List &amp; Adjacency List (Top 5 Super-Hubs)", h2))
    el_al_rows = [
        [Paragraph("<b>Sample Edge List (<font name='Courier'>clean_human_ppi.csv</font>)</b>", tbl_hdr), Paragraph("<b>Sample Adjacency List (Top 5 Hubs — First 6 Neighbors)</b>", tbl_hdr)],
        [
            Paragraph(
                "<font name='Courier' size='7.8'>"
                "source, target, confidence_score<br/>"
                "ARF4, ARF5, 999<br/>"
                "FKBP4, HSP90AA1, 999<br/>"
                "FKBP4, NR3C1, 996<br/>"
                "GGA3, M6PR, 972<br/>"
                "ARF1, ARF5, 963</font>", tbl_cell
            ),
            Paragraph(
                "<font name='Courier' size='7.8'>"
                "<b>RPS27A</b> (k=292): ABCE1, ACTB, ACTG1, ADRM1, AEBP2, AMFR, ...<br/>"
                "<b>UBC</b>    (k=274): ACTB, ACTG1, ADRM1, AEBP2, AMFR, ANAPC11, ...<br/>"
                "<b>UBA52</b>  (k=244): ACTB, ACTG1, ADRM1, AEBP2, AMFR, ANAPC2, ...<br/>"
                "<b>NUDCD1</b> (k=228): AARS2, ABCC9, ABCD3, ACACA, ACLY, AGO1, ...<br/>"
                "<b>TP53</b>   (k=225): ABL1, ATF3, ATM, ATR, AURKA, AURKB, ...</font>", tbl_cell
            ),
        ],
    ]
    story.append(styled_table(el_al_rows, [185, content_w - 185]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.2 Binary Adjacency Matrix Representation (Top 15 Hubs)", h2))
    story.append(scaled_image(FIG_DIR / "fig4_adjacency_heatmap.png", max_w=content_w * 0.72, max_h=305))
    story.append(Paragraph(
        "<b>Figure 1 (Matrix Representation):</b> Binary adjacency submatrix A of the top 15 hub proteins. "
        "Notice two key course axioms verified visually: (1) all main-diagonal entries are <b>0</b> (confirming zero self-loops), "
        "and (2) the matrix is perfectly <b>symmetric</b> across the diagonal (A_ij = A_ji, confirming an undirected graph). "
        "The dense blue block among RPS27A, UBC, UBA52, UBB, and histones (H4C6, H3C1) visually exposes their tightly "
        "coupled core complex.",
        caption,
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: NODE DEGREES, DEGREE DISTRIBUTION & SCALE-FREE STRUCTURE
    # =========================================================================
    story.append(Paragraph("5. Node Degrees, Average Degree & Scale-Free Structure", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))

    deg_rows = [
        [Paragraph("<b>Degree Metric</b>", tbl_hdr), Paragraph("<b>Value</b>", tbl_hdr), Paragraph("<b>Formula / Verification</b>", tbl_hdr)],
        [Paragraph("Sum of All Node Degrees", tbl_cell), Paragraph("141,594", tbl_cell), Paragraph("Euler's Handshaking Lemma: Sum(k_i) = 2E = 2(70,797) = 141,594", tbl_cell)],
        [Paragraph("Average Degree (&lt;k&gt;)", tbl_cell), Paragraph("12.3749", tbl_cell), Paragraph("&lt;k&gt; = 2E / N = 141,594 / 11,442", tbl_cell)],
        [Paragraph("Median / Min / Max Degree", tbl_cell), Paragraph("5.0 / 1 / 292", tbl_cell), Paragraph("Strong right-skew: Mean (12.37) is 2.5x larger than Median (5.0)", tbl_cell)],
        [Paragraph("Power-Law Exponent (gamma)", tbl_cell), Paragraph("gamma = 2.038", tbl_cell), Paragraph("Log-Log OLS fit on tail (k &gt;= 5): R² = 0.915 (Scale-Free regime 2 &lt; gamma &lt; 3)", tbl_cell)],
    ]
    story.append(styled_table(deg_rows, [145, 95, content_w - 240]))
    story.append(Spacer(1, 8))

    story.append(scaled_image(FIG_DIR / "fig1_degree_distribution.png", max_w=content_w, max_h=240))
    story.append(Paragraph(
        "<b>Figure 2 (Degree Distribution P(k)):</b> Left — Linear histogram up to the 99th percentile showing extreme right "
        "skewness (most proteins interact with only 1–5 partners, while a tiny fraction act as super-hubs). Right — Log-Log "
        "plot confirming a linear heavy-tailed decay P(k) ~ k^(-gamma) with gamma = 2.04 and R² = 0.92.",
        caption,
    ))
    story.append(Spacer(1, 4))

    story.append(make_callout(
        "<b>Biological &amp; Theoretical Insight (Lecture 5 — Scale-Free Networks):</b> Unlike an Erdos-Renyi random graph "
        "(which produces a symmetric bell-shaped Poisson distribution), the human physical interactome is strongly "
        "<b>scale-free</b> (gamma = 2.04, strictly inside Barabasi's ultra-small regime 2 &lt; gamma &lt; 3). This topology "
        "provides an evolutionary advantage called <i>robustness against random failure</i>: random genetic mutations usually "
        "hit low-degree peripheral proteins (degree 1–5) without collapsing the cell. Conversely, the cell exhibits "
        "<i>targeted hub vulnerability</i> (the <b>Centrality-Lethality Rule</b>): mutations hitting top hubs such as "
        "<b>TP53</b> (k = 225) or <b>EGFR</b> (k = 194) disrupt hundreds of interactions simultaneously, driving cancer."
    ))

    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 6 (STARTS ON PAGE 5 FOR CLEAN LAYOUT)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("6. Connectivity, Special Graphs & Small-World Verification", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))

    conn_rows = [
        [Paragraph("<b>Connectivity / Structural Property</b>", tbl_hdr), Paragraph("<b>Measured Value</b>", tbl_hdr), Paragraph("<b>Topological &amp; Biological Meaning</b>", tbl_hdr)],
        [Paragraph("Total Connected Components (s)", tbl_cell), Paragraph("443 components", tbl_cell), Paragraph("Network is disconnected overall (full-graph diameter = infinity)", tbl_cell)],
        [Paragraph("Giant Connected Component (GCC)", tbl_cell), Paragraph("10,196 nodes (89.11%)", tbl_cell), Paragraph("Contains 69,580 edges (98.3% of all physical links in the cell)", tbl_cell)],
        [Paragraph("Small Isolated Complexes (size 2–10)", tbl_cell), Paragraph("438 components", tbl_cell), Paragraph("272 isolated dyads (K_2 pairs) + 98 triads (size 3) + 68 modules", tbl_cell)],
        [Paragraph("Bridge Edges (Cut-Edges)", tbl_cell), Paragraph("2,228 bridges", tbl_cell), Paragraph("Edges not lying on any cycle; removal disconnects components", tbl_cell)],
        [Paragraph("Articulation Points (Cut-Vertices)", tbl_cell), Paragraph("1,524 proteins", tbl_cell), Paragraph("Single-point-of-failure proteins whose knockout fragments pathways", tbl_cell)],
        [Paragraph("Exact Diameter (Giant Component)", tbl_cell), Paragraph("16 hops", tbl_cell), Paragraph("Longest shortest path across all 10,196 GCC proteins (SciPy BFS)", tbl_cell)],
        [Paragraph("Exact Avg Shortest Path (L_actual)", tbl_cell), Paragraph("4.9764 hops", tbl_cell), Paragraph("Any two core human proteins communicate in under 5 binding hops", tbl_cell)],
        [Paragraph("Avg Clustering Coefficient (C_actual)", tbl_cell), Paragraph("0.4692", tbl_cell), Paragraph("Global Transitivity = 0.4829 — dense local triadic closure", tbl_cell)],
    ]
    story.append(styled_table(conn_rows, [165, 110, content_w - 275]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.1 Formal Small-World Network Verification (Watts-Strogatz Criteria)", h2))
    story.append(Paragraph(
        "To formally test whether the human interactome is a <b>Small-World Network</b>, we compared the Giant Component "
        "(N_GCC = 10,196, &lt;k&gt;_GCC = 13.65) against an equivalent Erdos-Renyi random graph G(N_GCC, p = &lt;k&gt;/N):",
        body,
    ))
    sw_rows = [
        [Paragraph("<b>Property</b>", tbl_hdr), Paragraph("<b>Human PPI (Observed)</b>", tbl_hdr), Paragraph("<b>Random Graph Baseline</b>", tbl_hdr), Paragraph("<b>Small-World Verdict</b>", tbl_hdr)],
        [Paragraph("Clustering Coefficient (C)", tbl_cell), Paragraph("<b>0.4692</b>", tbl_cell), Paragraph("0.00134  (&lt;k&gt; / N)", tbl_cell), Paragraph("<b>PASS: 351x higher clustering!</b>", tbl_cell)],
        [Paragraph("Avg Shortest Path (L)", tbl_cell), Paragraph("<b>4.9764 hops</b>", tbl_cell), Paragraph("3.5314 hops  (ln N / ln &lt;k&gt;)", tbl_cell), Paragraph("<b>PASS: Same log-scale (~5 hops)</b>", tbl_cell)],
    ]
    story.append(styled_table(sw_rows, [130, 115, 130, content_w - 375]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.2 Special Graphs &amp; Real Biological Case Study (Open Triad &amp; Cut-Vertex)", h2))
    story.append(make_callout(
        "<b>Special Subgraph Discovery — The <font name='Courier'>FLRT3 — ADGRL3 — TENM2</font> Isolated Triad:</b><br/>"
        "Inspecting the 98 isolated 3-node components outside the Giant Component reveals textbook special graphs with real "
        "medical significance. One isolated component consists of the 3-node open triad (path graph P_3): "
        "<b>FLRT3 — ADGRL3 — TENM2</b>.<br/>"
        "&#8226; <b>SNA Properties:</b> Diameter = 2 (maximum possible N - 1 = 3 - 1 = 2); Local Clustering C_ADGRL3 = 0 "
        "(neighbors FLRT3 and TENM2 do not directly touch); <b>ADGRL3</b> is an <b>articulation point (cut-vertex)</b>, "
        "and both edges are <b>bridges</b>.<br/>"
        "&#8226; <b>Biological Meaning:</b> In human neuroscience, ADGRL3 (Latrophilin-3) sits on one brain neuron and binds "
        "FLRT3 and TENM2 across the synaptic gap to wire excitatory synapses in the cortex. Knocking out the cut-vertex "
        "ADGRL3 severs this synaptic complex completely (linked clinically to neurodevelopmental disorders).<br/>"
        "&#8226; <b>Static Aggregation Caveat:</b> Because PPI networks aggregate interactions across tissues and time, "
        "connected components show <i>possible</i> functional modules, not necessarily simultaneous binding in every cell.",
        bg=ACCENT_BG, border=TEAL,
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: CENTRALITY MEASURES
    # =========================================================================
    story.append(Paragraph("7. Centrality Analysis — Hubs, Bridges & Master Regulators", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "We computed four complementary centrality measures across all 11,442 proteins: <b>Degree Centrality</b> (local hubs), "
        "<b>Betweenness Centrality</b> (cross-pathway bottlenecks/bridges, Brandes k=500 pivots), <b>Closeness Centrality</b> "
        "(exact Wasserman-Faust global reach), and <b>PageRank</b> (recursive prestige connected to other influential hubs).",
        body,
    ))

    story.append(scaled_image(FIG_DIR / "fig2_top_centralities.png", max_w=content_w, max_h=335))
    story.append(Paragraph(
        "<b>Figure 3 (Centrality Leaders):</b> Top 10 human proteins ranked across Degree, Betweenness, Closeness, and PageRank. "
        "Notice how different centralities surface distinct biological roles: Ubiquitin/Ribosomal proteins dominate Degree, "
        "while NUDCD1, TP53, EGFR, and Alzheimer's Tau (MAPT) dominate Betweenness bridges, and TP53 sits #1 in Closeness.",
        caption,
    ))
    story.append(Spacer(1, 3))

    cent_rows = [
        [Paragraph("<b>Protein</b>", tbl_hdr), Paragraph("<b>Key Rank(s)</b>", tbl_hdr), Paragraph("<b>Comm.</b>", tbl_hdr), Paragraph("<b>Biological Role &amp; SNA Interpretation</b>", tbl_hdr)],
        [Paragraph("<b>TP53</b>", tbl_cell), Paragraph("#1 Closeness (0.2855)<br/>#2 Betweenness (0.0533)<br/>#5 Degree (225)", tbl_cell), Paragraph("C1", tbl_cell), Paragraph("<b>Tumor Suppressor p53 (Guardian of the Genome):</b> Geometric center of the human interactome; fastest reach to all cellular pathways.", tbl_cell)],
        [Paragraph("<b>RPS27A / UBC / UBA52</b>", tbl_cell), Paragraph("#1–#3 Degree<br/>(292, 274, 244)", tbl_cell), Paragraph("C1", tbl_cell), Paragraph("<b>Ubiquitin-Ribosomal System:</b> Universal cellular recycling tags; physically bind hundreds of proteins across nearly every process.", tbl_cell)],
        [Paragraph("<b>NUDCD1</b>", tbl_cell), Paragraph("#1 Betweenness (0.0959)<br/>#2 Closeness &amp; PageRank", tbl_cell), Paragraph("C17", tbl_cell), Paragraph("<b>Primary Pathway Bottleneck:</b> Acts as a critical cross-module bridge linking disparate clusters; strong candidate drug/disruption node.", tbl_cell)],
        [Paragraph("<b>EGFR</b>", tbl_cell), Paragraph("#3 Betweenness (0.0505)<br/>#5 PageRank / #6 Degree", tbl_cell), Paragraph("C0", tbl_cell), Paragraph("<b>Epidermal Growth Factor Receptor:</b> Master cell-growth signaling hub and primary targeted-therapy receptor in lung/colon cancers.", tbl_cell)],
        [Paragraph("<b>MAPT</b>", tbl_cell), Paragraph("#4 Betweenness (0.0425)<br/>#5 Closeness (0.2753)", tbl_cell), Paragraph("C0", tbl_cell), Paragraph("<b>Microtubule-Associated Protein Tau:</b> Critical neuronal structural bridge; misfolding causes Alzheimer's disease &amp; frontotemporal dementia.", tbl_cell)],
        [Paragraph("<b>GNB1 / GNAI1</b>", tbl_cell), Paragraph("#1 &amp; #3 PageRank<br/>(0.00217, 0.00161)", tbl_cell), Paragraph("C7", tbl_cell), Paragraph("<b>G-Protein Signal Subunits:</b> Prestigious signal-transduction switches linked to hundreds of high-value membrane receptors.", tbl_cell)],
    ]
    story.append(styled_table(cent_rows, [75, 112, 46, content_w - 233]))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: COMMUNITY DETECTION & MODULARITY
    # =========================================================================
    story.append(Paragraph("8. Community Detection (Louvain) & Modularity Analysis", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "While connected components separate small isolated complexes from the 10,196-node Giant Component, uncovering "
        "functional biological departments <i>inside</i> the Giant Component requires community detection. Applying the "
        "<b>Louvain Modularity Optimization Algorithm</b> (<font name='Courier'>seed=42</font>) partitioned the network "
        "into <b>495 distinct communities</b> with an exceptionally high modularity score of <b>Q = 0.8146</b>.",
        body,
    ))
    story.append(make_callout(
        "<b>Modularity Quality Benchmark (Q = 0.8146):</b> In network science (Newman &amp; Girvan), real-world networks with "
        "meaningful community structure typically exhibit Q between 0.30 and 0.70. Achieving <b>Q = 0.8146</b> proves that "
        "physical interactions inside human cells are overwhelmingly modular—proteins interact densely inside specialized "
        "molecular machines and sparsely across distinct biological systems."
    ))
    story.append(Spacer(1, 8))

    story.append(scaled_image(FIG_DIR / "fig3_community_sizes.png", max_w=content_w, max_h=225))
    story.append(Paragraph(
        "<b>Figure 4 (Louvain Community Size Distribution):</b> Protein counts across the 15 largest Louvain communities "
        "(C0 through C14), ordered by size. Together, the top 15 communities capture 6,795 proteins (59.4% of the entire "
        "human physical interactome), while the remaining tail captures smaller specialized complexes.",
        caption,
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("8.1 Top 5 Largest Biological Communities Discovered Purely from Topology", h2))
    comm_rows = [
        [Paragraph("<b>ID</b>", tbl_hdr), Paragraph("<b>Size</b>", tbl_hdr), Paragraph("<b>Top Hub Proteins</b>", tbl_hdr), Paragraph("<b>Identified Biological Machinery / Pathway</b>", tbl_hdr)],
        [Paragraph("<b>C0</b>", tbl_cell), Paragraph("1,068", tbl_cell), Paragraph("EGFR, GRB2, MAPT, COPS5, DYNLL1", tbl_cell), Paragraph("<b>Growth-Factor Signaling &amp; Neuronal Cytoskeleton:</b> Cell proliferation receptors and microtubule transport.", tbl_cell)],
        [Paragraph("<b>C1</b>", tbl_cell), Paragraph("771", tbl_cell), Paragraph("RPS27A, UBC, UBA52, TP53, H4C6", tbl_cell), Paragraph("<b>Ubiquitin-Proteasome, DNA Repair &amp; Chromatin Core:</b> Protein recycling, histone packaging, and tumor suppression.", tbl_cell)],
        [Paragraph("<b>C2</b>", tbl_cell), Paragraph("634", tbl_cell), Paragraph("TRAF6, TRAF2, SQSTM1, BIRC2, BTRC", tbl_cell), Paragraph("<b>Innate Immunity &amp; Inflammation (NF-kB):</b> Cytokine signaling, autophagy, and programmed cell death.", tbl_cell)],
        [Paragraph("<b>C3</b>", tbl_cell), Paragraph("554", tbl_cell), Paragraph("HDAC1, ACTB, ACTG1, RBBP4, HDAC2", tbl_cell), Paragraph("<b>Epigenetic Regulation &amp; Actin Cytoskeleton:</b> Histone deacetylase transcriptional silencing and cell structure.", tbl_cell)],
        [Paragraph("<b>C4</b>", tbl_cell), Paragraph("501", tbl_cell), Paragraph("DCTN1, AP2B1, CAPZB, RAB7A, AP2M1", tbl_cell), Paragraph("<b>Intracellular Vesicle Trafficking:</b> Endocytosis, cargo transport along microtubules, and membrane sorting.", tbl_cell)],
    ]
    story.append(styled_table(comm_rows, [32, 42, 165, content_w - 239]))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: CYTOSCAPE VISUALIZATION & BIOLOGICAL MACHINE IDENTIFICATION
    # =========================================================================
    story.append(Paragraph("9. Cytoscape Core Interactome Visualization", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "Rendering all 70,797 edges simultaneously in a 2D GUI creates an unreadable visual hairball. Following network "
        "visualization best practices, all mathematical metrics were computed on the full 11,442-node graph, and we "
        "exported the <b>Top-300 Core Hub Subnetwork</b> (<font name='Courier'>top300_core_ppi.graphml</font>, 300 nodes, "
        "6,896 edges) into <b>Cytoscape</b> with embedded Louvain <font name='Courier'>community_id</font> and "
        "<font name='Courier'>degree</font> attributes. Styling used Prefuse Force-Directed Layout, Discrete Rainbow color "
        "mapping by community, Continuous node sizing by degree, and 60/255 edge transparency.",
        body,
    ))
    story.append(Spacer(1, 4))

    story.append(scaled_image(cyto_cropped, max_w=content_w, max_h=345))
    story.append(Paragraph(
        "<b>Figure 5 (Cytoscape Visualization — Top 300 Core Hubs):</b> Force-directed layout of the human core physical "
        "interactome colored by Louvain Community ID (Q = 0.8146) and sized by node degree. Purely from graph topology, "
        "distinct cellular molecular machines spontaneously separate into tightly bound color clusters.",
        caption,
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("9.1 Visual Identification of Seven Human Cellular Machines", h2))
    vis_rows = [
        [Paragraph("<b>Cluster Color &amp; Location</b>", tbl_hdr), Paragraph("<b>Visible Landmark Proteins</b>", tbl_hdr), Paragraph("<b>Biological Molecular Machine</b>", tbl_hdr)],
        [Paragraph("<b>Orange</b> (Top Center)", tbl_cell), Paragraph("H2A/H2B/H3/H4, UBC, RPS27A, PCNA", tbl_cell), Paragraph("<b>Chromatin, Histone Nucleosome &amp; Ubiquitin Core</b>", tbl_cell)],
        [Paragraph("<b>Mint-Teal</b> (Middle Right)", tbl_cell), Paragraph("RPL9, RPL15, RPS6, RPL22, RPL27, NPM1", tbl_cell), Paragraph("<b>Cytosolic Ribosome</b> (cell's protein synthesis factory)", tbl_cell)],
        [Paragraph("<b>Purple</b> (Upper Right Island)", tbl_cell), Paragraph("MRPS30, MRPL42, MRPL52, NDUFAB1, NDUFA13", tbl_cell), Paragraph("<b>Mitochondrial Ribosome &amp; Respiratory Chain</b>", tbl_cell)],
        [Paragraph("<b>Lime-Green</b> (Bottom)", tbl_cell), Paragraph("SF3B1, SF3B3, SNRNP200, PRPF31, SNIP1", tbl_cell), Paragraph("<b>The Spliceosome</b> (pre-mRNA splicing machinery)", tbl_cell)],
        [Paragraph("<b>Red-Orange</b> (Mid-Left)", tbl_cell), Paragraph("EGFR, GRB2, MAPT, PIK3R1, CBL, COPS5", tbl_cell), Paragraph("<b>Cancer Growth-Factor Signaling &amp; Tau Pathway</b>", tbl_cell)],
        [Paragraph("<b>Bright-Green</b> (Lower-Left)", tbl_cell), Paragraph("CCT2–CCT7, TCP1, HSP90AB1, PPP2CA", tbl_cell), Paragraph("<b>TRiC/CCT Chaperonin Complex</b> (3D protein folding)", tbl_cell)],
        [Paragraph("<b>Blue</b> (Central Core)", tbl_cell), Paragraph("POLR2A, POLR2E, TAF4–TAF9, GTF2B, MED1", tbl_cell), Paragraph("<b>RNA Polymerase II Transcription Initiation Complex</b>", tbl_cell)],
    ]
    story.append(styled_table(vis_rows, [120, 175, content_w - 295]))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: PART B FEATURE HANDOFF CONTRACT & CONCLUSION
    # =========================================================================
    story.append(Paragraph("10. Part B Handoff Contract: Exported Feature Matrix for ML", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "To directly support Part B (<i>Machine Learning: Before vs. After SNA</i>), our Part A pipeline exported "
        "<b><font name='Courier'>output/node_features_for_ml.csv</font></b> (11,442 rows x 12 columns) alongside the "
        "cleaned edge list <b><font name='Courier'>data/clean_human_ppi.csv</font></b>. Every protein record cleanly "
        "separates non-network baseline features from engineered SNA features:",
        body,
    ))

    schema_rows = [
        [Paragraph("<b>Column Name</b>", tbl_hdr), Paragraph("<b>Feature Set</b>", tbl_hdr), Paragraph("<b>Data Type</b>", tbl_hdr), Paragraph("<b>Description &amp; Predictive Signal</b>", tbl_hdr)],
        [Paragraph("<font name='Courier'>gene_name</font>", tbl_cell), Paragraph("Identifier", tbl_cell), Paragraph("string", tbl_cell), Paragraph("Unique HGNC human gene symbol (join key).", tbl_cell)],
        [Paragraph("<font name='Courier'>protein_size</font>", tbl_cell), Paragraph("<b>Before SNA</b>", tbl_cell), Paragraph("int", tbl_cell), Paragraph("Amino acid sequence length (non-network baseline attribute).", tbl_cell)],
        [Paragraph("<font name='Courier'>description</font>", tbl_cell), Paragraph("<b>Before SNA</b>", tbl_cell), Paragraph("string", tbl_cell), Paragraph("Biological annotation text (for TF-IDF / label extraction).", tbl_cell)],
        [Paragraph("<font name='Courier'>degree</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("int", tbl_cell), Paragraph("Direct physical binding partner count (hubness).", tbl_cell)],
        [Paragraph("<font name='Courier'>degree_centrality</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("float", tbl_cell), Paragraph("Normalized degree k_i / (N - 1).", tbl_cell)],
        [Paragraph("<font name='Courier'>betweenness</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("float", tbl_cell), Paragraph("Cross-pathway bottleneck score (Brandes k=500).", tbl_cell)],
        [Paragraph("<font name='Courier'>closeness</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("float", tbl_cell), Paragraph("Exact Wasserman-Faust normalized global reach.", tbl_cell)],
        [Paragraph("<font name='Courier'>pagerank</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("float", tbl_cell), Paragraph("Recursive importance via prestigious neighbors.", tbl_cell)],
        [Paragraph("<font name='Courier'>clustering_coeff</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("float", tbl_cell), Paragraph("Local triadic density C_i in [0, 1] (complex membership).", tbl_cell)],
        [Paragraph("<font name='Courier'>community_id</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("int", tbl_cell), Paragraph("Louvain functional cluster ID (0 = largest; Q = 0.8146).", tbl_cell)],
        [Paragraph("<font name='Courier'>in_giant_component</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("int (0/1)", tbl_cell), Paragraph("Indicates membership in the 10,196-node cellular core.", tbl_cell)],
        [Paragraph("<font name='Courier'>is_articulation_point</font>", tbl_cell), Paragraph("<b>After SNA</b>", tbl_cell), Paragraph("int (0/1)", tbl_cell), Paragraph("Indicates single-point-of-failure structural cut-vertex.", tbl_cell)],
    ]
    story.append(styled_table(schema_rows, [128, 72, 54, content_w - 254]))
    story.append(Spacer(1, 8))

    story.append(make_callout(
        "<b>Critical Data-Leakage Safeguard for Part B (Project Rule B4):</b><br/>"
        "&#8226; <b>For Node Classification</b> (e.g., predicting essential/cancer proteins or biological classes): "
        "Part B can directly compare baseline features (<font name='Courier'>protein_size</font>, annotation keywords) "
        "against Baseline + Part A SNA features using identical train/test splits (or k-fold CV).<br/>"
        "&#8226; <b>For Link Prediction</b> (predicting hidden protein interactions): To strictly prevent data leakage, "
        "Part B must first split <font name='Courier'>clean_human_ppi.csv</font> into train/test edges, <b>remove all "
        "test edges from the graph</b>, and compute node/pair features (Common Neighbors, Jaccard, Adamic-Adar, "
        "Preferential Attachment, PageRank) exclusively on the training graph.",
        bg=WARN_BG, border=WARN_BORDER,
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("11. Part A Summary &amp; Key Conclusions", h1))
    story.append(HRFlowable(width="100%", thickness=0.7, color=TEAL, spaceAfter=5))
    story.append(Paragraph(
        "1. <b>Scale-Free &amp; Ultra-Small Architecture:</b> The Human Physical Interactome (11,442 proteins, 70,797 links) "
        "strictly obeys a power-law degree distribution (gamma = 2.04, R² = 0.915) and exhibits massive Small-World "
        "clustering (C = 0.4692, 351x higher than random) alongside short signaling paths (L = 4.98 hops, Diameter = 16).",
        bullet,
    ))
    story.append(Paragraph(
        "2. <b>Centrality Surfaces Master Disease Regulators:</b> Pure graph topology automatically elevates clinically "
        "critical human proteins—placing tumor suppressor <b>TP53</b> at #1 in Closeness, Ubiquitin regulators "
        "(<b>RPS27A, UBC</b>) at #1–#2 in Degree, and cancer/neurodegenerative bottlenecks (<b>NUDCD1, EGFR, MAPT</b>) "
        "at the top of Betweenness Centrality.",
        bullet,
    ))
    story.append(Paragraph(
        "3. <b>Modularity Reconstructs Cellular Biology:</b> Louvain clustering achieved <b>Q = 0.8146</b> across 495 "
        "communities and visually separated seven real molecular machines—including the Ribosome, Spliceosome, "
        "Chromatin/Histone Core, Chaperonin CCT Complex, and RNA Polymerase II—providing a rich relational foundation "
        "for Part B Machine Learning.",
        bullet,
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {OUT_PDF}")


if __name__ == "__main__":
    build_report()
