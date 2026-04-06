"""A test script for gemma's installation"""

import ollama

response = ollama.chat(
    model='gemma4:e2b',
    messages=[{'role': 'user', 'content': 'Qui est tu? Que sais tu faire?'}]
)

print(response.message.content)
