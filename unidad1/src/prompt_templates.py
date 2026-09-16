"""Plantillas de prompting para el caso de uso: asistente de clasificación y
respuesta de reclamos de una billetera virtual.

Técnica aplicada (consigna 3): few-shot prompting + chain-of-thought.
- Few-shot: se muestran reclamos ya resueltos con la salida esperada.
- Chain-of-thought: se le pide al modelo razonar paso a paso antes de
  decidir la categoría y la prioridad.
"""

# --- Contexto del asistente (rol, reglas, categorías y prioridades) ---
INSTRUCCIONES_SISTEMA = """Sos el asistente de triage de reclamos de "BilleteraYa", una billetera virtual argentina.
Tu trabajo es analizar el reclamo de un cliente y devolver una clasificación y un borrador de respuesta que después revisa un operador humano.

Reglas:
- Nunca pidas contraseñas, códigos de verificación ni datos completos de tarjetas.
- No prometas reintegros ni plazos que no estén confirmados.
- Respondé en español argentino, con tono cordial y profesional.
- Los datos sensibles ya vienen enmascarados como [DATO].

Categorías posibles (usar exactamente uno de estos valores):
TRANSFERENCIAS, COBROS_Y_PAGOS, CUENTA_Y_ACCESO, SEGURIDAD_Y_FRAUDE, RENDIMIENTOS, OTROS

Criterios de prioridad:
- ALTA: posible fraude, dinero faltante o no acreditado, cuenta bloqueada.
- MEDIA: cobros incorrectos o problemas que afectan el uso pero sin pérdida de dinero.
- BAJA: consultas informativas o dudas generales."""

# --- Ejemplos few-shot de referencia (reclamos ficticios, datos enmascarados) ---
EJEMPLOS_FEW_SHOT = [
    {
        "consulta": "Hice una transferencia de $50.000 a la cuenta [DATO] hace dos días y todavía no le llegó a la otra persona. En mi app figura como enviada.",
        "respuesta": """{
  "razonamiento": "1) El problema principal es una transferencia enviada que no fue acreditada al destinatario. 2) Hay dinero en tránsito que el cliente no puede ubicar y pasaron 2 días, eso es señal de urgencia. 3) Categoría: TRANSFERENCIAS. Prioridad: ALTA por dinero no acreditado.",
  "categoria": "TRANSFERENCIAS",
  "prioridad": "ALTA",
  "resumen": "Transferencia de $50.000 enviada hace 2 días sin acreditar al destinatario.",
  "respuesta_sugerida": "Hola, gracias por avisarnos. Entendemos la preocupación. Ya derivamos tu caso al equipo de transferencias para rastrear la operación y te vamos a contactar a la brevedad con novedades. Por favor, no repitas la transferencia mientras lo revisamos."
}""",
    },
    {
        "consulta": "Me llegó un mensaje de alguien que dice ser de BilleteraYa pidiéndome el código que me llegó por SMS. ¿Es de ustedes?",
        "respuesta": """{
  "razonamiento": "1) El cliente reporta un contacto sospechoso que le pide un código de verificación. 2) Es un intento típico de phishing y hay riesgo de robo de cuenta, señal de urgencia aunque todavía no haya pérdida. 3) Categoría: SEGURIDAD_Y_FRAUDE. Prioridad: ALTA por posible fraude.",
  "categoria": "SEGURIDAD_Y_FRAUDE",
  "prioridad": "ALTA",
  "resumen": "Cliente recibió pedido de código SMS de un supuesto empleado: posible phishing.",
  "respuesta_sugerida": "Hola, gracias por consultarnos antes de hacer nada. BilleteraYa nunca te va a pedir códigos por mensaje ni por teléfono. No compartas ese código. Si ya lo compartiste, avisanos por este medio para bloquear preventivamente tu cuenta."
}""",
    },
    {
        "consulta": "Me cobraron dos veces la suscripción del streaming este mes, veo los dos débitos en mis movimientos.",
        "respuesta": """{
  "razonamiento": "1) El problema es un cobro duplicado de un servicio. 2) Hay un débito incorrecto pero identificado y sin indicios de fraude ni cuenta bloqueada. 3) Categoría: COBROS_Y_PAGOS. Prioridad: MEDIA.",
  "categoria": "COBROS_Y_PAGOS",
  "prioridad": "MEDIA",
  "resumen": "Débito duplicado de una suscripción de streaming en el mes.",
  "respuesta_sugerida": "Hola, gracias por escribirnos. Vamos a revisar los dos débitos junto con el comercio para verificar el cobro duplicado. Te vamos a informar el resultado del análisis por este medio."
}""",
    },
    {
        "consulta": "¿Cada cuánto se acreditan los rendimientos del dinero que tengo en la cuenta?",
        "respuesta": """{
  "razonamiento": "1) Es una consulta informativa sobre rendimientos. 2) No hay dinero faltante ni riesgo de seguridad. 3) Categoría: RENDIMIENTOS. Prioridad: BAJA.",
  "categoria": "RENDIMIENTOS",
  "prioridad": "BAJA",
  "resumen": "Consulta sobre la frecuencia de acreditación de rendimientos.",
  "respuesta_sugerida": "Hola, gracias por tu consulta. Los rendimientos se calculan y acreditan de forma periódica en tu cuenta; podés ver el detalle en la sección Rendimientos de la app. Si tenés alguna otra duda, escribinos."
}""",
    },
]

