import os
from openai import OpenAI

API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = "https://labs-ai-proxy.acloud.guru/rest/openai/chatgpt-4o/v1"

client = OpenAI(api_key=API_KEY)
client.base_url = BASE_URL
model = "openai/chatgpt-4o/"

messages = [
    {
        "role": "system",
        "content": "You are a poetic assistant, skilled in writing satirical doggerel with creative flair.",
    },
    {
        "role": "user",
        "content": "Compose a limerick about baboons and racoons.",
    },
]

response = client.chat.completions.create(
    model=model,
    messages=messages,
    stream=False,
)
