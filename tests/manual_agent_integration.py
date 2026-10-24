from agent import ask_agent


question = (
    "Use the inventory analysis tool to check the current inventory. "
    "Tell me which products require reorder, "
    "and identify the product with the lowest estimated stock cover. "
    "Use the actual tool results."
)

answer = ask_agent(question)

print("Agent final answer:")
print(answer)
