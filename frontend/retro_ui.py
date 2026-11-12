"""
Retro pixel-arcade theme for Streamlit.

Neon cyberpunk palette, pixel fonts, CRT scanlines, stepped pixel borders and a small
library of hand-drawn pixel sprites rendered as crisp inline SVG. Everything here is
plain HTML/CSS, so it works on Streamlit Community Cloud with no extra packages.
"""
from __future__ import annotations

from functools import lru_cache

import streamlit as st

# ── palette ──────────────────────────────────────────────────────────
NIGHT = "#0B0420"      # page ground
PANEL = "#160A33"      # cards, sidebar
PANEL_2 = "#221047"
CYAN = "#00F0FF"
MAGENTA = "#FF2E97"
YELLOW = "#FFE600"
GREEN = "#39FF14"
ORANGE = "#FF7A00"
RED = "#FF3355"
VIOLET = "#B26BFF"
TEXT = "#F2E9FF"

# ── sprites: one character per pixel, '.' is transparent ────────────
SPRITES: dict[str, tuple[list[str], dict[str, str]]] = {
    # an original energy-drink can: silver rims, black body, neon claw marks
    "can": (
        [
            "..kkkkkk..",
            ".kssssssk.",
            ".kwssssk..",
            ".kkkkkkkk.",
            ".khddddddk",
            ".khgddgdgk",
            ".khgdgdgdk",
            ".khgdgdgdk",
            ".khgdgdgdk",
            ".khdgdgdgk",
            ".khdgdgdgk",
            ".khdgddgdk",
            ".khddddddk",
            ".khddddddk",
            ".kkkkkkkkk",
            ".kssssssk.",
            "..kkkkkk..",
        ],
        {"k": "#05020F", "s": "#C9C9D6", "w": "#FFFFFF", "d": "#141414",
         "h": "#3A3A3A", "g": GREEN},
    ),
    "heart": (
        [
            ".kk...kk.",
            "kppk.kppk",
            "kpwppppkk",
            "kpppppppk",
            "kpppppppk",
            ".kpppppk.",
            "..kpppk..",
            "...kpk...",
            "....k....",
        ],
        {"k": "#05020F", "p": MAGENTA, "w": "#FFC2E2"},
    ),
    "coin": (
        [
            "..kkkk..",
            ".kyyyyk.",
            "kyywyyyk",
            "kyyokyyk",
            "kyyokyyk",
            "kyyokyyk",
            ".kyyyyk.",
            "..kkkk..",
        ],
        {"k": "#05020F", "y": YELLOW, "w": "#FFFFFF", "o": ORANGE},
    ),
    "star": (
        [
            "....k....",
            "...kyk...",
            "...kyk...",
            "kkkkyykkk",
            "kyyyyyyyk",
            ".kyyyyyk.",
            "..kyyyk..",
            ".kyykyyk.",
            "kyk...kyk",
            "kk.....kk",
        ],
        {"k": "#05020F", "y": YELLOW},
    ),
    "rocket": (
        [
            "....k....",
            "...krk...",
            "..krrrk..",
            "..kwwwk..",
            "..kwcwk..",
            "..kwwwk..",
            ".kkwwwkk.",
            "krkwwwkrk",
            "kk.kok.kk",
            "...kyk...",
            "....k....",
        ],
        {"k": "#05020F", "r": RED, "w": "#E8E8F0", "c": CYAN, "o": ORANGE, "y": YELLOW},
    ),
    "cat": (
        [
            "k........k..",
            "kok.....kok.",
            "kook...kook.",
            "kbbbkkkwwwok",
            "kbbbbwwwwwwk",
            "kbybbwwwywwk",
            "kbkbbwwwkwwk",
            "kbbbwwpwwwwk",
            ".kbbwkwkwwk.",
            "..kkkkkkkk..",
        ],
        {"k": "#05020F", "o": ORANGE, "b": "#2B2140", "w": "#FFF4DD", "y": YELLOW,
         "p": MAGENTA},
    ),
    "joystick": (
        [
            "...kkk...",
            "..krrrk..",
            "..krwrk..",
            "..krrrk..",
            "...kkk...",
            "....k....",
            "....k....",
            ".kkkkkkk.",
            "kvvvvvcvk",
            "kvvvvvvvk",
            "kkkkkkkkk",
        ],
        {"k": "#05020F", "r": RED, "w": "#FFFFFF", "v": "#5B3FB5", "c": CYAN},
    ),
    "cabinet": (
        [
            ".kkkkkkk.",
            "kmmmmmmmk",
            "kkkkkkkkk",
            "kvkkkkkvk",
            "kvkcgckvk",
            "kvkcmckvk",
            "kvkkkkkvk",
            "kvvyvrvvk",
            "kvvvvvvvk",
            "kvvvvvvvk",
            "kkkkkkkkk",
        ],
        {"k": "#05020F", "m": MAGENTA, "v": "#5B3FB5", "c": CYAN, "g": GREEN,
         "y": YELLOW, "r": RED},
    ),
}


