from unittest.mock import patch

from agent import ask_agent


def fake_ollama_chat(*args, **kwargs):
    """Simulate an LLM requesting a tool with invalid arguments."""
    from types import SimpleNamespace

    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "calculate_total",
                        "arguments": {
                            "price": "abc",
                            "quantity": 8,
                        },
                    }
                }
            ],
        }
    }


with patch("agent.ollama.chat", side_effect=[
    fake_ollama_chat(),
    {
        "message": {
            "role": "assistant",
            "content": "The calculation could not be completed because the price must be a number.",
        }
    },
]):
    answer = ask_agent("Calculate the total.")

print("Agent final answer:")
print(answer)
