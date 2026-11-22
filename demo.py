"""Demo mode: the same agent steps without an AI key, using simple rules.

It sorts each note by looking for a few words, finds owners and dates where it can, and
lists questions for anything that is missing. A real AI model (add your key) does this far better.
"""
import re

SECTIONS = ["Highlights", "Progress", "Risks", "Blockers", "Next week"]

KEYWORDS = {
    "Blockers": ["blocked", "waiting on", "waiting for", "stuck", "cannot", "can't", "pending approval", "no access"],
    "Risks": ["risk", "delay", "delayed", "may slip", "might", "could affect", "concern", "worried", "behind", "tight"],
    "Next week": ["next week", "will ", "plan to", "planning", "to do", "todo", "going to", "prepare"],
    "Highlights": ["shipped", "launched", "released", "won", "signed", "praised", "went well", "milestone", "completed ahead"],
}

DAY = re.compile(r"^\s*(mon|tue|wed|thu|fri|sat|sun)[a-z]*\s*[:\-]\s*", re.I)
NAME_TO = re.compile(r"\b([A-Z][a-z]+) to follow up\b")
NAME_START = re.compile(r"^([A-Z][a-z]+)\s+(?:is|was|spent|finished|fixed|stuck|raised|working|started)\b")
DATE = re.compile(r"\b(\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|Monday|Tuesday|Wednesday|Thursday|Friday|next week|tomorrow)\b", re.I)


def _clean(line: str) -> str:
    return DAY.sub("", re.sub(r"^[\s\-\*•\d\.\)]+(?=[A-Za-z])", "", line)).strip()


def _owner(line: str) -> str:
    m = NAME_TO.search(line) or NAME_START.search(line)
    return m.group(1) if m else ""


def demo_analyse(notes: str) -> dict:
    """Return the same structure the AI model returns (see agent.py)."""
    items = []
    for raw in notes.splitlines():
        line = _clean(raw)
        if not line:
            continue
        low = line.lower()
        section = "Progress"
        for name in ("Blockers", "Risks", "Next week", "Highlights"):
            if any(w in low for w in KEYWORDS[name]):
                section = name
                break
        d = DATE.search(line)
        impact = "High" if section == "Blockers" else "Medium" if section == "Risks" else ""
        items.append({"section": section, "text": line, "owner": _owner(line), "due": d.group(1) if d else "", "impact": impact})

    risks = [i for i in items if i["section"] == "Risks"]
    blockers = [i for i in items if i["section"] == "Blockers"]
    status = "Red" if len(blockers) >= 2 else "Amber" if blockers or risks else "Green"
    questions = []
    for i in blockers + risks:
        if not i["owner"]:
            questions.append(f"Who owns this, and by when will it be resolved: \"{i['text']}\"?")
    if not items:
        questions.append("Not enough information: no notes were given.")
    def n(k, word):
        return f"{k} {word}" if k == 1 else f"{k} {word}s"

    hl = len([i for i in items if i["section"] == "Highlights"])
    actions = [{"action": "Resolve: " + i["text"], "owner": i["owner"], "why": i["section"][:-1]} for i in (blockers + risks)[:3]]
    lead = (blockers + risks)[0]["text"] if (blockers or risks) else "No risks or blockers reported"
    email = ("Hi,\n\nThis week's status is " + status + ". " + n(len(items), "update") + ": " + n(hl, "highlight") + ", "
             + n(len(risks), "risk") + " and " + n(len(blockers), "blocker") + ". Main point: " + lead + ".\n\nThe full report is attached.")
    return {
        "headline": f"{status}: {lead}.",
        "actions": actions,
        "decisions": [],
        "email": email,
        "status": status,
        "status_reason": f"{n(len(blockers), 'blocker')} and {n(len(risks), 'risk')} this week.",
        "summary": f"{n(len(items), 'update')} this week: {n(hl, 'highlight')}, {n(len(risks), 'risk')} and {n(len(blockers), 'blocker')}.",
        "items": items,
        "questions": questions[:5],
    }
