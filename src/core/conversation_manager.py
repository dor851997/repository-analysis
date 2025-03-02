import uuid
from typing import List, Dict

# A simple in-memory conversation store.
conversation_store: Dict[str, List[Dict[str, str]]] = {}

def create_conversation() -> str:
    conv_id = str(uuid.uuid4())
    conversation_store[conv_id] = []
    return conv_id

def add_message(conv_id: str, role: str, content: str):
    if conv_id not in conversation_store:
        conversation_store[conv_id] = []
    conversation_store[conv_id].append({"role": role, "content": content})

def get_conversation(conv_id: str) -> List[Dict[str, str]]:
    return conversation_store.get(conv_id, [])

def clear_conversation(conv_id: str):
    if conv_id in conversation_store:
        del conversation_store[conv_id]