"""
Nexus Research Platform — Workflow Graph Component
Plotly-based directed-graph visualisation of the agent data flow.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Any


# ── graph topology ───────────────────────────────────────────────────
_NODES = [
    {"id": "planner",    "label": "📋 Planner",    "x": 0, "y": 2},
    {"id": "researcher", "label": "🔎 Researcher", "x": 1, "y": 3},
    {"id": "analyst",    "label": "📊 Analyst",    "x": 2, "y": 2},
    {"id": "writer",     "label": "✍️ Writer",     "x": 3, "y": 3},
    {"id": "critic",     "label": "🧪 Critic",     "x": 4, "y": 2},
]

_EDGES = [
    ("planner", "researcher"),
    ("researcher", "analyst"),
    ("analyst", "writer"),
    ("writer", "critic"),
    ("critic", "writer"),       # revision loop
]


def _status_color(status: str) -> str:
    return {
        "pending":   "#444",
        "active":    "#6C63FF",
        "completed": "#00E676",
        "failed":    "#FF5252",
    }.get(status, "#444")


def _status_size(status: str) -> int:
    return {"active": 52, "completed": 44, "failed": 44}.get(status, 38)


def render_workflow_graph(status_data: dict) -> None:
    """
    Render an interactive Plotly directed graph of the agent workflow.

    Expected *status_data* shape::

        {
            "agents": {
                "planner":    {"status": "completed", ...},
                "researcher": {"status": "active", ...},
                ...
            }
        }
    """

    agents_info: dict = status_data.get("agents", {})

    st.markdown(
        "<p style='font-family:Inter,sans-serif;font-weight:700;"
        "font-size:1.1rem;color:#E0E0E0;margin-bottom:0.5rem;'>"
        "🔀 Workflow Graph</p>",
        unsafe_allow_html=True,
    )

    # ── build edge traces ───────────────────────────────────────────
    node_map = {n["id"]: n for n in _NODES}

    edge_traces = []
    annotations = []

    for src_id, dst_id in _EDGES:
        src = node_map[src_id]
        dst = node_map[dst_id]

        src_status = agents_info.get(src_id, {}).get("status", "pending")
        dst_status = agents_info.get(dst_id, {}).get("status", "pending")

        # highlight edge if source is completed or active
        is_hot = src_status in ("completed", "active")
        is_revision = (src_id == "critic" and dst_id == "writer")

        edge_color = (
            "#FF9800" if is_revision and is_hot
            else "#6C63FF" if is_hot
            else "rgba(255,255,255,0.08)"
        )
        edge_width = 3 if is_hot else 1.5
        dash = "dot" if is_revision else None

        # curved revision loop
        if is_revision:
            mid_x = (src["x"] + dst["x"]) / 2
            mid_y = max(src["y"], dst["y"]) + 1.2
            x_pts = [src["x"], mid_x, dst["x"]]
            y_pts = [src["y"], mid_y, dst["y"]]
        else:
            x_pts = [src["x"], dst["x"]]
            y_pts = [src["y"], dst["y"]]

        edge_traces.append(
            go.Scatter(
                x=x_pts,
                y=y_pts,
                mode="lines",
                line=dict(color=edge_color, width=edge_width, dash=dash),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # arrow annotation
        annotations.append(
            dict(
                ax=x_pts[-2],
                ay=y_pts[-2],
                x=dst["x"],
                y=dst["y"],
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=1.5,
                arrowwidth=edge_width,
                arrowcolor=edge_color,
                opacity=0.7 if is_hot else 0.3,
            )
        )

    # ── build node trace ────────────────────────────────────────────
    node_x = [n["x"] for n in _NODES]
    node_y = [n["y"] for n in _NODES]
    node_colors = [_status_color(agents_info.get(n["id"], {}).get("status", "pending")) for n in _NODES]
    node_sizes = [_status_size(agents_info.get(n["id"], {}).get("status", "pending")) for n in _NODES]
    node_labels = [n["label"] for n in _NODES]

    hover_texts = []
    for n in _NODES:
        info = agents_info.get(n["id"], {})
        status = info.get("status", "pending")
        tokens = info.get("tokens", 0)
        latency = info.get("latency_ms", 0)
        hover_texts.append(
            f"<b>{n['label']}</b><br>"
            f"Status: {status.upper()}<br>"
            f"Tokens: {tokens:,}<br>"
            f"Latency: {latency / 1000:.1f}s"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="rgba(255,255,255,0.15)"),
            opacity=0.95,
        ),
        text=node_labels,
        textposition="bottom center",
        textfont=dict(family="Inter, sans-serif", size=12, color="#E0E0E0"),
        hovertext=hover_texts,
        hoverinfo="text",
        showlegend=False,
    )

    # ── assemble figure ─────────────────────────────────────────────
    fig = go.Figure(data=[*edge_traces, node_trace])

    fig.update_layout(
        height=340,
        margin=dict(l=20, r=20, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[-0.5, 4.5],
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[0.5, 4.5],
        ),
        annotations=annotations,
        hoverlabel=dict(
            bgcolor="#1A1F2E",
            bordercolor="#6C63FF",
            font=dict(family="Inter, sans-serif", size=12, color="#E0E0E0"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── revision loop indicator ─────────────────────────────────────
    revision_count = status_data.get("revision_count", 0)
    if revision_count > 0:
        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 0.9rem;
                background: rgba(255,152,0,0.08);
                border: 1px solid rgba(255,152,0,0.25);
                border-radius: 10px;
                margin-top: -0.5rem;
                margin-bottom: 1rem;
            ">
                <span style="font-size:1.1rem;">🔄</span>
                <span style="
                    font-family: 'Inter', sans-serif;
                    font-size: 0.8rem;
                    color: #FF9800;
                    font-weight: 600;
                ">Revision Loop × {revision_count}</span>
                <span style="
                    font-family: 'Inter', sans-serif;
                    font-size: 0.7rem;
                    color: rgba(255,152,0,0.5);
                ">Critic sent the report back to Writer for refinement</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
