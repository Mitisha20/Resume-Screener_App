# backend/app/routes/scan.py
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required
from app.utils.responses import ok, fail
import json, os, re

scan_bp = Blueprint("scan", __name__, url_prefix="/api/scan")

# -------- skills + synonyms --------
_SKILLS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills.json")
try:
    with open(_SKILLS_PATH, "r", encoding="utf-8") as f:
        ALL_SKILLS = [s.strip() for s in json.load(f) if s and isinstance(s, str)]
except Exception:
    ALL_SKILLS = []

if not ALL_SKILLS:  # fallback list
    ALL_SKILLS = [
        "python","java","javascript","typescript","react","node.js","express",
        "html","css","rest","api","graphql","docker","kubernetes","aws","gcp","azure","linux",
        "postgresql","mysql","mongodb","redis","git","github","ci/cd",
        "unit testing","integration testing","pytest","jest",
        "django","flask","fastapi","spring","next.js",
        "pandas","numpy","scikit-learn","nlp","machine learning",
        "data structures","algorithms"
    ]

_SYNONYMS = {
    "c++": ["c++", "c plus plus", "c-plus-plus"],
    "node.js": ["node.js", "nodejs", "node js"],
    "react": ["reactjs", "react.js"],
    "postgresql": ["postgres", "postgre sql"],
    "mongodb": ["mongo", "mongo db"],
    "mysql": ["my sql"],
    "ci/cd": ["ci cd", "ci-cd", "continuous integration", "continuous delivery", "continuous deployment"],
    "unit testing": ["unit tests", "unit test"],
    "integration testing": ["integration tests", "integration test"],
    "end-to-end testing": ["e2e testing", "e2e tests", "end to end testing"],
    "code review": ["code reviews"],
    "nlp": ["natural language processing"],
    "ml": ["machine learning"],  # we block bare "ml" below; only phrase match via synonym
    "http": ["https"],
    "graphql": ["graph ql"],
}

# ignore very short/ambiguous tokens (and bare "ml")
_BLOCKLIST = {"c", "r", "go", "ml"}

# optional soft skills treated as "optional" requirements
INCLUDE_SOFT_SKILLS = True
SOFT_SKILLS = [
    "teamwork", "collaboration", "communication", "leadership",
    "problem solving", "ownership", "adaptability", "time management",
    "agile", "scrum", "kanban"
]
SOFT_SYNONYMS = {
    "teamwork": ["teamwork", "team player", "working in a team"],
    "collaboration": ["collaboration", "collaborate", "collaborative"],
    "communication": ["communication", "communicate", "communicator"],
    "leadership": ["leadership", "lead", "led"],
    "problem solving": ["problem solving", "problem-solving"],
    "ownership": ["ownership", "own", "owned"],
    "adaptability": ["adaptable", "adaptability", "flexible", "flexibility"],
    "time management": ["time management"],
    "agile": ["agile"],
    "scrum": ["scrum"],
    "kanban": ["kanban"]
}

# section weights used when counting occurrences
_SECTION_W = {
    "experience": 1.0,
    "projects": 0.95,
    "certifications": 0.9,
    "skills": 0.75,
    "education": 0.7,
    "summary": 0.55,
    "other": 0.7,
}

# rubric weights (sum = 1.0)
W_REQUIRED = 0.45
W_OPTIONAL = 0.20
W_DISTRIB  = 0.15
W_TITLE    = 0.10
W_YEARS    = 0.10

# penalty for each missing required skill (capped later)
_REQ_MISS_PENALTY = 0.10

# -------- helpers --------
_STOP = {
    "the","a","an","to","of","and","or","for","with","in","on","at","by","as","is","are",
    "be","this","that","your","our","we","you","their","his","her"
}

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _lc(s: str) -> str:
    return (s or "").lower()

def _word_in(text_lc: str, phrase: str) -> re.Match | None:
    return re.search(rf"(?<!\w){re.escape((phrase or '').lower())}(?!\w)", text_lc)

def _first_snippet(original: str, variant: str, m: re.Match | None) -> str | None:
    if not original or not variant:
        return None
    if not m:
        m = re.search(rf"(?<!\w){re.escape(variant)}(?!\w)", original, flags=re.IGNORECASE)
        if not m:
            return None
    start, end = m.start(), m.end()
    lo = max(0, start - 40)
    hi = min(len(original), end + 40)
    return original[lo:hi].strip()