@lru_cache(maxsize=128)
def pixel_svg(name: str, px: int = 4, label: str | None = None) -> str:
    """Return a crisp inline SVG of a sprite, `px` screen pixels per art pixel."""
    rows, palette = SPRITES[name]
    w, h = max(len(r) for r in rows), len(rows)
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == ".":
                x += 1
                continue
            run = 1
            while x + run < len(row) and row[x + run] == ch:
                run += 1
            rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{palette[ch]}"/>')
            x += run
    a11y = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    return (
        f'<svg class="px-sprite" {a11y} width="{w * px}" height="{h * px}" '
        f'viewBox="0 0 {w} {h}" shape-rendering="crispEdges" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(rects)}</svg>'
    )


@lru_cache(maxsize=4)
def sunset_scene(rider: bool = True) -> str:
    """A pixel desert at sunset: banded sun, mesas, dunes and a lone rider."""
    W, H = 160, 44
    r = []
    sky = ["#2A0B4A", "#3E0F5C", "#5C1466", "#86196B", "#B3216A", "#D93A5E", "#F06048"]
    band = H // len(sky) + 1
    for i, c in enumerate(sky):
        r.append(f'<rect x="0" y="{i * band}" width="{W}" height="{band}" fill="{c}"/>')
    # stars
    for x, y in [(8, 3), (23, 6), (41, 2), (63, 5), (97, 3), (118, 7), (139, 2), (151, 6)]:
        r.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="#FFF4DD"/>')
    # banded sun
    cx, cy, rad = 104, 26, 13
    for y in range(cy - rad, cy + 1):
        dy = cy - y
        half = int((rad * rad - dy * dy) ** 0.5)
        if dy % 3 == 2 and dy < 9:
            continue  # the retro stripe gaps
        color = YELLOW if dy > 6 else ("#FFB000" if dy > 3 else ORANGE)
        r.append(f'<rect x="{cx - half}" y="{y}" width="{half * 2}" height="1" fill="{color}"/>')
    # mesas
    for x0, top, wid in [(12, 14, 22), (126, 10, 18), (60, 22, 10)]:
        r.append(f'<rect x="{x0}" y="{top}" width="{wid}" height="{H - top}" fill="#5A0F2E"/>')
        r.append(f'<rect x="{x0 - 2}" y="{top + 4}" width="{wid + 4}" height="{H - top}" fill="#7A1630"/>')
        r.append(f'<rect x="{x0}" y="{top}" width="{wid}" height="1" fill="{ORANGE}"/>')
    # dunes and ground
    r.append(f'<rect x="0" y="33" width="{W}" height="11" fill="#8A2A1C"/>')
    r.append(f'<rect x="0" y="36" width="{W}" height="8" fill="#5C1A14"/>')
    r.append(f'<rect x="0" y="33" width="{W}" height="1" fill="{ORANGE}"/>')
    # grid lines on the ground (synthwave nod)
    for x in range(0, W, 16):
        r.append(f'<rect x="{x}" y="37" width="1" height="7" fill="{MAGENTA}" opacity="0.45"/>')
    r.append(f'<rect x="0" y="40" width="{W}" height="1" fill="{MAGENTA}" opacity="0.35"/>')
    if rider:
        k = "#14051F"
        for x, y, w, h in [(78, 26, 2, 1), (77, 27, 4, 1), (78, 28, 2, 2), (77, 30, 3, 2),
                           (73, 31, 10, 1), (72, 32, 12, 2), (71, 31, 2, 1), (84, 30, 2, 2),
                           (85, 29, 2, 1), (73, 34, 1, 3), (75, 34, 1, 3), (80, 34, 1, 3),
                           (82, 34, 1, 3)]:
            r.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{k}"/>')
    return (
        f'<svg class="px-scene" aria-hidden="true" viewBox="0 0 {W} {H}" '
        f'preserveAspectRatio="xMidYMid slice" shape-rendering="crispEdges" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(r)}</svg>'
    )


