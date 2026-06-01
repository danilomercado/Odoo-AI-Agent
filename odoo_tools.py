# Herramienta LangChain para interactuar con el módulo CRM de Odoo vía XML-RPC.
# El agente de IA utiliza esta herramienta para crear Leads/Oportunidades de forma autónoma.

import os
import xmlrpc.client
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

ODOO_URL      = os.getenv("ODOO_URL")
ODOO_DB       = os.getenv("ODOO_DB")
ODOO_USER     = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")
OPENAI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Autenticador

def _autenticar_odoo() -> tuple[xmlrpc.client.ServerProxy, int]:
    """
    Autentica contra Odoo y devuelve (models_proxy, uid).
    Lanza RuntimeError si la autenticación falla.
    """
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

    if not uid: 
        raise RuntimeError(
            "Autenticación fallida en Odoo."
            "Verificá las variables ODOO_URL, ODOO_DB, ODOO_USER y ODOO_PASSWORD."
        )
    
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return models, uid

# Tool


@tool
def registrar_oportunidad_crm(
    nombre_cliente: str,
    correo: str,
    requerimiento: str
) -> str:
    """
    Registra una nueva oportunidad (Lead) en el módulo CRM de Odoo.

    Usá esta herramienta SIEMPRE que identifiques en el mensaje del usuario:
      - Un nombre de persona o empresa (nombre_cliente).
      - Una dirección de correo electrónico de contacto (correo).
      - Un requerimiento, necesidad, solicitud de presupuesto o consulta comercial
        que deba ser gestionada por el equipo de ventas (requerimiento).

    Parámetros:
        nombre_cliente : Nombre completo del contacto o razón social de la empresa.
        correo         : Dirección de e-mail del prospecto.
        requerimiento  : Descripción clara del pedido, necesidad o consulta del cliente.

    Retorna un mensaje de confirmación con el ID del Lead creado en Odoo,
    o un mensaje de error descriptivo si la operación falla.

    Ejemplo de cuándo invocarla:
        El usuario escribe: "Soy Juan Pérez, juan@acme.com, necesito cotizar 20 laptops."
        → nombre_cliente="Juan Pérez", correo="juan@acme.com",
          requerimiento="Cotización de 20 laptops"
    """
    try: 
        models, uid = _autenticar_odoo()

        # Payload
        lead_data = {
            "name": f"Oportunidad: {nombre_cliente}",
            "contact_name": nombre_cliente,
            "email_from": correo,
            "description": requerimiento,
            "type": "opportunity",
            "priority": "1",              # 0=normal | 1=alta
        }

        lead_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            "crm.lead", #modelo odoo
            "create", #met
            [lead_data], #lista
        )

        return(
            f"✅ Lead creado exitosamente en Odoo CRM.\n"
            f"   ID del Lead : {lead_id}\n"
            f"   Cliente     : {nombre_cliente}\n"
            f"   Correo      : {correo}\n"
            f"   Requerimiento: {requerimiento}"
        )
    
    except RuntimeError as auth_err:
        return f"❌ Error de autenticación: {auth_err}"

    except xmlrpc.client.Fault as xml_err:
        return f"❌ Error XML-RPC de Odoo: {xml_err.faultString}"

    except Exception as e:
        return f"❌ Error inesperado al crear el Lead: {type(e).__name__}: {e}"

