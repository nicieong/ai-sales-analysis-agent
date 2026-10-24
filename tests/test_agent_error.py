from unittest.mock import patch

from agent import ask_agent


def fake_ollama_chat(*args, **kwargs):
    """Simulate an LLM requesting a tool with invalid arguments."""
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


def test_agent_handles_invalid_tool_arguments():
    with patch(
        "agent.ollama.chat",
        side_effect=[
            fake_ollama_chat(),
            {
                "message": {
                    "role": "assistant",
                    "content": (
                        "The calculation could not be completed "
                        "because the price must be a number."
                    ),
                }
            },
        ],
    ) as mock_chat:
        answer = ask_agent("Calculate the total.")

    # The agent should call the LLM again after the tool error.
    assert mock_chat.call_count == 2

    # The final answer should explain the invalid price.
    assert "price must be a number" in answer.lower()

    # It must not present a fabricated numerical result.
    assert "800" not in answer

    print("Agent final answer:")
    print(answer)