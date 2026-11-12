"""
Nexus Research Platform — Header Component
Renders the retro arcade title screen with connection status.
"""
import streamlit as st

from retro_ui import arcade_hero


def render_header(connected: bool = True) -> None:
    """Render the arcade title screen with a live status chip."""
    color = "#39FF14" if connected else "#FF3355"
    text = "PLAYER 1 READY" if connected else "NO SIGNAL"
    status = (
        f'<span class="hud-chip" style="color:{color};border-color:{color}">'
        f'<span class="{"blink" if connected else ""}">&#9632;</span> {text}</span>'
    )
    arcade_hero(
        title="NEXUS",
        subtitle="MULTI-AGENT RESEARCH QUEST",
        tagline="Assemble a party of five AI agents. They plan, scout, analyse, write and "
                "battle the Critic until your report is cited and ready.",
        status_html=status,
        stickers=("rocket", "coin", "heart", "star", "joystick"),
    )
