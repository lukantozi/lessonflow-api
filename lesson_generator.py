from openai import OpenAI
import os
import argparse
import datetime
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from markdown import markdown
from weasyprint import HTML
import re
from typing import List, Tuple, Optional, Any, TypedDict

# =========================
# Config (keep it light)
# =========================
MODEL_SUGGESTIONS = "gpt-4o"
MODEL_GENERATION  = "gpt-4o"

SUGGESTION_TEMPERATURE = 0.9   # a bit creative, but not wild
GENERATION_TEMPERATURE = 0.4   # tighter adherence to structure

CONFIRM_BEFORE_GEN = True

# =========================
# Setup
# =========================
BASE = Path(__file__).parent
load_dotenv(dotenv_path=BASE / ".env")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env")

client = OpenAI(api_key=api_key)

PROMPTS = BASE / "prompts"
LESSONS = BASE / "lessons"
LESSONS.mkdir(exist_ok=True)

# =========================
# Helpers
# =========================
def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")

_TS_RE = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})')

def _extract_ts_from_name(p: Path) -> Optional[datetime.datetime]:
    m = _TS_RE.search(p.name)
    if not m:
        return None
    date_s, time_s = m.group(1), m.group(2)
    try:
        return datetime.datetime.strptime(f"{date_s}_{time_s}", "%Y-%m-%d_%H-%M")
    except Exception:
        return None

def _safe_content(resp: Any) -> str:
    try:
        c = resp.choices[0].message.content
        return c or ""
    except Exception:
        return ""

class ChatMessage(TypedDict):
    role: str
    content: str

def chat_content(*, model: str, messages: List[ChatMessage], temperature: float = 0.7, **kwargs) -> str:
    """Wrapper that always returns a plain string response."""
    api: Any = client  # silence static checker about dynamic attrs
    resp = api.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        **kwargs,
    )
    return _safe_content(resp)

def get_last_lesson() -> str:
    files = list(LESSONS.glob("*_lesson.md"))
    if not files:
        return ""
    with_ts: list[tuple[Path, Optional[datetime.datetime]]] = [
        (p, _extract_ts_from_name(p)) for p in files
    ]
    with_ts_valid: list[tuple[Path, datetime.datetime]] = [
        (p, ts) for (p, ts) in with_ts if ts is not None
    ]
    if with_ts_valid:
        latest_path = max(with_ts_valid, key=lambda item: item[1])[0]
    else:
        latest_path = max(files, key=lambda f: f.stat().st_mtime)
    print(f"[DEBUG] Using previous lesson file: {latest_path.name}")
    return latest_path.read_text(encoding="utf-8")

def save_lesson(content: str, topic1: str, level: str, reading_mode: str) -> Path:
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_topic = re.sub(r"\W+", "_", topic1).strip("_")[:30] or "lesson"
    safe_level = re.sub(r"[^A-Za-z0-9]+", "", (level or "").upper()) or "LEVEL"
    mode_tag = {"paragraphs": "P", "dialogue": "D"}.get(reading_mode, "P")
    md_path = LESSONS / f"{now}_{safe_level}_{mode_tag}_{safe_topic}_lesson.md"
    md_path.write_text(content, encoding="utf-8")
    print(f"\nSaved Markdown: {md_path}")
    return md_path

def convert_to_pdf(md_path: Path) -> Path:
    pdf_path = md_path.with_suffix(".pdf")
    html_content = markdown(md_path.read_text(encoding="utf-8"))
    HTML(string=html_content).write_pdf(str(pdf_path))
    print(f"Converted to PDF: {pdf_path}")
    return pdf_path

def sync_to_ipad(pdf_path: Path):
    dest = Path.home() / "Nextcloud/iPad/Lessons" / pdf_path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "--remove-destination", str(pdf_path), str(dest)])
    print(f"Synced to iPad: {dest}")

def adjacent_levels(level: str) -> Tuple[str, str]:
    order = ["A2", "B1", "B2", "C1"]
    if level not in order:
        return ("A2", "B2")
    i = order.index(level)
    lower = order[max(0, i - 1)]
    higher = order[min(len(order) - 1, i + 1)]
    return (lower, higher)