def xp_bar(pct: float, color: str = GREEN, segments: int = 10) -> str:
    """A segmented pixel XP/HP bar."""
    pct = max(0.0, min(1.0, pct))
    filled = round(pct * segments)
    cells = "".join(
        f'<span class="xp-cell" style="background:{color if i < filled else "rgba(255,255,255,0.08)"}"></span>'
        for i in range(segments)
    )
    return f'<div class="xp-bar" role="img" aria-label="{int(pct * 100)} percent">{cells}</div>'


def energy_can_egg(where=None) -> None:
    """Sidebar easter egg: tap the can for a power-up."""
    target = where or st.sidebar
    target.markdown(
        f"""
        <details class="can-egg">
        <summary title="Psst. Tap me.">{pixel_svg("can", 5, "Energy drink can")}
        <span class="can-hint">FUEL: 99%</span></summary>
        <div class="can-pop">+1 UP &middot; ENERGY RESTORED<br/>
        <span>coded on cans, not coffee</span></div>
        </details>
        """,
        unsafe_allow_html=True,
    )


def sticker_row(names: list[str], px: int = 4) -> str:
    return '<div class="sticker-row">' + "".join(
        f'<span class="sticker">{pixel_svg(n, px)}</span>' for n in names
    ) + "</div>"


def inject_theme() -> None:
    """Global arcade CSS. Call once near the top of the app, after set_page_config."""
    st.markdown(_theme_css(), unsafe_allow_html=True)


@lru_cache(maxsize=1)
def _theme_css() -> str:
    """Built once per process; Streamlit reruns the script on every interaction."""
    return (
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');
:root {{
  --night:{NIGHT}; --panel:{PANEL}; --panel2:{PANEL_2}; --cyan:{CYAN}; --magenta:{MAGENTA};
  --yellow:{YELLOW}; --green:{GREEN}; --orange:{ORANGE}; --red:{RED}; --text:{TEXT};
  --px: 4px;
}}
html, body, [class*="css"], .stApp, .stMarkdown, .stMarkdown *, p, li, label, input, textarea, button,
[data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] * {{
  font-family: 'VT323', ui-monospace, monospace !important;
  font-size-adjust: 0.56;
}}
/* keep Streamlit's icon font intact */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-icons"] {{
  font-family: 'Material Symbols Rounded' !important; font-size-adjust: none !important;
}}
.stApp {{
  background-color: var(--night) !important;
  background-image:
    radial-gradient(rgba(255,255,255,0.9) 1px, transparent 1px),
    radial-gradient(rgba(0,240,255,0.6) 1px, transparent 1px);
  background-size: 120px 120px, 70px 70px;
  background-position: 0 0, 35px 55px;
  color: var(--text) !important;
  font-size: 1.15rem;
}}
/* CRT scanlines over everything, never blocking clicks */
.stApp::after {{
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 999990;
  background: repeating-linear-gradient(to bottom, rgba(0,0,0,0) 0, rgba(0,0,0,0) 2px,
              rgba(0,0,0,0.18) 3px, rgba(0,0,0,0) 4px);
}}
.stApp::before {{
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 999989;
  background: radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.45) 100%);
}}
h1, h2, h3, h4, .px-title, [class$="-title"], [class*="-title "] {{
  font-family: 'Press Start 2P', monospace !important;
  letter-spacing: 1px; line-height: 1.5 !important;
}}
h1 {{ font-size: 1.6rem !important; }} h2 {{ font-size: 1.15rem !important; }}
h3 {{ font-size: 0.95rem !important; }} h4 {{ font-size: 0.8rem !important; }}
[class$="-title"] {{ font-size: 0.85rem !important; font-size-adjust: none; }}
h1, h2, h3, h4, .px-title, .arcade-title, .arcade-sub, .hud-chip, .insert-coin, .agent-class {{ font-size-adjust: none !important; }}
code, pre {{ font-family: 'VT323', monospace !important; font-size: 1.1rem !important; }}

