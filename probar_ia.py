import os

from dotenv import load_dotenv
from google import genai

# Cargar las variables del archivo .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "No se ha encontrado GEMINI_API_KEY en el archivo .env"
    )

# Crear el cliente de Gemini
client = genai.Client(api_key=api_key)

# Hacer una peticion sencilla
respuesta = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Responde en español: ¿qué es un informe de scouting futbolístico?"
)

print(respuesta.text)
