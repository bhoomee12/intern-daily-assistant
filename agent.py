import os, json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MEMORY_PATH = "data/memory.json"

def load_memory():
    with open(MEMORY_PATH) as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)


# --- Tool 1: triage inbox ---
def triage_inbox():
    """Reads all emails and classifies each as reply_needed, fyi, or waiting_on_other."""
    with open("data/emails.json") as f:
        emails = json.load(f)

    results = []
    for email in emails:
        prompt = f"""Classify this email into exactly one category:
"reply_needed", "fyi", or "waiting_on_other".
Respond with ONLY the category word.

Subject: {email['subject']}
Body: {email['body']}"""
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        category = response.text.strip()
        results.append({"subject": email["subject"], "category": category})

    return results


# --- Tool 2: check stale tasks ---
def check_stale_tasks():
    """Checks memory.json for tasks that have been open for a while."""
    memory = load_memory()
    return [t["task"] for t in memory.get("tasks", []) if t["status"] == "open"]


# --- Tool 3: mentor meeting scheduler ---
def check_mentor_meeting():
    """Checks how long it's been since the last mentor meeting and suggests booking if overdue."""
    memory = load_memory()
    last_meeting = datetime.strptime(memory["last_mentor_meeting"], "%Y-%m-%d")
    days_since = (datetime.now() - last_meeting).days

    if days_since >= 7:
        return {
            "status": "overdue",
            "days_since_last_meeting": days_since,
            "suggested_slots": ["Tomorrow 3:00 PM", "Thursday 11:00 AM", "Friday 4:00 PM"]
        }
    else:
        return {"status": "on_track", "days_since_last_meeting": days_since}

# --- Tool 5: blocking meeting ---
def book_mentor_meeting(slot):
    """Books a mentor meeting for the given time slot and updates memory."""
    memory = load_memory()
    memory["last_mentor_meeting"] = datetime.now().strftime("%Y-%m-%d")
    memory["upcoming_mentor_meeting"] = slot
    save_memory(memory)
    return {"status": "booked", "slot": slot}

# --- Tool 4: EOD wrap-up ---
def eod_wrapup(notes):
    """Takes the user's rough end-of-day notes and turns them into a structured status update and tomorrow's plan. Also logs it to memory."""
    prompt = f"""The user gave these rough end-of-day notes:
"{notes}"

Turn this into:
1. A clean, professional status update (2-3 sentences)
2. A short prioritized to-do list for tomorrow (bullet points)

Format your response with clear headers "Status Update:" and "Tomorrow's Plan:"."""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )
    summary = response.text.strip()

    # persist to memory
    memory = load_memory()
    memory.setdefault("eod_logs", []).append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "raw_notes": notes,
        "summary": summary
    })
    save_memory(memory)

    return summary


# --- Register all four tools ---
tools = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="triage_inbox",
        description="Reads the user's inbox and classifies each email as reply_needed, fyi, or waiting_on_other. Use this when the user asks about their emails, inbox, or what needs attention.",
    ),
    types.FunctionDeclaration(
        name="check_stale_tasks",
        description="Checks for tasks that have been open for a while and might be forgotten. Use this when the user asks about pending tasks, to-dos, or what they might be forgetting.",
    ),
    types.FunctionDeclaration(
        name="check_mentor_meeting",
        description="Checks how long it's been since the user's last mentor meeting and suggests new time slots if overdue. Use this when the user asks about their mentor, 1:1s, check-ins, or syncs.",
    ),
    types.FunctionDeclaration(
        name="eod_wrapup",
        description="Turns the user's rough end-of-day notes into a clean status update and tomorrow's plan. Use this when the user shares what they did today, wants a daily summary, or wants to wrap up their day.",
        parameters=types.Schema(
            type="OBJECT",
            properties={"notes": types.Schema(type="STRING", description="The user's raw end-of-day notes")},
            required=["notes"]
        )
    ),
        types.FunctionDeclaration(
        name="book_mentor_meeting",
        description="Books a mentor meeting for a specific time slot the user has chosen. Use this ONLY when the user explicitly confirms or picks a time slot to book, not when they're just asking whether they should meet.",
        parameters=types.Schema(
            type="OBJECT",
            properties={"slot": types.Schema(type="STRING", description="The time slot the user chose, e.g. 'Tomorrow 3:00 PM'")},
            required=["slot"]
        )
    ),
])

config = types.GenerateContentConfig(tools=[tools])


# --- The agent loop, now with conversation memory ---
conversation_history = []

def run_agent(user_message):
    conversation_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=conversation_history,
        config=config
    )

    part = response.candidates[0].content.parts[0]

    if part.function_call:
        tool_name = part.function_call.name
        args = dict(part.function_call.args) if part.function_call.args else {}
        print(f"[agent decided to call tool: {tool_name}]")

        if tool_name == "triage_inbox":
            tool_result = triage_inbox()
        elif tool_name == "check_stale_tasks":
            tool_result = check_stale_tasks()
        elif tool_name == "check_mentor_meeting":
            tool_result = check_mentor_meeting()
        elif tool_name == "eod_wrapup":
            tool_result = eod_wrapup(args.get("notes", ""))
        elif tool_name == "book_mentor_meeting":
            tool_result = book_mentor_meeting(args.get("slot", ""))

        follow_up_prompt = f"""Tool result: {json.dumps(tool_result)}
Give a short, helpful natural-language response to the user based on this real result. Do not claim anything happened that isn't reflected in the tool result above."""

        follow_up = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=follow_up_prompt
        )
        answer = follow_up.text
    else:
        answer = part.text

    conversation_history.append(types.Content(role="model", parts=[types.Part(text=answer)]))
    print(answer)


# --- Try it ---
if __name__ == "__main__":
    print("Intern Daily Assistant — type 'quit' to exit\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        run_agent(user_input)
        print()