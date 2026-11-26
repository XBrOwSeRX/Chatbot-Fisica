# ============================================================
# CHATBOT DE FÍSICA APLICADA - CON INTELIGENCIA ARTIFICIAL (MACHINE LEARNING)
# ============================================================

import streamlit as st
import re
import numpy as np
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="Chatbot Física Aplicada", page_icon="⚡", layout="centered")
st.title("⚡ Asistente Virtual de Física Aplicada")
st.markdown(
    "Hola. Soy tu tutor virtual. Puedo **explicarte fórmulas**, "
    "**resolver ejercicios paso a paso** y **mostrarte gráficas** de los 4 módulos del curso.\n\n"
    "Escribe **ayuda** para ver todos los temas."
)

# ------------------------------------------------------------
# ESTADO DE LA SESIÓN
# ------------------------------------------------------------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "flujo" not in st.session_state:
    st.session_state.flujo = None
if "datos" not in st.session_state:
    st.session_state.datos = {}
if "paso" not in st.session_state:
    st.session_state.paso = 0
if "grafica" not in st.session_state:
    st.session_state.grafica = None
if "q_rlc" not in st.session_state:
    st.session_state.q_rlc = 1
if "sugerencias" not in st.session_state:
    st.session_state.sugerencias = None  # temas que la IA propone cuando duda
if "graf_params" not in st.session_state:
    # Datos del último ejercicio de cada tema, para dibujar su gráfica
    st.session_state.graf_params = {}

for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------
# UTILIDADES Y FORMATOS
# ------------------------------------------------------------
def normalizar(texto):
    """Pasa a minúsculas y quita tildes para comparar palabras sin fallos."""
    texto = texto.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ü", "u")):
        texto = texto.replace(a, b)
    return texto

# Prefijos del SI escritos con símbolo (ej: 5 cm, 2 µC, 4.7 kΩ, 10 mH, 3 MHz)
PREFIJOS_SIMBOLO = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6,
                    "m": 1e-3, "c": 1e-2, "k": 1e3, "K": 1e3, "M": 1e6}
# Prefijos escritos con palabra (ej: 2 micro, 5 centimetros, 3 mili)
PREFIJOS_PALABRA = [("pico", 1e-12), ("nano", 1e-9), ("micro", 1e-6), ("mili", 1e-3),
                    ("centi", 1e-2), ("kilo", 1e3), ("mega", 1e6)]
# Unidades que pueden ir después de un prefijo
UNIDADES = {"m", "c", "f", "h", "t", "a", "v", "w", "j", "n", "s", "hz", "wb", "ω",
            "ohm", "ohms", "ohmio", "ohmios"}
SUPERINDICES = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")

def convertir_unidades(texto):
    """Lee un número con notación científica y prefijos del SI.
    Ejemplos válidos: '2 micro', '2 µC', '2e-6', '2x10^-6', '2×10⁻⁶', '5 cm', '4,7 kΩ', '60 Hz'."""
    texto = texto.replace(",", ".").replace("−", "-").translate(SUPERINDICES)
    patron = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    match = re.search(patron, texto)
    if not match:
        return None
    valor = float(match.group())
    resto = texto[match.end():]

    # Notación tipo 2x10^-6 / 2 × 10^-6 / 2*10-6
    pot = re.match(r"\s*[x×*]\s*10\s*\^?\s*([-+]?\d+)", resto)
    if pot:
        valor *= 10 ** int(pot.group(1))
        resto = resto[pot.end():]

    # Primera palabra después del número (la unidad)
    unidad = re.match(r"\s*([^\s\d.,;:!?()]+)", resto)
    if not unidad:
        return valor
    token = unidad.group(1)
    token_min = normalizar(token)
    cuadrado = resto[unidad.end():unidad.end() + 1] in ("2", "²") or token.endswith("²")
    token = token.rstrip("²")

    multiplicador = 1.0
    for palabra, factor in PREFIJOS_PALABRA:
        if token_min.startswith(palabra):
            multiplicador = factor
            break
    else:
        if len(token) >= 2 and token[0] in PREFIJOS_SIMBOLO and normalizar(token[1:]) in UNIDADES:
            multiplicador = PREFIJOS_SIMBOLO[token[0]]
        elif token in ("k", "K", "M", "µ", "μ", "u"):  # prefijo suelto: "1k", "4.7k ohm", "10 u"
            multiplicador = PREFIJOS_SIMBOLO[token]

    if cuadrado:  # ej: 20 cm² -> el prefijo se eleva al cuadrado
        multiplicador **= 2
    return valor * multiplicador

# Se mantiene el nombre anterior para no romper el resto del código
extraer_numero = convertir_unidades

def formato_cientifico(numero, decimales=2):
    if numero == 0:
        return "0"
    formato = f"{numero:.{decimales}e}" 
    mantisa, exponente = formato.split('e')
    return f"{mantisa} × 10^{int(exponente)}"

def formato_inteligente(numero):
    if numero == 0:
        return "0"
    if 0.01 <= abs(numero) < 10000:
        return f"{numero:.4g}" 
    else:
        return formato_cientifico(numero)

C_LUZ = 3e8  # velocidad de la luz (m/s)

def aviso_valor(nombre, valor, limite, sugerencia):
    """Devuelve una advertencia si un dato es sospechosamente grande (posible error de unidades)."""
    if abs(valor) > limite:
        return (f"\n\n⚠️ **Revisa tus datos:** {nombre} = {formato_inteligente(valor)} es un valor muy grande "
                f"para un ejercicio típico. {sugerencia}")
    return ""

# ------------------------------------------------------------
# RESPUESTAS TEÓRICAS
# ------------------------------------------------------------
def respuesta_teorica(p):
    # Pasamos todo a minúsculas y quitamos las tildes para evitar fallos
    p = normalizar(p)

    if "coulomb" in p:
        return ("⚡ **Ley de Coulomb:**\n\n"
                "**Concepto:** Describe la fuerza eléctrica de atracción o repulsión entre dos cargas puntuales.\n"
                "**Fórmula:** F = k * (|q1 * q2|) / r²\n"
                "**Dato clave:** k = 9×10⁹ N·m²/C². Si las cargas tienen el mismo signo se repelen, si son opuestas se atraen.\n\n"
                "*Escribe 'resuelve un ejercicio de coulomb' si quieres que calculemos uno paso a paso.*")
                
    elif "campo" in p and "electrico" in p:
        return ("🔋 **Campo Eléctrico:**\n\n"
                "**Concepto:** Es la fuerza eléctrica que experimenta una unidad de carga en un punto del espacio.\n"
                "**Fórmula:** E = F / q\n"
                "**Unidades:** Se mide en Newtons por Coulomb (N/C) o Voltios por metro (V/m).\n\n"
                "*Escribe 'resuelve un ejercicio de campo' para practicar.*")
                
    elif "carga" in p and "electrica" in p:
        return ("⚛️ **Carga Eléctrica:**\n\n"
                "**Concepto:** Propiedad fundamental de la materia que se manifiesta mediante fuerzas de atracción o repulsión (positiva y negativa).\n"
                "**Fórmula:** Q = n * e\n"
                "**Dato clave:** e = 1.602 x 10⁻¹⁹ C (carga del electrón). La carga siempre está cuantizada.\n\n"
                "*Escribe 'resuelve un ejercicio de carga' para calcular el número de electrones.*")
                
    elif "gauss" in p:
        return ("🌐 **Ley de Gauss:**\n\n"
                "**Concepto:** El flujo eléctrico neto a través de una superficie cerrada es proporcional a la carga neta encerrada.\n"
                "**Fórmula:** Φ = Q_encerrada / ε₀\n\n"
                "*Esta es una ley fundamental del electromagnetismo.*")
                
    elif "potencial" in p:
        return ("🔌 **Potencial Eléctrico:**\n\n"
                "**Concepto:** Es la energía potencial eléctrica por unidad de carga en un punto.\n"
                "**Fórmulas:** V = U / q  |  Carga puntual: V = k·q / r\n"
                "**Unidades:** Se mide en Voltios (V).\n\n"
                "*Escribe 'resuelve un ejercicio de potencial' para calcularlo.*")
                
    elif "capacitor" in p or "capacitancia" in p:
        return ("🔋 **Capacitores:**\n\n"
                "**Concepto:** Dispositivo que almacena energía en forma de campo eléctrico.\n"
                "**Fórmula principal:** C = Q / V\n"
                "**Asociaciones:** En serie: 1/Ct = 1/C1 + 1/C2. En paralelo: Ct = C1 + C2.\n\n"
                "*Escribe 'resuelve un ejercicio de capacitor' para calcular la energía almacenada (U = ½·C·V²).*")
                
    elif "ohm" in p:
        return ("📏 **Ley de Ohm:**\n\n"
                "**Concepto:** La corriente que pasa por un conductor es directamente proporcional al voltaje aplicado.\n"
                "**Fórmula:** V = I * R\n"
                "**Variables:** V (Voltaje), I (Corriente), R (Resistencia).\n\n"
                "*Escribe 'resuelve un ejercicio de ohm' si quieres calcular V, I o R.*")
                
    elif "resistencia" in p and ("serie" in p or "paralelo" in p):
        return ("🔗 **Resistencias en Serie y Paralelo:**\n\n"
                "**En Serie:** Se suman directamente -> Req = R1 + R2 + ...\n"
                "**En Paralelo:** Se suman los inversos -> 1/Req = 1/R1 + 1/R2 + ...\n\n"
                "*Escribe 'resuelve un ejercicio de resistencias' para practicar.*")
                
    elif "potencia" in p:
        return ("⚡ **Potencia Eléctrica:**\n\n"
                "**Concepto:** Es la energía consumida o generada por un circuito por unidad de tiempo.\n"
                "**Fórmulas:** P = V * I  |  P = I² * R  |  P = V² / R\n"
                "**Unidades:** Se mide en Watts (W).\n\n"
                "*Escribe 'resuelve un ejercicio de potencia' para calcularla.*")
                
    elif "kirchhoff" in p:
        return ("🔀 **Leyes de Kirchhoff:**\n\n"
                "**1ra Ley (Nodos):** La suma de corrientes que entran a un nodo es igual a la suma de las que salen.\n"
                "**2da Ley (Mallas):** La suma algebraica de los voltajes en una malla cerrada es cero.\n\n"
                "*Escribe 'resuelve un ejercicio de kirchhoff' para ver un ejemplo.*")
                
    elif "circuito rc" in p or "transitorio" in p:
        return ("⏱️ **Circuito RC:**\n\n"
                "**Concepto:** Circuito con resistencia y capacitor. La constante de tiempo indica qué tan rápido se carga o descarga.\n"
                "**Fórmulas:** τ = R·C  |  Carga: Vc(t) = V·(1 − e^(−t/τ))  |  Descarga: Vc(t) = V·e^(−t/τ)\n\n"
                "*Escribe 'resuelve un ejercicio de circuito rc' para calcular el tiempo.*")
                
    elif "campo" in p and "magnetico" in p:
        return ("🧭 **Campo Magnético de un conductor recto:**\n\n"
                "**Concepto:** Una corriente eléctrica crea un campo magnético en forma de círculos alrededor del cable.\n"
                "**Fórmula:** B = μ₀ · I / (2π · r)\n"
                "**Dato clave:** μ₀ = 4π×10⁻⁷ T·m/A. El sentido se obtiene con la regla de la mano derecha. Se mide en Teslas (T).\n\n"
                "*Escribe 'resuelve un ejercicio de campo magnetico' para calcularlo.*")

    elif "magnetica" in p and "fuerza" in p:
        return ("🧲 **Fuerza Magnética:**\n\n"
                "**Concepto:** Fuerza que ejerce un campo magnético sobre una carga en movimiento.\n"
                "**Fórmula:** F = q * (v × B)  →  módulo: F = |q| · v · B · sen(θ)\n"
                "**Dato clave:** Es perpendicular a la velocidad y al campo magnético. Es máxima con θ = 90° y nula con θ = 0° o 180°.\n\n"
                "*Escribe 'resuelve un ejercicio de fuerza magnetica' para practicar.*")
                
    elif "faraday" in p or "lenz" in p:
        return ("🔄 **Ley de Faraday y Lenz:**\n\n"
                "**Faraday:** Un campo magnético variable genera una fuerza electromotriz inducida. Fórmula: ε = -N · ΔΦ/Δt, con Φ = B · A · cos(θ).\n"
                "**Lenz:** La corriente inducida siempre se opone al cambio que la produjo.\n\n"
                "*Escribe 'resuelve un ejercicio de faraday' para calcular la fem.*")
                
    elif "alterna" in p or "eficaz" in p or "rms" in p:
        return ("〰️ **Corriente Alterna (CA):**\n\n"
                "**Concepto:** La corriente y el voltaje varían cíclicamente en el tiempo.\n"
                "**Fórmulas:** V_rms = V_max / √2  |  I_rms = V_rms / R  |  P = V_rms · I_rms  |  ω = 2πf\n"
                "**Dato clave:** El valor eficaz (RMS) equivale al de una corriente continua que produce el mismo efecto térmico.\n\n"
                "*Escribe 'resuelve un ejercicio de corriente alterna' para calcularlo.*")
                
    elif "impedancia" in p or "rlc" in p:
        return ("📈 **Impedancia y Resonancia RLC:**\n\n"
                "**Impedancia (Z):** Es la oposición total al flujo de corriente alterna. Combina la resistencia (R) y la reactancia (X).\n"
                "**Resonancia:** Ocurre cuando la reactancia inductiva (Xl) iguala a la capacitiva (Xc), minimizando la impedancia.\n\n"
                "**Fórmulas:** X_L = 2πfL  |  X_C = 1/(2πfC)  |  Z = √(R² + (X_L − X_C)²)  |  f₀ = 1/(2π√(LC))\n\n"
                "*Escribe 'resuelve un ejercicio de rlc' para calcular la impedancia, o 'muéstrame la gráfica de resonancia' para ver la curva.*")
                
    elif "diodo" in p and "zener" not in p:
        return ("💡 **Diodo Semiconductor:**\n\n"
                "**Concepto:** Componente que permite el paso de corriente en un solo sentido (polarización directa) y lo bloquea en el inverso.\n"
                "**Dato clave:** En silicio, la barrera de potencial es de aproximadamente 0.7 V.\n\n"
                "*Escribe 'resuelve un ejercicio de diodo' para calcular la corriente en un circuito.*")
                
    elif "semiconductor" in p:
        return ("🔬 **Semiconductores:**\n\n"
                "**Concepto:** Materiales con conductividad intermedia entre un conductor y un aislante.\n"
                "**Dopaje:** Tipo N (exceso de electrones, carga negativa) y Tipo P (exceso de huecos, carga positiva).\n\n"
                "*Escribe 'muéstrame la gráfica del diodo' para ver la curva I-V.*")
                
    elif "zener" in p:
        return ("🛡️ **Diodo Zener:**\n\n"
                "**Concepto:** Diodo especial que permite el flujo de corriente en polarización inversa cuando se alcanza su voltaje Zener.\n"
                "**Uso:** Se utiliza para regular el voltaje en circuitos.\n\n"
                "*Escribe 'resuelve un ejercicio de zener' para ver un ejemplo de regulación.*")
                
    else:
        return None

