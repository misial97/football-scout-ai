import os

from dotenv import load_dotenv
from google import genai

# Load variables from the .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "No se ha encontrado GEMINI_API_KEY en el archivo .env"
    )

# Create the Gemini client
client = genai.Client(api_key=api_key)

# Make a simple request
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Responde en español: ¿qué es un informe de scouting futbolístico?"
)

print(response.text)
