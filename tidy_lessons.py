from pathlib import Path
import re
import datetime as dt
import argparse
import sys

BASE = Path(__file__).parent
LESSONS = BASE / "lessons"

_TS_RE = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})')

def extract_ts_from_name(p: Path):
    m = _TS_RE.search(p.name)
    if not m:
        return None
    try:
        return dt.datetime.strptime(f"{m.group(1)}_{m.group(2)}", "%Y-%m-%d_%H-%M")
    except Exception:
        return None

def find_latest_md(md_files):
    with_ts = [(p, extract_ts_from_name(p)) for p in md_files]
    with_ts_valid = [x for x in with_ts if x[1] is not None]
    if with_ts_valid:
        return max(with_ts_valid, key=lambda x: x[1])[0]
    return max(md_files, key=lambda f: f.stat().st_mtime)

def main():
    ap = argparse.ArgumentParser(
        description="Keep only the newest *_lesson.md and (optionally) remove PDFs in lessons/."
    )
    ap.add_argument("--delete", action="store_true",
                    help="Actually delete files (default is dry run).")
    ap.add_argument("--keep-md", type=int, default=1,
                    help="How many newest *_lesson.md files to keep (default: 1).")
    ap.add_argument("--keep-pdf", type=int, default=0,
                    help="How many newest PDFs to keep (default: 0 = delete all).")
    ap.add_argument("--no-pdf", action="store_true",
                    help="Do not touch PDFs at all.")
    args = ap.parse_args()

    if not LESSONS.exists():
        print(f"[ERR] Lessons folder not found: {LESSONS}")
        sys.exit(1)

    md_files = sorted(LESSONS.glob("*_lesson.md"))
    if not md_files:
        print("[INFO] No markdown lesson files found. Nothing to do.")
        return

    # newest-first ordering using filename timestamp (fallback to mtime)
    md_sorted = sorted(md_files, key=lambda p: extract_ts_from_name(p) or dt.datetime.fromtimestamp(p.stat().st_mtime), reverse=True)
    md_keep = md_sorted[:max(1, args.keep_md)]
    md_delete = md_sorted[max(1, args.keep_md):]

    pdf_files = sorted(LESSONS.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if args.no_pdf:
        pdf_keep, pdf_delete = pdf_files, []
    else:
        pdf_keep = pdf_files[:max(0, args.keep_pdf)]
        pdf_delete = pdf_files[max(0, args.keep_pdf):]

    print("[PLAN] Will keep these markdown files:")
    for p in md_keep:
        print("  KEEP MD:", p.name)
    if md_delete:
        print("[PLAN] Will delete these markdown files:")
        for p in md_delete:
            print("  DEL  MD:", p.name)
    else:
        print("[PLAN] No extra markdown files to delete.")

    if not args.no_pdf:
        if pdf_keep:
            print("[PLAN] Will keep these PDFs:")
            for p in pdf_keep:
                print("  KEEP PDF:", p.name)
        if pdf_delete:
            print("[PLAN] Will delete these PDFs:")
            for p in pdf_delete:
                print("  DEL  PDF:", p.name)
        if not pdf_files:
            print("[PLAN] No PDFs found.")

    if not args.delete:
        print("\n[DRY RUN] Nothing deleted. Re-run with --delete to apply.")
        return

    # Execute deletions
    for p in md_delete:
        try:
            p.unlink()
            print("Deleted:", p.name)
        except Exception as e:
            print("Failed to delete", p.name, "->", e)

    for p in pdf_delete:
        try:
            p.unlink()
            print("Deleted:", p.name)
        except Exception as e:
            print("Failed to delete", p.name, "->", e)

    print("[DONE] Cleanup complete.")

if __name__ == "__main__":
    main()

