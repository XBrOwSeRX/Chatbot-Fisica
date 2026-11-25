# ============================================================
# CHATBOT DE FÍSICA APLICADA - VERSIÓN FINAL DEFINITIVA
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
    "**resolver ejercicios paso a paso** y **mostrarte gráficas** de los 4 módulos del curso."
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

for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------
# UTILIDADES Y FORMATOS
# ------------------------------------------------------------
def extraer_numero(texto):
    texto = texto.replace(",", ".")
    match = re.search(r"-?\d+(\.\d+)?", texto)
    return float(match.group()) if match else None

def convertir_unidades(texto):
    texto = texto.lower().replace(",", ".")
    multiplicador = 1.0
    
    if "cm" in texto or "centi" in texto:
        multiplicador = 1e-2
    elif "micro" in texto or "μ" in texto or "microcoloumb" in texto:
        multiplicador = 1e-6
    elif "nano" in texto:
        multiplicador = 1e-9
    elif "mili" in texto or "mm" in texto:
        multiplicador = 1e-3
    elif "kilo" in texto or "k" in texto:
        multiplicador = 1e3

    match = re.search(r"-?\d+(\.\d+)?", texto)
    if match:
        return float(match.group()) * multiplicador
    return None

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

# ------------------------------------------------------------
# RESPUESTAS TEÓRICAS
# ------------------------------------------------------------
def respuesta_teorica(p):
    # Pasamos todo a minúsculas y quitamos las tildes para evitar fallos
    p = p.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
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
                "**Fórmula:** V = U / q\n"
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
                
    elif "rc" in p or "transitorio" in p:
        return ("⏱️ **Circuito RC:**\n\n"
                "**Concepto:** Circuito con resistencia y capacitor. La constante de tiempo indica qué tan rápido se carga o descarga.\n"
                "**Fórmula:** τ = R * C\n\n"
                "*Escribe 'resuelve un ejercicio de circuito rc' para calcular el tiempo.*")
                
    elif "magnetica" in p and "fuerza" in p:
        return ("🧲 **Fuerza Magnética:**\n\n"
                "**Concepto:** Fuerza que ejerce un campo magnético sobre una carga en movimiento.\n"
                "**Fórmula:** F = q * (v × B)\n"
                "**Dato clave:** Es perpendicular a la velocidad y al campo magnético.\n\n"
                "*Escribe 'resuelve un ejercicio de fuerza magnetica' para practicar.*")
                
    elif "faraday" in p or "lenz" in p:
        return ("🔄 **Ley de Faraday y Lenz:**\n\n"
                "**Faraday:** Un campo magnético variable genera una fuerza electromotriz inducida. Fórmula: ε = -dΦ/dt.\n"
                "**Lenz:** La corriente inducida siempre se opone al cambio que la produjo.\n\n"
                "*Escribe 'resuelve un ejercicio de faraday' para calcular la fem.*")
                
    elif "alterna" in p or "eficaz" in p or "rms" in p:
        return ("〰️ **Corriente Alterna (CA):**\n\n"
                "**Concepto:** La corriente y el voltaje varían cíclicamente en el tiempo.\n"
                "**Fórmula:** V_rms = V_max / √2\n"
                "**Dato clave:** El valor eficaz (RMS) equivale al de una corriente continua que produce el mismo efecto térmico.\n\n"
                "*Escribe 'resuelve un ejercicio de corriente alterna' para calcularlo.*")
                
    elif "impedancia" in p or "rlc" in p:
        return ("📈 **Impedancia y Resonancia RLC:**\n\n"
                "**Impedancia (Z):** Es la oposición total al flujo de corriente alterna. Combina la resistencia (R) y la reactancia (X).\n"
                "**Resonancia:** Ocurre cuando la reactancia inductiva (Xl) iguala a la capacitiva (Xc), minimizando la impedancia.\n\n"
                "*Escribe 'muéstrame la gráfica de resonancia' para ver la curva.*")
                
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
    p = p.lower()
    gatillos = ["resuelve", "resuelbe", "calcula", "ejercicio", "problema", "ayuda", "quiero calcular", "hazme"]
    
    if ("coulom" in p or "fuerza electrica" in p) and any(w in p for w in gatillos):
        return "coulomb"
    if "ohm" in p and any(w in p for w in gatillos):
        return "ohm"
    if "potencia" in p and any(w in p for w in gatillos):
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
    p = p.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    if "grafica" in p or "grafico" in p or "curva" in p or "muestra" in p:
        if "diodo" in p or "i-v" in p:
            return "diodo"
        if "carga" in p and "capacitor" in p:
            return "carga_capacitor"
        if "descarga" in p and "capacitor" in p:
            return "descarga_capacitor"
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
            return (f"✅ **Resultado:** F = {F_f} N\n\n"
                    f"**Fórmula:** F = k·|q1·q2|/r² = 9x10⁹ · |({q1_f})·({q2_f})| / ({r_f})²\n\n"
                    f"La fuerza es de **{tipo}**.")

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
            
            if inc == "V":
                V = datos["a"] * datos["b"]
                return f"✅ **Resultado:** V = {formato_inteligente(V)} V\n\n**Fórmula:** V = I·R = {formato_inteligente(datos['a'])}·{formato_inteligente(datos['b'])}"
            elif inc == "I":
                I = datos["a"] / datos["b"]
                return f"✅ **Resultado:** I = {formato_inteligente(I)} A\n\n**Fórmula:** I = V/R = {formato_inteligente(datos['a'])}/{formato_inteligente(datos['b'])}"
            else:
                R = datos["a"] / datos["b"]
                st.session_state.datos["R_grafica"] = R
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

    return "Algo salió mal. Reinicia el cálculo escribiendo 'resuelve un ejercicio'."

