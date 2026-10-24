from unittest.mock import patch

from agent import ask_agent


def test_unknown_tool_handling():
    fake_responses = [
        {
            "message": {
                "tool_calls": [
                    {
                        "function": {
                            "name": "unknown_tool",
                            "arguments": {},
                        }
                    }
                ]
            }
        },
        {
            "message": {
                "content": (
                    "I cannot execute that tool because it is not supported."
                )
            }
        },
    ]

    with patch("agent.ollama.chat", side_effect=fake_responses) as mock_chat:
        answer = ask_agent("Test unknown tool handling")

    assert mock_chat.call_count == 2, (
        f"Expected 2 LLM calls, got {mock_chat.call_count}"
    )

    assert isinstance(answer, str), (
        f"Expected a string answer, got {type(answer).__name__}"
    )

    assert answer == (
        "I cannot execute that tool because it is not supported."
    ), f"Unexpected answer: {answer}"

    print("UNKNOWN TOOL AGENT LOOP PASS")
    print("LLM calls:", mock_chat.call_count)
    print("Agent answer:", answer)


if __name__ == "__main__":
    test_unknown_tool_handling()