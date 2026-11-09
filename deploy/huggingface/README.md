---
title: NEXUS Multi-Agent Research
emoji: 🔎
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: Five LangGraph agents turn a question into a cited report
---

# NEXUS: multi-agent research platform

Ask a research question. Five LangGraph agents (Planner, Researcher, Analyst, Writer, Critic) search the web
with Tavily, write a cited report with Gemini, and revise it until the Critic approves.

Code and benchmark: [github.com/Anikate001/Multi-Agent-System-Architechture](https://github.com/Anikate001/Multi-Agent-System-Architechture)

This free demo allows 25 research runs per day and one at a time, to stay within free API quotas.
Reports are not kept after the Space restarts.