# --- Instrucción de razonamiento paso a paso (chain-of-thought) ---
INSTRUCCION_CHAIN_OF_THOUGHT = (
    "Antes de clasificar, razoná paso a paso: "
    "1) identificá el problema principal del cliente; "
    "2) detectá señales de urgencia (fraude, dinero faltante o no acreditado, cuenta bloqueada); "
    "3) recién después decidí la categoría y la prioridad. "
    "Escribí ese razonamiento en el campo \"razonamiento\"."
)

INSTRUCCION_FORMATO = (
    "Devolvé únicamente un objeto JSON válido con los campos "
    "razonamiento, categoria, prioridad, resumen y respuesta_sugerida, "
    "igual que en los ejemplos. No agregues texto fuera del JSON."
)


def construir_prompt_few_shot(consulta: str, ejemplos: list[dict] = EJEMPLOS_FEW_SHOT) -> str:
    """Arma un prompt few-shot: muestra pares reclamo/salida de ejemplo y
    al final agrega el reclamo real sin resolver."""
    bloques_ejemplo = [
        f"Reclamo: {ejemplo['consulta']}\nSalida: {ejemplo['respuesta']}"
        for ejemplo in ejemplos
    ]
    ejemplos_formateados = "\n\n".join(bloques_ejemplo)

    return (
        f"{ejemplos_formateados}\n\n"
        f"Reclamo: {consulta}\n"
        "Salida:"
    )


def construir_prompt_chain_of_thought(consulta: str) -> str:
    """Arma un prompt chain-of-thought sin ejemplos."""
    return f"{INSTRUCCIONES_SISTEMA}\n\n{INSTRUCCION_CHAIN_OF_THOUGHT}\n\nReclamo: {consulta}"


def construir_prompt_few_shot_cot(consulta: str, ejemplos: list[dict] = EJEMPLOS_FEW_SHOT) -> str:
    """Técnica elegida en la consigna 3: combina contexto del asistente,
    ejemplos resueltos (few-shot) y razonamiento paso a paso (CoT)."""
    return (
        f"{INSTRUCCIONES_SISTEMA}\n\n"
        f"{INSTRUCCION_CHAIN_OF_THOUGHT}\n\n"
        f"{INSTRUCCION_FORMATO}\n\n"
        "Ejemplos de reclamos resueltos:\n\n"
        f"{construir_prompt_few_shot(consulta, ejemplos)}"
    )