"""The agent: plan, draft, check its own work, fix it, and ask about what is missing.

Steps (shown on the screen):
  1. Read the notes and sort every note into a section, with owner and due date (AI model, or rules in demo mode).
  2. Check the draft against three checks:
       a) every note is in one of the five sections,
       b) no number, ticket, owner or date appears that is not in the notes,
       c) when owners or dates are missing for risks and blockers, it asks about them.
  3. If a check fails, send the problem back to the model and fix the draft (once).
  4. Return the report, the questions for the team and the steps it took.
"""
from __future__ import annotations

import json
import re
import time

from demo import SECTIONS, demo_analyse

FORMAT = """
Answer with ONE JSON object and nothing else, in exactly this shape:
{
  "status": "Green" | "Amber" | "Red",
  "status_reason": "one short sentence",
  "headline": "one sentence a sponsor reads first: what matters most this week and why",
  "summary": "two short sentences for a busy manager",
  "items": [
    {"section": "Highlights" | "Progress" | "Risks" | "Blockers" | "Next week",
     "text": "the note, cleaned up, keeping names, numbers and tickets exactly",
     "owner": "a name from the notes, or empty",
     "due": "a date or day from the notes, or empty",
     "impact": "High" | "Medium" | "Low" | "" (only for Risks and Blockers: what it does to dates, money or customers)}
  ],
  "actions": [{"action": "the most important thing to do this week", "owner": "a name from the notes, or empty", "why": "the risk or blocker it removes"}],
  "decisions": ["a decision the manager or client must make, from the notes"],
  "email": "a status email to the sponsor, under 120 words, plain and factual, starting 'Hi,' and ending with no signature",
  "questions": ["questions the manager should ask about missing information"]
}
Every note must appear in exactly one item. At most 3 actions, most important first.
Connect the notes: if one problem threatens a date or another task, say so in the headline and the impact.
"""

TOKEN = re.compile(r"\b[A-Z]{2,}-\d+\b|\b\d+(?:\.\d+)?\b")


def _json_from(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("The model did not return the report in the expected format.")
    data = json.loads(m.group(0))
    for k in ("items", "questions", "actions", "decisions"):
        data.setdefault(k, [])
    data.setdefault("headline", "")
    data.setdefault("email", "")
    return data


def check(result: dict, notes: str) -> list[str]:
    """The three checks. Returns the problems found (empty list = all good)."""
    problems = []
    low_notes = notes.lower()
    items = result.get("items", [])
    # a) every note in one of the five sections
    bad = [i for i in items if i.get("section") not in SECTIONS]
    if bad or not items:
        problems.append("Check 1: some notes are not in one of the five sections." if items else "Check 1: no notes were sorted.")
    # b) nothing invented: numbers, tickets, owners and dates must be in the notes
    invented = []
    for i in items:
        for tok in TOKEN.findall(i.get("text", "")):
            if tok.lower() not in low_notes:
                invented.append(tok)
        for field in ("owner", "due"):
            v = (i.get(field) or "").strip()
            if v and v.lower() not in low_notes:
                invented.append(v)
    for a_ in result.get("actions", []):
        v = (a_.get("owner") or "").strip()
        if v and v.lower() not in low_notes:
            invented.append(v)
    for field in ("headline", "summary", "email"):
        for tok in TOKEN.findall(result.get(field, "") or ""):
            if tok.lower() not in low_notes:
                invented.append(tok)
    if invented:
        problems.append("Check 2: these do not appear in the notes: " + ", ".join(sorted(set(invented))[:8]) + ".")
    # c) missing owners for risks and blockers must lead to questions
    open_items = [i for i in items if i.get("section") in ("Risks", "Blockers") and not (i.get("owner") or "").strip()]
    if open_items and not result.get("questions"):
        problems.append("Check 3: risks or blockers have no owner, but no questions were asked about them.")
    return problems


def _ask_model(client, model: str, system: str, user: str) -> str:
    reply = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return reply.choices[0].message.content or ""


def run(notes: str, system_prompt: str, api_key: str = "", base_url: str = "", model: str = "") -> tuple[dict, list[dict]]:
    """Run the agent. Returns (result, steps)."""
    steps: list[dict] = []

    def step(name: str, detail: str, ok: bool = True):
        steps.append({"name": name, "detail": detail, "ok": ok})

    t0 = time.time()
    if not api_key:
        result = demo_analyse(notes)
        step("Read and sorted the notes", f"{len(result['items'])} notes sorted with simple rules (demo mode).")
    else:
        from openai import OpenAI  # imported here so demo mode needs no key and no network

        client = OpenAI(api_key=api_key, base_url=base_url or None)
        system = system_prompt.strip() + "\n\n" + FORMAT
        result = _json_from(_ask_model(client, model, system, notes))
        step("Read and sorted the notes", f"{len(result['items'])} notes sorted by the AI model in {time.time() - t0:.1f} s.")

    problems = check(result, notes)
    if not problems:
        step("Checked its own work", "All three checks passed: every note sorted, nothing invented, missing owners asked about.")
    else:
        step("Checked its own work", " ".join(problems), ok=False)
        if api_key:
            fix_user = (notes + "\n\nYour previous answer:\n" + json.dumps(result) +
                        "\n\nIt failed these checks:\n- " + "\n- ".join(problems) +
                        "\n\nFix only these problems and answer again in the same JSON shape.")
            result = _json_from(_ask_model(client, model, system, fix_user))
            again = check(result, notes)
            step("Fixed the problems", "All checks pass now." if not again else "Still open: " + " ".join(again), ok=not again)
        else:
            step("Flagged the problems", "In demo mode the agent shows the problems instead of fixing them.", ok=False)

    q = len(result.get("questions", []))
    step("Listed questions for the team", f"{q} question(s) about missing information." if q else "No information is missing.")
    return result, steps


def to_markdown(result: dict) -> str:
    """The report as plain text, for download or copy."""
    out = [f"# Weekly status report: {result.get('status', '')}", "", result.get("headline", ""), "", result.get("summary", ""), ""]
    for s in SECTIONS:
        out.append(f"## {s}")
        rows = [i for i in result.get("items", []) if i.get("section") == s]
        if not rows:
            out.append("- Nothing to report.")
        for i in rows:
            extra = ", ".join(x for x in [f"owner: {i['owner']}" if i.get("owner") else "", f"due: {i['due']}" if i.get("due") else ""] if x)
            out.append(f"- {i.get('text', '')}" + (f" ({extra})" if extra else ""))
        out.append("")
    if result.get("actions"):
        out.append("## Top actions this week")
        out.extend(f"- {x.get('action', '')} (owner: {x.get('owner') or 'not known'})" for x in result["actions"])
        out.append("")
    if result.get("email"):
        out += ["## Email to sponsor", result["email"], ""]
    if result.get("questions"):
        out.append("## Questions for the team")
        out.extend(f"- {q}" for q in result["questions"])
    return "\n".join(out)
