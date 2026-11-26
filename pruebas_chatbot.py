# ============================================================
# PRUEBAS AUTOMÁTICAS DEL CHATBOT DE FÍSICA
# ============================================================
# Comprueba que el chatbot:
#   1) Calcula bien cada ejercicio (comparado con resultados resueltos a mano).
#   2) Lee bien los números y las unidades.
#   3) Rechaza datos físicamente imposibles.
#   4) Dibuja todas las gráficas sin errores.
#   5) Entiende preguntas nuevas con la IA (examen con frases que NO usó al entrenar).
#
# Cómo ejecutarlo (en la terminal de Codespaces):
#     python pruebas_chatbot.py
# ============================================================

import sys
import types
import contextlib
import runpy
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")  # dibuja las gráficas sin abrir ventanas

ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Chatbot_Fisica.py")


# ---------- Simulador de Streamlit (para probar el chatbot sin abrir la página) ----------
class EstadoSesion(dict):
    __getattr__ = dict.__getitem__

    def __setattr__(self, k, v):
        self[k] = v


class Simulador:
    def __init__(self):
        self.estado = EstadoSesion()
        self.figuras = []
        self.entrada = None
        st = types.ModuleType("streamlit")
        st.session_state = self.estado
        for nombre in ("set_page_config", "title", "markdown"):
            setattr(st, nombre, lambda *a, **k: None)
        st.chat_message = lambda rol: contextlib.nullcontext()
        st.chat_input = lambda *a, **k: self.entrada
        st.pyplot = lambda fig: self.figuras.append(fig)
        st.cache_resource = lambda f: f
        sys.modules["streamlit"] = st
        self.funciones = runpy.run_path(ARCHIVO)

    def escribir(self, texto):
        """Envía un mensaje al chatbot y devuelve su respuesta."""
        self.entrada = texto
        runpy.run_path(ARCHIVO)
        self.entrada = None
        return self.estado["mensajes"][-1]["content"]

    def conversar(self, mensajes):
        respuesta = ""
        for m in mensajes:
            respuesta = self.escribir(m)
        return respuesta


# ---------- Utilidades del reporte ----------
resultados = {"ok": 0, "fallo": 0}


def comprobar(nombre, condicion, detalle=""):
    if condicion:
        resultados["ok"] += 1
        print(f"  ✅ {nombre}")
    else:
        resultados["fallo"] += 1
        print(f"  ❌ {nombre}  {detalle}")


def titulo(t):
    print(f"\n=== {t} ===")


sim = Simulador()
f = sim.funciones

