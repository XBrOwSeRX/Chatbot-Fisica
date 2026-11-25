# ============================================================
# CHATBOT DE FÍSICA APLICADA - VERSIÓN FINAL CON GRÁFICAS
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
    st.session_state.grafica = None   # Guarda qué gráfica mostrar

# ------------------------------------------------------------
# MOSTRAR HISTORIAL
# ------------------------------------------------------------
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------------------------
# UTILIDAD: EXTRAER NÚMERO
# ------------------------------------------------------------
def extraer_numero(texto):
    texto = texto.replace(",", ".")
    match = re.search(r"-?\d+(\.\d+)?", texto)
    return float(match.group()) if match else None
# ------------------------------------------------------------
# FUNCIÓN PARA CONVERTIR UNIDADES (micro, mili, centi, etc.)
# ------------------------------------------------------------
def convertir_unidades(texto):
    texto = texto.lower().replace(",", ".")
    multiplicador = 1.0
    
    # Evaluamos "cm" PRIMERO para que no lo confunda con "mili" o "m"
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

    # Busca el número en el texto
    match = re.search(r"-?\d+(\.\d+)?", texto)
    if match:
        return float(match.group()) * multiplicador
    return None
# ------------------------------------------------------------
# RESPUESTAS TEÓRICAS
# ------------------------------------------------------------
def respuesta_teorica(p):
    p = p.lower()
    if "coulomb" in p:
        return "La Ley de Coulomb: **F = k * (|q1 * q2|) / r²**. k = 9x10⁹ N·m²/C²."
    elif "campo" in p and "electrico" in p:
        return "Campo eléctrico: **E = F / q**. Se mide en N/C o V/m."
    elif "carga" in p and "electrica" in p:
        return "Carga eléctrica: **Q = n * e**, con e = 1.602 x 10⁻¹⁹ C."
    elif "gauss" in p:
        return "Ley de Gauss: **Φ = Q_encerrada / ε₀**."
    elif "potencial" in p:
        return "Potencial eléctrico: **V = U / q**. Se mide en Voltios."
    elif "capacitor" in p or "capacitancia" in p:
        return "Capacitor: **C = Q / V**. En serie: 1/Ct = 1/C1 + 1/C2. En paralelo: Ct = C1 + C2."
    elif "ohm" in p:
        return "Ley de Ohm: **V = I * R**."
    elif "resistencia" in p and ("serie" in p or "paralelo" in p):
        return "En serie: **Req = R1 + R2**. En paralelo: **1/Req = 1/R1 + 1/R2**."
    elif "potencia" in p:
        return "Potencia: **P = V * I**, **P = I² * R**, **P = V² / R**."
    elif "kirchhoff" in p:
        return "Kirchhoff: Nodos → corrientes entrantes = salientes. Mallas → suma de voltajes = 0."
    elif "rc" in p or "transitorio" in p:
        return "Circuito RC: constante de tiempo **τ = R * C**."
    elif "magnetica" in p and "fuerza" in p:
        return "Fuerza magnética: **F = q * (v × B)**."
    elif "faraday" in p or "lenz" in p:
        return "Faraday: **ε = -dΦ/dt**. Lenz: la corriente inducida se opone al cambio."
    elif "alterna" in p or "eficaz" in p or "rms" in p:
        return "En CA: **V_rms = V_max / √2**."
    elif "impedancia" in p or "rlc" in p:
        return "Impedancia Z combina R y X. Resonancia RLC cuando Xl = Xc."
    elif "diodo" in p and "zener" not in p:
        return "Un diodo conduce en polarización directa y bloquea en inversa."
    elif "semiconductor" in p:
        return "Tipo N: exceso de electrones. Tipo P: exceso de huecos."
    elif "zener" in p:
        return "Diodo Zener: regula voltaje permitiendo flujo inverso al alcanzar su voltaje Zener."
    else:
        return None

# ------------------------------------------------------------
# DETECTAR SI QUIERE RESOLVER UN EJERCICIO O VER UNA GRÁFICA
# ------------------------------------------------------------
def detectar_ejercicio(p):
    p = p.lower()
    gatillos = ["resuelve", "calcula", "ejercicio", "problema", "ayuda", "quiero calcular"]
    if ("coulomb" in p or "fuerza electrica" in p) and any(w in p for w in gatillos):
        return "coulomb"
    if "ohm" in p and any(w in p for w in gatillos):
        return "ohm"
    if "potencia" in p and any(w in p for w in gatillos):
        return "potencia"
    return None

def detectar_grafica(p):
    p = p.lower()
    if "grafica" in p or "gráfico" in p or "curva" in p or "muestra" in p:
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
# INICIAR FLUJO DE EJERCICIO
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

