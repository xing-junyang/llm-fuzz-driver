from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
http_proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")

def generate_fuzz_driver_llm(prompt):
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    with open("../prompt_generator/gpt_prompt.txt", "r") as f:
        fread = f.read
        prompt = fread()
    response = generate_fuzz_driver_llm(prompt)
    print(response)