# ============================================================
# 1) CÁLCULOS (resultados verificados a mano)
# ============================================================
titulo("1) Cálculos de los ejercicios")
CASOS = [
    # (nombre, mensajes, textos que deben aparecer en la respuesta final)
    ("Coulomb: 2µC y -3µC a 5 cm -> 21.6 N, atracción",
     ["resuelve un ejercicio de coulomb", "2 micro", "-3 micro", "5 cm"], ["21.6 N", "atracción"]),
    ("Ohm: I=2 A, R=10 Ω -> V = 20 V",
     ["resuelve un ejercicio de ohm", "voltaje", "2", "10"], ["V = 20 V"]),
    ("Ohm: V=12 V, R=4 Ω -> I = 3 A",
     ["resuelve un ejercicio de ohm", "corriente", "12", "4"], ["I = 3 A"]),
    ("Ohm: V=9 V, I=0.5 A -> R = 18 Ω",
     ["resuelve un ejercicio de ohm", "resistencia", "9", "0.5"], ["R = 18 Ω"]),
    ("Potencia: 220 V y 0.5 A -> 110 W",
     ["resuelve un ejercicio de potencia", "220", "0.5"], ["110 W"]),
    ("Capacitor: 10 µF a 12 V -> 7.2×10⁻⁴ J",
     ["resuelve un ejercicio de capacitor", "10 micro", "12"], ["7.20 × 10^-4"]),
    ("Diodo: 5 V y 1 kΩ -> 4.3 mA",
     ["resuelve un ejercicio de diodo", "5", "1 kΩ"], ["4.3 mA"]),
    ("Diodo: 0.5 V -> no conduce",
     ["resuelve un ejercicio de diodo", "0.5", "100"], ["NO conduce"]),
    ("Campo eléctrico: 0.02 N y 4 µC -> 5000 N/C",
     ["resuelve un ejercicio de campo", "0.02", "4x10^-6"], ["5000 N/C"]),
    ("Carga: 5×10¹⁸ electrones -> 0.801 C",
     ["resuelve un ejercicio de carga", "5e18"], ["0.801 C"]),
    ("Resistencias: 4.7 kΩ y 2200 Ω -> serie 6900, paralelo 1499",
     ["resuelve un ejercicio de resistencias", "4.7 kΩ", "2200"], ["6900 Ω", "1499 Ω"]),
    ("Fuerza magnética: protón a 2×10⁶ m/s, 0.5 T, 90° -> 1.6×10⁻¹³ N",
     ["resuelve un ejercicio de fuerza magnetica", "1.6e-19", "2e6", "0.5", "90"], ["1.60 × 10^-13 N"]),
    ("Fuerza magnética: v paralela a B (0°) -> F = 0",
     ["resuelve un ejercicio de fuerza magnetica", "2 micro", "1000", "0.3", "0"], ["F = 0 N", "paralela"]),
    ("Campo magnético: 10 A a 5 cm -> 4×10⁻⁵ T",
     ["resuelve un ejercicio de campo magnetico", "10", "5 cm"], ["4.00 × 10^-5 T", "40 μT"]),
    ("Faraday: N=100, A=200 cm², 0.1→0.5 T en 50 ms -> ε = -16 V",
     ["resuelve un ejercicio de faraday", "100", "200 cm²", "0.1", "0.5", "50 ms"], ["ε = -16 V", "aumenta"]),
    ("Corriente alterna: 311 V pico, 100 Ω, 60 Hz -> 219.9 V rms, 483.6 W",
     ["resuelve un ejercicio de corriente alterna", "311", "100", "60"], ["219.9 V", "483.6 W", "377 rad/s"]),
    ("RLC: 10 Ω, 50 mH, 10 µF, 60 Hz, 120 V -> Z = 246.6 Ω, f₀ = 225.1 Hz",
     ["resuelve un ejercicio de rlc", "10", "50 mH", "10 µF", "60", "120"],
     ["246.6 Ω", "225.1 Hz", "0.4866 A", "capacitivo"]),
    ("RLC en resonancia: L=0.1 H, C=10 µF a 159.2 Hz -> resistivo",
     ["resuelve un ejercicio de rlc", "10", "0.1", "10 micro", "159.2", "50"], ["resonancia", "Z = √"]),
    ("Potencial: 2 µC a 30 cm -> 6×10⁴ V",
     ["resuelve un ejercicio de potencial", "2 micro", "30 cm"], ["6.00 × 10^4 V", "positivo"]),
    ("Potencial: carga negativa -> potencial negativo",
     ["resuelve un ejercicio de potencial", "-5 nC", "10 cm"], ["-450 V", "negativo"]),
    ("Kirchhoff: E1=12 V, E2=6 V, R1=2, R2=3, R3=6 -> I1=2 A, I2=-0.667 A, I3=1.333 A",
     ["resuelve un ejercicio de kirchhoff", "12", "6", "2", "3", "6"],
     ["I1 = 2 A", "I2 = -0.6667 A", "I3 = 1.333 A", "V_A = **8 V", "se está **cargando**"]),
    ("Kirchhoff: fuentes iguales -> corrientes simétricas",
     ["resuelve un ejercicio de mallas", "10", "10", "5", "5", "5"], ["I1 = 0.6667 A", "I2 = 0.6667 A", "I3 = 1.333 A"]),
    ("Circuito RC: 10 kΩ, 100 µF, 12 V, t=1 s -> τ=1 s, Vc=7.585 V (63.2%)",
     ["resuelve un ejercicio de circuito rc", "10 kΩ", "100 µF", "12", "1"],
     ["τ = R·C", "**1 s**", "7.585 V", "63.2%", "4.41"]),
    ("Zener: Vs=12 V, Rs=220 Ω, Vz=5.1 V, RL=1 kΩ -> Iz=26.3 mA, Pz=0.134 W",
     ["resuelve un ejercicio de zener", "12", "220", "5.1", "1 kΩ"],
     ["regula", "0.03136 A", "5.10 × 10^-3 A", "0.02626 A", "0.1339 W"]),
    ("Zener que no regula: Vs=12, Rs=1k, Vz=9.1, RL=1k -> 6 V sin regular",
     ["resuelve un ejercicio de diodo zener", "12", "1k ohm", "9.1", "1000"], ["NO regula", "6 V"]),
    ("RLC inductivo: alta frecuencia",
     ["resuelve un ejercicio de rlc", "10", "0.1", "10 micro", "1000", "50"], ["inductivo"]),
]
for nombre, mensajes, esperados in CASOS:
    r = sim.conversar(mensajes)
    faltan = [e for e in esperados if e not in r]
    comprobar(nombre, not faltan, f"(no aparece: {faltan})")

