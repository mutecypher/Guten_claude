#!/usr/bin/env python3
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage

llm = Ollama(model="llama3.1:8b", request_timeout=60.0)

response = llm.chat([
    ChatMessage(role="user", content="Who sailed down the Mississippi with Huck Finn?")
])

print(response.message.content)