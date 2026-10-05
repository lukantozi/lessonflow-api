# lessonflow-api

Python CLI that generates English lessons with the OpenAI API and saves
them as Markdown and PDF.

## Setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the project root:

```text
OPENAI_API_KEY=your_api_key_here
```

## Usage

```sh
python lesson_generator.py
```

Choose a CEFR level (A1–C2), reading format, two topics, and a grammar focus.

PDFs are copied to a lessons directory configured for my personal workflow.
Change that path before use.

API usage costs apply.

## License

MIT