# ------------------------------------------------------------
# GENERADOR DE GRÁFICAS
# ------------------------------------------------------------
def generar_grafica(tipo):
    fig, ax = plt.subplots(figsize=(6, 4))

    if tipo == "diodo":
        V = np.linspace(-1, 1, 200)
        I = np.where(V > 0, (np.exp(V / 0.05) - 1) * 1e-3, -1e-6)
        ax.plot(V, I, color="blue")
        ax.set_title("Curva I-V de un diodo")
        ax.set_xlabel("Voltaje (V)")
        ax.set_ylabel("Corriente (A)")
        ax.grid(True)

    elif tipo == "carga_capacitor":
        t = np.linspace(0, 5, 200)
        q = 1 - np.exp(-t)
        ax.plot(t, q, color="green")
        ax.set_title("Carga de un capacitor (Q vs t)")
        ax.set_xlabel("Tiempo (τ = RC)")
        ax.set_ylabel("Carga normalizada")
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
        R = st.session_state.datos.get("R_grafica", 5) 
        I = np.linspace(0, 10, 100)
        V = I * R
        ax.plot(I, V, color="purple")
        ax.set_title(f"Ley de Ohm: V = I·R (R = {R} Ω)") 
        ax.set_xlabel("Corriente (A)")
        ax.set_ylabel("Voltaje (V)")
        ax.grid(True)

    elif tipo == "resonancia":
        Q = st.session_state.datos.get("Q_rlc", 1) 
        f = np.linspace(0.1, 10, 500)
        Z = np.abs(1 / (1 + 1j * Q * (f - 1 / f)))
        ax.plot(f, Z, color="orange")
        ax.set_title(f"Resonancia en circuito RLC (Factor Q = {Q})")
        ax.set_xlabel("Frecuencia relativa (f/f₀)")
        ax.set_ylabel("Impedancia normalizada")
        ax.grid(True)

    return fig

# ------------------------------------------------------------
# LÓGICA PRINCIPAL
# ------------------------------------------------------------
pregunta = st.chat_input("Escribe tu pregunta, pide un ejercicio o una gráfica...")

if pregunta:
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    if st.session_state.flujo is not None:
        respuesta = continuar_flujo(pregunta)
        st.session_state.grafica = None
    else:
        tipo_graf = detectar_grafica(pregunta)
        if tipo_graf:
            respuesta = f"Aquí tienes la gráfica: **{tipo_graf.replace('_', ' ')}**."
            st.session_state.grafica = tipo_graf
        else:
            tipo_ej = detectar_ejercicio(pregunta)
            if tipo_ej:
                respuesta = iniciar_flujo(tipo_ej)
                st.session_state.grafica = None
            else:
                r = respuesta_teorica(pregunta)
                if r:
                    respuesta = r
                else:
                    respuesta = ("Lo siento, no entendí. Puedo **explicarte fórmulas**, "
                                 "**resolver ejercicios** o **mostrarte gráficas** de los 4 módulos. "
                                 "Ejemplo: 'resuelve un ejercicio de la ley de ohm' o 'muéstrame la gráfica del diodo'.")
                st.session_state.grafica = None

    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
    with st.chat_message("assistant"):
        st.markdown(respuesta)

if st.session_state.grafica:
    fig = generar_grafica(st.session_state.grafica)
    st.pyplot(fig)
