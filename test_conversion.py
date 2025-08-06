from pathlib import Path
from markdown import markdown
from weasyprint import HTML
from lesson_generator import clean_tables  # import your cleaning function

# Set the test markdown file path
test_md = Path("lessons/2025-08-04_lesson.md")  # replace with any existing .md
assert test_md.exists(), f"File not found: {test_md}"

# Clean, convert to HTML, and export PDF
raw = test_md.read_text(encoding="utf-8")
cleaned = clean_tables(raw)

pdf_path = test_md.with_suffix(".test.pdf")
html = markdown(cleaned)
HTML(string=html).write_pdf(str(pdf_path))

print(f"\n✅ Successfully converted: {pdf_path}")