# -------- skill extraction --------
def _extract_skills_with_evidence(text: str):
    original = text or ""
    t = _lc(_clean(original))
    found = set()
    evidence = {}

    for sk in ALL_SKILLS:
        s = (sk or "").strip().lower()
        if not s or s in _BLOCKLIST:
            continue
        m = _word_in(t, s)
        if m:
            found.add(s)
            evidence.setdefault(s, _first_snippet(original, s, m))

    for canon, variants in _SYNONYMS.items():
        for v in variants:
            m = _word_in(t, v)
            if m:
                key = canon.lower()
                found.add(key)
                evidence.setdefault(key, _first_snippet(original, v, m))
                break

    aliases = {
        "golang": "go",
        "c sharp": "c#", "c-sharp": "c#",
        "js": "javascript",
        "ts": "typescript",
        "sde": "software engineer", "software development engineer": "software engineer"
    }
    for a, canon in aliases.items():
        m = _word_in(t, a)
        if m:
            key = canon.lower()
            found.add(key)
            evidence.setdefault(key, _first_snippet(original, a, m))

    return sorted(found), evidence

def _extract_soft_skills_with_evidence(text: str):
    original = text or ""
    t = _lc(_clean(original))
    found = set()
    evidence = {}
    for sk in SOFT_SKILLS:
        s = sk.lower()
        m = _word_in(t, s)
        if m:
            found.add(s)
            evidence.setdefault(s, _first_snippet(original, s, m))
    for canon, variants in SOFT_SYNONYMS.items():
        for v in variants:
            m = _word_in(t, v)
            if m:
                key = canon.lower()
                found.add(key)
                evidence.setdefault(key, _first_snippet(original, v, m))
                break
    return sorted(found), evidence

# -------- JD parsing (required vs optional) --------
def _slice_block(text_lc: str, start_key: str, *end_keys: str) -> str | None:
    m = re.search(re.escape(start_key.lower()), text_lc)
    if not m:
        return None
    start = m.end()
    end = len(text_lc)
    for k in end_keys:
        m2 = re.search(re.escape(k.lower()), text_lc[start:])
        if m2:
            end = start + m2.start()
            break
    return text_lc[start:end].strip() or None

def _parse_jd_skills(jd_text: str):
    t = _lc(_clean(jd_text))

    m = re.search(r"\bskills?\s*:\s*([^\n]+)", t)
    if m:
        raw = [x.strip() for x in m.group(1).split(",") if x.strip()]
        req, _ = _extract_skills_with_evidence(", ".join(raw))
        return set(req), set()

    must_blk = _slice_block(t, "must-have", "nice to have", "requirements", "preferred", "what you’ll", "what you'll")
    nice_blk = _slice_block(t, "nice to have", "must-have", "preferred", "requirements", "what you’ll", "what you'll")

    req = set(_extract_skills_with_evidence(must_blk or "")[0]) if must_blk else set()
    opt = set(_extract_skills_with_evidence(nice_blk or "")[0]) if nice_blk else set()

    if not req and not opt:
        tech, _ = _extract_skills_with_evidence(jd_text)  # use original for better snippets
        req = set(tech)
    if not req and not opt and INCLUDE_SOFT_SKILLS:
        soft, _ = _extract_soft_skills_with_evidence(jd_text)
        opt = set(soft)

    return req, opt

# -------- resume sections --------
_HEADINGS = [
    ("experience", r"^\s*(work\s+experience|professional\s+experience|experience|employment|work\s+history)\b"),
    ("projects", r"^\s*(projects|personal\s+projects)\b"),
    ("skills", r"^\s*(skills|technical\s+skills|technologies|tools)\b"),
    ("education", r"^\s*(education|academics)\b"),
    ("certifications", r"^\s*(certifications|certificates|licenses)\b"),
    ("summary", r"^\s*(summary|profile|objective)\b"),
]

