import json
from google.genai import types
from agent import client, config

test_cases = [
    {"input": "What's on my plate today?", "expected_tool": "triage_inbox"},
    {"input": "Summarize my inbox", "expected_tool": "triage_inbox"},
    {"input": "Am I forgetting any tasks?", "expected_tool": "check_stale_tasks"},
    {"input": "Any pending items I should worry about?", "expected_tool": "check_stale_tasks"},
    {"input": "Should I schedule a sync with my mentor?", "expected_tool": "check_mentor_meeting"},
    {"input": "How long since my last mentor check-in?", "expected_tool": "check_mentor_meeting"},
    {"input": "Book my mentor meeting for Thursday 11am", "expected_tool": "book_mentor_meeting"},
    {"input": "Finished the sprint demo, need to fix the login bug tomorrow", "expected_tool": "eod_wrapup"},
    {"input": "Wrap up my day: fixed the auth bug, blocked on staging deploy", "expected_tool": "eod_wrapup"},
]

correct = 0
for case in test_cases:
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=case["input"],
        config=config
    )
    part = response.candidates[0].content.parts[0]
    actual_tool = part.function_call.name if part.function_call else "no_tool_called"

    passed = actual_tool == case["expected_tool"]
    correct += passed
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] \"{case['input']}\" → expected: {case['expected_tool']}, got: {actual_tool}")

print(f"\nAccuracy: {correct}/{len(test_cases)} ({round(100*correct/len(test_cases))}%)")