# =========================
# Suggestions: exactly 10 per reading (1–5 human, 6–10 situational)
# =========================
def get_topic_suggestions(level: str) -> str:
    prompt_template = read_file(PROMPTS / "suggestion_prompt.txt")
    last_lesson = get_last_lesson()
    full_prompt = (
        prompt_template.replace("{level}", level)
        + "\n\n---\n\nPrevious Lesson (avoid overlap of themes/keywords):\n```markdown\n"
        + last_lesson + "\n```"
    )
    return chat_content(
        model=MODEL_SUGGESTIONS,
        messages=[{"role": "user", "content": full_prompt}],
        temperature=SUGGESTION_TEMPERATURE,
    )

_ITEM_RE = re.compile(r'^\s*\d+\.\s*(.+?)\s*$')

def _strip(s: str) -> str:
    return s.strip().strip("*_ ").replace("—","-").replace("–","-")

def parse_suggestions(raw: str) -> Tuple[List[str], List[str], List[str]]:
    r1, r2, g = [], [], []
    section = None
    for line in raw.splitlines():
        s = _strip(line)
        if not s:
            continue
        lo = s.lower()
        if "reading 1 topics" in lo:
            section = "r1"; continue
        if "reading 2 topics" in lo:
            section = "r2"; continue
        if "grammar focus" in lo:
            section = "g"; continue

        m = _ITEM_RE.match(s)
        if m and section:
            txt = _strip(m.group(1))
            if section == "r1": r1.append(txt)
            elif section == "r2": r2.append(txt)
            else: g.append(txt)

    return r1, r2, g

