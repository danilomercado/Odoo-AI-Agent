"""
app.py
------
Orquestador del Agente de IA — compatible con LangChain v0.3+
Usa LCEL (LangChain Expression Language) con bind_tools en lugar de AgentExecutor.
"""

import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

from odoo_tools import registrar_oportunidad_crm

# ---------------------------------------------------------------------------
# Carga de variables de entorno
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Configuración del LLM
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
Sos un asistente comercial inteligente de una empresa de tecnología.
Tu única responsabilidad es analizar mensajes de clientes potenciales,
extraer sus datos de contacto y su requerimiento, y registrarlos en el CRM.

Reglas:
1. Si el mensaje contiene nombre, correo y algún requerimiento comercial,
   invocá SIEMPRE la herramienta registrar_oportunidad_crm.
2. Extraé el requerimiento de forma clara y concisa (máx. 200 caracteres).
3. Si falta algún dato clave (nombre o correo), indicá qué información necesitás.
4. Respondé siempre en español.
"""

def build_llm_with_tools():
    """Instancia el LLM y le vincula las herramientas disponibles."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    tools = [registrar_oportunidad_crm]
    return llm.bind_tools(tools), tools


def run_agent(mensaje: str) -> str:
    """
    Loop de razonamiento:
    1. LLM decide si usar una tool y con qué argumentos
    2. Si hay tool_calls → ejecutamos la tool localmente
    3. Devolvemos el resultado al LLM para la respuesta final
    """
    llm_with_tools, tools = build_llm_with_tools()
    tools_map = {t.name: t for t in tools}

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=mensaje),
    ]

    print("\n> Enviando mensaje al LLM...")
    response = llm_with_tools.invoke(messages)
    messages.append(response)

    # Si el LLM decidió llamar a una herramienta
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            print(f"\n> Invocando herramienta: `{tool_name}`")
            print(f"  Argumentos: {json.dumps(tool_args, ensure_ascii=False, indent=2)}")

            # Ejecutar la tool localmente
            tool_fn = tools_map.get(tool_name)
            if tool_fn:
                tool_result = tool_fn.invoke(tool_args)
            else:
                tool_result = f"Herramienta '{tool_name}' no encontrada."

            print(f"\n> Resultado de la herramienta:\n  {tool_result}")

            # Agregar el resultado al historial de mensajes
            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
            )

        # Segunda llamada al LLM para generar la respuesta final en lenguaje natural
        final_response = llm_with_tools.invoke(messages)
        return final_response.content

    # Si no usó tools, devolver la respuesta directamente
    return response.content


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    mensaje_cliente = (
        "Hola, soy Danilo Mercado, mi mail es danilo@mail.com "
        "y estamos necesitando un presupuesto para la instalación "
        "de 50 servidores en nuestra planta de Rosario."
    )

    print("=" * 60)
    print("🤖  AGENTE CRM — Inicio de procesamiento")
    print("=" * 60)
    print(f"\n📩  Mensaje recibido:\n    {mensaje_cliente}")
    print("-" * 60)

    resultado = run_agent(mensaje_cliente)

    print("-" * 60)
    print(f"\n✅  Respuesta final del agente:\n    {resultado}")
    print("=" * 60)


if __name__ == "__main__":
    main()