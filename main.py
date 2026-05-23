# Inicializador

import os
import time
import requests
import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyAsT0BhvD0jCYA2Aj4CYezoGCRnr3Hjtng"
TELEGRAM_TOKEN = "8787645725:AAH7mnwBUrWzoVpaR-KtKkLk2QsJ4nMwHeo"
TELEGRAM_CHAT_ID = "7210756206"
PROJECT_TOPIC = "sistema de gestion empresarial con microservicios, autenticacion OAuth2, panel de administracion y API REST"

TOTAL_CYCLES = 8
SLEEP_SECONDS = 900

CYCLE_FOCUS = [
    "vision general del proyecto, objetivos de negocio, alcance funcional y stakeholders principales",
    "modelado de datos, esquema de base de datos relacional y no relacional, relaciones entre entidades y estrategia de migraciones",
    "arquitectura de microservicios, separacion de responsabilidades, contratos entre servicios y estrategia de comunicacion sincrona y asincrona",
    "flujos de usuario detallados, diagramas de navegacion, experiencia de usuario y accesibilidad",
    "infraestructura cloud, orquestacion de contenedores, estrategia CI/CD, monitoreo y observabilidad",
    "seguridad perimetral, gestion de secretos, autenticacion, autorizacion, cifrado en reposo y en transito",
    "estrategia de testing, cobertura de pruebas, pruebas de carga y plan de recuperacion ante desastres",
    "modelo de negocio, roadmap de producto, metricas clave de exito y plan de escalabilidad a 3 anos",
]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
accumulated_context = []


# Respuestas a requests

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunks = [text[i:i + 4096] for i in range(0, len(text), 4096)]
    for chunk in chunks:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        for attempt in range(5):
            try:
                response = requests.post(url, json=payload, timeout=30)
                response.raise_for_status()
                time.sleep(1)
                break
            except requests.exceptions.RequestException as error:
                wait = 10 * (attempt + 1)
                print(f"Error enviando mensaje intento {attempt + 1}: {error}. Reintentando en {wait}s.")
                time.sleep(wait)


def send_telegram_document(file_path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    for attempt in range(5):
        try:
            with open(file_path, "rb") as file_obj:
                response = requests.post(
                    url,
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},
                    files={"document": file_obj},
                    timeout=60,
                )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as error:
            wait = 15 * (attempt + 1)
            print(f"Error enviando documento intento {attempt + 1}: {error}. Reintentando en {wait}s.")
            time.sleep(wait)
    return False


def call_gemini(prompt):
    for attempt in range(6):
        try:
            result = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )
            return result.text
        except Exception as error:
            wait = 20 * (attempt + 1)
            print(f"Error Gemini intento {attempt + 1}: {error}. Reintentando en {wait}s.")
            time.sleep(wait)
    return "No se pudo obtener respuesta de Gemini despues de multiples intentos."


def build_cycle_prompt(cycle_index, focus):
    context_block = ""
    if accumulated_context:
        context_block = "\n\nCONTEXTO ACUMULADO DE CICLOS ANTERIORES:\n"
        for i, entry in enumerate(accumulated_context, start=1):
            context_block += f"\n--- CICLO {i} ({CYCLE_FOCUS[i - 1]}) ---\n{entry[:1500]}\n"

    return f"""Eres un arquitecto de software senior con 20 anos de experiencia en sistemas de escala empresarial.
Estas planificando el siguiente proyecto de software:

PROYECTO: {PROJECT_TOPIC}
CICLO ACTUAL: {cycle_index + 1} de {TOTAL_CYCLES}
ENFOQUE DE ESTE CICLO: {focus}
{context_block}

INSTRUCCIONES:
- NO repitas informacion que ya fue cubierta en ciclos anteriores.
- Profundiza exclusivamente en el enfoque de este ciclo.
- Usa encabezados claros y listas estructuradas.
- Sé tecnico, preciso y exhaustivo.
- El output debe ser sustancial y de alta calidad, no generico.
- No uses emojis en tu respuesta.

Genera el plan detallado para el enfoque indicado."""


