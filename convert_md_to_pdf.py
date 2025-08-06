from pathlib import Path
from markdown import markdown
from weasyprint import HTML

# Paths
LESSONS_DIR = Path(__file__).parent / "lessons"
md_files = list(LESSONS_DIR.glob("*.md"))

if not md_files:
    raise FileNotFoundError("No .md files found in the lessons directory.")

# Use the most recent file (you can hardcode one instead if preferred)
md_path = max(md_files, key=lambda f: f.stat().st_mtime)
pdf_path = md_path.with_suffix(".pdf")

# Convert markdown to HTML
md_content = md_path.read_text(encoding="utf-8")
html_content = markdown(md_content, output_format="html5")

# Basic HTML wrapper to ensure clean rendering
full_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: 'DejaVu Sans', sans-serif;
      margin: 2em;
      line-height: 1.6;
    }}
    h1, h2, h3 {{
      color: #333;
    }}
    code {{
      background-color: #f4f4f4;
      padding: 2px 4px;
      font-family: monospace;
    }}
  </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Generate PDF
HTML(string=full_html).write_pdf(pdf_path)

print(f"\n✅ Converted {md_path.name} to PDF → {pdf_path.name}")

