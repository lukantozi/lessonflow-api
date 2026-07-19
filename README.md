# lessonflow-api

Interactive Python CLI for generating structured English lesson packs with the OpenAI API.

Built for my teaching workflow: it generates a lesson from reusable prompts,
saves it as Markdown and PDF, and syncs the PDF to my lessons directory. It has
been used to create materials for 200+ real lessons.

## Features

- Selects a CEFR level from A1 to C2
- Suggests and accepts custom reading topics and grammar focuses
- Supports paragraph and dialogue reading formats
- Generates lessons with the OpenAI API
- Saves lessons as Markdown and PDF
- Includes small utilities for lesson cleanup and PDF-conversion testing

## Setup

```sh
git clone https://github.com/lukantozi/lessonflow-api.git
cd lessonflow-api

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```text
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run:

```sh
$ python lesson_generator.py
```

The program interactively asks for:

- CEFR level
- Reading format: paragraphs or dialogue
- Two reading topics
- Grammar focus

It then generates a Markdown lesson, converts it to PDF, and syncs the PDF to
the configured lessons directory.

```sh
Select difficulty level (A1, A2, B1, B2, C1, C2): B1
Reading format (P = paragraphs, D = dialogue-as-reading) [P/D]: P

-- Choices --
Reading 1 topics (1–5 human-centered • 6–10 situational):
1. A Day in the Life of an Artist
2. Meeting a New Neighbor
...

Reading 2 topics (1–5 knowledge/discovery • 6–10 situational/applied):
1. Discovering the Solar System
2. The Basics of Plant Care
...

Grammar focuses:
1. Present Simple vs. Present Continuous
2. Forming Questions with "Do" and "Does"
...

Use these suggestions? (y/n): y

Your choice for Topic 1 (psych/social or situational) (number or text): 1
[INFO] Selected Topic 1 (psych/social or situational): A Day in the Life of an Artist

Your choice for Topic 2 (knowledge or situational/applied) (number or text): 1
[INFO] Selected Topic 2 (knowledge or situational/applied): Discovering the Solar System

Your choice for Grammar Focus (number or text): 2
[INFO] Selected Grammar Focus: Forming Questions with "Do" and "Does"

[SELECTIONS]
Topic 1: A Day in the Life of an Artist
Topic 2: Discovering the Solar System
Grammar: Forming Questions with "Do" and "Does"
Reading mode: paragraphs

Generate lesson now? (y/n): y

[STEP] Generating lesson...
[STEP] Saving Markdown...

Saved Markdown: lessons/2026-07-19_13-49_B1_P_A_Day_in_the_Life_of_an_Artist_lesson.md
[STEP] Converting to PDF...
Converted to PDF: lessons/2026-07-19_13-49_B1_P_A_Day_in_the_Life_of_an_Artist_lesson.pdf
[STEP] Moving to Lessons...
Synced to configured lessons directory
[DONE]
```

## Tech

Python, OpenAI API, `python-dotenv`, Markdown, WeasyPrint, `pathlib`

## Notes

- Requires an OpenAI API key and incurs API usage costs.
- Generated lessons are reviewed and edited before use.
- The output sync directory is currently configured for my personal workflow.

## License

MIT