def build_final_prompt():
    full_context = ""
    for i, entry in enumerate(accumulated_context, start=1):
        full_context += f"\n\n=== CICLO {i}: {CYCLE_FOCUS[i - 1]} ===\n{entry}"

    return f"""Eres el CTO de una corporacion tecnologica Fortune 500.
Has supervisado la planificacion completa del siguiente sistema:

PROYECTO: {PROJECT_TOPIC}

A continuacion tienes el contexto completo de todos los ciclos de planificacion:
{full_context}

Tu tarea es producir una SINTESIS MAGISTRAL Y DEFINITIVA que incluya obligatoriamente cada una de estas secciones:

1. RESUMEN EJECUTIVO DEL PROYECTO
   Descripcion del sistema, propuesta de valor y diferenciadores clave.

2. PASO 1 REAL PARA COMENZAR HOY
   Accion concreta, especifica y ejecutable que el equipo debe hacer manana en la manana.

3. ARQUITECTURA DE SOFTWARE RECOMENDADA
   Stack tecnologico definitivo, justificacion de cada decision, patrones de diseno y diagrama conceptual en texto.

4. PROTOCOLOS DE SEGURIDAD ESTRICTOS
   Lista exhaustiva de medidas: OWASP, gestion de secretos, WAF, pentest, compliance.

5. SERVICIOS Y SERVIDORES RECOMENDADOS
   Proveedor cloud, servicios especificos con nombres reales (AWS S3, RDS, etc.), configuracion de red.

6. COSTO ESTIMADO DE PRODUCCION Y DESPLIEGUE EN USD
   Desglose mensual y anual por servicio, equipo humano necesario y costo total del primer ano.

7. ESTRATEGIAS DE PROTECCION EMPRESARIAL CONTRA ATACANTES
   DDoS mitigation, zero trust, deteccion de intrusiones, plan de respuesta a incidentes.

8. VISION ESPECTACULAR DEL FUTURO DEL SISTEMA
   Como evolucionara el sistema en 1, 3 y 5 anos. Integracion con IA, expansion global y modelo de monetizacion.

Escribe con autoridad de CTO corporativo. Sin emojis. Con cifras reales, nombres de servicios reales y recomendaciones accionables."""


def save_cycle_output(cycle_index, content):
    filename = f"ciclo_{cycle_index + 1:02d}_planificacion.txt"
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"CICLO {cycle_index + 1} DE {TOTAL_CYCLES}\n")
        f.write(f"ENFOQUE: {CYCLE_FOCUS[cycle_index]}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)
    return filepath


def run_planning_cycle(cycle_index):
    focus = CYCLE_FOCUS[cycle_index]
    print(f"\nIniciando ciclo {cycle_index + 1}/{TOTAL_CYCLES}: {focus}")

    prompt = build_cycle_prompt(cycle_index, focus)
    response_text = call_gemini(prompt)
    accumulated_context.append(response_text)

    filepath = save_cycle_output(cycle_index, response_text)
    caption = f"Ciclo {cycle_index + 1}/{TOTAL_CYCLES} completado.\nEnfoque: {focus}"
    success = send_telegram_document(filepath, caption)

    if success:
        print(f"Ciclo {cycle_index + 1} enviado a Telegram correctamente.")
    else:
        print(f"Ciclo {cycle_index + 1} guardado localmente. No se pudo enviar a Telegram.")

    return response_text


def run_final_synthesis():
    print("\nGenerando sintesis final de nivel CTO...")
    prompt = build_final_prompt()
    synthesis = call_gemini(prompt)

    filepath = os.path.join(os.getcwd(), "sintesis_final_cto.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("SINTESIS FINAL - NIVEL CTO\n")
        f.write("=" * 60 + "\n\n")
        f.write(synthesis)

    send_telegram_message("Jefe termine de planificar todo")
    time.sleep(2)
    send_telegram_message(synthesis)
    send_telegram_document(filepath, "Sintesis final completa en documento adjunto.")

    print("Sintesis final enviada.")
    return synthesis


def main():
    print("Iniciando orquestador de planificacion autonoma.")
    print(f"Proyecto: {PROJECT_TOPIC}")
    print(f"Ciclos totales: {TOTAL_CYCLES} | Espera entre ciclos: {SLEEP_SECONDS // 60} minutos")

    send_telegram_message(
        f"*INICIO DE MISION DE PLANIFICACION*\n\nProyecto: {PROJECT_TOPIC}\n"
        f"Ciclos programados: {TOTAL_CYCLES}\nDuracion total estimada: {(TOTAL_CYCLES * SLEEP_SECONDS) // 60} minutos"
    )

    for cycle_index in range(TOTAL_CYCLES):
        run_planning_cycle(cycle_index)

        if cycle_index < TOTAL_CYCLES - 1:
            remaining = TOTAL_CYCLES - cycle_index - 1
            print(f"Esperando {SLEEP_SECONDS // 60} minutos antes del siguiente ciclo. Ciclos restantes: {remaining}")
            time.sleep(SLEEP_SECONDS)

    run_final_synthesis()
    print("\nMision completada. Todos los archivos guardados y enviados.")


# Finalizador

if __name__ == "__main__":
    main()