# ============================================================
# 2) LECTURA DE NÚMEROS Y UNIDADES
# ============================================================
titulo("2) Lectura de números y unidades")
convertir = f["convertir_unidades"]
UNIDADES = [
    ("2 micro", 2e-6), ("2 µC", 2e-6), ("2e-6", 2e-6), ("2x10^-6", 2e-6), ("2×10⁻⁶", 2e-6),
    ("5 cm", 0.05), ("3 mm", 0.003), ("5 metros", 5), ("4,7 kΩ", 4700), ("10 nC", 1e-8),
    ("50 mH", 0.05), ("200 mT", 0.2), ("50 ms", 0.05), ("60 Hz", 60), ("2 kHz", 2000),
    ("5 MHz", 5e6), ("1k ohm", 1000), ("4.7k", 4700), ("2.2 K", 2200), ("3 M", 3e6), ("5 m", 5), ("200 cm²", 0.02), ("12 voltios", 12), ("-3 micro", -3e-6), ("abc", None),
]
for texto, esperado in UNIDADES:
    valor = convertir(texto)
    ok = (valor is None and esperado is None) or (
        valor is not None and esperado is not None and np.isclose(valor, esperado, rtol=1e-9))
    comprobar(f"'{texto}' -> {esperado}", ok, f"(leyó {valor})")

# ============================================================
# 3) VALIDACIÓN DE DATOS IMPOSIBLES
# ============================================================
titulo("3) Rechazo de datos imposibles o sospechosos")
VALIDACIONES = [
    ("Distancia 0 en Coulomb",
     ["resuelve un ejercicio de coulomb", "2 micro", "3 micro", "0"], "Error físico"),
    ("Velocidad mayor que la de la luz",
     ["resuelve un ejercicio de fuerza magnetica", "1.6e-19", "4e8"], "velocidad de la luz"),
    ("División entre 0 en Ohm",
     ["resuelve un ejercicio de ohm", "corriente", "12", "0"], "No se puede dividir entre 0"),
    ("Resistencia 0 en RLC",
     ["resuelve un ejercicio de rlc", "0"], "mayor a 0"),
    ("Tiempo 0 en Faraday",
     ["resuelve un ejercicio de faraday", "100", "0.02", "0.1", "0.5", "0"], "mayor a 0"),
    ("Texto en vez de número",
     ["resuelve un ejercicio de campo magnetico", "diez"], "No detecté un número"),
    ("Carga enorme (posible error de unidades)",
     ["resuelve un ejercicio de coulomb", "2", "3", "1"], "Revisa tus datos"),
]
for nombre, mensajes, esperado in VALIDACIONES:
    r = sim.conversar(mensajes)
    comprobar(nombre, esperado in r, f"(respondió: {r[:80]!r})")
    sim.escribir("cancelar")

# ============================================================
# 4) GRÁFICAS
# ============================================================
titulo("4) Gráficas")
GRAFICAS = ["diodo", "carga_capacitor", "descarga_capacitor", "potencial", "ohm", "resonancia",
            "fuerza_magnetica", "campo_magnetico", "faraday", "alterna"]
for tipo in GRAFICAS:
    try:
        fig = f["generar_grafica"](tipo)
        datos_ok = all(np.all(np.isfinite(linea.get_ydata()))
                       for ax in fig.axes for linea in ax.get_lines() if len(linea.get_ydata()) > 1)
        comprobar(f"Gráfica '{tipo}' se dibuja con valores válidos", datos_ok)
    except Exception as e:
        comprobar(f"Gráfica '{tipo}'", False, f"(error: {e})")

# La gráfica debe usar los datos del último ejercicio
sim.conversar(["resuelve un ejercicio de rlc", "10", "50 mH", "10 µF", "60", "120"])
r = sim.escribir("muéstrame la gráfica de resonancia")
titulo_graf = sim.figuras[-1].axes[0].get_title()
comprobar("La gráfica de resonancia usa el Q del ejercicio (7.07)", "7.07" in titulo_graf, f"({titulo_graf})")
comprobar("La gráfica avisa que usa tus datos", "tu último ejercicio" in r)

