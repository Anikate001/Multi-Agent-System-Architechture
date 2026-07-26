"""
Nexus Research Platform — Analytics Component
Plotly-powered dashboards for token usage, cost, latency, and quality metrics.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Any


# ── shared Plotly layout defaults ────────────────────────────────────
_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="rgba(224,224,224,0.6)", size=11),
    margin=dict(l=30, r=15, t=30, b=30),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(255,255,255,0.06)",
        font=dict(size=10, color="rgba(224,224,224,0.5)"),
    ),
    hoverlabel=dict(
        bgcolor="#1A1F2E",
        bordercolor="#6C63FF",
        font=dict(family="Inter, sans-serif", size=11, color="#E0E0E0"),
    ),
)

_AGENT_COLORS = {
    "planner":    "#6C63FF",
    "researcher": "#63B3FF",
    "analyst":    "#FF9800",
    "writer":     "#00E676",
    "critic":     "#A78BFA",
}


def _metric_card(label: str, value: str, icon: str, color: str) -> str:
    return f"""
    <div style="
        flex: 1;
        min-width: 120px;
        padding: 0.85rem 0.9rem;
        background: linear-gradient(135deg, {color}12 0%, {color}06 100%);
        border: 1px solid {color}25;
        border-radius: 12px;
        text-align: center;
    ">
        <div style="font-size:1.3rem;margin-bottom:0.2rem;">{icon}</div>
        <div style="
            font-family:'Inter',sans-serif; font-size:1.2rem; font-weight:800;
            color:{color};
        ">{value}</div>
        <div style="
            font-family:'Inter',sans-serif; font-size:0.65rem;
            color:rgba(224,224,224,0.4); text-transform:uppercase; letter-spacing:1px;
        ">{label}</div>
    </div>
    """


def render_analytics(metrics_data: dict) -> None:
    """
    Render the analytics dashboard sidebar.

    Expected *metrics_data* shape::

        {
            "agents": {
                "planner":    {"tokens": 1240, "latency_ms": 3200, "cost_usd": 0.012},
                "researcher": {"tokens": 4200, "latency_ms": 8400, "cost_usd": 0.042},
                ...
            },
            "total_tokens": 12400,
            "total_cost_usd": 0.124,
            "total_latency_ms": 28000,
            "revision_count": 1,
            "quality_scores": [6.2, 8.1],
        }
    """

    agents: dict = metrics_data.get("agents", {})
    total_tokens = metrics_data.get("total_tokens", 0)
    total_cost = metrics_data.get("total_cost_usd", 0.0)
    total_latency = metrics_data.get("total_latency_ms", 0)
    revision_count = metrics_data.get("revision_count", 0)
    quality_scores = metrics_data.get("quality_scores", [])

    # ── section title ───────────────────────────────────────────────
    st.markdown(
        """
        <p style="
            font-family:'Inter',sans-serif; font-weight:700; font-size:1rem;
            color:#E0E0E0; margin-bottom:0.8rem;
        ">📈 Analytics</p>
        """,
        unsafe_allow_html=True,
    )

    # ── metric cards ────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1rem;">
            {_metric_card("Tokens", f"{total_tokens:,}", "🔤", "#6C63FF")}
            {_metric_card("Cost", f"${total_cost:.3f}", "💰", "#00E676")}
        </div>
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1rem;">
            {_metric_card("Latency", f"{total_latency / 1000:.1f}s", "⏱️", "#FF9800")}
            {_metric_card("Revisions", str(revision_count), "🔄", "#A78BFA")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── token usage bar chart ───────────────────────────────────────
    if agents:
        agent_names = list(agents.keys())
        token_vals = [agents[a].get("tokens", 0) for a in agent_names]
        colors = [_AGENT_COLORS.get(a, "#6C63FF") for a in agent_names]

        fig_tokens = go.Figure(
            go.Bar(
                x=[a.capitalize() for a in agent_names],
                y=token_vals,
                marker=dict(
                    color=colors,
                    line=dict(width=0),
                    opacity=0.85,
                ),
                hovertemplate="<b>%{x}</b><br>Tokens: %{y:,}<extra></extra>",
            )
        )
        fig_tokens.update_layout(
            **_PLOTLY_LAYOUT,
            height=220,
            title=dict(text="Token Usage by Agent", font=dict(size=12)),
            xaxis=dict(showgrid=False),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                gridwidth=1,
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_tokens, use_container_width=True, config={"displayModeBar": False})

    # ── cost breakdown pie chart ────────────────────────────────────
    if agents:
        cost_vals = [agents[a].get("cost_usd", 0) for a in agent_names]

        if any(v > 0 for v in cost_vals):
            fig_cost = go.Figure(
                go.Pie(
                    labels=[a.capitalize() for a in agent_names],
                    values=cost_vals,
                    marker=dict(
                        colors=colors,
                        line=dict(color="#0E1117", width=2),
                    ),
                    hole=0.55,
                    textinfo="percent",
                    textfont=dict(size=10, color="#E0E0E0"),
                    hovertemplate="<b>%{label}</b><br>$%{value:.4f}<br>%{percent}<extra></extra>",
                )
            )
            fig_cost.update_layout(
                **_PLOTLY_LAYOUT,
                height=230,
                title=dict(text="Cost Breakdown", font=dict(size=12)),
                annotations=[
                    dict(
                        text=f"${total_cost:.3f}",
                        x=0.5, y=0.5,
                        font=dict(size=16, color="#E0E0E0", family="Inter, sans-serif"),
                        showarrow=False,
                    )
                ],
            )
            st.plotly_chart(fig_cost, use_container_width=True, config={"displayModeBar": False})

    # ── latency timeline ────────────────────────────────────────────
    if agents:
        latency_vals = [agents[a].get("latency_ms", 0) / 1000 for a in agent_names]

        fig_latency = go.Figure(
            go.Scatter(
                x=[a.capitalize() for a in agent_names],
                y=latency_vals,
                mode="lines+markers",
                line=dict(color="#6C63FF", width=2.5, shape="spline"),
                marker=dict(size=8, color=colors, line=dict(width=2, color="#0E1117")),
                fill="tozeroy",
                fillcolor="rgba(108,99,255,0.08)",
                hovertemplate="<b>%{x}</b><br>%{y:.1f}s<extra></extra>",
            )
        )
        fig_latency.update_layout(
            **_PLOTLY_LAYOUT,
            height=200,
            title=dict(text="Latency Timeline (s)", font=dict(size=12)),
            xaxis=dict(showgrid=False),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_latency, use_container_width=True, config={"displayModeBar": False})

    # ── quality score history ───────────────────────────────────────
    if quality_scores:
        iterations = list(range(1, len(quality_scores) + 1))

        fig_quality = go.Figure(
            go.Scatter(
                x=[f"Draft {i}" for i in iterations],
                y=quality_scores,
                mode="lines+markers+text",
                line=dict(color="#00E676", width=2.5, shape="spline"),
                marker=dict(
                    size=12,
                    color=["#FF5252" if s < 6 else "#FF9800" if s < 8 else "#00E676" for s in quality_scores],
                    line=dict(width=2, color="#0E1117"),
                ),
                text=[f"{s:.1f}" for s in quality_scores],
                textposition="top center",
                textfont=dict(size=10, color="#E0E0E0"),
                hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}/10<extra></extra>",
            )
        )
        fig_quality.update_layout(
            **_PLOTLY_LAYOUT,
            height=200,
            title=dict(text="Quality Score History", font=dict(size=12)),
            xaxis=dict(showgrid=False),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                range=[0, 10.5],
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_quality, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            """
            <div style="
                text-align:center; padding:1rem;
                color:rgba(224,224,224,0.25);
                font-family:'Inter',sans-serif; font-size:0.78rem;
            ">No quality scores recorded yet</div>
            """,
            unsafe_allow_html=True,
        )
