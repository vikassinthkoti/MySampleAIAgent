"""Weekly Status Report Agent: the starter for Zero to Live AI Agent on Cloud.

A delivery manager pastes a week of rough team notes. The agent sorts every note, writes a
one-minute status report with a Red / Amber / Green status, checks its own work, fixes it,
and lists the questions to ask the team.

It works the moment you run it. With no AI key it runs in DEMO MODE using simple rules.
Add your own AI key (see README) and it switches to a real model.

You can change:
  prompts.py  -> the agent's job description
  app.py      -> the screen
  agent.py    -> the agent's steps (plan, check, fix)
"""
import os

import pandas as pd
import streamlit as st

from agent import run, to_markdown
from demo import SECTIONS
from prompts import SYSTEM_PROMPT

st.set_page_config(page_title="Weekly Status Report Agent", page_icon="📊", layout="wide")


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets first, then from the environment."""
    try:
        value = st.secrets.get(name, "")
    except Exception:  # no secrets file: perfectly normal in demo mode
        value = ""
    return str(value or os.getenv(name, default)).strip()


API_KEY = setting("AI_API_KEY")
BASE_URL = setting("AI_BASE_URL", "https://api.openai.com/v1")
MODEL = setting("AI_MODEL", "gpt-4o-mini")

STATUS_COLOUR = {"Green": "#16a34a", "Amber": "#d97706", "Red": "#dc2626"}
SECTION_ICON = {"Highlights": "🌟", "Progress": "✅", "Risks": "⚠️", "Blockers": "⛔", "Next week": "📅"}

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; max-width: 1150px;}
      .hero {background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #fff; padding: 22px 26px;
             border-radius: 16px; margin-bottom: 18px;}
      .hero h1 {font-size: 1.7rem; margin: 0 0 4px 0; color: #fff;}
      .hero p {margin: 0; opacity: .85;}
      .card {background: #ffffff; color: #0f172a; border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px;
             box-shadow: 0 1px 2px rgba(0,0,0,.04);}
      .card h4 {margin: 0 0 8px 0; font-size: 1.02rem;}
      .item {padding: 6px 0; border-top: 1px dashed #eef0f3; font-size: .95rem;}
      .item:first-of-type {border-top: none;}
      .tag {display: inline-block; font-size: .75rem; padding: 1px 8px; border-radius: 999px; background: #eef2ff; color: #3730a3;
            margin-left: 6px;}
      .status {display: inline-block; color: #fff; font-weight: 700; padding: 6px 14px; border-radius: 999px; font-size: 1rem;}
      .step {color: #0f172a; padding: 8px 12px; border-left: 4px solid #16a34a; background: #f8fafc; margin-bottom: 8px; border-radius: 6px;}
      .step.bad {border-left-color: #d97706;}
      .footer {color: #6b7280; font-size: .8rem; margin-top: 28px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>📊 Weekly Status Report Agent</h1>'
    "<p>Paste a week of rough team notes. Get a one-minute status report, a risk and blocker register, "
    "and the questions to ask your team. The agent checks its own work before it answers.</p></div>",
    unsafe_allow_html=True,
)

if API_KEY:
    st.success(f"Using a real AI model ({MODEL}).")
else:
    st.info("Demo mode: no AI key added yet, so the agent uses simple rules. Add your key to use a real model (see the README).")

SAMPLES = {"Banking portal (sample_updates.txt)": "sample_updates.txt",
           "Cloud migration": "samples/cloud_migration.txt",
           "Telecom billing": "samples/telecom_billing.txt"}


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""

if "updates" not in st.session_state:
    st.session_state.updates = ""

left, right = st.columns([1, 1.35], gap="large")

with left:
    pick = st.selectbox("Choose a sample week", list(SAMPLES))
    c1, c2 = st.columns(2)
    if c1.button("Load a sample week", use_container_width=True):
        st.session_state.updates = read(SAMPLES[pick])
    up = c2.file_uploader("or upload a .txt file", type=["txt", "md", "csv"], label_visibility="collapsed")
    if up is not None and st.session_state.get("_uploaded") != up.name:
        st.session_state.updates = up.read().decode("utf-8", errors="ignore")
        st.session_state._uploaded = up.name
    updates = st.text_area("Your team's notes for the week", key="updates", height=330,
                           placeholder="Paste stand-up notes, Jira lines or emails, one per line...")
    go = st.button("Write my report", type="primary", use_container_width=True)

with right:
    if go:
        if not updates.strip():
            st.warning("Paste some notes first, or press 'Load a sample week'.")
        else:
            with st.spinner("The agent is reading the notes, writing the report and checking its own work..."):
                try:
                    result, steps = run(updates, SYSTEM_PROMPT, API_KEY, BASE_URL, MODEL)
                except Exception as err:  # a wrong key, no credit, no network: say it in plain words
                    st.error(f"The AI model could not answer. Check your key and model name, then try again. Details: {err}")
                    st.stop()
            st.session_state.result, st.session_state.steps = result, steps

    result = st.session_state.get("result")
    steps = st.session_state.get("steps", [])
    if not result:
        st.markdown('<div class="card"><h4>How it works</h4>'
                    '<div class="item">1. Paste your notes, or press <b>Load a sample week</b>.</div>'
                    '<div class="item">2. Press <b>Write my report</b>.</div>'
                    '<div class="item">3. The agent sorts every note, checks its own work, fixes it and lists questions.</div></div>',
                    unsafe_allow_html=True)
    else:
        items = result.get("items", [])
        count = lambda s: len([i for i in items if i.get("section") == s])
        colour = STATUS_COLOUR.get(result.get("status", ""), "#6b7280")
        st.markdown(f'<span class="status" style="background:{colour}">Overall status: {result.get("status", "Not enough information")}</span>'
                    f'&nbsp;&nbsp;<span style="color:#475569">{result.get("status_reason", "")}</span>', unsafe_allow_html=True)
        st.write("")
        if result.get("headline"):
            st.markdown(f'<div class="card" style="border-left:6px solid {colour}"><h4>What matters most this week</h4>'
                        f'<div style="font-size:1.08rem">{result["headline"]}</div></div>', unsafe_allow_html=True)
        st.markdown(f"**Summary.** {result.get('summary', 'Not enough information.')}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Highlights", count("Highlights"))
        k2.metric("Risks", count("Risks"))
        k3.metric("Blockers", count("Blockers"))
        k4.metric("Questions", len(result.get("questions", [])))

        tab_report, tab_register, tab_actions, tab_email, tab_questions, tab_steps = st.tabs(
            ["Report", "Risks and blockers", "Actions and decisions", "Email to sponsor", "Questions for the team", "Agent steps"])
        with tab_report:
            for s in SECTIONS:
                rows = [i for i in items if i.get("section") == s]
                body = "".join(
                    f'<div class="item">{i.get("text", "")}'
                    + (f'<span class="tag">👤 {i["owner"]}</span>' if i.get("owner") else "")
                    + (f'<span class="tag">📅 {i["due"]}</span>' if i.get("due") else "")
                    + "</div>" for i in rows) or '<div class="item">Nothing to report.</div>'
                st.markdown(f'<div class="card"><h4>{SECTION_ICON[s]} {s}</h4>{body}</div>', unsafe_allow_html=True)
        with tab_register:
            reg = [i for i in items if i.get("section") in ("Risks", "Blockers")]
            if reg:
                st.dataframe(pd.DataFrame([{"Type": i["section"][:-1], "Impact": i.get("impact") or "Not known", "Owner": i.get("owner") or "Not known", "Due": i.get("due") or "Not known",
                                            "Item": i.get("text", "")} for i in reg]),
                             use_container_width=True, hide_index=True)
            else:
                st.write("No risks or blockers this week.")
        with tab_actions:
            st.markdown("**Top actions this week**")
            for n, a in enumerate(result.get("actions", []) or [], 1):
                st.markdown(f'<div class="step"><b>{n}. {a.get("action", "")}</b><br><span style="color:#475569">Owner: {a.get("owner") or "Not known"}'
                            f'  ·  Why: {a.get("why", "")}</span></div>', unsafe_allow_html=True)
            if not result.get("actions"):
                st.write("No actions needed.")
            st.markdown("**Decisions needed**")
            for dcs in result.get("decisions", []) or ["None this week."]:
                st.markdown(f"- {dcs}")
        with tab_email:
            st.text_area("Ready to copy and send", result.get("email", "") or "Not enough information.", height=240)
        with tab_questions:
            for q in result.get("questions", []) or ["No information is missing."]:
                st.markdown(f"- {q}")
        with tab_steps:
            for n, s in enumerate(steps, 1):
                st.markdown(f'<div class="step {"" if s["ok"] else "bad"}"><b>{n}. {s["name"]}</b> {"✓" if s["ok"] else "!"}<br>'
                            f'<span style="color:#475569">{s["detail"]}</span></div>', unsafe_allow_html=True)

        st.download_button("Download the report", to_markdown(result), file_name="weekly-status-report.md", use_container_width=True)
        st.caption("Check the report before you send it. The agent only uses what is in the notes.")

st.markdown('<div class="footer">Built at Zero to Live AI Agent on Cloud, Future Proof India.</div>', unsafe_allow_html=True)