def choose_topics(level: str):
    while True:
        raw = get_topic_suggestions(level)
        r1, r2, g = parse_suggestions(raw)

        if len(r1) == 10 and len(r2) == 10 and 6 <= len(g) <= 8:
            print("\n-- Choices --")
            print("Reading 1 topics (1–5 human-centered • 6–10 situational):")
            for i, t in enumerate(r1, 1): print(f"{i}. {t}")
            print("\nReading 2 topics (1–5 knowledge/discovery • 6–10 situational/applied):")
            for i, t in enumerate(r2, 1): print(f"{i}. {t}")
            print("\nGrammar focuses:")
            for i, t in enumerate(g, 1): print(f"{i}. {t}")
        else:
            print("\n[WARN] Suggestions not in expected counts. Regenerating...")
            continue

        use = input("\nUse these suggestions? (y/n): ").strip().lower()
        if use == "y":
            break

    def pick(label: str, options: List[str]) -> str:
        choice = input(f"\nYour choice for {label} (number or text): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                picked = options[idx]
                print(f"[INFO] Selected {label}: {picked}")
                return picked
            print("[WARN] Number out of range; using raw input.")
        return choice

    topic1 = pick("Topic 1 (psych/social or situational)", r1)
    topic2 = pick("Topic 2 (knowledge or situational/applied)", r2)
    grammar = pick("Grammar Focus", g)

    return topic1, topic2, grammar

# =========================
# Generation (single reading mode for both readings)
# =========================
REQUIRED_HEADERS = [
    "## Reading Material 1", "## Reading 1",
    "## Reading Material 2", "## Reading 2",
    "## Dialogue 1", "## Dialogue 1 – Questions",
    "## Dialogue 2", "## Dialogue 2 – Questions",
    "## Vocabulary Focus", "## Vocabulary Exercises",
    "## Grammar Focus", "## General Discussion Prompts",
    "## Guided Role-Plays",
]

def _has_all_headers(md_text: str) -> bool:
    lines = [ln.strip() for ln in md_text.splitlines()]
    return all(any(ln.startswith(h) for ln in lines) for h in REQUIRED_HEADERS)

def generate_lesson(level: str, topic1: str, topic2: str, grammar: str, reading_mode: str) -> str:
    gen_template = read_file(PROMPTS / "generation_prompt.txt")
    last_lesson = get_last_lesson()

    if reading_mode == "dialogue":
        reading_mode_block = (
            "## Reading Material 1 – (title)\n"
            "- 5 numbered dialogue scenes (1)–(5); each scene 10–14 short lines, alternating speakers; no narration.\n"
            "- Scenes should form a coherent storyline.\n\n"
            "## Reading 1 – Comprehension & Discussion Questions\n"
            "- 5 items; at least 2 invite opinion/discussion.\n\n"
            "## Reading Material 2 – (title)\n"
            "- 5 numbered dialogue scenes (1)–(5); each scene 10–14 short lines, alternating speakers; no narration.\n"
            "- Scenes should form a coherent storyline.\n\n"
            "## Reading 2 – Comprehension & Discussion Questions\n"
            "- 5 items; at least 2 invite opinion/discussion.\n"
        )
    else:
        reading_mode_block = (
            "## Reading Material 1 – (title)\n"
            "- 5 numbered paragraphs (1)–(5), approximately equal in characters.\n\n"
            "## Reading 1 – Comprehension & Discussion Questions\n"
            "- 5 items; at least 2 invite opinion/discussion.\n\n"
            "## Reading Material 2 – (title)\n"
            "- 5 numbered paragraphs (1)–(5), approximately equal in characters.\n\n"
            "## Reading 2 – Comprehension & Discussion Questions\n"
            "- 5 items; at least 2 invite opinion/discussion.\n"
        )

    lower, higher = adjacent_levels(level)

    prompt_filled = (
        gen_template
        .replace("{level}", level)
        .replace("{READING_MODE_BLOCK}", reading_mode_block)
        .replace("{level-1}", lower)
        .replace("{level+1}", higher)
    )

    exact_titles_block = (
        "Use these exact H2 headings (copy verbatim):\n"
        f"## Reading Material 1 – {topic1}\n"
        f"## Reading Material 2 – {topic2}\n"
        f"## Grammar Focus – {grammar}\n"
    )

    final_prompt = (
        "Use EXACTLY the following selections. Do not substitute or invent alternatives.\n"
        f"Topic 1 (Reading 1): {topic1}\n"
        f"Topic 2 (Reading 2): {topic2}\n"
        f"Grammar Focus: {grammar}\n\n"
        + exact_titles_block + "\n"
        + prompt_filled +
        "\n\nPrevious Lesson (STRUCTURE ONLY):\n```markdown\n" + last_lesson + "\n```"
    )

    md = chat_content(
        model=MODEL_GENERATION,
        messages=[{"role": "user", "content": final_prompt}],
        temperature=GENERATION_TEMPERATURE,
    )

    # one retry if any section is missing
    if not _has_all_headers(md):
        md_retry = chat_content(
            model=MODEL_GENERATION,
            messages=[{"role": "user", "content":
                       "Your previous output missed required sections. "
                       "Re-output the ENTIRE lesson with ALL required headers present and fully filled, "
                       "without changing topics/grammar or the format constraints.\n\n" + final_prompt}],
            temperature=0.3,
        )
        md = md_retry or md

    return md

# =========================
# Main
# =========================
def main():
    level = input("Select difficulty level (A2, B1, B2, C1): ").strip().upper()
    mode_raw = input("Reading format (P = paragraphs, D = dialogue-as-reading) [P/D]: ").strip().upper() or "P"
    reading_mode = "dialogue" if mode_raw == "D" else "paragraphs"

    topic1, topic2, grammar = choose_topics(level)

    print("\n[SELECTIONS]")
    print(f"Topic 1: {topic1}")
    print(f"Topic 2: {topic2}")
    print(f"Grammar: {grammar}")
    print(f"Reading mode: {reading_mode}")

    if CONFIRM_BEFORE_GEN:
        go = input("\nGenerate lesson now? (y/n): ").strip().lower()
        if go != "y":
            print("[INFO] Canceled before generation.")
            return

    print("\n[STEP] Generating lesson...")
    lesson = generate_lesson(level, topic1, topic2, grammar, reading_mode)

    print("[STEP] Saving Markdown...")
    md_file = save_lesson(lesson, topic1, level, reading_mode)

    print("[STEP] Converting to PDF...")
    pdf_file = convert_to_pdf(md_file)

    print("[STEP] Syncing to iPad...")
    sync_to_ipad(pdf_file)

    print("[DONE]")

if __name__ == "__main__":
    main()

















