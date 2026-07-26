"""
Nexus Research Platform — Header Component
Renders the animated gradient hero header with connection status.
"""

import streamlit as st


def render_header(connected: bool = True) -> None:
    """Render the premium hero header with live status indicator."""

    status_color = "#00E676" if connected else "#FF5252"
    status_text = "Online" if connected else "Offline"
    status_pulse = "pulse-green" if connected else ""

    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

            .nexus-header-wrap {{
                position: relative;
                padding: 2.5rem 2rem 1.8rem 2rem;
                margin: -1rem -1rem 1.5rem -1rem;
                background: linear-gradient(
                    135deg,
                    rgba(108, 99, 255, 0.12) 0%,
                    rgba(30, 33, 48, 0.95) 40%,
                    rgba(14, 17, 23, 0.98) 100%
                );
                border-bottom: 1px solid rgba(108, 99, 255, 0.2);
                overflow: hidden;
            }}

            .nexus-header-wrap::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(
                    circle at 20% 50%,
                    rgba(108, 99, 255, 0.06) 0%,
                    transparent 50%
                ),
                radial-gradient(
                    circle at 80% 20%,
                    rgba(99, 179, 255, 0.04) 0%,
                    transparent 50%
                );
                animation: header-drift 20s ease-in-out infinite alternate;
            }}

            @keyframes header-drift {{
                0%   {{ transform: translate(0, 0) rotate(0deg); }}
                100% {{ transform: translate(-20px, 10px) rotate(2deg); }}
            }}

            .nexus-header-content {{
                position: relative;
                z-index: 1;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 1rem;
            }}

            .nexus-title-block {{
                display: flex;
                flex-direction: column;
                gap: 0.2rem;
            }}

            .nexus-title {{
                font-family: 'Inter', sans-serif;
                font-weight: 900;
                font-size: 2.8rem;
                letter-spacing: 6px;
                background: linear-gradient(
                    135deg,
                    #6C63FF 0%,
                    #8B83FF 25%,
                    #63B3FF 50%,
                    #6C63FF 75%,
                    #A78BFA 100%
                );
                background-size: 300% 300%;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                animation: gradient-shift 8s ease infinite;
                margin: 0;
                line-height: 1.1;
            }}

            @keyframes gradient-shift {{
                0%   {{ background-position: 0% 50%; }}
                50%  {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}

            .nexus-subtitle {{
                font-family: 'Inter', sans-serif;
                font-weight: 400;
                font-size: 0.95rem;
                color: rgba(224, 224, 224, 0.6);
                letter-spacing: 3px;
                text-transform: uppercase;
                margin: 0;
            }}

            .nexus-status-badge {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.45rem 1.1rem;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 999px;
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
            }}

            .status-dot {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: {status_color};
                box-shadow: 0 0 6px {status_color}80;
            }}

            .status-dot.pulse-green {{
                animation: dot-pulse 2s ease-in-out infinite;
            }}

            @keyframes dot-pulse {{
                0%, 100% {{ opacity: 1; box-shadow: 0 0 6px {status_color}80; }}
                50%      {{ opacity: 0.6; box-shadow: 0 0 14px {status_color}CC; }}
            }}

            .status-label {{
                font-family: 'Inter', sans-serif;
                font-size: 0.75rem;
                font-weight: 600;
                color: {status_color};
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }}

            .nexus-tagline {{
                position: relative;
                z-index: 1;
                font-family: 'Inter', sans-serif;
                font-size: 0.82rem;
                font-weight: 300;
                color: rgba(224, 224, 224, 0.35);
                margin-top: 0.6rem;
                letter-spacing: 0.5px;
            }}
        </style>

        <div class="nexus-header-wrap">
            <div class="nexus-header-content">
                <div class="nexus-title-block">
                    <h1 class="nexus-title">NEXUS</h1>
                    <p class="nexus-subtitle">Multi-Agent Research Platform</p>
                </div>
                <div class="nexus-status-badge">
                    <span class="status-dot {status_pulse}"></span>
                    <span class="status-label">{status_text}</span>
                </div>
            </div>
            <p class="nexus-tagline">
                Orchestrate autonomous AI agents to research, analyse, and synthesise any topic.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
