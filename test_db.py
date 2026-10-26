
from backend.repositories.conversation_repository import (
    create_conversation,
    save_message,
    get_messages
)

conversation_id = create_conversation("Learning Python")

message_id = save_message(
    conversation_id=conversation_id,
    role="user",
    content="What is a Python function?",
    intent="teacher"
)

save_message(
    conversation_id=conversation_id,
    role="assistant",
    content="A function is a reusable block of code that performs a task.",
    intent="teacher"
)

print("Conversation ID:", conversation_id)
print("First message ID:", message_id)

messages = get_messages(conversation_id)

for message in messages:
    print(f"{message['role']}: {message['content']}")
