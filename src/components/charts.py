"""
Charts Module — All Plotly visualizations for the platform.
Dark-themed, interactive, branded charts.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional, Any
import streamlit as st

# ── Shared Plotly theme ───────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        bgcolor="rgba(255,255,255,0.04)",
        bordercolor="rgba(255,255,255,0.08)",
        borderwidth=1,
    ),
    hoverlabel=dict(
        bgcolor="rgba(15,15,30,0.95)",
        font_color="#f1f5f9",
        bordercolor="#6366f1",
    ),
)

COLORS = {
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "accent": "#06b6d4",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "gradient": ["#6366f1", "#8b5cf6", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444"],
}


def _apply_layout(fig: go.Figure, title: str = "", height: int = 350) -> go.Figure:
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text=title, font=dict(color="#f1f5f9", size=14, family="Inter"), x=0.01),
        height=height,
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)", showgrid=True, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", showgrid=True, zeroline=False)
    return fig


# ─────────────────────────────────────────────
# Skill Radar Chart
# ─────────────────────────────────────────────

def radar_chart(scores: Dict[str, float], title: str = "Skill Distribution") -> go.Figure:
    categories = list(scores.keys())
    values = list(scores.values())
    values.append(values[0])  # close the polygon
    categories.append(categories[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories,
        fill="toself",
        fillcolor="rgba(99,102,241,0.15)",
        line=dict(color="#6366f1", width=2),
        marker=dict(color="#6366f1", size=6),
        name="Your Scores",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[80] * len(categories), theta=categories,
        fill="toself",
        fillcolor="rgba(139,92,246,0.05)",
        line=dict(color="#8b5cf6", width=1, dash="dot"),
        name="Target",
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.08)", color="#64748b"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)", color="#94a3b8"),
        ),
        title=dict(text=title, font=dict(color="#f1f5f9", size=14), x=0.01),
        height=380,
        showlegend=True,
    )
    return fig


# ─────────────────────────────────────────────
# Performance Line Chart
# ─────────────────────────────────────────────

def performance_line_chart(history: List[Dict], title: str = "Performance Trend") -> go.Figure:
    if not history:
        return go.Figure()

    df = pd.DataFrame(history)
    df["metric_date"] = pd.to_datetime(df["metric_date"])

    fig = go.Figure()
    score_cols = {
        "overall_score": ("#6366f1", "Overall"),
        "technical_score": ("#06b6d4", "Technical"),
        "hr_score": ("#8b5cf6", "HR"),
        "coding_score": ("#22c55e", "Coding"),
        "communication_score": ("#f59e0b", "Communication"),
    }
    for col, (color, name) in score_cols.items():
        if col in df.columns and df[col].any():
            fig.add_trace(go.Scatter(
                x=df["metric_date"], y=df[col],
                name=name, line=dict(color=color, width=2.5),
                mode="lines+markers",
                marker=dict(size=6, color=color, line=dict(color="#0a0a0f", width=1)),
                hovertemplate=f"<b>{name}</b>: %{{y:.1f}}<br>Date: %{{x|%b %d}}<extra></extra>",
            ))

    fig = _apply_layout(fig, title, height=380)
    fig.update_xaxes(tickformat="%b %d")
    return fig


# ─────────────────────────────────────────────
# Score Distribution Bar Chart
# ─────────────────────────────────────────────

def score_bar_chart(scores: Dict[str, float], title: str = "Score Breakdown") -> go.Figure:
    labels = list(scores.keys())
    values = list(scores.values())
    bar_colors = ["#22c55e" if v >= 80 else "#f59e0b" if v >= 60 else "#ef4444" for v in values]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:.0f}" for v in values],
        textposition="outside",
        textfont=dict(color="#f1f5f9", size=12),
        hovertemplate="<b>%{x}</b>: %{y:.1f}/100<extra></extra>",
    ))
    fig = _apply_layout(fig, title, height=320)
    fig.update_yaxes(range=[0, 110])
    return fig


# ─────────────────────────────────────────────
# Interviews Heatmap (calendar-like activity)
# ─────────────────────────────────────────────

def activity_heatmap(history: List[Dict], title: str = "Practice Activity") -> go.Figure:
    if not history:
        return go.Figure()
    df = pd.DataFrame(history)
    df["metric_date"] = pd.to_datetime(df["metric_date"])
    df["week"] = df["metric_date"].dt.isocalendar().week
    df["dow"] = df["metric_date"].dt.dayofweek
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    fig = go.Figure(go.Heatmap(
        z=df["interviews_completed"].values,
        x=df["week"].values,
        y=[day_names[d] for d in df["dow"].values],
        colorscale=[[0, "rgba(99,102,241,0.05)"], [0.5, "#6366f1"], [1, "#4f46e5"]],
        hovertemplate="Week %{x}, %{y}: %{z} interviews<extra></extra>",
        showscale=False,
    ))
    fig = _apply_layout(fig, title, height=200)
    return fig


# ─────────────────────────────────────────────
# Pie Chart — Interview type distribution
# ─────────────────────────────────────────────

def pie_chart(labels: List[str], values: List[float], title: str = "") -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=COLORS["gradient"], line=dict(color="#0a0a0f", width=2)),
        hole=0.5,
        textinfo="label+percent",
        textfont=dict(color="#f1f5f9"),
        hovertemplate="<b>%{label}</b>: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text=title, font=dict(color="#f1f5f9", size=14), x=0.01),
        height=300,
        showlegend=True,
    )
    return fig


# ─────────────────────────────────────────────
# Weekly Progress Grouped Bar
# ─────────────────────────────────────────────

def weekly_progress_chart(history: List[Dict]) -> go.Figure:
    if not history:
        return go.Figure()
    df = pd.DataFrame(history)
    df["metric_date"] = pd.to_datetime(df["metric_date"])

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Weekly Interviews", "Avg Scores"),
        shared_yaxes=False,
    )
    # Interviews
    fig.add_trace(go.Bar(
        x=df["metric_date"], y=df.get("interviews_completed", []),
        marker_color="#6366f1", name="Interviews", showlegend=False,
    ), row=1, col=1)
    # Scores
    for col, color in [("technical_score", "#06b6d4"), ("hr_score", "#8b5cf6"), ("coding_score", "#22c55e")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["metric_date"], y=df[col],
                mode="lines+markers", name=col.replace("_score", "").title(),
                line=dict(color=color, width=2),
            ), row=1, col=2)

    fig.update_layout(**PLOT_LAYOUT, height=320, title=dict(text="Weekly Progress", font=dict(color="#f1f5f9", size=14)))
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
    return fig


# ─────────────────────────────────────────────
# Readiness Gauge
# ─────────────────────────────────────────────

def readiness_gauge(score: float, title: str = "Interview Readiness") -> go.Figure:
    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"color": "#f1f5f9", "size": 14}},
        delta={"reference": 70, "increasing": {"color": "#22c55e"}, "decreasing": {"color": "#ef4444"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#64748b"},
            "bar": {"color": color},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(255,255,255,0.1)",
            "steps": [
                {"range": [0, 50], "color": "rgba(239,68,68,0.1)"},
                {"range": [50, 70], "color": "rgba(245,158,11,0.1)"},
                {"range": [70, 100], "color": "rgba(34,197,94,0.1)"},
            ],
            "threshold": {"line": {"color": "#6366f1", "width": 4}, "thickness": 0.8, "value": 80},
        },
        number={"font": {"color": color, "size": 40, "family": "Inter"}},
    ))
    fig.update_layout(**PLOT_LAYOUT, height=280)
    return fig


# ─────────────────────────────────────────────
# Leaderboard Bar Chart
# ─────────────────────────────────────────────

def leaderboard_chart(data: List[Dict]) -> go.Figure:
    if not data:
        return go.Figure()
    names = [d.get("profiles", {}).get("full_name", "User")[:15] for d in data[:10]]
    xps = [d.get("xp_gained", 0) for d in data[:10]]

    fig = go.Figure(go.Bar(
        y=names[::-1], x=xps[::-1],
        orientation="h",
        marker=dict(
            color=xps[::-1],
            colorscale=[[0, "#4f46e5"], [1, "#06b6d4"]],
            line=dict(width=0),
        ),
        text=[f"⚡ {x:,} XP" for x in xps[::-1]],
        textposition="inside",
        textfont=dict(color="white", size=11),
        hovertemplate="<b>%{y}</b>: %{x:,} XP<extra></extra>",
    ))
    fig = _apply_layout(fig, "🏆 Weekly XP Leaderboard", height=350)
    fig.update_xaxes(title="XP Points")
    return fig
