# Intern Daily Assistant

An AI agent built to solve a real problem I had as a new intern: tracking emails, staying on top of tasks, and remembering to check in with my mentor. Built with Google's Gemini API using a hand-written ReAct-style agent loop (no framework), so I could actually understand the mechanics of tool calling and agent routing rather than relying on a black-box library.

## What it does

The agent exposes 5 tools and decides which one to call based on the natural language meaning of what you type — there's no hardcoded routing.

- **`triage_inbox`** — classifies emails as reply_needed / fyi / waiting_on_other
- **`check_stale_tasks`** — surfaces tasks that have been open for a while
- **`check_mentor_meeting`** — checks days since last mentor sync, suggests slots if overdue
- **`book_mentor_meeting`** — books a chosen slot and persists it to memory
- **`eod_wrapup`** — turns messy end-of-day notes into a structured status update + tomorrow's plan, and logs it

## How it works

1. User sends a natural language message
2. The model decides whether a tool is needed, and which one, based on tool descriptions (no hardcoded if/else routing on my end)
3. If a tool needs arguments (like `eod_wrapup`'s notes, or `book_mentor_meeting`'s slot), the model extracts them from the message itself
4. My code executes the actual tool function
5. The tool's result is fed back to the model, which generates a grounded natural-language response
6. Conversation history is maintained across turns, so follow-ups like "yes, book that" resolve correctly against earlier context

## A real bug I found and fixed

Early on, the agent would say "I've booked that for you!" without actually calling any booking tool — a classic hallucinated confirmation. I traced this to the agent having no memory between turns, so a follow-up like "yes, book it" had no context to resolve against. I fixed it by maintaining a conversation history list passed on every turn, and verified the fix by checking the underlying JSON file actually updated — not just that the response text sounded correct.

## Evaluation

I built a 9-case test set checking tool-routing accuracy: **8/9 (89%)**. The one failure ("What's on my plate today?" sometimes routes to task-checking instead of inbox-triage) reflects genuine ambiguity in the phrasing rather than a bug — a good reminder that LLM routing isn't fully deterministic and evaluation should account for that.

## Tech stack

- Python
- Google Gemini API (`gemini-3.5-flash-lite`)
- JSON files for data and persistent memory (no database needed at this scale)

## Setup

\`\`\`bash
pip install -r requirements.txt
\`\`\`

Create a `.env` file with:
\`\`\`
GEMINI_API_KEY=your-key-here
\`\`\`

Run the interactive assistant:
\`\`\`bash
python agent.py
\`\`\`

Run the evaluation suite:
\`\`\`bash
python evaluate.py
\`\`\`