# ------------------------------------------------------------
# DETECCIÓN DE INTENCIONES
# ------------------------------------------------------------
def detectar_ejercicio(p):
    p = normalizar(p)
    gatillos = ["resuelve", "resuelbe", "calcula", "ejercicio", "problema", "ayuda", "quiero calcular", "hazme"]
    if not any(w in p for w in gatillos):
        return None

    # ----- Módulo 3: Magnetismo y Corriente Alterna -----
    if "magnetic" in p and "fuerza" in p:
        return "fuerza_magnetica"
    if "campo" in p and "magnetico" in p:
        return "campo_magnetico"
    if "faraday" in p or "lenz" in p or "inducid" in p or "induccion" in p:
        return "faraday"
    if "rlc" in p or "impedancia" in p or "resonancia" in p:
        return "rlc"
    if "alterna" in p or "rms" in p or "eficaz" in p:
        return "alterna"

    # ----- Temas que antes solo tenían teoría -----
    if "zener" in p:  # va antes que "diodo", porque "diodo zener" contiene ambas palabras
        return "zener"
    if re.search(r"\brc\b", p) or "constante de tiempo" in p:
        return "circuito_rc"
    if "kirchhoff" in p or "kirchof" in p or re.search(r"\b(mallas?|nodos?)\b", p):
        return "kirchhoff"
    if "potencial" in p:
        return "potencial"

    # ----- Resto de módulos -----
    if ("coulom" in p or "fuerza electrica" in p) and any(w in p for w in gatillos):
        return "coulomb"
    if "ohm" in p and any(w in p for w in gatillos):
        return "ohm"
    if "potencia" in p and "potencial" not in p and any(w in p for w in gatillos):
        return "potencia"
    if "capacitor" in p and any(w in p for w in gatillos):
        return "capacitor"
    if "diodo" in p and any(w in p for w in gatillos):
        return "diodo"
    if "campo" in p and any(w in p for w in gatillos):
        return "campo"
    if "carga" in p and any(w in p for w in gatillos):
        return "carga"
    if "resistencia" in p and any(w in p for w in gatillos):
        return "resistencia"    
    return None

def detectar_grafica(p):
    # Pasamos todo a minúsculas y reemplazamos tildes para que no falle
    p = normalizar(p)

    if "grafica" in p or "grafico" in p or "curva" in p or "muestra" in p:
        # ----- Módulo 3 -----
        if "fuerza" in p and "magnetic" in p:
            return "fuerza_magnetica"
        if "campo" in p and "magnetico" in p:
            return "campo_magnetico"
        if "faraday" in p or "lenz" in p or "induc" in p or "flujo" in p:
            return "faraday"
        if "alterna" in p or "senoidal" in p or "sinusoidal" in p or "rms" in p:
            return "alterna"
        # ----- Otros módulos -----
        if "potencial" in p:
            return "potencial"
        if re.search(r"\brc\b", p) and "descarga" not in p:
            return "carga_capacitor"
        if "diodo" in p or "i-v" in p:
            return "diodo"
        # "descarga" contiene la palabra "carga", por eso se revisa primero
        if "descarga" in p and "capacitor" in p:
            return "descarga_capacitor"
        if "carga" in p and "capacitor" in p:
            return "carga_capacitor"
        if "ohm" in p or "v-i" in p:
            return "ohm"
        if "resonancia" in p or "rlc" in p:
            return "resonancia"
    return None

# ------------------------------------------------------------
# INICIAR FLUJOS
# ------------------------------------------------------------
def iniciar_flujo(nombre):
    st.session_state.flujo = nombre
    st.session_state.datos = {}
    st.session_state.paso = 0
    if nombre == "coulomb":
        return "¡Claro! Vamos a calcular la **fuerza eléctrica (Ley de Coulomb)**. Pásame la **carga q1 en Coulombs (C)**."
    if nombre == "ohm":
        return "¡Claro! Vamos con la **Ley de Ohm (V = I * R)**. ¿Qué quieres calcular: **voltaje**, **corriente** o **resistencia**?"
    if nombre == "potencia":
        return "¡Claro! Vamos con **Potencia (P = V * I)**. Pásame el **voltaje (V)** en Voltios."
    if nombre == "capacitor":
        return "¡Claro! Vamos a calcular la **energía de un capacitor (U = ½ · C · V²)**. Pásame la **capacitancia (C) en Faradios (F)**."
    if nombre == "diodo":
        return "¡Claro! Vamos a resolver un **circuito con diodo de silicio (0.7 V)**. Pásame el **voltaje de la fuente (V) en Voltios**."
    if nombre == "campo":
        return "¡Claro! Vamos a calcular el **Campo Eléctrico (E = F/q)**. Pásame la **fuerza (F) en Newtons**."
    if nombre == "carga":
        return "¡Claro! Vamos a calcular la **Carga Eléctrica (Q = n * e)**. Pásame el **número de electrones (n)**."
    if nombre == "resistencia":
        return "¡Claro! Vamos a calcular la **Resistencia Equivalente**. Pásame el valor de **R1 en Ohmios**."
    if nombre == "potencial":
        return ("¡Claro! Vamos a calcular el **Potencial Eléctrico de una carga puntual (V = k·q / r)**. "
                "Pásame la **carga q en Coulombs (C)** (ej: 2 micro, −3 µC).")
    if nombre == "kirchhoff":
        return ("¡Claro! Vamos a resolver un **circuito de dos mallas con las Leyes de Kirchhoff**. Este es el circuito:\n\n"
                "```\n"
                "  ┌──R1──┬──R2──┐\n"
                "  │      A      │\n"
                " (+)     │     (+)\n"
                "  E1     R3     E2\n"
                " (−)     │     (−)\n"
                "  └──────┴──────┘\n"
                "```\n"
                "Dos fuentes (E1 y E2, con el polo + arriba) alimentan una resistencia central R3.\n\n"
                "Pásame el **voltaje de la fuente E1 en Voltios**.")
    if nombre == "circuito_rc":
        return ("¡Claro! Vamos a analizar la **carga de un capacitor en un circuito RC (τ = R·C)**. "
                "Pásame la **resistencia R en Ohmios (Ω)** (ej: 10 kΩ).")
    if nombre == "zener":
        return ("¡Claro! Vamos a resolver un **regulador de voltaje con diodo Zener**. Este es el circuito:\n\n"
                "```\n"
                "  ┌──Rs──┬──────┐\n"
                " (+)     │      │\n"
                "  Vs   Zener    RL  (carga)\n"
                " (−)     │      │\n"
                "  └──────┴──────┘\n"
                "```\n"
                "Pásame el **voltaje de la fuente Vs en Voltios**.")
    # ----- Módulo 3 -----
    if nombre == "fuerza_magnetica":
        return ("¡Claro! Vamos a calcular la **Fuerza Magnética sobre una carga (F = |q|·v·B·sen θ)**. "
                "Pásame la **carga q en Coulombs (C)** (ej: 2 micro, 1.6e-19).")
    if nombre == "campo_magnetico":
        return ("¡Claro! Vamos a calcular el **Campo Magnético de un conductor recto (B = μ₀·I / 2πr)**. "
                "Pásame la **corriente I en Amperios (A)**.")
    if nombre == "faraday":
        return ("¡Claro! Vamos a calcular la **fem inducida (Ley de Faraday: ε = −N·ΔΦ/Δt)**. "
                "Pásame el **número de espiras N** de la bobina.")
    if nombre == "alterna":
        return ("¡Claro! Vamos con **Corriente Alterna**. Calcularemos valores eficaces (RMS) y la potencia. "
                "Pásame el **voltaje máximo (pico) V_max en Voltios**.")
    if nombre == "rlc":
        return ("¡Claro! Vamos a resolver un **circuito RLC en serie**. Calcularemos reactancias, impedancia, "
                "corriente y frecuencia de resonancia. Pásame la **resistencia R en Ohmios (Ω)**.")
