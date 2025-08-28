import json, os

# skills.json lives next to this file (see below)
SKILL_FILE = os.path.join(os.path.dirname(__file__), "skills.json")

def load_known_skills():
    if os.path.exists(SM := SKILL_FILE):
        with open(SM, "r", encoding="utf-8") as f:
            skills = json.load(f)
            return set(s.strip().lower() for s in skills if s.strip())
    # fallback
    return {"python","java","sql","mongodb","flask","react","node","express","html","css","javascript","power bi","excel"}

KNOWN_SKILLS = load_known_skills()

def extract_skills_from_text(text: str):
    """
    Very simple extractor:
    - lowercase the text
    - check if each known skill appears as a substring
    """
    t = (text or "").lower()
    found = [s for s in KNOWN_SKILLS if s in t]
    # unique + sorted for stable output
    return sorted(set(found))