/* pixel frame: stepped corners instead of rounded ones */
.px-frame, [data-testid="stExpander"] details, [data-testid="stMetric"],
[data-testid="stForm"], [data-testid="stAlert"] {{
  border-radius: 0 !important;
  border: none !important;
  background: var(--panel) !important;
  box-shadow:
    0 calc(-1*var(--px)) 0 0 var(--cyan), 0 var(--px) 0 0 var(--cyan),
    calc(-1*var(--px)) 0 0 0 var(--cyan), var(--px) 0 0 0 var(--cyan),
    0 0 24px rgba(0,240,255,0.25) !important;
  margin: var(--px);
}}
[data-testid="stMetric"] {{ padding: 0.6rem 0.8rem; }}
[data-testid="stMetricValue"] {{ font-family: 'Press Start 2P' !important; color: var(--yellow) !important; font-size: 1.1rem !important; }}
[data-testid="stMetricLabel"] p {{ text-transform: uppercase; color: var(--cyan) !important; letter-spacing: 2px; }}

/* buttons: chunky arcade keys that press down */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {{
  font-family: 'Press Start 2P', monospace !important; font-size: 0.7rem !important;
  text-transform: uppercase; letter-spacing: 1px;
  border-radius: 0 !important; border: none !important;
  color: var(--night) !important; background: var(--cyan) !important;
  box-shadow: 0 var(--px) 0 0 #007C85, inset calc(-1*var(--px)) calc(-1*var(--px)) 0 0 rgba(0,0,0,0.25) !important;
  transition: transform 60ms steps(1), box-shadow 60ms steps(1);
  min-height: 46px; padding: 0.7rem 1rem !important;
}}
.stButton > button p, .stDownloadButton > button p {{ font-family: 'Press Start 2P' !important; font-size: 0.7rem !important; }}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {{
  background: var(--magenta) !important; color: #fff !important;
  box-shadow: 0 var(--px) 0 0 #8A0E4D, 0 0 18px rgba(255,46,151,0.55) !important;
}}
.stButton > button:hover {{ filter: brightness(1.12); }}
.stButton > button:active {{ transform: translateY(var(--px)); box-shadow: 0 0 0 0 #000 !important; }}
.stButton > button:focus-visible {{ outline: 3px dashed var(--yellow) !important; outline-offset: 4px; }}

/* inputs */
textarea, input[type="text"], input[type="password"], input[type="number"],
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {{
  border-radius: 0 !important; background: #0E0626 !important; color: var(--green) !important;
  font-size: 1.25rem !important; caret-color: var(--magenta);
}}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {{
  border: 2px solid var(--magenta) !important;
}}
[data-baseweb="textarea"]:focus-within, [data-baseweb="input"]:focus-within {{
  border-color: var(--cyan) !important; box-shadow: 0 0 16px rgba(0,240,255,0.45) !important;
}}
textarea::placeholder {{ color: rgba(242,233,255,0.45) !important; }}
.stTextArea textarea, .stTextInput input {{
  border: 2px solid var(--magenta) !important; border-radius: 0 !important; background: #0E0626 !important;
}}
.stTextArea textarea:focus, .stTextInput input:focus {{ border-color: var(--cyan) !important; box-shadow: 0 0 16px rgba(0,240,255,0.45) !important; }}
.research-card, .metric-card, .report-card, .approval-card {{
  border-radius: 0 !important; border: none !important; background: var(--panel) !important;
  box-shadow: 0 -4px 0 0 var(--magenta), 0 4px 0 0 var(--magenta), -4px 0 0 0 var(--magenta), 4px 0 0 0 var(--magenta),
    0 0 24px rgba(255,46,151,0.25) !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stToolbar"] * {{ color: var(--text) !important; }}
.st-key-btn_approve .stButton > button, .st-key-btn_approve button[data-testid] {{ background: var(--green) !important; color: var(--night) !important; box-shadow: 0 var(--px) 0 0 #1A7A08, 0 0 18px rgba(57,255,20,.45) !important; }}
.st-key-btn_revise .stButton > button, .st-key-btn_revise button[data-testid] {{ background: var(--yellow) !important; color: var(--night) !important; box-shadow: 0 var(--px) 0 0 #8A7C00 !important; }}
.st-key-btn_reject .stButton > button, .st-key-btn_reject button[data-testid] {{ background: var(--red) !important; color: #fff !important; box-shadow: 0 var(--px) 0 0 #7A0F22 !important; }}
.st-key-btn_approve button[data-testid] p, .st-key-btn_revise button[data-testid] p {{ color: var(--night) !important; }}
.stat-item {{
  border-radius: 0 !important; border: none !important; background: #05020F !important;
  box-shadow: 0 -4px 0 0 var(--cyan), 0 4px 0 0 var(--cyan), -4px 0 0 0 var(--cyan), 4px 0 0 0 var(--cyan),
    0 0 18px rgba(0,240,255,0.25) !important; margin: 4px;
}}
.stat-value {{ color: var(--yellow) !important; text-shadow: 0 0 10px rgba(255,230,0,.55); }}
.stat-label {{ color: var(--cyan) !important; letter-spacing: 2px; }}
[data-testid="stChatInput"] {{ border-radius: 0 !important; }}
[data-testid="stChatInput"] > div {{ border-radius: 0 !important; border: 2px solid var(--magenta) !important; background: #0E0626 !important; }}
[data-testid="stChatInput"] textarea {{ border: none !important; color: var(--green) !important; }}
[data-testid="stChatInput"] button {{ border-radius: 0 !important; }}
[data-testid="stChatMessage"] {{
  border-radius: 0 !important; background: var(--panel) !important; padding: 12px 14px !important;
  box-shadow: 0 -4px 0 0 var(--panel2), 0 4px 0 0 var(--panel2), -4px 0 0 0 var(--panel2), 4px 0 0 0 var(--panel2);
  margin: 10px 4px !important;
}}
[data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"], [data-testid="stChatMessage"] img {{ border-radius: 0 !important; }}
[data-testid="stFileUploaderDropzone"] {{ border-radius: 0 !important; border: 2px dashed var(--cyan) !important; background: #0E0626 !important; }}
.px-num, .px-num * {{ font-family: 'Press Start 2P', monospace !important; font-size-adjust: none !important; font-size: 1.05rem !important; }}
.chunk-card {{
  background: #05020F !important; border: none !important; border-radius: 0 !important; margin: 10px 4px !important;
  box-shadow: 0 -3px 0 0 var(--panel2), 0 3px 0 0 var(--panel2), -3px 0 0 0 var(--panel2), 3px 0 0 0 var(--panel2) !important;
}}
.chunk-card:hover {{ box-shadow: 0 -3px 0 0 var(--cyan), 0 3px 0 0 var(--cyan), -3px 0 0 0 var(--cyan), 3px 0 0 0 var(--cyan), 0 0 16px rgba(0,240,255,.3) !important; }}
.chunk-card .xp-bar {{ margin: 6px 0 4px; }} .chunk-card .xp-cell {{ height: 6px; }}
.chunk-rank {{ color: var(--yellow) !important; }}
[class*="st-key-chip_"] button, [class*="st-key-chip_"] button[data-testid] {{
  background: var(--panel) !important; color: var(--cyan) !important; min-height: 44px;
  box-shadow: 0 -3px 0 0 var(--cyan), 0 3px 0 0 var(--cyan), -3px 0 0 0 var(--cyan), 3px 0 0 0 var(--cyan) !important;
}}
[class*="st-key-chip_"] button p {{ font-family: 'VT323', monospace !important; font-size: 1.1rem !important; text-transform: none; color: var(--cyan) !important; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.1; }}
[class*="st-key-chip_"] button:hover {{ background: var(--cyan) !important; }}
[class*="st-key-chip_"] button:hover p {{ color: var(--night) !important; }}
.empty-icon .px-sprite {{ filter: drop-shadow(0 0 12px rgba(255,46,151,.6)); }}
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {{
  background: var(--magenta) !important; color: #fff !important; border-radius: 0 !important;
  box-shadow: 0 3px 0 0 #8A0E4D, 0 0 14px rgba(255,46,151,.6) !important; min-width: 40px; min-height: 40px;
}}
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] button * {{ color: #fff !important; }}
/* sliders: square thumb */
[data-testid="stSlider"] [role="slider"] {{
  border-radius: 0 !important; background: var(--yellow) !important;
  box-shadow: 0 0 0 3px var(--night), 0 0 12px var(--yellow) !important;
}}
[data-testid="stSlider"] [data-testid="stThumbValue"] {{ font-family: 'Press Start 2P' !important; font-size: 0.6rem; color: var(--yellow) !important; }}
/* radios and toggles */
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{ font-size: 1.2rem !important; }}
[data-baseweb="checkbox"] > div:first-child, [role="radio"] {{ border-radius: 0 !important; }}
/* tabs */
[data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 2px solid var(--magenta); }}
[data-baseweb="tab"] {{ border-radius: 0 !important; background: var(--panel) !important; }}
[data-baseweb="tab"] p {{ font-family: 'Press Start 2P' !important; font-size: 0.6rem !important; }}
[data-baseweb="tab"][aria-selected="true"] {{ background: var(--magenta) !important; }}
[data-baseweb="tab"][aria-selected="true"] p {{ color: #fff !important; }}
[data-baseweb="tab-highlight"] {{ background: var(--yellow) !important; }}
/* expanders */
[data-testid="stExpander"] summary p {{ font-family: 'Press Start 2P' !important; font-size: 0.65rem !important; color: var(--cyan) !important; }}
/* progress */
[data-testid="stProgress"] > div > div {{ border-radius: 0 !important; height: 14px !important; background: #2A1650 !important; }}
[data-testid="stProgress"] > div > div > div > div {{
  border-radius: 0 !important;
  background: repeating-linear-gradient(90deg, var(--green) 0 12px, transparent 12px 16px) !important;
}}
/* sidebar */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
  background: var(--panel) !important; border-right: 4px solid var(--magenta);
  box-shadow: 4px 0 24px rgba(255,46,151,0.25);
}}
[data-testid="stSidebar"] * {{ color: var(--text); }}
/* alerts */
[data-testid="stAlert"] p {{ font-size: 1.2rem !important; }}
/* scrollbars */
::-webkit-scrollbar {{ width: 12px; height: 12px; }}
::-webkit-scrollbar-track {{ background: var(--night); }}
::-webkit-scrollbar-thumb {{ background: var(--magenta); border: 3px solid var(--night); }}
::selection {{ background: var(--magenta); color: #fff; }}

/* ── reusable pieces ──────────────────────────────────────────── */
.px-sprite {{ image-rendering: pixelated; display: inline-block; vertical-align: middle; }}
.px-scene {{ position: absolute; inset: 0; width: 100%; height: 100%; display: block; }}
.sticker-row {{ display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; }}
.sticker {{ filter: drop-shadow(0 0 6px rgba(255,255,255,0.25)); animation: bob 2.4s steps(2) infinite; }}
.sticker:nth-child(2n) {{ animation-delay: .6s; }} .sticker:nth-child(3n) {{ animation-delay: 1.2s; }}
@keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} }}
.blink {{ animation: blink 1.1s steps(1) infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
.neon-c {{ color: var(--cyan); text-shadow: 0 0 6px var(--cyan), 0 0 18px rgba(0,240,255,.6); }}
.neon-m {{ color: var(--magenta); text-shadow: 0 0 6px var(--magenta), 0 0 18px rgba(255,46,151,.6); }}
.neon-y {{ color: var(--yellow); text-shadow: 0 0 6px var(--yellow), 0 0 18px rgba(255,230,0,.5); }}
.neon-g {{ color: var(--green); text-shadow: 0 0 6px var(--green), 0 0 18px rgba(57,255,20,.5); }}
.xp-bar {{ display: flex; gap: 2px; padding: 2px; background: #05020F; border: 2px solid #05020F; }}
.xp-cell {{ flex: 1; height: 8px; display: block; }}
.hud-chip {{
  display: inline-flex; align-items: center; gap: 8px; padding: 6px 10px;
  font-family: 'Press Start 2P' !important; font-size: 0.55rem; letter-spacing: 1px;
  background: #05020F; color: var(--yellow); border: 2px solid var(--yellow);
}}
/* the hero */
.arcade-hero {{
  position: relative; overflow: hidden; min-height: 230px; margin: -1rem -1rem 1.4rem -1rem;
  border-bottom: 4px solid var(--magenta); box-shadow: 0 6px 30px rgba(255,46,151,0.35);
}}
.arcade-hero-inner {{
  position: relative; z-index: 2; padding: 1.6rem 2rem 1.2rem; display: flex;
  flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 1rem;
}}
.arcade-title {{
  font-family: 'Press Start 2P', monospace !important; margin: 0 !important;
  font-size: clamp(2rem, 6vw, 3.6rem) !important; line-height: 1.05 !important; color: var(--cyan);
  text-shadow: 4px 4px 0 var(--magenta), 8px 8px 0 #05020F, 0 0 24px rgba(0,240,255,.7);
  letter-spacing: 4px;
}}
.arcade-sub {{
  font-family: 'Press Start 2P', monospace !important; font-size: 0.7rem; color: var(--yellow);
  margin-top: 14px; letter-spacing: 2px; text-shadow: 2px 2px 0 #05020F;
}}
.arcade-copy {{
  background: rgba(11,4,32,0.78); padding: 16px 20px 14px; max-width: 620px;
  box-shadow: 0 -4px 0 0 #05020F, 0 4px 0 0 #05020F, -4px 0 0 0 #05020F, 4px 0 0 0 #05020F;
}}
.arcade-tag {{ font-size: 1.35rem; color: #FFF4DD; margin-top: 10px; text-shadow: 2px 2px 0 #05020F; max-width: 560px; }}
.arcade-right {{ display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }}
.insert-coin {{ font-family: 'Press Start 2P' !important; font-size: 0.65rem; color: #fff; text-shadow: 2px 2px 0 #05020F; }}
/* energy can easter egg */
.can-egg {{ margin-top: 1.2rem; }}
.can-egg summary {{ list-style: none; cursor: pointer; display: flex; align-items: center; gap: 12px; }}
.can-egg summary::-webkit-details-marker {{ display: none; }}
.can-egg summary .px-sprite {{ filter: drop-shadow(0 0 8px rgba(57,255,20,.7)); transition: transform 80ms steps(1); }}
.can-egg summary:hover .px-sprite {{ transform: rotate(-8deg) translateY(-3px); }}
.can-egg .can-hint {{ font-family: 'Press Start 2P' !important; font-size: 0.55rem; color: var(--green); }}
.can-egg[open] .can-hint {{ color: var(--yellow); }}
.can-pop {{
  margin-top: 10px; padding: 8px 10px; background: #05020F; border: 2px solid var(--green);
  font-family: 'Press Start 2P' !important; font-size: 0.55rem; line-height: 1.8; color: var(--green);
  box-shadow: 0 0 18px rgba(57,255,20,.45); animation: pop .25s steps(3);
}}
.can-pop span {{ font-family: 'VT323' !important; font-size: 1.1rem; color: #FFF4DD; }}
@keyframes pop {{ from {{ transform: scale(.6); opacity: 0; }} to {{ transform: scale(1); opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
@media (max-width: 640px) {{
  .arcade-right {{ align-items: flex-start; }}
  .arcade-hero {{ min-height: 260px; }}
}}
</style>
        """
    )


def arcade_hero(title: str, subtitle: str, tagline: str, status_html: str = "",
                stickers: tuple[str, ...] = ("coin", "heart", "star", "joystick")) -> None:
    """The game title screen at the top of the page."""
    st.markdown(
        f"""
<div class="arcade-hero">
{sunset_scene()}
<div class="arcade-hero-inner">
<div class="arcade-copy">
<h1 class="arcade-title">{title}</h1>
<div class="arcade-sub">{subtitle}</div>
<div class="arcade-tag">{tagline}</div>
</div>
<div class="arcade-right">
{status_html}
{sticker_row(list(stickers), 4)}
<div class="insert-coin blink">&#9654; INSERT COIN</div>
</div>
</div>
</div>
        """,
        unsafe_allow_html=True,
    )
