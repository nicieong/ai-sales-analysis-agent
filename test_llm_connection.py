import ollama


# 1. Define a real Python tool
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity


# 2. Describe the tool to the LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate_total",
            "description": "Calculate total price by multiplying unit price and quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "price": {
                        "type": "number",
                        "description": "Unit price"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity"
                    }
                },
                "required": ["price", "quantity"]
            }
        }
    }
]


# 3. Start the conversation
messages = [
    {
        "role": "user",
        "content": (
            "A product costs $12.50 each. "
            "I want to buy 8. Calculate the total using the tool."
        )
    }
]

response = ollama.chat(
    model="qwen3:4b",
    messages=messages,
    tools=tools,
)

# 4. Agent loop: execute tools and return results to the LLM
max_tool_rounds = 3

for round_number in range(max_tool_rounds):
    message = response["message"]

    # Save the assistant's response, including its tool call
    messages.append(message)

    tool_calls = message.get("tool_calls", [])

    # No more tool calls: the LLM has produced its final answer
    if not tool_calls:
        print("\nFinal answer:")
        print(message.get("content", "No text returned."))
        break

    # Execute each requested tool
    for tool_call in tool_calls:
        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]

        print(f"\nTool requested: {function_name}")
        print(f"Arguments: {arguments}")

        if function_name == "calculate_total":
            result = calculate_total(
                price=arguments["price"],
                quantity=arguments["quantity"],
            )
        else:
            result = {"error": f"Unknown tool: {function_name}"}

        print(f"Actual Python result: {result}")

        # Return the real tool result to the LLM
        messages.append({
            "role": "tool",
            "name": function_name,
            "content": str(result),
        })

    # Ask the LLM to continue using the updated conversation
    response = ollama.chat(
        model="qwen3:4b",
        messages=messages,
        tools=tools,
    )
else:
    print("\nStopped: maximum tool rounds reached.")