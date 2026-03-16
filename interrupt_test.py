"""
interrupt_test.py

Minimal orchestrator that demonstrates LangGraph human-in-the-loop interrupts.

Two tools are registered:
  1. get_weather      – runs automatically, no human approval needed.
  2. send_alert_email – pauses execution and asks the human to confirm before
                        sending, using LangGraph's interrupt() mechanism.

Run:
    python interrupt_test.py
"""

import os
from uuid import uuid4
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.types import interrupt, Command
from models.checkpointer import shared_checkpointer


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o-mini",
    api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),
)


# ---------------------------------------------------------------------------
# Tool 1 – runs without human involvement
# ---------------------------------------------------------------------------
@tool
def get_weather(city: str) -> str:
    """Return a fake weather report for the given city. No approval needed."""
    fake_data = {
        "london": "Cloudy, 12°C",
        "new york": "Sunny, 22°C",
        "tokyo": "Rainy, 18°C",
    }
    return fake_data.get(city.lower(), f"Weather data unavailable for '{city}'.")


# ---------------------------------------------------------------------------
# Tool 2 – pauses and asks for human confirmation before proceeding
# ---------------------------------------------------------------------------
@tool
def send_alert_email(recipient: str, subject: str, body: str) -> str:
    """
    Send an alert email.  Because this is a side-effectful action the tool
    pauses execution and waits for the human operator to approve or reject it.
    """
    # interrupt() suspends the graph at this point.
    # The dict passed to it is surfaced to whoever is resuming the graph.
    human_decision: str = interrupt(
        {
            "prompt": "An email is about to be sent. Do you approve? (yes/no)",
            "details": {
                "recipient": recipient,
                "subject": subject,
                "body": body,
            },
        }
    )

    if human_decision.strip().lower() in ("yes", "y"):
        # In a real scenario you would call an SMTP / SendGrid client here.
        return f"Email sent to {recipient} with subject '{subject}'."
    else:
        return f"Email to {recipient} was cancelled by the operator."


# ---------------------------------------------------------------------------
# Build the agent
# ---------------------------------------------------------------------------
agent = create_agent(
    model=llm,
    tools=[get_weather, send_alert_email],
    checkpointer=shared_checkpointer,
    system_prompt=(
        """
        You are a monitoring assistant. When the user asks you to check the
        weather and send an alert email, do both — call get_weather first,
        then call send_alert_email with a concise summary.
        """
    ),
)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run():
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    user_message = (
        "Check the weather in London and send an alert email to "
        "ops@example.com with the result."
    )

    print("=" * 60)
    print("USER:", user_message)
    print("=" * 60)

    # ── First invoke ──────────────────────────────────────────────────────
    # The agent will call get_weather (automatic) then hit the interrupt
    # inside send_alert_email and pause.
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config,
    )

    # Check whether the graph suspended at an interrupt
    interrupted = result.get("__interrupt__")
    if interrupted:
        payload = interrupted[0].value          # dict we passed to interrupt()
        print("\n[INTERRUPT] Human approval required:")
        print(f"  Prompt  : {payload['prompt']}")
        print(f"  Details : {payload['details']}")

        while True:
            human_input = input("\nYour decision (yes/no): ").strip().lower()
            if human_input in ("yes", "y", "no", "n"):
                break
            print("  Invalid input. Please enter 'yes' or 'no'.")

        # ── Resume with human answer ──────────────────────────────────────
        # Pass the human's answer back via Command(resume=...).
        final = agent.invoke(Command(resume=human_input), config=config)
        messages = final.get("messages", [])
    else:
        messages = result.get("messages", [])

    # Print the final assistant message
    for msg in reversed(messages):
        if hasattr(msg, "content") and getattr(msg, "type", "") == "ai":
            print("\n[ASSISTANT]:", msg.content)
            break


if __name__ == "__main__":
    run()
