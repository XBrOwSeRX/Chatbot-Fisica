import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Chatbot Física Aplicada", page_icon="⚡", layout="centered")
st.title("⚡ Asistente Virtual de Física Aplicada")
st.markdown("Hola. Soy tu tutor virtual. Pregúntame sobre **Electrostática, Electrodinámica, Magnetismo/CA o Fundamentos de Electrónica**.")

# Inicializar el historial del chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mostrar los mensajes anteriores
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Función que contiene toda la lógica de respuestas (El "Cerebro")
def obtener_respuesta(pregunta):
    p = pregunta.lower() # Convertir a minúsculas para facilitar la búsqueda

    # --- MÓDULO 1: ELECTROSTÁTICA ---
    if "carga" in p and "electrica" in p:
        return "La carga eléctrica es una propiedad fundamental de la materia. Fórmula: **Q = n * e**, donde 'n' es el número de electrones y 'e' es 1.602 x 10⁻¹⁹ C."
    elif "coulomb" in p:
        return "La Ley de Coulomb describe la fuerza entre dos cargas. Fórmula: **F = k * (|q1 * q2|) / r²**. k es 9x10⁹ N·m²/C². Si las cargas tienen el mismo signo se repelen, si son opuestas se atraen."
    elif "campo" in p and "electrico" in p:
        return "El campo eléctrico (E) es la fuerza por unidad de carga. Fórmula: **E = F / q**. Se mide en N/C o V/m. Las líneas de campo salen de las cargas positivas y entran a las negativas."
    elif "gauss" in p:
        return "La Ley de Gauss establece que el flujo eléctrico neto a través de una superficie cerrada es igual a la carga neta encerrada dividida por la permitividad del vacío. Fórmula: **Φ = Q_encerrada / ε₀**."
    elif "potencial" in p:
        return "El potencial eléctrico es la energía potencial por unidad de carga. Fórmula: **V = U / q**. Se mide en Voltios (V)."
    elif "capacitor" in p or "capacitancia" in p or "condensador" in p:
        return "Un capacitor almacena carga. Fórmula: **C = Q / V**. En paralelo se suman (Ct = C1+C2) y en serie se suman los inversos (1/Ct = 1/C1 + 1/C2)."

    # --- MÓDULO 2: ELECTRODINÁMICA ---
    elif "ohm" in p:
        return "La Ley de Ohm establece que el voltaje (V) es igual a la corriente (I) por la resistencia (R). Fórmula: **V = I * R**."
    elif "resistencia" in p and ("serie" in p or "paralelo" in p):
        return "En serie las resistencias se suman: **Req = R1 + R2**. En paralelo se suman los inversos: **1/Req = 1/R1 + 1/R2**."
    elif "potencia" in p:
        return "La potencia eléctrica es la energía consumida por unidad de tiempo. Fórmulas: **P = V * I**, **P = I² * R**, **P = V² / R**. Se mide en Watts (W)."
    elif "kirchhoff" in p:
        return "1ra Ley (Nodos): Suma de corrientes que entran = suma de las que salen. 2da Ley (Mallas): La suma algebraica de voltajes en una malla cerrada es cero."
    elif "rc" in p or "transitorio" in p:
        return "En un circuito RC, la constante de tiempo (τ) indica qué tan rápido se carga el capacitor. Fórmula: **τ = R * C**."

    # --- MÓDULO 3: MAGNETISMO Y CORRIENTE ALTERNA ---
    elif "magnetica" in p and "fuerza" in p:
        return "La fuerza magnética sobre una carga en movimiento se calcula como: **F = q * (v × B)**. Es perpendicular a la velocidad y al campo magnético."
    elif "biot" in p or "ampere" in p:
        return "Biot-Savart calcula el campo magnético de un segmento de corriente. Ampere relaciona el campo con la corriente que lo genera: **∮B·dl = μ₀ * I**."
    elif "faraday" in p or "lenz" in p or "induccion" in p:
        return "La Ley de Faraday dice que un campo magnético variable genera una fuerza electromotriz inducida (**ε = -dΦ/dt**). La Ley de Lenz indica que la corriente inducida se opone al cambio."
    elif "alterna" in p or "eficaz" in p or "rms" in p:
        return "En corriente alterna (CA), el valor eficaz (RMS) equivale al de una corriente continua. Para una onda senoidal: **V_rms = V_max / √2**."
    elif "impedancia" in p or "rlc" in p or "resonancia" in p:
        return "La impedancia (Z) es la oposición total al flujo de CA (combina R y X). En un circuito RLC, la resonancia ocurre cuando Xl = Xc, minimizando la impedancia."

    # --- MÓDULO 4: FUNDAMENTOS DE ELECTRÓNICA ---
    elif "semiconductor" in p or "dopaje" in p:
        return "Un semiconductor tiene conductividad intermedia. El tipo N tiene exceso de electrones (carga negativa) y el tipo P tiene exceso de huecos (carga positiva)."
    elif "diodo" in p and "zener" not in p:
        return "Un diodo permite el paso de corriente en un solo sentido (polarización directa) y lo bloquea en el otro (inversa). Su curva I-V muestra esta relación."
    elif "rectificador" in p or "filtro" in p:
        return "Un rectificador convierte CA en CC. El de media onda usa un diodo; el de onda completa usa un puente de diodos. El filtro capacitivo suaviza la señal."
    elif "zener" in p:
        return "El diodo Zener permite el flujo inverso cuando se alcanza su voltaje Zener. Se usa para regular el voltaje en circuitos."

    # --- RESPUESTA POR DEFECTO (Fallback) ---
    else:
        return "Lo siento, aún no tengo información sobre ese tema. Mi base de datos actual cubre: **Electrostática, Electrodinámica, Magnetismo/CA y Fundamentos de Electrónica**. ¿Podrías reformular tu pregunta usando términos del curso?"

# Entrada de texto del usuario
pregunta_usuario = st.chat_input("Escribe tu pregunta de Física aquí...")

if pregunta_usuario:
    # 1. Guardar y mostrar la pregunta del usuario
    st.session_state.mensajes.append({"role": "user", "content": pregunta_usuario})
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)

    # 2. Obtener la respuesta del bot usando la función
    respuesta_bot = obtener_respuesta(pregunta_usuario)
    
    # 3. Guardar y mostrar la respuesta del bot
    st.session_state.mensajes.append({"role": "assistant", "content": respuesta_bot})
    with st.chat_message("assistant"):
        st.markdown(respuesta_bot)
