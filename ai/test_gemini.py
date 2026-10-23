import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors
import httpx
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY was not found.")
    exit()

print("API key found.")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=15_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

models = ("gemini-3.5-flash-lite", "gemini-3.5-flash")
response = None

for model in models:
    print(f"Trying {model}...", flush=True)
    try:
        response = client.models.generate_content(
            model=model,
            contents="What is the capital of France? Answer with one word."
        )
        print(f"Answered by {model}:")
        print(response.text)
        break
    except httpx.TimeoutException:
        print(f"{model} timed out after 15 seconds; trying the next model.")
    except errors.APIError as error:
        if error.code not in (429, 500, 502, 503, 504):
            raise
        print(f"{model} is temporarily unavailable ({error.code}); trying next model.")

if response is None:
    raise RuntimeError("All configured Gemini models are temporarily unavailable.")