sim.conversar(["resuelve un ejercicio de circuito rc", "10 kΩ", "100 µF", "12", "1"])
sim.escribir("muéstrame la gráfica de carga del capacitor")
eje_x = sim.figuras[-1].axes[0].get_xlabel()
comprobar("La gráfica RC usa tus datos (tiempo real en segundos)", "(s)" in eje_x, f"({eje_x})")

sim2 = Simulador()
r = sim2.escribir("muéstrame la gráfica de faraday")
comprobar("Sin ejercicio previo, avisa que usa valores de ejemplo", "valores de ejemplo" in r)

# Física de las gráficas
fig = f["generar_grafica"]("diodo")
V, I = fig.axes[0].get_lines()[0].get_data()
I_07 = np.interp(0.7, V, I)
comprobar("Diodo: corriente realista a 0.7 V (entre 0.1 y 100 mA)", 0.1 < I_07 < 100, f"({I_07:.3g} mA)")
fig = f["generar_grafica"]("resonancia")
x, I_rel = fig.axes[0].get_lines()[0].get_data()
comprobar("Resonancia: la corriente es máxima en f = f₀", abs(x[np.argmax(I_rel)] - 1) < 0.02)

# ============================================================
# 5) INTELIGENCIA ARTIFICIAL: EXAMEN CON PREGUNTAS NUEVAS
# ============================================================
titulo("5) IA: examen con preguntas que NO usó al entrenar")
EXAMEN = [
    ("cuantos electrones le faltan a un cuerpo con carga positiva", "carga"),
    ("valor de la carga de un electron en coulombs", "carga"),
    ("se frota una regla y atrae papelitos", "carga"),
    ("que fuerza hay entre dos cargas de 1 microcoulomb a un metro", "coulomb"),
    ("por que dos cargas negativas se alejan", "coulomb"),
    ("fuerza electrica si la distancia se reduce a la mitad", "coulomb"),
    ("intensidad electrica en un punto cercano a una carga", "campo"),
    ("hacia donde apuntan las lineas de campo de una carga negativa", "campo"),
    ("cuanto campo electrico hay entre dos placas", "campo"),
    ("flujo que sale de un cubo con una carga adentro", "gauss"),
    ("usar una superficie esferica imaginaria", "gauss"),
    ("campo de un cascaron esferico", "gauss"),
    ("energia necesaria para mover un electron entre dos puntos", "potencial"),
    ("cuantos voltios hay a 10 cm de una carga", "potencial"),
    ("que son las lineas equipotenciales", "potencial"),
    ("cuanta carga guarda un condensador de 47 microfaradios", "capacitor"),
    ("para que sirve un capacitor", "capacitor"),
    ("energia de un capacitor de un flash", "capacitor"),
    ("que corriente pasa por un foco de 240 ohmios en 120 voltios", "ohm"),
    ("si duplico la resistencia que pasa con la corriente", "ohm"),
    ("cuanto voltaje cae en un resistor", "ohm"),
    ("como conecto resistencias para que la total sea menor", "resistencia"),
    ("tres resistores iguales en paralelo", "resistencia"),
    ("resistencia total de una serie de focos", "resistencia"),
    ("cuanto consume una refrigeradora en watts", "potencia"),
    ("energia por segundo de un motor", "potencia"),
    ("cuanto calor disipa un resistor", "potencia"),
    ("como resuelvo un circuito con dos baterias", "kirchhoff"),
    ("la corriente que entra a un nodo es igual a la que sale", "kirchhoff"),
    ("ecuaciones de las mallas del circuito", "kirchhoff"),
    ("en cuanto tiempo se descarga un capacitor por una resistencia", "circuito rc"),
    ("que significa la constante tau", "circuito rc"),
    ("curva de carga de un condensador", "circuito rc"),
    ("por que un iman desvia un haz de electrones", "fuerza magnetica"),
    ("radio de la trayectoria de un proton en un campo", "fuerza magnetica"),
    ("fuerza sobre un cable con corriente dentro de un iman", "fuerza magnetica"),
    ("que tan fuerte es el campo cerca de un cable", "campo magnetico"),
    ("campo en el interior de un solenoide", "campo magnetico"),
    ("por que se mueve la brujula cerca de un cable", "campo magnetico"),
    ("por que se enciende un foco al mover un iman en una bobina", "faraday"),
    ("como funciona un transformador", "faraday"),
    ("voltaje inducido al cambiar el flujo", "faraday"),
    ("cual es el voltaje maximo si en casa hay 220 voltios", "alterna"),
    ("diferencia entre valor pico y eficaz", "alterna"),
    ("cuantas veces cambia de sentido la corriente por segundo", "alterna"),
    ("a que frecuencia entra en resonancia un circuito", "rlc"),
    ("como se calcula la impedancia", "rlc"),
    ("bobina y condensador en serie con una fuente alterna", "rlc"),
    ("que es un material tipo p", "semiconductor"),
    ("por que se dopa el silicio", "semiconductor"),
    ("que son los portadores de carga", "semiconductor"),
    ("por que un led solo prende en un sentido", "diodo"),
    ("cuanto voltaje cae en un diodo de silicio", "diodo"),
    ("como convertir corriente alterna en continua", "diodo"),
    ("como mantener 5 voltios fijos en un circuito", "zener"),
    ("diodo que funciona en ruptura", "zener"),
    ("para que sirve el zener", "zener"),
]
alta, media = f["UMBRAL_RESPONDER"], f["UMBRAL_PREGUNTAR"]
aciertos = responde_bien = responde_mal = pregunta_ok = pregunta_mal = no_entiende = 0
for frase, esperado in EXAMEN:
    top = f["predecir_temas"](frase, 3)
    tema, conf = top[0]
    aciertos += tema == esperado
    if conf >= alta:
        if tema == esperado:
            responde_bien += 1
        else:
            responde_mal += 1
            print(f"  ⚠️ Respondió mal: {frase!r} -> {tema} ({conf:.0%}), esperado {esperado}")
    elif conf >= media:
        if esperado in [t for t, c in top if c >= 0.08][:3]:
            pregunta_ok += 1
        else:
            pregunta_mal += 1
    else:
        no_entiende += 1