# ------------------------------------------------------------
# CONTINUAR FLUJO
# ------------------------------------------------------------
def continuar_flujo(texto):
    flujo = st.session_state.flujo
    datos = st.session_state.datos
    paso = st.session_state.paso

    if flujo == "coulomb":
        if paso == 0:
            n = convertir_unidades(texto)  # <-- CAMBIO AQUÍ
            if n is None:
                return "No detecté un número. Pásame la **carga q1 en C** (ej: 2 micro, 0.000002)."
            datos["q1"] = n
            st.session_state.paso = 1
            return "Perfecto. Ahora pásame la **carga q2 en C**."
            
        elif paso == 1:
            n = convertir_unidades(texto)  # <-- CAMBIO AQUÍ
            if n is None:
                return "No detecté un número. Pásame la **carga q2 en C** (ej: 3 micro)."
            datos["q2"] = n
            st.session_state.paso = 2
            return "Bien. Ahora pásame la **distancia r en metros (m)**."
            
        elif paso == 2:
            n = convertir_unidades(texto)  # <-- CAMBIO AQUÍ
            if n is None or n == 0:
                return "No detecté una distancia válida. Pásame la **distancia r en m** (ej: 5 centi, 0.05)."
            datos["r"] = n
            
            k = 9e9
            F = k * abs(datos["q1"] * datos["q2"]) / (datos["r"] ** 2)
            tipo = "repulsión" if datos["q1"] * datos["q2"] > 0 else "atracción"
            st.session_state.flujo = None
            return (f"✅ **Resultado:** F = {F:.4e} N\n\n"
                    f"**Fórmula:** F = k·|q1·q2|/r² = 9x10⁹ · |{datos['q1']}·{datos['q2']}| / {datos['r']}²\n\n"
                    f"La fuerza es de **{tipo}**.")

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
            datos["b"] = n
            inc = datos["incognita"]
            st.session_state.flujo = None
            if inc == "V":
                V = datos["a"] * datos["b"]
                return f"✅ **Resultado:** V = {V} V\n\n**Fórmula:** V = I·R = {datos['a']}·{datos['b']}"
            elif inc == "I":
                if datos["b"] == 0:
                    return "La resistencia no puede ser 0. Reinicia el cálculo."
                I = datos["a"] / datos["b"]
                return f"✅ **Resultado:** I = {I} A\n\n**Fórmula:** I = V/R = {datos['a']}/{datos['b']}"
            else:
                if datos["b"] == 0:
                    return "La corriente no puede ser 0. Reinicia el cálculo."
                R = datos["a"] / datos["b"]
                return f"✅ **Resultado:** R = {R} Ω\n\n**Fórmula:** R = V/I = {datos['a']}/{datos['b']}"

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
            return f"✅ **Resultado:** P = {P} W\n\n**Fórmula:** P = V·I = {datos['V']}·{datos['I']}"

    return "Algo salió mal. Reinicia el cálculo escribiendo 'resuelve un ejercicio'."

# ------------------------------------------------------------
# FUNCIÓN QUE GENERA LAS GRÁFICAS
# Devuelve una figura de matplotlib según el tipo.
# ------------------------------------------------------------
def generar_grafica(tipo):
    fig, ax = plt.subplots(figsize=(6, 4))

    # --- Curva I-V de un diodo ---
    if tipo == "diodo":
        V = np.linspace(-1, 1, 200)
        I = np.where(V > 0, (np.exp(V / 0.05) - 1) * 1e-3, -1e-6)
        ax.plot(V, I, color="blue")
        ax.set_title("Curva I-V de un diodo")
        ax.set_xlabel("Voltaje (V)")
        ax.set_ylabel("Corriente (A)")
        ax.grid(True)

    # --- Carga de un capacitor ---
    elif tipo == "carga_capacitor":
        t = np.linspace(0, 5, 200)
        q = 1 - np.exp(-t)
        ax.plot(t, q, color="green")
        ax.set_title("Carga de un capacitor (Q vs t)")
        ax.set_xlabel("Tiempo (τ = RC)")
        ax.set_ylabel("Carga normalizada")
        ax.grid(True)

    # --- Descarga de un capacitor ---
    elif tipo == "descarga_capacitor":
        t = np.linspace(0, 5, 200)
        q = np.exp(-t)
        ax.plot(t, q, color="red")
        ax.set_title("Descarga de un capacitor (Q vs t)")
        ax.set_xlabel("Tiempo (τ = RC)")
        ax.set_ylabel("Carga normalizada")
        ax.grid(True)

    # --- Ley de Ohm (V vs I) DINÁMICA ---
    elif tipo == "ohm":
        # Buscamos si el alumno ya calculó una Resistencia antes
        R = st.session_state.datos.get("R_grafica", 5) 
        I = np.linspace(0, 10, 100)
        V = I * R
        ax.plot(I, V, color="purple")
        ax.set_title(f"Ley de Ohm: V = I·R (R = {R} Ω)") # El título cambia
        ax.set_xlabel("Corriente (A)")
        ax.set_ylabel("Voltaje (V)")
        ax.grid(True)

    # --- Resonancia RLC (Agregamos un ejemplo para que cambie la curva) ---
    elif tipo == "resonancia":
        # Buscamos si el alumno dio un factor de calidad (Q), si no, usamos 1
        Q = st.session_state.datos.get("Q_rlc", 1) 
        f = np.linspace(0.1, 10, 500)
        # Fórmula más realista de resonancia con factor Q
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

          # 1) Si hay flujo activo, continuar
    if st.session_state.flujo is not None:
        respuesta = continuar_flujo(pregunta)
        st.session_state.grafica = None

    # 2) Si no, ver si pide gráfica
    else:
        tipo_graf = detectar_grafica(pregunta)
        if tipo_graf:
            respuesta = f"Aquí tienes la gráfica: **{tipo_graf.replace('_', ' ')}**."
            st.session_state.grafica = tipo_graf
        else:
            # 3) Ver si pide ejercicio
            tipo_ej = detectar_ejercicio(pregunta)
            if tipo_ej:
                respuesta = iniciar_flujo(tipo_ej)
                st.session_state.grafica = None
            else:
                # 4) Respuesta teórica
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

# ------------------------------------------------------------
# MOSTRAR GRÁFICA (si hay una activa)
# ------------------------------------------------------------
if st.session_state.grafica:
    fig = generar_grafica(st.session_state.grafica)
    st.pyplot(fig)