def _section_spans(original: str):
    text = original or ""
    lc = text.lower()
    hits = []
    for name, pat in _HEADINGS:
        for m in re.finditer(pat, lc, flags=re.MULTILINE):
            hits.append((m.start(), name))
    if not hits:
        return [("other", 0, len(text))]
    hits.sort(key=lambda x: x[0])
    spans, prev_end = [], 0
    for i, (start, name) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        if start > prev_end:
            spans.append(("other", prev_end, start))
        spans.append((name, start, end))
        prev_end = end
    if prev_end < len(text):
        spans.append(("other", prev_end, len(text)))
    return spans

def _locate_section_for_skill(skill: str, original: str, spans):
    if not original:
        return "other"
    lc = original.lower()
    variants = [skill] + _SYNONYMS.get(skill, [])
    if skill == "go":        variants += ["golang"]
    if skill == "c#":        variants += ["c sharp","c-sharp"]
    if skill == "javascript":variants += ["js"]
    if skill == "typescript":variants += ["ts"]
    first_idx = None
    for v in variants:
        m = re.search(rf"(?<!\w){re.escape(v)}(?!\w)", lc)
        if m:
            idx = m.start()
            first_idx = idx if first_idx is None else min(first_idx, idx)
    if first_idx is None:
        return "other"
    for name, start, end in spans:
        if start <= first_idx < end:
            return name
    return "other"

# -------- simple title + years parsing --------
_ROLE_SYNS = {
    "software engineer": {"software", "engineer", "developer", "swe", "sde"},
    "data scientist": {"data", "scientist", "ml", "ai"},
    "data engineer": {"data", "engineer", "etl"},
    "ml engineer": {"machine", "learning", "ml", "engineer"},
    "backend engineer": {"backend", "back-end", "server", "api"},
    "frontend engineer": {"frontend", "front-end", "react", "ui"},
}

def _first_line_tokens(text: str):
    line = (_clean(text).split("\n") or [""])[0][:120].lower()
    toks = [t for t in re.split(r"[^a-z0-9#+]+", line) if t and t not in _STOP]
    return set(toks)

def _title_score(resume_text: str, jd_text: str) -> float:
    r = _first_line_tokens(resume_text)
    j = _first_line_tokens(jd_text)
    def expand(token_set):
        out = set(token_set)
        for canon, syns in _ROLE_SYNS.items():
            if (set(canon.split()) & token_set) or (syns & token_set):
                out |= syns | set(canon.split())
        return out
    r2, j2 = expand(r), expand(j)
    inter = len(r2 & j2)
    denom = max(1, len(j2))
    return min(1.0, inter / denom)

def _extract_years(text: str) -> int | None:
    t = _lc(text)
    years = []
    for m in re.finditer(r"(\d+)\s*(\+)?\s*(years|year|yrs)", t):
        try:
            years.append(int(m.group(1)))
        except:
            pass
    return max(years) if years else None

def _years_score(resume_text: str, jd_text: str) -> float:
    need = _extract_years(jd_text)
    have = _extract_years(resume_text)
    if need is None:
        return 1.0
    if have is None:
        return 0.0
    if have >= need:
        return 1.0
    return max(0.0, have / max(1, need))

# -------- PDF --------
def _pdf_to_text(file_storage):
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_storage.stream)
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages)
    except Exception as e:
        raise RuntimeError(f"pdf_read_error: {e}")

