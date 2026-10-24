from unittest.mock import patch

from agent import ask_agent


def test_general_question_without_tools():
    expected_answer = (
        "An AI agent is a system that can understand a task "
        "and use tools to accomplish it."
    )

    fake_response = {
        "message": {
            "content": expected_answer,
            "tool_calls": [],
        }
    }

    with patch(
        "agent.ollama.chat",
        return_value=fake_response,
    ) as mock_chat:
        answer = ask_agent(
            "What is an AI agent? Explain in simple terms."
        )

    assert mock_chat.call_count == 1, (
        f"Expected 1 LLM call, got {mock_chat.call_count}"
    )

    assert answer == expected_answer, (
        f"Unexpected answer: {answer}"
    )

    print("GENERAL QUESTION WITHOUT TOOLS PASS")
    print("LLM calls:", mock_chat.call_count)
    print("Agent answer:", answer)


if __name__ == "__main__":
    test_general_question_without_tools()