# coding: utf-8
"""
Plotly Chart Builders
=====================
Bloomberg-terminal style visualizations for VPP trading.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import List


# Professional color scheme (dark mode)
COLORS = {
    'profit': '#00D9FF',     # Cyan (buy/charge)
    'loss': '#FF4B4B',       # Red (sell/discharge)
    'price': '#FFD93D',      # Gold
    'soc': '#6BCF7F',        # Green
    'grid_limit': '#FF4B4B',  # Red danger
    'grid_safe': '#00D9FF',  # Cyan safe
    'background': '#0E1117',
    'grid_color': '#262730'
}


def create_price_chart(
    hours: List[float],
    price_gbp_kwh: List[float],
    charge_kw: List[float],
    discharge_kw: List[float],
    soc_pct: List[float]
) -> go.Figure:
    """
    Create dual-axis price and battery action chart.

    Left axis: Market price (line)
    Right axis: Battery actions (bars) + SoC (line)
    """
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )

    # Price line
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=price_gbp_kwh,
            name="Market Price",
            line=dict(color=COLORS['price'], width=2),
            hovertemplate='%{y:.3f} GBP/kWh<extra></extra>'
        ),
        secondary_y=False
    )

    # Charge bars (negative = buying)
    fig.add_trace(
        go.Bar(
            x=hours,
            y=[-c for c in charge_kw],
            name="Charging (Buy)",
            marker_color=COLORS['profit'],
            opacity=0.7,
            hovertemplate='Charge: %{y:.2f} kW<extra></extra>'
        ),
        secondary_y=True
    )

    # Discharge bars (positive = selling)
    fig.add_trace(
        go.Bar(
            x=hours,
            y=discharge_kw,
            name="Discharging (Sell)",
            marker_color=COLORS['loss'],
            opacity=0.7,
            hovertemplate='Discharge: %{y:.2f} kW<extra></extra>'
        ),
        secondary_y=True
    )

    # SoC line
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=soc_pct,
            name="Battery SoC",
            line=dict(color=COLORS['soc'], width=2, dash='dot'),
            yaxis='y3',
            hovertemplate='SoC: %{y:.1f}%<extra></extra>'
        ),
        secondary_y=True
    )

    # Layout
    fig.update_layout(
        title=dict(
            text="<b>FINANCIAL OPTIMIZATION</b> | Price Arbitrage Strategy",
            font=dict(size=16, color='white'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Hour of Day",
            showgrid=True,
            gridcolor=COLORS['grid_color'],
            color='white'
        ),
        yaxis=dict(
            title="Price (GBP/kWh)",
            showgrid=True,
            gridcolor=COLORS['grid_color'],
            color='white'
        ),
        yaxis2=dict(
            title="Battery Power (kW)",
            showgrid=False,
            color='white'
        ),
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font=dict(color='white'),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=450
    )

    return fig


def create_grid_flow_chart(
    hours: List[float],
    grid_export_kw: List[float],
    grid_limit_kw: float
) -> go.Figure:
    """
    Create grid export chart with constraint visualization.

    Shows net grid power vs. DNO limit (red line).
    """
    fig = go.Figure()

    # Actual grid flow
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=grid_export_kw,
            name="Net Grid Export",
            fill='tozeroy',
            line=dict(color=COLORS['grid_safe'], width=2),
            fillcolor='rgba(0, 217, 255, 0.2)',
            hovertemplate='Export: %{y:.2f} kW<extra></extra>'
        )
    )

    # Grid limit line
    fig.add_hline(
        y=grid_limit_kw,
        line_dash="dash",
        line_color=COLORS['grid_limit'],
        line_width=3,
        annotation_text=f"Grid Limit ({grid_limit_kw} kW)",
        annotation_position="right"
    )

    # Highlight violations
    violations = [g for g in grid_export_kw if g > grid_limit_kw]
    if violations:
        violation_hours = [h for h, g in zip(hours, grid_export_kw) if g > grid_limit_kw]
        fig.add_trace(
            go.Scatter(
                x=violation_hours,
                y=violations,
                mode='markers',
                name="VIOLATION",
                marker=dict(color=COLORS['loss'], size=12, symbol='x'),
                hovertemplate='VIOLATION: %{y:.2f} kW<extra></extra>'
            )
        )

    fig.update_layout(
        title=dict(
            text="<b>GRID CONSTRAINT ENFORCEMENT</b> | DNO G99 Compliance Check",
            font=dict(size=16, color='white'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Hour of Day",
            showgrid=True,
            gridcolor=COLORS['grid_color'],
            color='white'
        ),
        yaxis=dict(
            title="Power (kW)",
            showgrid=True,
            gridcolor=COLORS['grid_color'],
            color='white'
        ),
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font=dict(color='white'),
        hovermode='x unified',
        height=450
    )

    return fig
