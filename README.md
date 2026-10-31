# Football Scout AI

Aplicación de scouting futbolístico que permite explorar jugadores a partir de sus estadísticas, filtrar candidatos por posición y minutos disputados, y generar un informe de scouting en español mediante Google Gemini.

## Qué hace el proyecto

El proyecto combina análisis de datos y una interfaz web:

1. Lee un conjunto de estadísticas de jugadores.
2. Limpia los datos y calcula métricas por cada 90 minutos.
3. Permite filtrar jugadores por perfil: delantero, centrocampista o defensa.
4. Ordena los resultados según un indicador principal del perfil seleccionado.
5. Envía las estadísticas del jugador seleccionado a Gemini para generar un informe interpretativo.
6. Puede crear un ranking ponderado de delanteros.

El informe generado por la IA debe considerarse una ayuda para el análisis, no una decisión automática de fichaje. La aplicación solo proporciona las estadísticas disponibles y no analiza vídeos, partidos, mapas de calor ni contexto táctico.

## Requisitos

- Python 3.10 o superior recomendado.
- Una clave de API de Google Gemini para generar informes con IA.
- Los archivos de datos CSV incluidos en el proyecto.
- Conexión a Internet únicamente para las peticiones a la API de Gemini.

## Estructura del proyecto

```text
football-scout-ai/
├── app.py                              # Interfaz web de Streamlit
├── scouting_ai.py                      # Integración con Google Gemini
├── limpiar_datos.py                    # Limpieza y transformación de datos
├── explorar_datos.py                   # Inspección y diagnóstico del dataset original
├── ranking_delanteros.py               # Generación de ranking de delanteros
├── probar_ia.py                         # Prueba rápida de conexión con Gemini
├── players_data-2025_2026.csv          # Dataset original principal
├── players_data_light-2025_2026.csv    # Variante ligera del dataset
├── players_clean.csv                    # Dataset preparado para la aplicación
├── ranking_delanteros.csv               # Resultado generado por el ranking
├── .env                                # Configuración local; no debe publicarse
└── .gitignore                          # Archivos excluidos del control de versiones
```

`players_clean.csv` se genera a partir de `players_data-2025_2026.csv` y es el archivo que consume `app.py`. La variante `players_data_light-2025_2026.csv` no se utiliza automáticamente por los scripts actuales.

## Instalación

Desde la carpeta raíz del proyecto, crea y activa un entorno virtual:

### macOS o Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Instala las dependencias:

```bash
python -m pip install --upgrade pip
python -m pip install pandas streamlit python-dotenv google-genai
```

## Configuración de Gemini

1. Crea una clave de API de Google Gemini.
2. Crea un archivo `.env` en la raíz del proyecto.
3. Añade la clave con este formato:

```env
GEMINI_API_KEY=tu_clave_de_gemini
```

No compartas este archivo ni subas la clave a Git. `.env` ya está incluido en `.gitignore`.

El modelo configurado actualmente en `scouting_ai.py` y `probar_ia.py` es `gemini-3.5-flash-lite`.

## Preparar los datos

Si `players_clean.csv` no existe o quieres regenerarlo después de actualizar el dataset original, ejecuta:

```bash
python limpiar_datos.py
```

El script:

- selecciona las columnas relevantes;
- convierte las estadísticas numéricas;
- elimina filas sin jugador, posición o minutos;
- calcula `Gls_90`, `Ast_90`, `Sh_90` y `SoT_90`;
- guarda el resultado en `players_clean.csv`.

El dataset original debe contener, como mínimo, estas columnas:

```text
Player, Nation, Pos, Squad, Comp, Age, MP, Min, Gls, Ast, Sh, SoT
```

## Ejecutar la aplicación

Con el entorno virtual activado y `players_clean.csv` disponible:

```bash
streamlit run app.py
```

Streamlit abrirá la aplicación en el navegador, normalmente en `http://localhost:8501`.

### Uso de la interfaz

En la barra lateral se puede seleccionar:

- **Perfil de jugador:** delantero, centrocampista o defensa.
- **Minutos mínimos:** filtra a los jugadores con suficiente participación.

La aplicación muestra los candidatos ordenados inicialmente por:

| Perfil | Indicador principal |
|---|---|
| Delantero | `Gls_90` |
| Centrocampista | `Ast_90` |
| Defensa | `Int` |

Después se puede seleccionar un jugador y pulsar **Generar informe de scouting**. Esa acción necesita una `GEMINI_API_KEY` válida y conexión a Internet.

Las posiciones mixtas, como `MF,FW`, se incluyen en cada perfil correspondiente.

## Scripts auxiliares

### Explorar el dataset

```bash
python explorar_datos.py
```

Muestra dimensiones, columnas, ejemplos, valores ausentes, estadísticas descriptivas, distribución por posición y duplicados del archivo original.

### Crear un ranking de delanteros

```bash
python ranking_delanteros.py
```

Analiza delanteros con al menos 900 minutos y calcula una puntuación de 0 a 100 usando estos pesos:

- `Gls_90`: 50 %
- `Ast_90`: 20 %
- `SoT_90`: 20 %
- `Shot_accuracy`: 10 %

El resultado se muestra en la terminal y se guarda en `ranking_delanteros.csv`. El archivo se puede regenerar y está excluido de Git.

### Probar la API de Gemini

```bash
python probar_ia.py
```

Realiza una petición sencilla para comprobar que la clave de API y la conexión funcionan correctamente.

## Métricas calculadas

Las métricas por 90 minutos se calculan así:

```text
estadística_por_90 = estadística / minutos * 90
```

La precisión de tiro de la aplicación y del ranking se calcula como:

```text
precisión_de_tiro = tiros_a_puerta / tiros * 100
```

Si un jugador no tiene tiros registrados, la precisión se deja sin valor. Las tasas por 90 deben interpretarse junto con los minutos disputados: una muestra pequeña puede producir valores poco representativos.

## Solución de problemas

### `FileNotFoundError: players_clean.csv`

Genera el archivo preparado:

```bash
python limpiar_datos.py
```

### No se genera el informe de IA

Comprueba que:

1. El archivo `.env` está en la raíz del proyecto.
2. La variable se llama exactamente `GEMINI_API_KEY`.
3. La clave es válida y tiene acceso a Gemini.
4. Existe conexión a Internet.

También puedes ejecutar `python probar_ia.py` para aislar el problema.

### No hay candidatos

Reduce el valor de **Minutos mínimos** o selecciona otro perfil. La aplicación requiere que el jugador tenga la posición seleccionada y cumpla el mínimo de minutos.

### Error al instalar dependencias

Comprueba que el entorno virtual está activado y ejecuta:

```bash
python -m pip install --upgrade pip
python -m pip install pandas streamlit python-dotenv google-genai
```

## Consideraciones y limitaciones

- Los nombres y columnas dependen del dataset CSV disponible.
- La aplicación no valida la calidad ni la fecha de actualización de los datos.
- El ranking de delanteros utiliza percentiles relativos al grupo filtrado, por lo que la puntuación depende de los jugadores presentes en el dataset.
- No se deben comparar directamente puntuaciones calculadas sobre datasets diferentes sin revisar el contexto.
- Las recomendaciones deportivas no deben basarse únicamente en estas estadísticas ni en el texto generado por la IA.

## Flujo recomendado

```text
Dataset original
      ↓
python limpiar_datos.py
      ↓
players_clean.csv
      ├── streamlit run app.py
      └── python ranking_delanteros.py
```