total = len(EXAMEN)
precision_cv, n_frases, n_temas = f["evaluar_modelo"]()
print(f"  Modelo: {n_frases} frases de entrenamiento, {n_temas} temas")
print(f"  Precisión por validación cruzada (5 particiones): {precision_cv:.0%}")
print(f"  Examen ({total} preguntas nuevas) – primer tema acertado: {aciertos}/{total} = {aciertos / total:.0%}")
print(f"  Comportamiento final del chatbot:")
print(f"     Responde y acierta ............ {responde_bien}")
print(f"     Duda y ofrece la opción correcta {pregunta_ok}")
print(f"     Duda sin la opción correcta .... {pregunta_mal}")
print(f"     Admite que no entendió ......... {no_entiende}")
print(f"     Responde con un tema equivocado  {responde_mal}")
util = (responde_bien + pregunta_ok) / total
comprobar(f"La IA ayuda correctamente en al menos el 85% de las preguntas ({util:.0%})", util >= 0.85)
comprobar(f"La IA responde equivocada en menos del 10% ({responde_mal / total:.0%})", responde_mal / total < 0.10)

# Preguntas fuera de tema (tampoco están en el entrenamiento): debe admitir que no sabe
titulo("6) IA: preguntas que no son de física")
FUERA_DE_TEMA = ["receta de ceviche", "quien gano el partido de ayer", "cuentame un chiste", "que hora es",
                 "cual es la capital de francia", "como cocinar arroz", "hazme la tarea de historia",
                 "recomiendame una pelicula", "dame consejos de amor", "cuanto cuesta un celular"]
for frase in FUERA_DE_TEMA:
    r = Simulador().escribir(frase)
    comprobar(f"No inventa respuesta: '{frase}'", "no entendí" in r, f"({r[:60]!r})")

# ============================================================
# RESUMEN
# ============================================================
total_pruebas = resultados["ok"] + resultados["fallo"]
print(f"\n{'=' * 50}")
print(f"RESULTADO: {resultados['ok']}/{total_pruebas} pruebas superadas")
print("✅ Todo funciona correctamente." if resultados["fallo"] == 0 else f"❌ Hay {resultados['fallo']} pruebas con fallas.")
sys.exit(0 if resultados["fallo"] == 0 else 1)
