import os
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_KEY_HERE")
print("Key loaded:", API_KEY[:8] + "..." if API_KEY != "PASTE_YOUR_KEY_HERE" else "NO KEY SET")

client = genai.Client(api_key=API_KEY)

print("Calling Gemini...")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello in one sentence.",
)
print("Response:", response.text)