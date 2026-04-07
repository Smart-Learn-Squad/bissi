"""A test script for gemma's installation"""

import ollama
from configs.prompts import GLOBAL_SYSTEM_PROMPT

messages = [{'role': 'system', 'content': GLOBAL_SYSTEM_PROMPT}]

while True:
    user_input = input("You: ")
    if user_input.lower() in ['exit', 'quit', 'q']:
        break
    
    messages.append({'role': 'user', 'content': user_input})
    
    response = ollama.chat(
        model='gemma4:e4b',
        messages=messages
    )
    
    print(f"Bissi: {response.message.content}")
    messages.append({'role': 'assistant', 'content': response.message.content})
