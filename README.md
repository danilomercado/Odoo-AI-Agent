# 🤖 Agente IA → Odoo CRM (PoC)

Pipeline: Texto libre del usuario → LLM (Function Calling) → Tool Python → XML-RPC → `crm.lead` en Odoo

---

## PASO 1 — Arquitectura Conceptual

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO DE DATOS                           │
│                                                                 │
│  Texto libre   ──►  LLM (GPT-4o)  ──►  Function Calling        │
│  del usuario         │                       │                  │
│                      │ analiza intención      │ genera JSON con  │
│                      │ y extrae entidades     │ argumentos       │
│                      ▼                       ▼                  │
│              AgentExecutor  ◄──────  registrar_oportunidad_crm  │
│              (LangChain)              (@tool de LangChain)       │
│                      │                       │                  │
│                      │                       │ xmlrpc.client    │
│                      │                       ▼                  │
│                      │              /xmlrpc/2/common            │
│                      │              authenticate() → uid        │
│                      │                       │                  │
│                      │                       ▼                  │
│                      │              /xmlrpc/2/object            │
│                      │              execute_kw('crm.lead',      │
│                      │                         'create', [...]) │
│                      │                       │                  │
│                      │                       ▼                  │
│                      └──────────────  Lead ID (int) ◄── Odoo   │
└─────────────────────────────────────────────────────────────────┘
```

**Piezas clave:**

| Componente                  | Rol                                                                         |
| --------------------------- | --------------------------------------------------------------------------- |
| `ChatOpenAI`                | LLM con soporte nativo de Function Calling                                  |
| `@tool` (LangChain)         | Convierte la función Python en un schema JSON Tool que el LLM puede invocar |
| `create_tool_calling_agent` | Agente que delega la decisión de "qué tool usar" al LLM                     |
| `AgentExecutor`             | Loop de razonamiento → acción → observación                                 |
| `xmlrpc.client`             | Cliente XML-RPC nativo de Python (stdlib), sin dependencias extra           |
| `execute_kw`                | Método universal de Odoo para CRUD sobre cualquier modelo                   |

El LLM **no ejecuta código**; solo decide qué función llamar y con qué argumentos (JSON). LangChain intercepta esa decisión y ejecuta la función Python real.

---

## PASO 2 — Configuración del Entorno

### Instalación de dependencias

```bash
# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# 2. Instalar dependencias
pip install -r requirements.txt
```

### Variables de entorno

```bash
cp .env.example .env
# Editá .env con tus credenciales reales
```

### Verificar conexión Odoo (opcional, diagnóstico rápido)

```python
import xmlrpc.client
common = xmlrpc.client.ServerProxy("https://TU-INSTANCIA.odoo.com/xmlrpc/2/common")
print(common.version())   # debe devolver info de la versión de Odoo
```

---

## PASO 3 — Estructura del Proyecto

```
odoo_crm_agent/
├── .env.example        ← Template de variables de entorno
├── .env                ← Tus credenciales reales (NO commitear)
├── requirements.txt    ← Dependencias pip
├── odoo_tools.py       ← Tool LangChain (@tool) + cliente XML-RPC
└── app.py              ← Orquestador: LLM + Agent + Entry point
```

---

## PASO 4 — Ejecución

```bash
python app.py
```

---

## PASO 5 — Output esperado en consola

```
============================================================
🤖  AGENTE CRM — Inicio de procesamiento
============================================================

📩  Mensaje recibido:
    Hola, soy Danilo Mercado, mi mail es danilo@mail.com y estamos
    necesitando un presupuesto para la instalación de 50 servidores
    en nuestra planta de Rosario.

------------------------------------------------------------

> Entering new AgentExecutor chain...

Invoking: `registrar_oportunidad_crm` with {
    "nombre_cliente": "Danilo Mercado",
    "correo": "danilo@mail.com",
    "requerimiento": "Presupuesto para instalación de 50 servidores en planta de Rosario"
}

✅ Lead creado exitosamente en Odoo CRM.
   ID del Lead : 42
   Cliente     : Danilo Mercado
   Correo      : danilo@mail.com
   Requerimiento: Presupuesto para instalación de 50 servidores en planta de Rosario

> Finished chain.

------------------------------------------------------------

✅  Respuesta final del agente:
    He registrado la oportunidad de Danilo Mercado (danilo@mail.com)
    en el CRM con el Lead ID #42. El equipo de ventas recibirá la
    solicitud de presupuesto para la instalación de 50 servidores
    en la planta de Rosario.

============================================================
```

---

## Extensiones recomendadas para el portafolio

| Feature                   | Cómo implementarlo                                             |
| ------------------------- | -------------------------------------------------------------- |
| Soporte multi-turn (chat) | Agregar `ConversationBufferMemory`                             |
| Webhook (Slack/WhatsApp)  | FastAPI endpoint → `agent.invoke()`                            |
| Más tools Odoo            | `buscar_cliente()`, `actualizar_lead()`, `crear_presupuesto()` |
| LLM alternativo           | Reemplazar `ChatOpenAI` por `ChatAnthropic` (mismo contrato)   |
| Tests unitarios           | Mockear `xmlrpc.client.ServerProxy` con `unittest.mock`        |