# ------------------------------------------------------------
# CONTINUAR FLUJO (CON VALIDACIÓN DE ERRORES)
# ------------------------------------------------------------
def continuar_flujo(texto):
    flujo = st.session_state.flujo
    datos = st.session_state.datos
    paso = st.session_state.paso

    # ========== FLUJO COULOMB ==========
    if flujo == "coulomb":
        if paso == 0:
            n = convertir_unidades(texto) 
            if n is None:
                return "No detecté un número. Pásame la **carga q1 en C** (ej: 2 micro)."
            datos["q1"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **carga q2 en C**."
        elif paso == 1:
            n = convertir_unidades(texto) 
            if n is None:
                return "No detecté un número. Pásame la **carga q2 en C** (ej: 3 micro)."
            datos["q2"] = n
            st.session_state.paso = 2
            return "Bien. Ahora pásame la **distancia r en metros (m)**."
        elif paso == 2:
            n = convertir_unidades(texto) 
            if n is None:
                return "No detecté un número. Pásame la **distancia r en m** (ej: 5 centi)."
            if n == 0:
                return "❌ **Error físico:** La distancia no puede ser 0. Por favor, pásame una **distancia mayor a 0**."
            datos["r"] = n
            k = 9e9
            F = k * abs(datos["q1"] * datos["q2"]) / (datos["r"] ** 2)
            tipo = "repulsión" if datos["q1"] * datos["q2"] > 0 else "atracción"
            st.session_state.flujo = None
            q1_f = formato_inteligente(datos['q1'])
            q2_f = formato_inteligente(datos['q2'])
            r_f = formato_inteligente(datos['r'])
            F_f = formato_inteligente(F)
            aviso = (aviso_valor("q1", datos["q1"], 1e-2, "¿Quisiste escribir microcoulombs (ej: 2 micro)?")
                     or aviso_valor("q2", datos["q2"], 1e-2, "¿Quisiste escribir microcoulombs (ej: 3 micro)?"))
            return (f"✅ **Resultado:** F = {F_f} N\n\n"
                    f"**Fórmula:** F = k·|q1·q2|/r² = 9x10⁹ · |({q1_f})·({q2_f})| / ({r_f})²\n\n"
                    f"La fuerza es de **{tipo}**.{aviso}")

    # ========== FLUJO LEY DE OHM ==========
    if flujo == "ohm":
        if paso == 0:
            t = texto.lower()
            if "voltaje" in t or t.strip() == "v":
                datos["incognita"] = "V"
                st.session_state.paso = 1
                return "Ok, calcularemos **V**. Pásame la **corriente I en Amperios (A)**."
            elif "corriente" in t or t.strip() == "i":
                datos["incognita"] = "I"
                st.session_state.paso = 1
                return "Ok, calcularemos **I**. Pásame el **voltaje V en Voltios**."
            elif "resistencia" in t or t.strip() == "r":
                datos["incognita"] = "R"
                st.session_state.paso = 1
                return "Ok, calcularemos **R**. Pásame el **voltaje V en Voltios**."
            else:
                return "Dime qué quieres calcular: **voltaje**, **corriente** o **resistencia**."
        elif paso == 1:
            n = extraer_numero(texto)
            if n is None:
                return "No detecté un número. Pásame el valor numérico."
            datos["a"] = n
            st.session_state.paso = 2
            if datos["incognita"] in ("V", "I"):
                return "Ahora pásame la **resistencia R en Ohmios (Ω)**."
            else:
                return "Ahora pásame la **corriente I en Amperios (A)**."
        elif paso == 2:
            n = extraer_numero(texto)
            if n is None:
                return "No detecté un número. Pásame el valor numérico."
            inc = datos["incognita"]
            if n == 0 and inc in ("I", "R"):
                return "❌ **Error matemático:** No se puede dividir entre 0. Por favor, pásame un valor mayor a 0."
            datos["b"] = n
            st.session_state.flujo = None
            
            # R para la gráfica V-I (se guarda aparte para que no se pierda)
            R_graf = datos["b"] if inc in ("V", "I") else datos["a"] / datos["b"]
            st.session_state.graf_params["ohm"] = {"R": R_graf}
            if inc == "V":
                V = datos["a"] * datos["b"]
                return f"✅ **Resultado:** V = {formato_inteligente(V)} V\n\n**Fórmula:** V = I·R = {formato_inteligente(datos['a'])}·{formato_inteligente(datos['b'])}"
            elif inc == "I":
                I = datos["a"] / datos["b"]
                return f"✅ **Resultado:** I = {formato_inteligente(I)} A\n\n**Fórmula:** I = V/R = {formato_inteligente(datos['a'])}/{formato_inteligente(datos['b'])}"
            else:
                R = datos["a"] / datos["b"]
                return f"✅ **Resultado:** R = {formato_inteligente(R)} Ω\n\n**Fórmula:** R = V/I = {formato_inteligente(datos['a'])}/{formato_inteligente(datos['b'])}"

    # ========== FLUJO POTENCIA ==========
    if flujo == "potencia":
        if paso == 0:
            n = extraer_numero(texto)
            if n is None:
                return "Pásame el **voltaje V en Voltios**."
            datos["V"] = n
            st.session_state.paso = 1
            return "Ahora pásame la **corriente I en Amperios (A)**."
        elif paso == 1:
            n = extraer_numero(texto)
            if n is None:
                return "Pásame la **corriente I en Amperios**."
            datos["I"] = n
            st.session_state.flujo = None
            P = datos["V"] * datos["I"]
            return f"✅ **Resultado:** P = {formato_inteligente(P)} W\n\n**Fórmula:** P = V·I = {formato_inteligente(datos['V'])}·{formato_inteligente(datos['I'])}"

    # ========== FLUJO CAPACITOR ==========
    if flujo == "capacitor":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame la **capacitancia C en Faradios (F)** (ej: 5 micro)."
            datos["C"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame el **voltaje (V) en Voltios**."
        elif paso == 1:
            n = extraer_numero(texto)
            if n is None:
                return "No detecté un número. Pásame el **voltaje V en Voltios**."
            datos["V"] = n
            st.session_state.flujo = None
            U = 0.5 * datos["C"] * (datos["V"] ** 2)
            C_f = formato_inteligente(datos['C'])
            V_f = formato_inteligente(datos['V'])
            U_f = formato_inteligente(U)
            return (f"✅ **Resultado:** U = {U_f} Joules (J)\n\n"
                    f"**Fórmula:** U = ½ · C · V² = ½ · ({C_f}) · ({V_f})²\n\n"
                    f"La energía almacenada es de **{U_f} J**.")

    # ========== FLUJO DIODO ==========
    if flujo == "diodo":
        if paso == 0:
            n = extraer_numero(texto)
            if n is None:
                return "No detecté un número. Pásame el **voltaje de la fuente (V)** (ej: 12)."
            datos["V_fuente"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame el valor de la **resistencia (R) en Ohmios (Ω)**."
        elif paso == 1:
            n = extraer_numero(texto)
            if n is None or n == 0:
                return "No detecté una resistencia válida. Debe ser un número mayor a 0."
            datos["R"] = n
            st.session_state.flujo = None
            V_diodo = 0.7
            if datos["V_fuente"] <= V_diodo:
                return ("⚠️ **El diodo NO conduce.**\n\n"
                        "El voltaje de la fuente es menor o igual a la barrera de potencial del silicio (0.7 V), "
                        "por lo que el diodo está en corte (polarización inversa o insuficiente). La corriente es **0 A**.")
            V_resistencia = datos["V_fuente"] - V_diodo
            I = V_resistencia / datos["R"]
            I_mA = I * 1000
            V_f = formato_inteligente(datos["V_fuente"])
            R_f = formato_inteligente(datos["R"])
            I_f = formato_inteligente(I)
            return (f"✅ **Resultado:** El diodo conduce y la corriente es **I = {I_f} A** ({formato_inteligente(I_mA)} mA)\n\n"
                    f"**Fórmula de la malla:** V_fuente = V_diodo + V_resistencia\n"
                    f"1. Caída en la resistencia: {V_f} V - 0.7 V = {formato_inteligente(V_resistencia)} V\n"
                    f"2. Ley de Ohm: I = V_resistencia / R = {formato_inteligente(V_resistencia)} V / {R_f} Ω\n\n"
                    f"*(Nota: Se asume un diodo de silicio con caída típica de 0.7 V)*.")

    # ========== FLUJO CAMPO ELÉCTRICO ==========
    if flujo == "campo":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame la **fuerza F en Newtons (N)**."
            datos["F"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **carga de prueba q en Coulombs (C)** (ej: 2 micro)."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame la **carga q en C**."
            if n == 0:
                return "❌ **Error matemático:** La carga no puede ser 0 (no se puede dividir entre 0)."
            datos["q"] = n
            st.session_state.flujo = None
            E = datos["F"] / datos["q"]
            return (f"✅ **Resultado:** E = {formato_inteligente(E)} N/C\n\n"
                    f"**Fórmula:** E = F / q = {formato_inteligente(datos['F'])} / {formato_inteligente(datos['q'])}")

    # ========== FLUJO CARGA ELÉCTRICA ==========
    if flujo == "carga":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None or n < 0:
                return "No detecté un número válido. Pásame el **número de electrones n** (ej: 5e18 o 5x10^18)."
            datos["n"] = n
            st.session_state.flujo = None
            e = 1.602e-19
            Q = n * e
            return (f"✅ **Resultado:** |Q| = {formato_inteligente(Q)} C\n\n"
                    f"**Fórmula:** Q = n · e = {formato_inteligente(n)} · 1.602 × 10^-19 C\n\n"
                    f"*Si son electrones en exceso, la carga es negativa: Q = −{formato_inteligente(Q)} C.*")

    # ========== FLUJO RESISTENCIAS SERIE / PARALELO ==========
    if flujo == "resistencia":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "No detecté una resistencia válida. Pásame **R1 en Ohmios** (mayor a 0)."
            datos["R1"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame **R2 en Ohmios**."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "No detecté una resistencia válida. Pásame **R2 en Ohmios** (mayor a 0)."
            datos["R2"] = n
            st.session_state.flujo = None
            R1, R2 = datos["R1"], datos["R2"]
            Rs = R1 + R2
            Rp = (R1 * R2) / (R1 + R2)
            return (f"✅ **Resultados:**\n\n"
                    f"- **En serie:** Req = R1 + R2 = {formato_inteligente(R1)} + {formato_inteligente(R2)} = **{formato_inteligente(Rs)} Ω**\n"
                    f"- **En paralelo:** Req = (R1·R2)/(R1+R2) = **{formato_inteligente(Rp)} Ω**\n\n"
                    f"*En paralelo la resistencia equivalente siempre es menor que la menor de las resistencias.*")

    # ========== FLUJO POTENCIAL ELÉCTRICO ==========
    if flujo == "potencial":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame la **carga q en C** (ej: 2 micro)."
            datos["q"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **distancia r desde la carga en metros (m)** (ej: 30 cm)."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ **Error físico:** La distancia debe ser **mayor a 0**. Pásame **r en metros**."
            datos["r"] = n
            st.session_state.flujo = None
            k = 9e9
            V = k * datos["q"] / n
            st.session_state.graf_params["potencial"] = {"q": datos["q"], "r": n}
            signo = ("positivo: una carga positiva cerca **ganaría** energía potencial"
                     if V > 0 else "negativo: una carga positiva cerca **perdería** energía potencial")
            aviso = aviso_valor("q", datos["q"], 1e-2, "¿Quisiste escribir microcoulombs (ej: 2 micro)?")
            return (f"✅ **Resultado:** V = {formato_inteligente(V)} V\n\n"
                    f"**Fórmula:** V = k·q / r = 9×10⁹ · ({formato_inteligente(datos['q'])}) / {formato_inteligente(n)}\n\n"
                    f"El potencial es {signo}. *El potencial es un escalar: conserva el signo de la carga.*{aviso}\n\n"
                    f"*Escribe 'muéstrame la gráfica de potencial' para ver cómo cambia V con la distancia.*")

    # ========== FLUJO LEYES DE KIRCHHOFF (2 MALLAS) ==========
    if flujo == "kirchhoff":
        pedidos = [("E1", "Ahora pásame el **voltaje de la fuente E2 en Voltios**.", False),
                   ("E2", "Ahora pásame la **resistencia R1 en Ohmios (Ω)** (la de la izquierda).", False),
                   ("R1", "Ahora pásame la **resistencia R2 en Ohmios (Ω)** (la de la derecha).", True),
                   ("R2", "Último dato: pásame la **resistencia central R3 en Ohmios (Ω)**.", True),
                   ("R3", None, True)]
        clave, siguiente, es_resistencia = pedidos[paso]
        n = convertir_unidades(texto)
        if n is None:
            return f"No detecté un número. Pásame **{clave}**."
        if es_resistencia and n <= 0:
            return f"❌ La resistencia **{clave}** debe ser **mayor a 0**."
        datos[clave] = n
        if siguiente:
            st.session_state.paso = paso + 1
            return siguiente
        st.session_state.flujo = None
        E1, E2, R1, R2, R3 = datos["E1"], datos["E2"], datos["R1"], datos["R2"], datos["R3"]
        # Ley de nodos en A:  (E1 − VA)/R1 + (E2 − VA)/R2 = VA/R3
        VA = (E1 / R1 + E2 / R2) / (1 / R1 + 1 / R2 + 1 / R3)
        I1 = (E1 - VA) / R1
        I2 = (E2 - VA) / R2
        I3 = VA / R3
        def sentido(I, nombre, fuente):
            if abs(I) < 1e-12:
                return f"- **{nombre} = 0 A**"
            if I > 0:
                return f"- **{nombre} = {formato_inteligente(I)} A** (sale de {fuente} hacia el nodo A)"
            return (f"- **{nombre} = {formato_inteligente(I)} A** → el signo negativo indica que circula al revés: "
                    f"entra a {fuente} por su polo + (la fuente se está **cargando**)")
        malla1 = E1 - I1 * R1 - I3 * R3
        malla2 = E2 - I2 * R2 - I3 * R3
        return (f"✅ **Resultados:**\n\n"
                f"{sentido(I1, 'I1', 'E1')}\n"
                f"{sentido(I2, 'I2', 'E2')}\n"
                f"- **I3 = {formato_inteligente(I3)} A** (por la resistencia central R3)\n"
                f"- **Voltaje del nodo A:** V_A = **{formato_inteligente(VA)} V**\n\n"
                f"**1ra Ley (nodos) en A:** I1 + I2 = I3 → "
                f"{formato_inteligente(I1)} + ({formato_inteligente(I2)}) = {formato_inteligente(I1 + I2)} A ✔\n\n"
                f"**2da Ley (mallas):**\n"
                f"- Malla izquierda: E1 − I1·R1 − I3·R3 = {formato_inteligente(malla1 if abs(malla1) > 1e-9 else 0)} V ✔\n"
                f"- Malla derecha: E2 − I2·R2 − I3·R3 = {formato_inteligente(malla2 if abs(malla2) > 1e-9 else 0)} V ✔\n\n"
                f"*Cómo se resolvió:* con la ley de nodos, (E1 − V_A)/R1 + (E2 − V_A)/R2 = V_A/R3, "
                f"se despeja V_A y luego cada corriente con la ley de Ohm.")

    # ========== FLUJO CIRCUITO RC (CARGA DEL CAPACITOR) ==========
    if flujo == "circuito_rc":
        pedidos = [("R", "Ahora pásame la **capacitancia C en Faradios (F)** (ej: 100 µF)."),
                   ("C", "Ahora pásame el **voltaje de la fuente V en Voltios**."),
                   ("V", "Último dato: pásame el **tiempo t en segundos (s)** en que quieres conocer la carga (ej: 1 o 500 ms)."),
                   ("t", None)]
        clave, siguiente = pedidos[paso]
        n = convertir_unidades(texto)
        if n is None:
            return f"No detecté un número. Pásame **{clave}**."
        if clave in ("R", "C") and n <= 0:
            return f"❌ **{clave}** debe ser **mayor a 0**."
        if clave == "t" and n < 0:
            return "❌ El tiempo no puede ser negativo."
        datos[clave] = n
        if siguiente:
            st.session_state.paso = paso + 1
            return siguiente
        st.session_state.flujo = None
        R, C, V, t = datos["R"], datos["C"], datos["V"], datos["t"]
        tau = R * C
        frac = 1 - np.exp(-t / tau)
        Vc = V * frac
        I = (V / R) * np.exp(-t / tau)
        Q = C * Vc
        st.session_state.graf_params["rc"] = {"R": R, "C": C, "V": V, "t": t}
        return (f"✅ **Resultados (carga del capacitor):**\n\n"
                f"1. **Constante de tiempo:** τ = R·C = {formato_inteligente(R)} · {formato_inteligente(C)} = **{formato_inteligente(tau)} s**\n"
                f"2. **Voltaje del capacitor:** Vc(t) = V·(1 − e^(−t/τ)) = **{formato_inteligente(Vc)} V** "
                f"({frac * 100:.1f}% de la carga total)\n"
                f"3. **Corriente:** I(t) = (V/R)·e^(−t/τ) = **{formato_inteligente(I)} A**\n"
                f"4. **Carga almacenada:** Q = C·Vc = **{formato_inteligente(Q)} C**\n\n"
                f"*Datos clave:* en t = τ el capacitor llega al **63.2%** de su carga, y en t = 5τ "
                f"({formato_inteligente(5 * tau)} s) se considera **completamente cargado** (99.3%).\n\n"
                f"*Escribe 'muéstrame la gráfica de carga del capacitor' para verla con tus datos.*")

    # ========== FLUJO REGULADOR CON DIODO ZENER ==========
    if flujo == "zener":
        pedidos = [("Vs", "Ahora pásame la **resistencia limitadora Rs en Ohmios (Ω)**."),
                   ("Rs", "Ahora pásame el **voltaje Zener Vz en Voltios** (ej: 5.1)."),
                   ("Vz", "Último dato: pásame la **resistencia de carga RL en Ohmios (Ω)**."),
                   ("RL", None)]
        clave, siguiente = pedidos[paso]
        n = convertir_unidades(texto)
        if n is None or n <= 0:
            return f"Pásame un valor válido de **{clave}** (mayor a 0)."
        datos[clave] = n
        if siguiente:
            st.session_state.paso = paso + 1
            return siguiente
        st.session_state.flujo = None
        Vs, Rs, Vz, RL = datos["Vs"], datos["Rs"], datos["Vz"], datos["RL"]
        V_sin_zener = Vs * RL / (Rs + RL)  # voltaje que habría en la carga sin el Zener (divisor)
        paso1 = (f"**Paso 1 – ¿El Zener conduce?** Sin el Zener, la carga tendría "
                 f"V = Vs·RL/(Rs+RL) = {formato_inteligente(V_sin_zener)} V")
        if V_sin_zener < Vz:
            IL = V_sin_zener / RL
            return (f"⚠️ **El Zener NO regula.**\n\n{paso1}, que es **menor** que Vz = {formato_inteligente(Vz)} V, "
                    f"así que el Zener no llega a su voltaje de ruptura y queda apagado.\n\n"
                    f"- **Voltaje en la carga:** {formato_inteligente(V_sin_zener)} V (no está regulado)\n"
                    f"- **Corriente en la carga:** {formato_inteligente(IL)} A\n"
                    f"- **Corriente en el Zener:** 0 A\n\n"
                    f"*Para que regule, aumenta Vs o RL, o reduce Rs.*")
        Is = (Vs - Vz) / Rs
        IL = Vz / RL
        Iz = Is - IL
        Pz = Vz * Iz
        return (f"✅ **El Zener regula: la carga recibe {formato_inteligente(Vz)} V constantes.**\n\n"
                f"{paso1} ≥ Vz, así que el Zener conduce en inversa y fija el voltaje.\n\n"
                f"**Paso 2 – Corrientes:**\n"
                f"- Por Rs: Is = (Vs − Vz)/Rs = ({formato_inteligente(Vs)} − {formato_inteligente(Vz)})/{formato_inteligente(Rs)} = **{formato_inteligente(Is)} A**\n"
                f"- Por la carga: IL = Vz/RL = **{formato_inteligente(IL)} A**\n"
                f"- Por el Zener: Iz = Is − IL = **{formato_inteligente(Iz)} A**\n\n"
                f"**Paso 3 – Potencia en el Zener:** Pz = Vz·Iz = **{formato_inteligente(Pz)} W**\n\n"
                f"*Elige un Zener que soporte más de {formato_inteligente(Pz)} W (por ejemplo, uno de 0.5 W o 1 W).*")

    # ============================================================
    # MÓDULO 3: MAGNETISMO Y CORRIENTE ALTERNA
    # ============================================================

    # ========== FLUJO FUERZA MAGNÉTICA ==========
    if flujo == "fuerza_magnetica":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame la **carga q en C** (ej: 2 micro o 1.6e-19)."
            datos["q"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **velocidad v en m/s**."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None or n < 0:
                return "No detecté una velocidad válida. Pásame la **velocidad v en m/s** (ej: 3e5)."
            if n >= C_LUZ:
                return ("❌ **Error físico:** ninguna partícula con carga (y masa) puede alcanzar ni superar la "
                        "velocidad de la luz (3 × 10^8 m/s). Pásame una **velocidad menor**.")
            datos["v"] = n
            st.session_state.paso = 2
            return "Bien. Ahora pásame el **campo magnético B en Teslas (T)** (ej: 0.5 o 200 mT)."
        elif paso == 2:
            n = convertir_unidades(texto)
            if n is None or n < 0:
                return "No detecté un valor válido. Pásame el **campo B en Teslas (T)**."
            datos["B"] = n
            st.session_state.paso = 3
            return "Último dato: pásame el **ángulo θ entre v y B en grados** (si son perpendiculares, escribe 90)."
        elif paso == 3:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame el **ángulo θ en grados** (ej: 90)."
            datos["theta"] = n
            st.session_state.flujo = None
            seno = np.sin(np.radians(n))
            if abs(seno) < 1e-12:
                seno = 0.0
            F = abs(datos["q"]) * datos["v"] * datos["B"] * abs(seno)
            st.session_state.graf_params["fuerza_magnetica"] = {
                "q": datos["q"], "v": datos["v"], "B": datos["B"], "theta": n}
            extra = (aviso_valor("q", datos["q"], 1e-2, "¿Quisiste escribir microcoulombs o la carga de un electrón (1.6e-19)?")
                     + aviso_valor("B", datos["B"], 50, "Los imanes más potentes del mundo rondan los 45 T. ¿Quisiste escribir mT?"))
            if F == 0:
                extra = "\n\n*Como v es paralela a B (θ = 0° o 180°), la carga no siente fuerza magnética.*"
            return (f"✅ **Resultado:** F = {formato_inteligente(F)} N\n\n"
                    f"**Fórmula:** F = |q|·v·B·sen(θ) = |{formato_inteligente(datos['q'])}| · "
                    f"{formato_inteligente(datos['v'])} · {formato_inteligente(datos['B'])} · sen({formato_inteligente(n)}°)\n\n"
                    f"La fuerza es **perpendicular** a la velocidad y al campo (regla de la mano derecha; "
                    f"si la carga es negativa, el sentido se invierte).{extra}\n\n"
                    f"*Escribe 'muéstrame la gráfica de fuerza magnética' para ver cómo cambia F con el ángulo.*")

    # ========== FLUJO CAMPO MAGNÉTICO (CONDUCTOR RECTO) ==========
    if flujo == "campo_magnetico":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame la **corriente I en Amperios (A)**."
            datos["I"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **distancia r al cable en metros (m)** (ej: 5 cm)."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ La distancia debe ser un número **mayor a 0**. Pásame **r en metros**."
            datos["r"] = n
            st.session_state.flujo = None
            mu0 = 4 * np.pi * 1e-7
            B = mu0 * abs(datos["I"]) / (2 * np.pi * n)
            st.session_state.graf_params["campo_magnetico"] = {"I": abs(datos["I"]), "r": n}
            aviso = aviso_valor("r", n, 1e4, "¿Quisiste escribir la distancia en cm (ej: 5 cm)?")
            return (f"✅ **Resultado:** B = {formato_inteligente(B)} T ({formato_inteligente(B * 1e6)} μT)\n\n"
                    f"**Fórmula:** B = μ₀·I / (2π·r) = (4π×10⁻⁷ · {formato_inteligente(abs(datos['I']))}) / "
                    f"(2π · {formato_inteligente(n)})\n\n"
                    f"*Las líneas de campo son círculos alrededor del cable (regla de la mano derecha).*\n\n"
                    f"*Escribe 'muéstrame la gráfica de campo magnético' para ver cómo disminuye B con la distancia.*{aviso}")

    # ========== FLUJO LEY DE FARADAY ==========
    if flujo == "faraday":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "Pásame un **número de espiras N** válido (mayor a 0)."
            datos["N"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame el **área A de la espira en m²** (ej: 0.02 o 200 cm²)."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "Pásame un **área A** válida en m² (mayor a 0)."
            datos["A"] = n
            st.session_state.paso = 2
            return "Bien. Ahora pásame el **campo magnético inicial B₀ en Teslas (T)**."
        elif paso == 2:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame **B₀ en Teslas**."
            datos["B0"] = n
            st.session_state.paso = 3
            return "Ahora pásame el **campo magnético final B₁ en Teslas (T)**."
        elif paso == 3:
            n = convertir_unidades(texto)
            if n is None:
                return "No detecté un número. Pásame **B₁ en Teslas**."
            datos["B1"] = n
            st.session_state.paso = 4
            return "Último dato: pásame el **tiempo Δt en segundos (s)** que tarda el cambio (ej: 0.1 o 50 ms)."
        elif paso == 4:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ El tiempo debe ser **mayor a 0**. Pásame **Δt en segundos**."
            datos["dt"] = n
            st.session_state.flujo = None
            N, A, B0, B1 = datos["N"], datos["A"], datos["B0"], datos["B1"]
            phi0, phi1 = B0 * A, B1 * A
            dphi = phi1 - phi0
            fem = -N * dphi / n
            st.session_state.graf_params["faraday"] = {
                "N": N, "phi0": phi0, "phi1": phi1, "dt": n, "fem": fem}
            if dphi > 0:
                lenz = "El flujo **aumenta**, así que la corriente inducida crea un campo **opuesto** a B (Ley de Lenz)."
            elif dphi < 0:
                lenz = "El flujo **disminuye**, así que la corriente inducida crea un campo **en el mismo sentido** que B para compensar (Ley de Lenz)."
            else:
                lenz = "El flujo no cambia, por eso **no hay fem inducida**."
            return (f"✅ **Resultado:** ε = {formato_inteligente(fem)} V  (|ε| = {formato_inteligente(abs(fem))} V)\n\n"
                    f"**Paso 1 – Flujos (Φ = B·A, con B perpendicular a la espira):**\n"
                    f"Φ₀ = {formato_inteligente(B0)} · {formato_inteligente(A)} = {formato_inteligente(phi0)} Wb\n"
                    f"Φ₁ = {formato_inteligente(B1)} · {formato_inteligente(A)} = {formato_inteligente(phi1)} Wb\n\n"
                    f"**Paso 2 – Cambio de flujo:** ΔΦ = Φ₁ − Φ₀ = {formato_inteligente(dphi)} Wb\n\n"
                    f"**Paso 3 – Faraday:** ε = −N·ΔΦ/Δt = −{formato_inteligente(N)} · ({formato_inteligente(dphi)}) / {formato_inteligente(n)}\n\n"
                    f"{lenz}\n\n"
                    f"*Escribe 'muéstrame la gráfica de faraday' para ver el flujo y la fem en el tiempo.*")

    # ========== FLUJO CORRIENTE ALTERNA ==========
    if flujo == "alterna":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "Pásame un **voltaje máximo V_max** válido en Voltios (mayor a 0)."
            datos["Vmax"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **resistencia R de la carga en Ohmios (Ω)**."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ La resistencia debe ser **mayor a 0**. Pásame **R en Ohmios**."
            datos["R"] = n
            st.session_state.paso = 2
            return "Último dato: pásame la **frecuencia f en Hertz (Hz)** (en Perú la red es de 60 Hz)."
        elif paso == 2:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "Pásame una **frecuencia f** válida en Hz (mayor a 0)."
            datos["f"] = n
            st.session_state.flujo = None
            Vmax, R, f = datos["Vmax"], datos["R"], n
            Vrms = Vmax / np.sqrt(2)
            Imax = Vmax / R
            Irms = Vrms / R
            P = Vrms * Irms
            w = 2 * np.pi * f
            T = 1 / f
            st.session_state.graf_params["alterna"] = {"Vmax": Vmax, "R": R, "f": f}
            return (f"✅ **Resultados (circuito resistivo en CA):**\n\n"
                    f"- **V_rms** = V_max/√2 = {formato_inteligente(Vmax)}/√2 = **{formato_inteligente(Vrms)} V**\n"
                    f"- **I_max** = V_max/R = **{formato_inteligente(Imax)} A**\n"
                    f"- **I_rms** = V_rms/R = **{formato_inteligente(Irms)} A**\n"
                    f"- **Potencia media** P = V_rms·I_rms = **{formato_inteligente(P)} W**\n"
                    f"- **Frecuencia angular** ω = 2πf = **{formato_inteligente(w)} rad/s**\n"
                    f"- **Periodo** T = 1/f = **{formato_inteligente(T)} s**\n\n"
                    f"**Expresión del voltaje:** v(t) = {formato_inteligente(Vmax)} · sen({formato_inteligente(w)}·t) V\n\n"
                    f"*Escribe 'muéstrame la gráfica de corriente alterna' para ver la onda senoidal.*")

    # ========== FLUJO CIRCUITO RLC SERIE ==========
    if flujo == "rlc":
        if paso == 0:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ Pásame una **resistencia R** válida en Ohmios (mayor a 0)."
            datos["R"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **inductancia L en Henrios (H)** (ej: 0.1 o 50 mH)."
        elif paso == 1:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ Pásame una **inductancia L** válida en H (mayor a 0)."
            datos["L"] = n
            st.session_state.paso = 2
            return "Bien. Ahora pásame la **capacitancia C en Faradios (F)** (ej: 10 micro o 10 µF)."
        elif paso == 2:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ Pásame una **capacitancia C** válida en F (mayor a 0)."
            datos["C"] = n
            st.session_state.paso = 3
            return "Ahora pásame la **frecuencia f de la fuente en Hertz (Hz)**."
        elif paso == 3:
            n = convertir_unidades(texto)
            if n is None or n <= 0:
                return "❌ Pásame una **frecuencia f** válida en Hz (mayor a 0)."
            datos["f"] = n
            st.session_state.paso = 4
            return "Último dato: pásame el **voltaje eficaz de la fuente V_rms en Voltios**."
        elif paso == 4:
            n = convertir_unidades(texto)
            if n is None or n < 0:
                return "Pásame un **voltaje V_rms** válido en Voltios."
            datos["V"] = n
            st.session_state.flujo = None
            R, L, C, f, V = datos["R"], datos["L"], datos["C"], datos["f"], n
            XL = 2 * np.pi * f * L
            XC = 1 / (2 * np.pi * f * C)
            X = XL - XC
            Z = np.sqrt(R ** 2 + X ** 2)
            I = V / Z
            phi = np.degrees(np.arctan2(X, R))
            f0 = 1 / (2 * np.pi * np.sqrt(L * C))
            Q = (1 / R) * np.sqrt(L / C)
            st.session_state.q_rlc = round(float(Q), 2)  # para la gráfica de resonancia
            if abs(X) < 0.01 * max(XL, XC):  # tolerancia de 1% (los datos suelen estar redondeados)
                caracter = "**resistivo**: el circuito está en **resonancia** (X_L ≈ X_C)."
            elif X > 0:
                caracter = "**inductivo**: X_L > X_C, la corriente va **atrasada** respecto al voltaje."
            else:
                caracter = "**capacitivo**: X_C > X_L, la corriente va **adelantada** respecto al voltaje."
            return (f"✅ **Resultados (RLC en serie):**\n\n"
                    f"1. **Reactancia inductiva:** X_L = 2πfL = **{formato_inteligente(XL)} Ω**\n"
                    f"2. **Reactancia capacitiva:** X_C = 1/(2πfC) = **{formato_inteligente(XC)} Ω**\n"
                    f"3. **Impedancia:** Z = √(R² + (X_L − X_C)²) = √({formato_inteligente(R)}² + ({formato_inteligente(X)})²) = **{formato_inteligente(Z)} Ω**\n"
                    f"4. **Corriente:** I_rms = V/Z = {formato_inteligente(V)}/{formato_inteligente(Z)} = **{formato_inteligente(I)} A**\n"
                    f"5. **Ángulo de fase:** φ = arctan((X_L − X_C)/R) = **{formato_inteligente(phi)}°**\n"
                    f"6. **Frecuencia de resonancia:** f₀ = 1/(2π√(LC)) = **{formato_inteligente(f0)} Hz**\n"
                    f"7. **Factor de calidad:** Q = (1/R)·√(L/C) = **{formato_inteligente(Q)}**\n\n"
                    f"El circuito es {caracter}\n\n"
                    f"*Escribe 'muéstrame la gráfica de resonancia' para ver la curva con este factor Q.*")

    return "Algo salió mal. Reinicia el cálculo escribiendo 'resuelve un ejercicio'."

# ------------------------------------------------------------
# GENERADOR DE GRÁFICAS
# ------------------------------------------------------------
def generar_grafica(tipo):
    fig, ax = plt.subplots(figsize=(6, 4))

    if tipo == "diodo":
        # Ecuación de Shockley: I = Is·(e^(V/(n·VT)) − 1), diodo de silicio a 25 °C
        Is, n_id, VT = 1e-14, 1.0, 0.02585
        V = np.linspace(-1, 0.78, 400)
        I = Is * (np.exp(V / (n_id * VT)) - 1)
        ax.plot(V, I * 1000, color="blue", label="I = Is·(e^(V/VT) − 1)")
        ax.axvline(0.7, color="red", linestyle=":", label="Umbral ≈ 0.7 V (silicio)")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title("Curva I-V de un diodo de silicio")
        ax.set_xlabel("Voltaje (V)")
        ax.set_ylabel("Corriente (mA)")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True)

    elif tipo == "carga_capacitor":
        d = st.session_state.graf_params.get("rc")
        if d:  # con los datos del último ejercicio RC
            tau = d["R"] * d["C"]
            t = np.linspace(0, 5 * tau, 300)
            Vc = d["V"] * (1 - np.exp(-t / tau))
            ax.plot(t, Vc, color="green", label="Vc(t) = V·(1 − e^(−t/τ))")
            ax.axhline(d["V"], color="gray", linestyle="--", linewidth=1, label=f"V fuente = {formato_inteligente(d['V'])} V")
            ax.axvline(tau, color="orange", linestyle=":", label=f"τ = {formato_inteligente(tau)} s (63.2%)")
            if d["t"] <= 5 * tau:
                ax.plot(d["t"], d["V"] * (1 - np.exp(-d["t"] / tau)), "o", color="red",
                        label=f"Tu ejercicio: t = {formato_inteligente(d['t'])} s")
            ax.set_title(f"Carga de un capacitor (R = {formato_inteligente(d['R'])} Ω, C = {formato_inteligente(d['C'])} F)")
            ax.set_xlabel("Tiempo (s)")
            ax.set_ylabel("Voltaje del capacitor (V)")
            ax.legend(fontsize=8, loc="lower right")
        else:
            t = np.linspace(0, 5, 200)
            q = 1 - np.exp(-t)
            ax.plot(t, q, color="green")
            ax.axvline(1, color="orange", linestyle=":", label="t = τ (63.2%)")
            ax.set_title("Carga de un capacitor (Q vs t)")
            ax.set_xlabel("Tiempo (en múltiplos de τ = RC)")
            ax.set_ylabel("Carga normalizada (Q / Q_max)")
            ax.legend(fontsize=8, loc="lower right")
        ax.grid(True)

    elif tipo == "potencial":
        d = st.session_state.graf_params.get("potencial", {"q": 2e-6, "r": 0.3})
        k = 9e9
        r = np.linspace(d["r"] * 0.2, d["r"] * 5, 400)
        V = k * d["q"] / r
        ax.plot(r, V, color="darkgreen", label=f"V = k·q/r  (q = {formato_inteligente(d['q'])} C)")
        ax.plot(d["r"], k * d["q"] / d["r"], "o", color="red", label=f"Tu ejercicio: r = {formato_inteligente(d['r'])} m")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title("Potencial eléctrico de una carga puntual vs distancia")
        ax.set_xlabel("Distancia r (m)")
        ax.set_ylabel("Potencial V (V)")
        ax.legend(fontsize=8)
        ax.grid(True)

    elif tipo == "descarga_capacitor":
        t = np.linspace(0, 5, 200)
        q = np.exp(-t)
        ax.plot(t, q, color="red")
        ax.set_title("Descarga de un capacitor (Q vs t)")
        ax.set_xlabel("Tiempo (τ = RC)")
        ax.set_ylabel("Carga normalizada")
        ax.grid(True)

    elif tipo == "ohm":
        R = st.session_state.graf_params.get("ohm", {"R": 5})["R"]
        I = np.linspace(0, 10, 100)
        V = I * R
        ax.plot(I, V, color="purple", label="V = I·R")
        ax.set_title(f"Ley de Ohm: V = I·R (R = {formato_inteligente(R)} Ω)")
        ax.text(0.03, 0.92, f"Pendiente = R = {formato_inteligente(R)} Ω", transform=ax.transAxes, fontsize=9)
        ax.set_xlabel("Corriente (A)")
        ax.set_ylabel("Voltaje (V)")
        ax.grid(True)

    # ============ MÓDULO 3 ============
    elif tipo == "fuerza_magnetica":
        d = st.session_state.graf_params.get(
            "fuerza_magnetica", {"q": 2e-6, "v": 3e5, "B": 0.2, "theta": 90})
        theta = np.linspace(0, 180, 361)
        F = abs(d["q"]) * d["v"] * d["B"] * np.sin(np.radians(theta))
        F_dato = abs(d["q"]) * d["v"] * d["B"] * abs(np.sin(np.radians(d["theta"])))
        ax.plot(theta, F, color="teal", label="F = |q|·v·B·sen θ")
        th = d["theta"] % 360          # se ubica el ángulo dentro de 0°–180°
        if th > 180:
            th = 360 - th
        ax.plot(th, F_dato, "o", color="red",
                label=f"Tu ejercicio: θ = {formato_inteligente(d['theta'])}°")
        ax.set_title("Fuerza magnética vs ángulo entre v y B")
        ax.set_xlabel("Ángulo θ (grados)")
        ax.set_ylabel("Fuerza (N)")
        ax.set_xticks(range(0, 181, 30))
        ax.legend(fontsize=8)
        ax.grid(True)

    elif tipo == "campo_magnetico":
        d = st.session_state.graf_params.get("campo_magnetico", {"I": 10, "r": 0.05})
        mu0 = 4 * np.pi * 1e-7
        r = np.linspace(d["r"] * 0.2, d["r"] * 5, 400)
        B = mu0 * d["I"] / (2 * np.pi * r)
        B_dato = mu0 * d["I"] / (2 * np.pi * d["r"])
        ax.plot(r, B * 1e6, color="navy", label=f"B = μ₀·I / 2πr  (I = {formato_inteligente(d['I'])} A)")
        ax.plot(d["r"], B_dato * 1e6, "o", color="red",
                label=f"Tu ejercicio: r = {formato_inteligente(d['r'])} m")
        ax.set_title("Campo magnético de un conductor recto vs distancia")
        ax.set_xlabel("Distancia al cable r (m)")
        ax.set_ylabel("Campo magnético B (μT)")
        ax.legend(fontsize=8)
        ax.grid(True)

    elif tipo == "faraday":
        d = st.session_state.graf_params.get(
            "faraday", {"N": 100, "phi0": 0.002, "phi1": 0.01, "dt": 0.05, "fem": -16})
        plt.close(fig)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 5), sharex=True)
        dt = d["dt"]
        t = np.linspace(-0.5 * dt, 1.5 * dt, 400)
        # El flujo cambia de forma lineal durante Δt y luego se mantiene
        phi = np.where(t < 0, d["phi0"],
                       np.where(t > dt, d["phi1"], d["phi0"] + (d["phi1"] - d["phi0"]) * t / dt))
        fem = np.where((t >= 0) & (t <= dt), d["fem"], 0.0)
        ax1.plot(t, phi, color="purple")
        ax1.set_title("Ley de Faraday: el flujo cambia y se induce una fem")
        ax1.set_ylabel("Flujo Φ (Wb)")
        ax1.grid(True)
        ax2.plot(t, fem, color="crimson")
        ax2.axhline(0, color="black", linewidth=0.8)
        ax2.set_xlabel("Tiempo (s)")
        ax2.set_ylabel("fem inducida ε (V)")
        ax2.margins(y=0.25)
        ax2.grid(True)
        ax2.text(0.5 * dt, d["fem"], f"  ε = {formato_inteligente(d['fem'])} V",
                 va="bottom" if d["fem"] >= 0 else "top", ha="center", fontsize=9)
        fig.tight_layout()

    elif tipo == "alterna":
        d = st.session_state.graf_params.get("alterna", {"Vmax": 311, "R": 100, "f": 60})
        T = 1 / d["f"]
        t = np.linspace(0, 2 * T, 500)
        v = d["Vmax"] * np.sin(2 * np.pi * d["f"] * t)
        i = v / d["R"]
        Vrms = d["Vmax"] / np.sqrt(2)
        ax.plot(t * 1000, v, color="royalblue", label="Voltaje v(t)")
        ax.axhline(Vrms, color="royalblue", linestyle="--", linewidth=1,
                   label=f"V_rms = {formato_inteligente(Vrms)} V")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Tiempo (ms)")
        ax.set_ylabel("Voltaje (V)", color="royalblue")
        ax2 = ax.twinx()
        ax2.plot(t * 1000, i, color="darkorange", linestyle="-.", label="Corriente i(t)")
        ax2.set_ylabel("Corriente (A)", color="darkorange")
        ax2.set_ylim(np.array(ax.get_ylim()) / d["R"])  # misma escala visual: v e i en fase
        ax.set_title(f"Corriente alterna (f = {formato_inteligente(d['f'])} Hz, R = {formato_inteligente(d['R'])} Ω)")
        lineas = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
        ax.legend(lineas, [l.get_label() for l in lineas], loc="lower left", fontsize=8)
        ax.grid(True)

    elif tipo == "resonancia":
        # Usa el factor Q del último ejercicio RLC resuelto (si no hay, Q = 1)
        Q = st.session_state.get("q_rlc", 1)
        x = np.linspace(0.1, 3, 500)                 # x = f / f0
        Z_rel = np.sqrt(1 + (Q * (x - 1 / x)) ** 2)  # Z / R  -> mínima en resonancia
        I_rel = 1 / Z_rel                            # I / I_max -> máxima en resonancia
        ax.plot(x, I_rel, color="orange", label="Corriente I / I_max")
        ax.set_xlabel("Frecuencia relativa (f/f₀)")
        ax.set_ylabel("Corriente normalizada", color="orange")
        ax2 = ax.twinx()
        ax2.plot(x, Z_rel, color="gray", linestyle="--", label="Impedancia Z / R")
        ax2.set_ylabel("Impedancia normalizada (Z/R)", color="gray")
        ax.axvline(1, color="red", linestyle=":", label="Resonancia (f = f₀)")
        ax.set_title(f"Resonancia en circuito RLC serie (Factor Q = {Q})")
        lineas = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
        ax.legend(lineas, [l.get_label() for l in lineas], loc="upper right", fontsize=8)
        ax.grid(True)

    fig.tight_layout()
    return fig

# ------------------------------------------------------------
# INTELIGENCIA ARTIFICIAL: CLASIFICADOR DE INTENCIONES (MACHINE LEARNING)
# ------------------------------------------------------------
# Cuando las reglas de palabras clave no entienden la pregunta, un modelo de
# aprendizaje automático (TF-IDF + Regresión Logística) predice de qué tema
# habla el usuario, aunque lo escriba con otras palabras o con errores.
#
#   1) Datos de entrenamiento: frases de ejemplo etiquetadas con su tema.
#   2) Vectorización TF-IDF: convierte cada frase en un vector de números
#      (usa fragmentos de 2 a 5 letras, así tolera errores de ortografía).
#   3) Regresión Logística: aprende qué patrones corresponden a cada tema.
#   4) Predicción: devuelve el tema más probable y su porcentaje de confianza.
# ------------------------------------------------------------
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

DATOS_ENTRENAMIENTO = {
    # ---------- Módulo 1: Electrostática ----------
    "carga": [
        "cuantos electrones tiene un cuerpo cargado", "carga de un electron",
        "cuantizacion de la carga", "un objeto gano electrones que carga tiene",
        "cuantos coulombs equivalen a muchos electrones", "cargas positivas y negativas",
        "que pasa si un cuerpo pierde electrones", "valor de la carga elemental",
        "frotar un globo y se electriza", "electrizacion por friccion",
        "ley de conservacion de la carga", "exceso de electrones",
        "defecto de electrones", "cuanto es 1.6 por 10 a la menos 19",
        "cuerpo electrizado", "carga neta de un objeto",
        "que es la carga electrica", "unidad de carga el coulomb",
        "electrones transferidos al frotar", "carga por induccion",
        "cuantos electrones forman un coulomb", "carga de un proton",
        "objeto neutro", "electroscopio",
        "cargar un cuerpo por contacto", "cuantos electrones hay en un microcoulomb",
        "numero de electrones transferidos", "q igual n por e",
        "un cuerpo con carga negativa tiene electrones de mas", "electrones que pierde una barra de vidrio",
        "carga total de varios electrones", "perdio electrones y quedo positivo",
        "cuantas cargas elementales", "la carga no se crea ni se destruye",
        "cuerpo neutro tiene igual protones y electrones",
    ],
    "coulomb": [
        "fuerza entre dos cargas", "cuanto se atraen dos cargas separadas",
        "dos cargas se repelen con que fuerza", "constante k de la electrostatica",
        "interaccion entre cargas puntuales", "atraccion entre un proton y un electron",
        "si duplico la distancia entre las cargas que pasa con la fuerza", "cargas iguales se repelen",
        "fuerza entre cargas electricas a cierta distancia", "9 por 10 a la 9 constante",
        "ley de coulomb", "fuerza electrostatica",
        "fuerza electrica entre particulas", "repulsion entre dos electrones",
        "fuerza inversamente proporcional al cuadrado de la distancia", "dos esferas cargadas separadas",
        "atraccion electrica", "cuanta fuerza ejercen dos cargas",
        "fuerza entre dos protones", "calcular la fuerza electrica",
        "cargas de distinto signo se atraen", "fuerza que una carga ejerce sobre otra",
        "interaccion electrostatica", "fuerza entre q1 y q2",
        "balanza de torsion", "fuerza entre dos esferas pequenas cargadas",
        "si triplico una carga como cambia la fuerza", "dos cargas puntuales en el vacio",
        "newtons de fuerza entre cargas", "repulsion electrostatica",
        "fuerza de atraccion entre cargas opuestas", "k por q1 por q2 entre r al cuadrado",
        "cargas separadas 3 centimetros", "fuerza neta sobre una carga por otras dos",
        "fuerza electrica entre dos particulas cargadas",
    ],
    "campo": [
        "intensidad del campo alrededor de una carga", "lineas de campo de una carga",
        "fuerza por unidad de carga", "newton sobre coulomb",
        "que siente una carga de prueba", "campo que produce una carga puntual",
        "direccion de las lineas de fuerza electricas", "carga de prueba en un punto del espacio",
        "campo uniforme entre placas", "que tan intenso es el campo en un punto",
        "campo electrico", "que es el campo electrico",
        "e igual a f sobre q", "intensidad de campo electrico",
        "vector campo electrico", "campo electrico de una carga puntual",
        "campo entre dos placas cargadas", "region donde una carga siente fuerza",
        "lineas de campo salen de cargas positivas", "campo electrico en volts por metro",
        "modulo del campo", "campo producido por varias cargas",
        "calcular el campo electrico", "campo electrico resultante",
        "fuerza que siente una carga de prueba positiva", "campo electrico de una carga a cierta distancia",
        "cuanto vale e a 2 metros de una carga", "campo electrico entre placas de un capacitor",
        "campo electrico que actua sobre un electron", "direccion del campo electrico",
        "campo electrico neto de dos cargas", "unidades del campo electrico",
        "campo electrico uniforme", "fuerza sobre una carga de prueba por unidad de carga",
        "campo electrico en el punto medio",
    ],
    "gauss": [
        "flujo electrico a traves de una superficie cerrada", "superficie gaussiana",
        "carga encerrada en una esfera", "flujo y permitividad del vacio epsilon cero",
        "simetria esferica para calcular campo", "flujo neto que atraviesa una superficie",
        "carga dentro de una superficie cerrada", "epsilon sub cero",
        "ley del flujo electrico", "cuanto flujo sale de una esfera",
        "ley de gauss", "flujo electrico",
        "teorema de gauss", "campo de una esfera cargada usando gauss",
        "flujo a traves de un cubo", "carga neta encerrada",
        "superficie cerrada imaginaria", "campo de un plano infinito",
        "campo de un cilindro cargado", "flujo igual a q entre epsilon",
        "flujo electrico total", "lineas de campo que atraviesan una superficie",
        "calcular flujo electrico", "gauss y simetria",
        "integral de superficie del campo", "campo de una esfera conductora cargada",
        "flujo de un campo uniforme sobre una superficie", "campo dentro de un conductor",
        "ley de gauss para una carga puntual", "carga encerrada y flujo",
        "superficie gaussiana cilindrica", "flujo nulo sin carga encerrada",
        "esfera hueca cargada", "gauss en un plano de carga",
        "calculo del flujo electrico",
    ],
    "potencial": [
        "energia por unidad de carga", "diferencia de potencial entre dos puntos",
        "cuantos voltios hay en un punto cerca de una carga", "trabajo para mover una carga",
        "superficies equipotenciales", "voltaje cerca de una carga puntual",
        "energia potencial electrica", "joules sobre coulomb",
        "potencial de una carga puntual", "trabajo electrico por carga",
        "potencial electrico", "que es el potencial electrico",
        "voltaje en un punto", "v igual a k q sobre r",
        "diferencia de potencial", "potencial de varias cargas",
        "energia potencial de un sistema de cargas", "volt como unidad de potencial",
        "trabajo para traer una carga desde el infinito", "potencial cero en el infinito",
        "gradiente de potencial", "electron volt",
        "potencial creado por una carga", "calcular el potencial en un punto",
        "energia por coulomb", "voltaje a cierta distancia de una carga",
        "potencial electrico en un punto", "trabajo para llevar una carga entre dos puntos",
        "energia potencial de dos cargas", "diferencia de voltaje entre placas",
        "potencial de un sistema de cargas puntuales", "potencial electrico creado por un proton",
        "superficie de igual voltaje", "potencial y campo relacion",
        "calcular el voltaje cerca de una carga",
    ],
    "capacitor": [
        "condensador", "almacenar energia en placas paralelas",
        "faradios", "cuanta energia guarda un condensador",
        "placas paralelas con dielectrico", "condensadores en serie y paralelo",
        "microfaradios", "carga almacenada en placas",
        "energia almacenada un medio c v cuadrado", "capacidad de un condensador",
        "capacitor", "capacitancia",
        "que es un capacitor", "c igual a q sobre v",
        "energia en un capacitor", "capacitores en paralelo",
        "capacitores en serie", "dielectrico entre placas",
        "condensador de placas paralelas", "capacitor cargado a cierto voltaje",
        "faradio unidad", "guardar carga en un dispositivo",
        "constante dielectrica", "calcular la capacitancia",
        "banco de condensadores", "capacitancia de placas paralelas epsilon a sobre d",
        "carga que almacena un capacitor", "energia de un condensador cargado",
        "capacitor de 100 microfaradios a 12 voltios", "condensadores en paralelo se suman",
        "condensadores en serie inverso", "que es un faradio",
        "capacitor electrolitico", "capacitor con dielectrico",
        "energia electrica almacenada en un capacitor",
    ],
    # ---------- Módulo 2: Circuitos de corriente continua ----------
    "ohm": [
        "relacion entre voltaje corriente y resistencia", "cuantos amperios pasan por un resistor",
        "como saco el voltaje si tengo corriente y resistencia", "v igual a i por r",
        "intensidad de corriente en un resistor", "corriente que circula por una resistencia",
        "conductor ohmico", "si aumento el voltaje aumenta la corriente",
        "calcular la corriente con 12 voltios y 4 de resistencia", "amperaje de un circuito simple",
        "ley de ohm", "que dice la ley de ohm",
        "calcular voltaje corriente o resistencia", "corriente igual a voltaje entre resistencia",
        "resistencia igual voltaje entre corriente", "cuantos ohmios tiene",
        "voltios amperios y ohmios", "caida de tension en un resistor",
        "foco conectado a una bateria que corriente pasa", "grafica voltaje corriente lineal",
        "proporcionalidad entre v e i", "resistor de 100 ohmios con 5 voltios",
        "que corriente circula", "que voltaje necesito",
        "resistencia de un conductor", "resistor de 220 ohmios a 9 voltios",
        "corriente en una resistencia de 1 kiloohm", "voltaje en los extremos de una resistencia",
        "pasa una corriente de 2 amperios por 10 ohmios", "resistencia de un foco encendido",
        "ley de ohm en corriente continua", "calcular la resistencia de un conductor con voltaje y corriente",
        "pila conectada a un resistor", "intensidad de corriente con la ley de ohm",
        "voltaje igual corriente por resistencia",
    ],
    "resistencia": [
        "resistencia equivalente", "resistores en serie",
        "resistores en paralelo", "como se suman las resistencias",
        "dos resistencias conectadas en paralelo", "combinacion de resistores",
        "reducir un circuito de resistores", "resistencias una despues de otra",
        "resistencias conectadas lado a lado", "req total",
        "resistencias en serie", "resistencias en paralelo",
        "sumar resistencias", "resistencia total del circuito",
        "inverso de la resistencia equivalente", "circuito mixto de resistencias",
        "tres resistencias en serie", "asociacion de resistores",
        "resistencias en paralelo formula", "producto sobre suma",
        "equivalente de dos resistores", "simplificar resistencias",
        "resistores conectados en cadena", "resistencias en derivacion",
        "calcular la resistencia equivalente", "resistencia equivalente de tres resistores en paralelo",
        "dos resistores de 10 ohmios en serie", "resistencia total en serie",
        "equivalente de resistencias mixtas", "como se combinan los resistores",
        "reducir resistencias en paralelo", "resistencia equivalente en paralelo es menor",
        "sumar resistores en serie", "asociacion en paralelo de resistencias",
        "circuito serie paralelo de resistores",
    ],
    "potencia": [
        "cuantos watts consume un foco", "energia consumida por segundo",
        "consumo de un aparato electrico", "p igual a v por i",
        "vatios de una plancha", "cuanto gasta una ducha electrica",
        "potencia disipada en un resistor", "calor generado por una resistencia efecto joule",
        "kilowatt hora", "watts de un artefacto",
        "potencia electrica", "que es la potencia electrica",
        "watts", "p igual i cuadrado por r",
        "p igual v cuadrado entre r", "energia por unidad de tiempo",
        "consumo de energia electrica", "potencia de un foco de 100 watts",
        "cuanto consume un motor", "potencia en un circuito",
        "calcular la potencia", "vatio",
        "disipacion de energia", "recibo de luz consumo",
        "potencia de una resistencia", "potencia de un foco de 60 watts a 220 voltios",
        "energia que consume una resistencia por segundo", "potencia disipada por efecto joule",
        "watts que gasta una terma", "cuanta potencia entrega una bateria",
        "potencia igual voltaje por corriente", "consumo en kilowatts",
        "potencia de un motor electrico", "calor que produce una resistencia",
        "vatios consumidos",
    ],
    "kirchhoff": [
        "ley de nodos", "ley de mallas",
        "suma de corrientes en un nodo", "suma de voltajes en una malla cerrada",
        "circuito con dos baterias", "corrientes que entran y salen de un nodo",
        "analisis de mallas", "conservacion de la carga en un nudo",
        "recorrer una malla sumando voltajes", "circuito con varias fuentes",
        "leyes de kirchhoff", "primera ley de kirchhoff",
        "segunda ley de kirchhoff", "nodos y mallas",
        "corrientes en un nodo", "voltajes en un lazo",
        "circuito de dos mallas", "ecuaciones de malla",
        "metodo de nodos", "suma algebraica de voltajes igual a cero",
        "corriente que entra igual a la que sale", "resolver un circuito complejo",
        "analisis nodal", "circuito con resistencias y dos fuentes",
        "conservacion de la energia en un circuito", "circuito con dos mallas y tres resistencias",
        "ley de corrientes de kirchhoff", "ley de voltajes de kirchhoff",
        "plantear ecuaciones de nodos", "corrientes de rama",
        "circuito con dos fuentes y resistencias", "suma de caidas de tension en un lazo",
        "metodo de mallas", "corriente en cada rama del circuito",
        "nodos de un circuito electrico",
    ],
    "circuito rc": [
        "constante de tiempo tau", "carga de un capacitor a traves de una resistencia",
        "descarga de un condensador en el tiempo", "resistencia y condensador en serie",
        "cuanto tarda en cargarse un capacitor", "tau igual r por c",
        "carga exponencial", "circuito resistencia condensador",
        "tiempo de carga del condensador", "respuesta transitoria",
        "circuito rc", "constante de tiempo",
        "carga y descarga del capacitor", "tau",
        "tiempo de descarga", "capacitor que se descarga por una resistencia",
        "63 por ciento de carga", "curva exponencial del capacitor",
        "transitorio rc", "temporizador con resistencia y capacitor",
        "e a la menos t sobre rc", "circuito de carga del condensador",
        "cuanto tiempo tarda en descargarse", "tiempo caracteristico",
        "flash de camara condensador", "capacitor cargandose con una resistencia en serie",
        "tiempo de carga de un capacitor", "descarga exponencial de un condensador",
        "voltaje del capacitor en funcion del tiempo", "cuanto tiempo tarda en cargarse al 63 por ciento",
        "constante de tiempo de un circuito rc", "circuito rc en serie",
        "resistencia y capacitor en corriente continua", "carga del capacitor despues de un tau",
        "proceso de carga y descarga",
    ],
    # ---------- Módulo 3: Magnetismo y corriente alterna ----------
    "fuerza magnetica": [
        "fuerza de lorentz", "particula cargada moviendose en un iman",
        "carga en movimiento dentro de un campo de un iman", "regla de la mano derecha para la fuerza",
        "q v b seno de theta", "electron entra perpendicular a un campo magnetico",
        "desviacion de un proton por un iman", "fuerza sobre un cable con corriente en un iman",
        "movimiento circular de una carga en campo b", "fuerza sobre carga en movimiento",
        "fuerza magnetica", "fuerza de un campo magnetico sobre una carga",
        "fuerza magnetica sobre un conductor", "f igual q v b",
        "carga moviendose en un campo magnetico", "por que un iman desvia electrones",
        "fuerza sobre una particula en campo magnetico", "producto vectorial v por b",
        "radio de giro de una particula", "espectrometro de masas",
        "fuerza perpendicular a la velocidad", "calcular la fuerza magnetica",
        "fuerza magnetica sobre un proton", "electron girando en un campo",
        "iman que desvia una carga", "fuerza que siente un electron en un campo magnetico",
        "fuerza sobre una carga que se mueve", "proton moviendose perpendicular al campo",
        "fuerza sobre una particula alfa en un campo b", "fuerza magnetica sobre un alambre con corriente",
        "f igual i l b", "trayectoria circular por fuerza magnetica",
        "fuerza de lorentz sobre una carga", "desviacion de electrones en un tubo",
        "carga con velocidad dentro de un campo magnetico",
    ],
    "campo magnetico": [
        "campo que genera un cable con corriente", "teslas alrededor de un conductor",
        "mu cero por i entre dos pi r", "iman y sus polos",
        "ley de ampere", "induccion magnetica de un alambre recto",
        "brujula cerca de un cable", "campo de un solenoide",
        "lineas de campo de un iman", "permeabilidad magnetica del vacio",
        "campo magnetico", "que es el campo magnetico",
        "campo magnetico de un cable", "b igual mu cero i sobre 2 pi r",
        "tesla unidad", "campo magnetico terrestre",
        "campo magnetico de una espira", "polos norte y sur",
        "electroiman", "campo producido por una corriente",
        "calcular el campo magnetico", "experimento de oersted",
        "gauss y tesla", "campo de una bobina",
        "magnetismo de un iman", "campo magnetico a cierta distancia de un cable",
        "teslas que produce una corriente", "campo magnetico en el centro de una espira",
        "campo magnetico de un solenoide largo", "campo creado por un alambre recto",
        "intensidad del campo magnetico de un conductor", "campo magnetico alrededor de un cable recto",
        "campo magnetico producido por corriente continua", "b de un conductor con corriente",
        "campo magnetico de la tierra",
    ],
    "faraday": [
        "fem inducida", "induccion electromagnetica",
        "flujo magnetico que cambia", "iman que entra a una bobina",
        "generador electrico como funciona", "voltaje inducido en una espira",
        "corriente inducida se opone al cambio", "webers",
        "bobina con muchas espiras y campo variable", "transformador induccion",
        "ley de faraday", "ley de lenz",
        "induccion", "fuerza electromotriz inducida",
        "flujo magnetico variable", "cambio de flujo genera voltaje",
        "iman moviendose cerca de una bobina", "como se genera electricidad",
        "dinamo de bicicleta", "la corriente inducida se opone",
        "fem igual menos n delta phi sobre delta t", "induccion en una espira",
        "generador de corriente", "calcular la fem inducida",
        "flujo magnetico que atraviesa una espira", "voltaje que se induce al mover un iman",
        "fem por cambio de flujo", "flujo magnetico que varia con el tiempo",
        "espira girando en un campo magnetico", "induccion de corriente en una bobina",
        "ley de lenz sentido de la corriente inducida", "fem inducida en una bobina de 100 espiras",
        "iman acercandose a una espira", "cambio de campo magnetico induce voltaje",
        "generacion de electricidad por induccion",
    ],
    "alterna": [
        "valor eficaz", "voltaje pico y voltaje eficaz",
        "220 voltios de la casa", "corriente que cambia de sentido",
        "onda senoidal de voltaje", "60 hertz de la red",
        "voltaje maximo entre raiz de dos", "frecuencia de la corriente domestica",
        "corriente del tomacorriente", "valor cuadratico medio",
        "corriente alterna", "que es la corriente alterna",
        "voltaje rms", "valor eficaz del voltaje",
        "vrms igual vmax entre raiz de 2", "diferencia entre corriente continua y alterna",
        "frecuencia y periodo de la corriente", "voltaje de la red electrica",
        "corriente sinusoidal", "valor pico",
        "onda de la corriente alterna", "calcular el valor eficaz",
        "50 o 60 hz", "potencia en corriente alterna",
        "ca y cc", "voltaje eficaz de 220 voltios",
        "voltaje pico de la red", "corriente alterna en una resistencia",
        "valor maximo y valor eficaz", "corriente alterna senoidal",
        "periodo de una corriente de 60 hz", "corriente eficaz en un resistor",
        "voltaje que oscila en el tiempo", "frecuencia de la corriente alterna",
        "potencia media en corriente alterna con resistencia",
    ],
    "rlc": [
        "reactancia inductiva", "reactancia capacitiva",
        "resistencia bobina y condensador en serie", "frecuencia de resonancia",
        "factor de calidad", "angulo de fase del circuito",
        "oposicion total a la corriente alterna", "bobina y condensador con corriente alterna",
        "uno entre dos pi raiz de lc", "circuito sintonizado de una radio",
        "circuito rlc", "impedancia",
        "resonancia", "que es la impedancia",
        "xl y xc", "circuito rlc en serie",
        "cuando ocurre la resonancia", "calcular la impedancia",
        "inductor y capacitor en corriente alterna", "reactancia",
        "f0 de resonancia", "desfase entre voltaje y corriente",
        "circuito inductivo o capacitivo", "sintonizar una frecuencia",
        "impedancia minima", "reactancia de una bobina",
        "reactancia de un condensador en ca", "impedancia de un circuito rlc",
        "resonancia en un circuito serie", "circuito con resistencia inductor y capacitor",
        "frecuencia a la que xl igual xc", "impedancia de una bobina y un condensador",
        "angulo de desfase en rlc", "factor de calidad de un circuito resonante",
        "oposicion a la corriente alterna de bobinas y condensadores",
    ],
    # ---------- Módulo 4: Semiconductores ----------
    "semiconductor": [
        "silicio y germanio", "dopaje tipo n y tipo p",
        "huecos y electrones libres", "material entre conductor y aislante",
        "union pn", "impurezas en el silicio",
        "banda prohibida", "conductividad intermedia",
        "portadores de carga mayoritarios", "cristal de silicio",
        "semiconductores", "que es un semiconductor",
        "semiconductor tipo n", "semiconductor tipo p",
        "dopaje", "material semiconductor",
        "como funcionan los chips", "electrones y huecos",
        "silicio dopado", "conduccion en semiconductores",
        "semiconductor intrinseco", "semiconductor extrinseco",
        "atomos donadores y aceptores", "transistores de silicio",
        "bandas de energia", "como funciona un semiconductor",
        "diferencia entre semiconductor tipo n y tipo p", "dopar silicio con fosforo",
        "dopar silicio con boro", "conduccion por huecos",
        "materiales semiconductores", "electrones libres en un semiconductor",
        "semiconductor puro", "por que el silicio conduce poco",
        "union de un material n y uno p",
    ],
    "diodo": [
        "dispositivo que deja pasar corriente en un solo sentido", "polarizacion directa",
        "polarizacion inversa", "0.7 voltios del silicio",
        "rectificador de media onda", "led con resistencia",
        "curva corriente voltaje no lineal", "anodo y catodo",
        "barrera de potencial", "rectificar la corriente alterna",
        "diodo", "que es un diodo",
        "diodo de silicio", "como funciona un diodo",
        "curva del diodo", "diodo en polarizacion directa",
        "diodo bloquea la corriente", "rectificador",
        "puente de diodos", "caida de voltaje en un diodo",
        "diodo led", "diodo conduce o no conduce",
        "circuito con diodo y resistencia", "diodo ideal",
        "umbral del diodo", "diodo conectado en directa",
        "diodo en inversa no conduce", "corriente en un circuito con diodo",
        "led necesita una resistencia", "diodo de silicio 0.7",
        "rectificar con un diodo", "curva caracteristica del diodo",
        "diodo en un circuito con fuente y resistencia", "sentido de conduccion del diodo",
        "diodo rectificador",
    ],
    # ---------- Clase especial: preguntas que NO son de física ----------
    # Enseña a la IA a reconocer lo que no sabe, para que no invente respuestas
    "fuera de tema": [
        "como preparar un lomo saltado", "receta de pollo a la brasa",
        "que comemos hoy", "ingredientes de una torta",
        "resultado del clasico", "cuando juega la seleccion",
        "quien es el mejor jugador del mundo", "partido de futbol de esta noche",
        "cuentame algo gracioso", "dime una adivinanza",
        "quiero escuchar musica", "que cancion me recomiendas",
        "que serie veo en netflix", "mejor pelicula del ano",
        "cual es la capital de italia", "cuantos habitantes tiene el peru",
        "historia de los incas", "quien descubrio america",
        "que fecha es manana", "a que hora cierra el banco",
        "como esta el tiempo manana", "va a llover hoy",
        "precio del dolar", "cuanto cuesta una laptop",
        "donde compro zapatillas", "ayudame con mi tarea de lenguaje",
        "escribe un poema", "traduce esto al ingles",
        "como hago una carta de presentacion", "consejos para dormir mejor",
        "como bajar de peso", "que es la fotosintesis",
        "tabla periodica de los elementos", "como se resuelve una ecuacion cuadratica",
        "derivada de x al cuadrado", "quien es el presidente del peru",
        "noticias de hoy", "como me inscribo en la universidad",
        "cual es tu nombre", "eres una persona",
        "me siento aburrido", "que opinas del amor",
        "como invertir mi dinero", "juego de playstation",
        "como aprender a programar en java", "quien gano el mundial",
        "que animal es el mas rapido", "cuantos planetas hay en el sistema solar",
        "como cuidar a mi perro", "telefono de una pizzeria",
    ],
    "zener": [
        "regulador de voltaje", "voltaje de ruptura",
        "diodo que trabaja en inversa", "mantener un voltaje constante",
        "regulacion de tension", "fuente regulada",
        "estabilizar el voltaje de salida", "diodo de avalancha",
        "tension de ruptura inversa", "proteger un circuito de sobrevoltaje",
        "diodo zener", "que es un diodo zener",
        "zener como regulador", "voltaje zener",
        "zener en polarizacion inversa", "regular voltaje con zener",
        "fuente de voltaje regulada", "diodo para regular",
        "zener de 5.1 voltios", "estabilizador de tension",
        "ruptura zener", "zener y resistencia limitadora",
        "mantener 5 voltios constantes", "proteccion contra picos de voltaje",
        "efecto zener", "zener regula la tension",
        "diodo zener en inversa", "voltaje de zener constante",
        "regulador con diodo zener", "zener de 12 voltios",
        "como regula un zener", "zener con resistencia en serie",
        "tension de zener", "usar un zener para estabilizar",
        "diodo zener como referencia de voltaje",
    ],
}

# Para cada tema: texto que activa la teoría, ejercicio disponible y gráfica disponible
TEMAS_IA = {
    "carga":            ("carga electrica",      "carga",            None),
    "coulomb":          ("coulomb",              "coulomb",          None),
    "campo":            ("campo electrico",      "campo",            None),
    "gauss":            ("gauss",                None,               None),
    "potencial":        ("potencial",            "potencial",        "potencial"),
    "capacitor":        ("capacitor",            "capacitor",        "carga_capacitor"),
    "ohm":              ("ohm",                  "ohm",              "ohm"),
    "resistencia":      ("resistencia serie",    "resistencia",      None),
    "potencia":         ("potencia",             "potencia",         None),
    "kirchhoff":        ("kirchhoff",            "kirchhoff",        None),
    "circuito rc":      ("circuito rc",          "circuito_rc",      "carga_capacitor"),
    "fuerza magnetica": ("fuerza magnetica",     "fuerza_magnetica", "fuerza_magnetica"),
    "campo magnetico":  ("campo magnetico",      "campo_magnetico",  "campo_magnetico"),
    "faraday":          ("faraday",              "faraday",          "faraday"),
    "alterna":          ("alterna",              "alterna",          "alterna"),
    "rlc":              ("rlc",                  "rlc",              "resonancia"),
    "semiconductor":    ("semiconductor",        None,               None),
    "diodo":            ("diodo",                "diodo",            "diodo"),
    "zener":            ("zener",                "zener",            None),
}
TEMA_FUERA = "fuera de tema"

UMBRAL_RESPONDER = 0.45   # con esta confianza o más, la IA responde directamente
UMBRAL_PREGUNTAR = 0.15   # entre 15% y 45%, la IA duda y pregunta; por debajo, admite que no entendió


def _datos_xy():
    X, y = [], []
    for tema, frases in DATOS_ENTRENAMIENTO.items():
        X += [normalizar(f) for f in frases]
        y += [tema] * len(frases)
    return X, y


def _crear_modelo():
    return make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
        LogisticRegression(C=20, max_iter=2000),
    )


@st.cache_resource
def entrenar_modelo():
    """Entrena el modelo una sola vez y lo guarda en memoria."""
    X, y = _datos_xy()
    modelo = _crear_modelo()
    modelo.fit(X, y)
    return modelo


@st.cache_resource
def evaluar_modelo():
    """Precisión con validación cruzada de 5 particiones (para el informe)."""
    X, y = _datos_xy()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    puntajes = cross_val_score(_crear_modelo(), X, y, cv=cv)
    return float(puntajes.mean()), len(X), len(set(y)) - 1  # temas de física (sin "fuera de tema")


def predecir_temas(texto, k=3):
    """Devuelve los k temas más probables según el modelo: [(tema, confianza), ...]."""
    modelo = entrenar_modelo()
    probs = modelo.predict_proba([normalizar(texto)])[0]
    orden = np.argsort(probs)[::-1][:k]
    return [(modelo.classes_[i], float(probs[i])) for i in orden]


def predecir_tema(texto):
    """Devuelve el tema más probable y su confianza."""
    return predecir_temas(texto, 1)[0]


def responder_tema(tema, pregunta, confianza=None):
    """Da teoría, ejercicio o gráfica del tema, según lo que pida la pregunta."""
    texto_teoria, ejercicio, grafica = TEMAS_IA[tema]
    nota = (f"\n\n---\n*🤖 IA: entendí que preguntas por **{tema}** (confianza: {confianza:.0%}).*"
            if confianza is not None else "")
    p = normalizar(pregunta)
    pide_ejercicio = any(w in p for w in ("resuelve", "calcula", "ejercicio", "problema", "hallar", "halla", "cuanto", "cuantos", "cuanta"))
    pide_grafica = any(w in p for w in ("grafica", "grafico", "curva", "dibuja", "muestra"))

    if pide_grafica and grafica:
        return f"Aquí tienes la gráfica: **{NOMBRES_GRAFICAS.get(grafica, grafica)}**." + nota, grafica
    if pide_ejercicio and ejercicio:
        return iniciar_flujo(ejercicio) + nota, None
    teoria = respuesta_teorica(texto_teoria)
    if pide_ejercicio and not ejercicio:
        teoria += "\n\n*(Todavía no tengo ejercicios paso a paso de este tema, pero aquí tienes la teoría.)*"
    return teoria + nota, None


def responder_con_ia(pregunta, permitir_preguntar=True):
    """Usa la IA para entender la pregunta.
    - Confianza alta  -> responde.
    - Confianza media -> pregunta al usuario cuál de los temas más probables quiso decir.
    - Confianza baja  -> no responde (evita inventar)."""
    top = predecir_temas(pregunta, 4)
    tema, confianza = top[0]
    if tema == TEMA_FUERA:
        return None, None  # la IA reconoce que la pregunta no es de física
    top = [(t, c) for t, c in top if t != TEMA_FUERA]
    if confianza >= UMBRAL_RESPONDER:
        return responder_tema(tema, pregunta, confianza)
    if confianza >= UMBRAL_PREGUNTAR and permitir_preguntar:
        opciones = [t for t, c in top if c >= 0.08][:3]
        st.session_state.sugerencias = {"temas": opciones, "pregunta": pregunta}
        lista = "\n".join(f"{i}. **{t}**" for i, t in enumerate(opciones, 1))
        return ("🤔 No estoy completamente seguro de lo que preguntas. ¿Te refieres a alguno de estos temas?\n\n"
                f"{lista}\n\nEscribe el **número** de la opción, o reformula tu pregunta."), None
    return None, None

# ------------------------------------------------------------
# LÓGICA PRINCIPAL
# ------------------------------------------------------------

GRAFICAS_CON_DATOS = {"potencial", "carga_capacitor", "ohm", "fuerza_magnetica", "campo_magnetico", "faraday", "alterna", "resonancia"}

NOMBRES_GRAFICAS = {
    "diodo": "curva I-V del diodo", "carga_capacitor": "carga del capacitor",
    "descarga_capacitor": "descarga del capacitor", "ohm": "ley de Ohm",
    "resonancia": "resonancia RLC", "fuerza_magnetica": "fuerza magnética vs ángulo",
    "campo_magnetico": "campo magnético vs distancia", "faraday": "ley de Faraday (flujo y fem)",
    "alterna": "corriente alterna (onda senoidal)", "potencial": "potencial eléctrico vs distancia"}

def respuesta_social(p):
    """Responde saludos, agradecimientos y despedidas (p ya viene normalizado)."""
    palabras = set(re.findall(r"[a-zñ]+", p))
    if palabras & {"gracias", "agradezco", "agradecido", "agradecida", "thanks"}:
        return ("😊 ¡De nada! Me alegra ayudarte. Si quieres, pídeme otro ejercicio, "
                "una fórmula o una gráfica. Escribe **ayuda** para ver todos los temas.")
    if palabras & {"adios", "chau", "chao", "bye"} or "hasta luego" in p or "nos vemos" in p or "hasta pronto" in p:
        return "👋 ¡Hasta luego! Éxitos con tus estudios de física. Vuelve cuando quieras."
    if (palabras & {"hola", "buenas", "buenos", "saludos", "hey", "holi"}
            or "que tal" in p or "como estas" in p or "como te va" in p):
        return ("👋 ¡Hola! Muy bien, gracias por preguntar. Soy tu tutor virtual de **Física Aplicada**.\n\n" + MENU)
    return None

def quitar_saludo(p):
    """Quita las palabras de saludo del inicio de la frase."""
    patron = r"^(hola|holi|hey|saludos|buenas|buenos|buen|dias|tardes|noches|que tal|como estas|como te va)\b[\s,!.?]*"
    resto, anterior = p.strip(" ¡!¿?.,"), None
    while resto != anterior:  # quita varios saludos seguidos: "hola buenas noches"
        anterior = resto
        resto = re.sub(patron, "", resto).strip()
    return resto

COMANDOS_CANCELAR = {"cancelar", "cancela", "salir", "reiniciar", "reinicia", "parar", "stop"}
COMANDOS_MENU = {"ayuda", "menu", "temas", "help", "que puedes hacer", "opciones"}

MENU = ("📚 **¿Qué puedo hacer?**\n\n"
        "**Módulo 1 – Electrostática:** carga eléctrica, ley de Coulomb, campo eléctrico, ley de Gauss, potencial, capacitores\n\n"
        "**Módulo 2 – Circuitos de corriente continua:** ley de Ohm, resistencias en serie y paralelo, potencia, Kirchhoff, circuito RC\n\n"
        "**Módulo 3 – Magnetismo y corriente alterna:** fuerza magnética, campo magnético, ley de Faraday y Lenz, "
        "corriente alterna (RMS), impedancia y resonancia RLC\n\n"
        "**Módulo 4 – Semiconductores:** semiconductores, diodo, diodo Zener\n\n"
        "**Ejemplos:**\n"
        "- *¿Qué es la ley de Faraday?*\n"
        "- *Resuelve un ejercicio de fuerza magnética*\n"
        "- *Resuelve un ejercicio de rlc*\n"
        "- *Muéstrame la gráfica de resonancia*\n"
        "- *Muéstrame la gráfica de corriente alterna*\n\n"
        "Durante un ejercicio puedes escribir **cancelar** para salir.\n\n"
        "🤖 También puedes preguntarme con tus propias palabras: uso **inteligencia artificial** para entenderte. "
        "Escribe **info ia** para saber cómo funciona.")

pregunta = st.chat_input("Escribe tu pregunta, pide un ejercicio o una gráfica...")

if pregunta:
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    p_norm = normalizar(pregunta).strip(" .!?¿¡")

    # Respuesta del usuario cuando la IA dudó y propuso opciones
    sug = st.session_state.sugerencias
    st.session_state.sugerencias = None
    eleccion = None
    if sug and st.session_state.flujo is None:
        mapa = {"1": 0, "2": 1, "3": 2, "uno": 0, "dos": 1, "tres": 2,
                "la 1": 0, "la 2": 1, "la 3": 2, "la primera": 0, "la segunda": 1, "la tercera": 2}
        if p_norm in mapa and mapa[p_norm] < len(sug["temas"]):
            eleccion = sug["temas"][mapa[p_norm]]
        elif p_norm in sug["temas"]:
            eleccion = p_norm

    if eleccion:
        respuesta, st.session_state.grafica = responder_tema(eleccion, sug["pregunta"])

    # 0) Cancelar un ejercicio a medias
    elif st.session_state.flujo is not None and p_norm in COMANDOS_CANCELAR:
        st.session_state.flujo = None
        st.session_state.paso = 0
        respuesta = "❎ Ejercicio cancelado. Pídeme otro ejercicio, una fórmula o una gráfica.\n\n" + MENU
        st.session_state.grafica = None

    # 1) Si hay un flujo activo, continuar
    elif st.session_state.flujo is not None:
        respuesta = continuar_flujo(pregunta)
        st.session_state.grafica = None

    # "cancelar" sin ningún ejercicio en curso
    elif p_norm in COMANDOS_CANCELAR:
        respuesta = "No hay ningún ejercicio en curso. Pídeme uno, por ejemplo: *resuelve un ejercicio de faraday*."
        st.session_state.grafica = None

    # 2) Menú de ayuda
    elif p_norm in COMANDOS_MENU:
        respuesta = MENU
        st.session_state.grafica = None

    # Información del modelo de IA (útil para la exposición)
    elif p_norm in ("info ia", "informacion ia", "como funciona la ia", "precision ia"):
        precision, n_frases, n_temas = evaluar_modelo()
        respuesta = ("🤖 **¿Cómo funciona mi inteligencia artificial?**\n\n"
                     "Uso un modelo de **machine learning** para entender preguntas escritas con tus propias palabras:\n\n"
                     "1. **Datos de entrenamiento:** frases de ejemplo etiquetadas con su tema.\n"
                     "2. **Vectorización TF-IDF:** convierto el texto en números usando fragmentos de 2 a 5 letras "
                     "(por eso tolero errores de ortografía).\n"
                     "3. **Regresión logística:** el modelo aprende qué patrones corresponden a cada tema.\n"
                     "4. **Predicción:** elijo el tema más probable y muestro mi porcentaje de confianza.\n\n"
                     f"**Datos del modelo:** {n_frases} frases de entrenamiento · {n_temas} temas de física + 1 clase \"fuera de tema\" · "
                     f"precisión por validación cruzada (5 particiones): **{precision:.0%}**\n\n"
                     "*Primero intento con reglas de palabras clave (exactas); si no te entiendo, usa la IA.*")
        st.session_state.grafica = None

    else:
        tipo_ej = detectar_ejercicio(pregunta)
        tipo_graf = detectar_grafica(pregunta)

        # 3) Ver si pide un ejercicio
        if tipo_ej:
            respuesta = iniciar_flujo(tipo_ej)
            st.session_state.grafica = None

        # 4) Ver si pide una gráfica
        elif tipo_graf:
            respuesta = f"Aquí tienes la gráfica: **{NOMBRES_GRAFICAS.get(tipo_graf, tipo_graf)}**."
            if tipo_graf in GRAFICAS_CON_DATOS:
                if (tipo_graf in st.session_state.graf_params
                        or (tipo_graf == "carga_capacitor" and "rc" in st.session_state.graf_params)
                        or (tipo_graf == "resonancia" and st.session_state.q_rlc != 1)):
                    respuesta += "\n\n*Dibujada con los datos de tu último ejercicio.*"
                else:
                    respuesta += ("\n\n*Dibujada con **valores de ejemplo**. Resuelve primero un ejercicio de este tema "
                                  "para verla con tus propios datos.*")
            st.session_state.grafica = tipo_graf

        # Pidió una gráfica que no existe
        elif any(w in p_norm for w in ("grafica", "grafico", "curva")) and not responder_con_ia(pregunta, permitir_preguntar=False)[1]:
            respuesta = ("Dime qué gráfica quieres ver: **diodo**, **carga del capacitor**, "
                         "**descarga del capacitor**, **potencial**, **ley de ohm**, **fuerza magnética**, **campo magnético**, "
                         "**faraday**, **corriente alterna** o **resonancia**.")
            st.session_state.grafica = None

        # 5) Si no pide ejercicio, dar respuesta teórica
        else:
            r = respuesta_teorica(pregunta)
            st.session_state.grafica = None
            social = respuesta_social(p_norm)
            # Si después del saludo viene una pregunta ("buenas, como funciona un generador"),
            # se responde la pregunta y no solo el saludo
            resto = quitar_saludo(p_norm)
            if social and len(resto.split()) >= 2 and responder_con_ia(resto, permitir_preguntar=False)[0]:
                social = None
                pregunta = resto
            if r:
                respuesta = r
            elif social:
                # Saludos, agradecimientos y despedidas
                respuesta = social
            else:
                # 6) Si las reglas no entienden, responde la IA (machine learning)
                r_ia, graf_ia = responder_con_ia(pregunta)
                if r_ia:
                    respuesta = r_ia
                    st.session_state.grafica = graf_ia
                else:
                    respuesta = ("Lo siento, no entendí. Puedo **explicarte fórmulas**, "
                                 "**resolver ejercicios** o **mostrarte gráficas** de los 4 módulos. "
                                 "Ejemplo: 'resuelve un ejercicio de la ley de ohm' o 'muéstrame la gráfica del diodo'.\n\n"
                                 "Escribe **ayuda** para ver todos los temas.")

    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
    with st.chat_message("assistant"):
        st.markdown(respuesta)

if st.session_state.grafica:
    fig = generar_grafica(st.session_state.grafica)
    st.pyplot(fig)