# -------- route --------
@scan_bp.post("/")
@jwt_required()
def scan():
    resume_text, jd_text = "", ""

    if request.content_type and "multipart/form-data" in request.content_type:
        file = request.files.get("file")

        max_mb = float(current_app.config.get("MAX_FILE_MB", 10))
        if file and getattr(file, "content_length", None):
            if file.content_length > max_mb * 1024 * 1024:
                return fail(f"file too large (>{max_mb}MB)", 413)

        if file and file.mimetype not in ("application/pdf", "application/x-pdf"):
            return fail("only PDF files are allowed", 415)

        jd_text = _clean(request.form.get("jd_text"))
        if not file or not jd_text:
            return fail("pdf file and jd_text are required", 422)
        try:
            resume_text = _pdf_to_text(file)
        except Exception as e:
            return fail("could not read pdf", 400, details=str(e))
    else:
        data = request.get_json(silent=True) or {}
        resume_text = _clean(data.get("resume_text"))
        jd_text = _clean(data.get("jd_text"))
        if not resume_text or not jd_text:
            return fail("resume_text and jd_text are required", 422)

    # skills & sections
    resume_skills, resume_ev = _extract_skills_with_evidence(resume_text)
    jd_req, jd_opt = _parse_jd_skills(jd_text)
    jd_union = jd_req | jd_opt

    if len(jd_union) == 0:
        return ok(
            "scan complete",
            score=0.0, overlap_ratio=0.0,
            matched_skills=[], missing_skills=[], extra_skills=[],
            jd_required=[], jd_optional=[], evidence={},
            breakdown={}, diagnostics={"jd_total": 0, "resume_detected": len(resume_skills)}
        )

    r = set(resume_skills)
    match_req = sorted(r & jd_req); miss_req = sorted(jd_req - r)
    match_opt = sorted(r & jd_opt); miss_opt = sorted(jd_opt - r)
    matched_union = sorted((r & jd_union))
    missing_union = sorted(jd_union - r)
    extra_union = sorted(r - jd_union)

    overlap_union = len(matched_union) / max(1, len(jd_union))

    # distribution score (counts, capped, weighted by section)
    spans = _section_spans(resume_text)
    distrib_raw, distrib_max = 0.0, 0.0
    for sk in jd_union:
        w = 1.0 if sk in jd_req else 0.5
        distrib_max += 2.0 * w
        occ = 0.0
        variants = [sk] + _SYNONYMS.get(sk, [])
        if sk == "go":        variants += ["golang"]
        if sk == "c#":        variants += ["c sharp","c-sharp"]
        if sk == "javascript":variants += ["js"]
        if sk == "typescript":variants += ["ts"]
        for v in variants:
            for m in re.finditer(rf"(?<!\w){re.escape(v)}(?!\w)", resume_text, flags=re.IGNORECASE):
                idx = m.start()
                sec = "other"
                for name, start, end in spans:
                    if start <= idx < end:
                        sec = name; break
                occ += _SECTION_W.get(sec, 0.7)
                if occ >= 2.0:
                    break
            if occ >= 2.0:
                break
        distrib_raw += w * min(2.0, occ)
    distrib_score = (distrib_raw / max(1.0, distrib_max)) if distrib_max > 0 else 1.0

    # title + years
    title_score = _title_score(resume_text, jd_text)
    years_score = _years_score(resume_text, jd_text)

    # coverage parts
    req_cov = (len(match_req) / max(1, len(jd_req))) if jd_req else 1.0
    opt_cov = (len(match_opt) / max(1, len(jd_opt))) if jd_opt else 1.0

    # combine
    base = (
        W_REQUIRED * req_cov +
        W_OPTIONAL * opt_cov +
        W_DISTRIB  * distrib_score +
        W_TITLE    * title_score +
        W_YEARS    * years_score
    )

    penalty = min(0.50, _REQ_MISS_PENALTY * len(miss_req))
    very_low_overlap = overlap_union < 0.03

    if (len(matched_union) == 0) and very_low_overlap:
        final = 0.0
    else:
        final = max(0.0, min(1.0, base - penalty))

    evidence = {sk: resume_ev.get(sk) for sk in matched_union if resume_ev.get(sk)}

    return ok(
        "scan complete",
        score=round(float(final), 4),
        overlap_ratio=round(float(overlap_union), 4),
        matched_skills=matched_union,
        missing_skills=missing_union,
        extra_skills=extra_union,
        jd_required=sorted(jd_req),
        jd_optional=sorted(jd_opt),
        matched_required=match_req,
        missing_required=miss_req,
        matched_optional=match_opt,
        missing_optional=miss_opt,
        evidence=evidence,
        breakdown={
            "required_coverage": round(req_cov, 4),
            "optional_coverage": round(opt_cov, 4),
            "distribution": round(distrib_score, 4),
            "title": round(title_score, 4),
            "years": round(years_score, 4),
            "penalty_missing_required": round(penalty, 4),
        },
        diagnostics={
            "jd_total": len(jd_union),
            "resume_detected": len(resume_skills),
            "matched": len(matched_union),
            "overlap_union": round(float(overlap_union), 4),
            "base_before_penalty": round(float(base), 4),
            "skills_count": len(ALL_SKILLS),
        }
    )
