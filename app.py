"""
VITRUVIO — Ficha de Evaluación Antropométrica
Inspirado en el Hombre de Vitruvio de Leonardo da Vinci
Fórmulas: Literatura ISAK / Durnin-Womersley / Rose y Gurfinkel / Harris-Benedict
"""

import math
import csv
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from fpdf import FPDF
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

# ─────────────────────────────────────────────
# LÓGICA / CÁLCULOS
# ─────────────────────────────────────────────

def calcular(datos: dict, config: dict = None) -> dict:
    """Recibe el dict con todos los inputs y devuelve dict con los calculados.
    config puede indicar qué variante de fórmula usar para cada grupo."""
    if config is None:
        config = {}
    res = {}
    try:
        edad   = float(datos["edad"])
        peso   = float(datos["peso"])
        talla  = float(datos["talla"])   # metros
        fcr    = float(datos["fcr"])
        sexo   = datos["sexo"]           # "Masculino" / "Femenino"

        # Pliegues
        bici   = float(datos["bicipital"])
        tri    = float(datos["tricipital"])
        sub    = float(datos["subescapular"])
        supil  = float(datos["suprailiaco"])
        abd    = float(datos["abdominal"])
        muslo  = float(datos["muslo"])
        panto  = float(datos["pantorrilla"])

        # Diámetros
        humeral = float(datos["humeral"])
        femoral = float(datos["femoral"])
        muneca  = float(datos["muneca"])

        # Perímetros
        p_cintura = float(datos["cintura"])
        p_cadera  = float(datos["cadera"])

        # Test Ruffier Dickson
        fc_post = float(datos.get("fc_post", 0) or 0)
        fc_rec  = float(datos.get("fc_rec", 0) or 0)

        # ── Frecuencia cardíaca máxima
        fcm_formula = config.get("fcm", "Fox — 220 − edad")
        if "Tanaka" in fcm_formula:
            res["fcm"] = round(208 - 0.7 * edad, 1)
        elif "Nes" in fcm_formula:
            res["fcm"] = round(211 - 0.64 * edad, 1)
        else:  # Fox
            res["fcm"] = round(220 - edad, 1)

        # ── Suma de pliegues
        suma_pli = bici + tri + sub + supil + abd + muslo + panto
        res["suma_pliegues"] = round(suma_pli, 2)

        # ── Densidad corporal
        dc_formula = config.get("densidad", "Durnin & Womersley (4 pliegues)")
        # Suma de 4 pliegues estándar D&W: bicipital + tricipital + subescapular + suprailiaco
        sum_dw = bici + tri + sub + supil
        if suma_pli > 0:
            if "Jackson" in dc_formula and "♂" in dc_formula:
                s = bici + abd + muslo  # pecho aprox. bicipital
                dc = 1.10938 - 0.0008267*s + 0.0000016*(s**2) - 0.0002574*edad
            elif "Jackson" in dc_formula and "♀" in dc_formula:
                s = tri + supil + muslo
                dc = 1.0994921 - 0.0009929*s + 0.0000023*(s**2) - 0.0001392*edad
            else:
                # Durnin & Womersley (1974) — 4 pliegues, coeficientes por sexo y edad
                if sum_dw > 0:
                    log_sum = math.log10(sum_dw)
                    if sexo == "Masculino":
                        if   edad < 20: c, k = 1.1620, 0.0630
                        elif edad < 30: c, k = 1.1631, 0.0632
                        elif edad < 40: c, k = 1.1422, 0.0544
                        elif edad < 50: c, k = 1.1620, 0.0700
                        else:           c, k = 1.1715, 0.0779
                    else:
                        if   edad < 20: c, k = 1.1549, 0.0678
                        elif edad < 30: c, k = 1.1599, 0.0717
                        elif edad < 40: c, k = 1.1423, 0.0632
                        elif edad < 50: c, k = 1.1333, 0.0612
                        else:           c, k = 1.1339, 0.0645
                    dc = c - k * log_sum
                else:
                    dc = 0
        else:
            dc = 0
        res["densidad_corporal"] = round(dc, 5)

        # ── Grasa corporal %
        grasa_formula = config.get("grasa_pct", "Siri (1956)")
        if dc > 0:
            if "Brozek" in grasa_formula:
                gc_pct = (4.57 / dc - 4.142) * 100
            else:  # Siri
                gc_pct = (4.95 / dc - 4.5) * 100
        else:
            gc_pct = 0
        res["grasa_pct"] = round(gc_pct, 2)

        # ── 4 componentes Rose & Gurfinkel
        # ── 4 componentes (Matiegka / Drinkwater-Ross)
        # Masa Grasa por Faulkner (1968):
        #   %Grasa = 5.783 + 0.153 × Σ(tri+sub+supil+abd)
        #   MG (kg) = peso × %Grasa / 100
        sum4 = tri + sub + supil + abd
        pct_grasa_faulkner = 5.783 + 0.153 * sum4
        masa_grasa = peso * pct_grasa_faulkner / 100

        # Masa Ósea (Rocha 1975 / Von Döbeln):
        #   MO (g) = 3.02 × (h² × femoral × muñeca × 400)^0.712
        #   MO (kg) = MO(g) / 1000        ← el Excel tenía este bug
        masa_osea = 3.02 * (talla**2 * femoral * muneca * 400) ** 0.712 / 1000

        # Masa Residual (Würch 1974) — sexo-dependiente
        if sexo == "Masculino":
            masa_residual = peso * 0.241   # 24.1 %
        else:
            masa_residual = peso * 0.209   # 20.9 %

        # Masa Muscular = Peso − (grasa + ósea + residual)
        masa_muscular = peso - (masa_grasa + masa_osea + masa_residual)

        res["masa_grasa"]    = round(masa_grasa, 2)
        res["masa_osea"]     = round(masa_osea, 2)
        res["masa_residual"] = round(masa_residual, 2)
        res["masa_muscular"] = round(masa_muscular, 2)
        res["masa_grasa_pct"]    = round(masa_grasa / peso * 100, 1) if peso > 0 else 0
        res["masa_osea_pct"]     = round(masa_osea / peso * 100, 1) if peso > 0 else 0
        res["masa_residual_pct"] = round(masa_residual / peso * 100, 1) if peso > 0 else 0
        res["masa_muscular_pct"] = round(masa_muscular / peso * 100, 1) if peso > 0 else 0

        # ── IMC
        res["imc"] = round(peso / talla**2, 2)

        # ── ICC
        if p_cadera > 0:
            res["icc"] = round(p_cintura / p_cadera, 4)
        else:
            res["icc"] = 0

        # ── Ruffier-Dickson (índice de recuperación cardiovascular)
        #   IRD = ((P1 + P2 + P3) − 200) / 10
        #   donde P1=FC reposo, P2=FC post-esfuerzo, P3=FC recuperación a 1′
        if fc_post > 0 and fc_rec > 0:
            rd = ((fcr + fc_post + fc_rec) - 200) / 10
            res["ruffier_dickson"] = round(rd, 2)
            if rd < 0:
                res["ruffier_clasif"] = "Excelente"
            elif rd < 5:
                res["ruffier_clasif"] = "Muy bueno"
            elif rd < 10:
                res["ruffier_clasif"] = "Bueno"
            elif rd < 15:
                res["ruffier_clasif"] = "Regular"
            else:
                res["ruffier_clasif"] = "Insuficiente"
        else:
            res["ruffier_dickson"] = None
            res["ruffier_clasif"] = None

        # ── TMB
        tmb_formula = config.get("tmb", "Harris-Benedict (1919)")
        talla_cm = talla * 100
        if "Mifflin" in tmb_formula:
            if sexo == "Masculino":
                tmb = 10*peso + 6.25*talla_cm - 5*edad + 5
            else:
                tmb = 10*peso + 6.25*talla_cm - 5*edad - 161
        elif "OMS" in tmb_formula or "FAO" in tmb_formula:
            if sexo == "Masculino":
                tmb = (15.3*peso + 679) if edad < 30 else (11.6*peso + 879)
            else:
                tmb = (14.7*peso + 496) if edad < 30 else (8.7*peso + 829)
        else:  # Harris-Benedict
            if sexo == "Masculino":
                tmb = 66 + (13.7 * peso) + (5 * talla_cm) - (6.8 * edad)
            else:
                tmb = 655 + (9.6 * peso) + (1.8 * talla_cm) - (4.7 * edad)
        res["tmb"] = round(tmb, 2)

        # ── Clasificaciones
        imc = res["imc"]
        if imc < 18.5:
            res["clasificacion_imc"] = "Bajo peso"
        elif imc < 25:
            res["clasificacion_imc"] = "Normal"
        elif imc < 30:
            res["clasificacion_imc"] = "Sobrepeso"
        elif imc < 35:
            res["clasificacion_imc"] = "Obesidad I"
        elif imc < 40:
            res["clasificacion_imc"] = "Obesidad II"
        else:
            res["clasificacion_imc"] = "Obesidad III"

        icc = res["icc"]
        if sexo == "Masculino":
            res["tipo_obesidad"] = "Androide" if icc >= 1.0 else ("Riesgo Androide" if icc >= 0.95 else "Ginoide")
        else:
            res["tipo_obesidad"] = "Androide" if icc >= 0.85 else ("Riesgo Androide" if icc >= 0.80 else "Ginoide")

        gc = res["grasa_pct"]
        if sexo == "Masculino":
            if gc < 6:
                res["clasificacion_grasa"] = "Muy bajo"
            elif gc < 14:
                res["clasificacion_grasa"] = "Atlético"
            elif gc < 18:
                res["clasificacion_grasa"] = "Óptimo"
            elif gc < 25:
                res["clasificacion_grasa"] = "Aceptable"
            else:
                res["clasificacion_grasa"] = "Exceso"
        else:
            if gc < 14:
                res["clasificacion_grasa"] = "Muy bajo"
            elif gc < 21:
                res["clasificacion_grasa"] = "Atlético"
            elif gc < 25:
                res["clasificacion_grasa"] = "Óptimo"
            elif gc < 32:
                res["clasificacion_grasa"] = "Aceptable"
            else:
                res["clasificacion_grasa"] = "Exceso"

    except Exception as e:
        res["_error"] = str(e)

    return res


# ─────────────────────────────────────────────
# EXPORTACIÓN CSV
# ─────────────────────────────────────────────

def exportar_csv(datos: dict, resultados: dict, filepath: str):
    todas = {**datos, **resultados}
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Campo", "Valor"])
        for k, v in todas.items():
            writer.writerow([k, v])


# ─────────────────────────────────────────────
# EXPORTACIÓN PDF
# ─────────────────────────────────────────────

def exportar_pdf(datos: dict, resultados: dict, filepath: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Título
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Ficha de Evaluación Antropométrica", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Formulas: ISAK / Durnin-Womersley / Rose y Gurfinkel — ver configuracion de formulas", ln=True, align="C")
    pdf.ln(4)

    def seccion(titulo):
        pdf.set_fill_color(30, 90, 160)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, f"  {titulo}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)

    def fila(label, value, fill=False):
        pdf.set_fill_color(235, 240, 255)
        pdf.cell(90, 6, f"  {label}", border=1, fill=fill)
        pdf.cell(100, 6, f"  {value}", border=1, fill=fill, ln=True)

    seccion("Datos Personales")
    fila("Nombre", datos.get("nombre", ""))
    fila("Ocupación", datos.get("ocupacion", ""))
    fila("Edad (años)", datos.get("edad", ""))
    fila("Sexo", datos.get("sexo", ""))
    fila("Peso (kg)", datos.get("peso", ""))
    fila("Talla (m)", datos.get("talla", ""))
    fila("FC Reposo (lpm)", datos.get("fcr", ""))
    fila("FC Máxima calc. (lpm)", resultados.get("fcm", ""))
    fila("PA (mmHg)", datos.get("pa", ""))
    pdf.ln(2)

    seccion("Pliegues Cutáneos (mm)")
    pliegues = ["bicipital","tricipital","subescapular","suprailiaco","abdominal","muslo","pantorrilla"]
    for p in pliegues:
        fila(p.capitalize(), datos.get(p, ""))
    fila("Suma de pliegues", resultados.get("suma_pliegues", ""))
    fila("Densidad Corporal", resultados.get("densidad_corporal", ""))
    fila("Grasa Corporal %", f"{resultados.get('grasa_pct','')} %  →  {resultados.get('clasificacion_grasa','')}")
    pdf.ln(2)

    seccion("Diámetros Óseos (cm)")
    fila("Húmeral", datos.get("humeral", ""))
    fila("Femoral", datos.get("femoral", ""))
    fila("Muñeca", datos.get("muneca", ""))
    pdf.ln(2)

    seccion("Composicion Corporal - 4 Componentes (Matiegka)")
    fila("Masa Grasa (kg)", f"{resultados.get('masa_grasa','')}  ({resultados.get('masa_grasa_pct','')} %)")
    fila("Masa Osea (kg)",  f"{resultados.get('masa_osea','')}  ({resultados.get('masa_osea_pct','')} %)")
    fila("Masa Muscular (kg)", f"{resultados.get('masa_muscular','')}  ({resultados.get('masa_muscular_pct','')} %)")
    fila("Masa Residual (kg)", f"{resultados.get('masa_residual','')}  ({resultados.get('masa_residual_pct','')} %)")
    pdf.ln(2)

    seccion("Índices")
    fila("IMC (kg/m²)", f"{resultados.get('imc','')}  →  {resultados.get('clasificacion_imc','')}")
    fila("ICC (cintura/cadera)", f"{resultados.get('icc','')}  →  {resultados.get('tipo_obesidad','')}")
    pdf.ln(2)

    seccion("Perímetros Corporales (cm)")
    perimetros = ["brazo_relajado","brazo_tension","antebrazo","torax","cintura","c_umbilical","cadera","muslo_p","pantorrilla_p"]
    labels_p   = ["Brazo relajado","Brazo en tensión","Antebrazo","Tórax","Cintura","C. Umbilical","Cadera","Muslo","Pantorrilla"]
    for k, l in zip(perimetros, labels_p):
        fila(l, datos.get(k, ""))
    pdf.ln(2)

    seccion("Metabolismo y Condicion Fisica")
    fila("TMB (kcal/dia)", resultados.get("tmb", ""))
    if resultados.get("ruffier_dickson") is not None:
        fila("Ruffier-Dickson", f"{resultados.get('ruffier_dickson','')}  ({resultados.get('ruffier_clasif','')})")
    fila("Factor de actividad", datos.get("factor_actividad", ""))
    pdf.ln(2)

    seccion("Biotipo")
    fila("Biotipo", datos.get("biotipo", ""))

    pdf.output(filepath)


# ─────────────────────────────────────────────
# CATÁLOGO DE FÓRMULAS
# ─────────────────────────────────────────────

FORMULA_OPTS = {
    "densidad": {
        "label": "Densidad Corporal",
        "default": "Durnin & Womersley (4 pliegues)",
        "options": {
            "Durnin & Womersley (4 pliegues)": {
                "ref": "Durnin & Womersley, 1974. Br J Nutrition 32:77-97",
                "desc": "Estándar internacional. Usa 4 pliegues (bicipital + tricipital + "
                        "subescapular + supra-iliaco) con coeficientes específicos por sexo "
                        "y grupo etario. Validada en >480 adultos. Es la más usada en ISAK.",
                "eq": "DC = c − k × log₁₀(Σ4pl)\n"
                      "(c, k varían por sexo y rango de edad)",
            },
            "Jackson & Pollock 3 pl. (♂)": {
                "ref": "Jackson & Pollock, 1978. Br J Nutrition 40:497",
                "desc": "Para varones. Utiliza pliegues de pecho, abdomen y muslo. "
                        "Práctica cuando no se pueden medir los 7 pliegues. "
                        "Nota: en esta app pecho se aproxima con bicipital.",
                "eq": "S = pecho + abdomen + muslo\n"
                      "DC = 1.10938 − 0.0008267×S + 0.0000016×S² − 0.0002574×edad",
            },
            "Jackson & Pollock 3 pl. (♀)": {
                "ref": "Jackson et al., 1980. Medicine and Science in Sports 12:175",
                "desc": "Para mujeres. Utiliza tríceps, supra-iliaco y muslo. "
                        "Alta correlación con hidrodensitometría en población femenina.",
                "eq": "S = tríceps + supra-iliaco + muslo\n"
                      "DC = 1.0994921 − 0.0009929×S + 0.0000023×S² − 0.0001392×edad",
            },
        },
    },
    "grasa_pct": {
        "label": "% Grasa Corporal",
        "default": "Siri (1956)",
        "options": {
            "Siri (1956)": {
                "ref": "Siri WE, 1956. Advances in Biological and Medical Physics 4:239",
                "desc": "La ecuación de conversión más utilizada en el mundo. "
                        "Asume densidad de grasa = 0.9 g/cm³ y masa magra = 1.1 g/cm³. "
                        "Recomendada para sujetos adultos con adiposidad normal.",
                "eq": "% Grasa = (4.95 / DC − 4.5) × 100",
            },
            "Brozek (1963)": {
                "ref": "Brozek J et al., 1963. Annals of the NY Academy of Sciences 110:113",
                "desc": "Alternativa más conservadora. Produce valores ligeramente menores "
                        "que Siri. Recomendada para personas con alta densidad ósea o "
                        "poblaciones con morfología distinta a caucásica.",
                "eq": "% Grasa = (4.57 / DC − 4.142) × 100",
            },
        },
    },
    "fcm": {
        "label": "Frecuencia Cardíaca Máxima",
        "default": "Fox — 220 − edad",
        "options": {
            "Fox — 220 − edad": {
                "ref": "Fox SM et al., 1971. Annals of Clinical Research 3:404",
                "desc": "Fórmula clásica y de uso universal. Ampliamente adoptada en "
                        "clínica y deporte. Sobreestima en personas mayores de 40 años. "
                        "Error estándar ≈ ±10-12 lpm.",
                "eq": "FCM = 220 − edad",
            },
            "Tanaka — 208 − 0.7×edad": {
                "ref": "Tanaka H et al., 2001. J Am Coll Cardiology 37(1):153-156",
                "desc": "Derivada de meta-análisis de 351 estudios (18,712 sujetos). "
                        "Más precisa que Fox en adultos ≥40 años. "
                        "Menor sobreestimación en personas sedentarias.",
                "eq": "FCM = 208 − 0.7 × edad",
            },
            "Nes — 211 − 0.64×edad": {
                "ref": "Nes BM et al., 2013. Scand J Medicine & Science in Sports 23:697",
                "desc": "Desarrollada en población noruega activa (n=3320). "
                        "Alta precisión en adultos jóvenes activos. "
                        "Error estándar ≈ ±10 lpm.",
                "eq": "FCM = 211 − 0.64 × edad",
            },
        },
    },
    "tmb": {
        "label": "Tasa Metabólica Basal (TMB)",
        "default": "Harris-Benedict (1919)",
        "options": {
            "Harris-Benedict (1919)": {
                "ref": "Harris JA & Benedict FG, 1919. Carnegie Institute of Washington",
                "desc": "Fórmula histórica, revisada por Roza y Shizgal (1984). "
                        "Válida para adultos sanos de peso normal. "
                        "Puede sobreestimar en personas con sobrepeso/obesidad.",
                "eq": "Hombre: 66 + 13.7×P + 5×T(cm) − 6.8×edad\n"
                      "Mujer:  655 + 9.6×P + 1.8×T(cm) − 4.7×edad",
            },
            "Mifflin-St Jeor (1990)": {
                "ref": "Mifflin MD et al., 1990. Am J Clinical Nutrition 51(2):241-247",
                "desc": "La más precisa para población actual según la AND (Academy of "
                        "Nutrition and Dietetics). Recomendada para personas con sobrepeso. "
                        "Error ≈ ±10% en la mayoría de adultos.",
                "eq": "Hombre: 10×P + 6.25×T(cm) − 5×edad + 5\n"
                      "Mujer:  10×P + 6.25×T(cm) − 5×edad − 161",
            },
            "OMS/FAO (1985)": {
                "ref": "WHO Technical Report Series 724, 1985. Geneva",
                "desc": "Basada en grupos etarios. Recomendada para estudios "
                        "epidemiológicos y salud pública internacional. "
                        "Solo requiere peso corporal.",
                "eq": "Hombre 18-30: 15.3×P + 679\nHombre 30-60: 11.6×P + 879\n"
                      "Mujer 18-30:  14.7×P + 496\nMujer 30-60:  8.7×P + 829",
            },
        },
    },
}


# ─────────────────────────────────────────────
# PALETA Y TEMA
# ─────────────────────────────────────────────

COLORS = {
    "bg":        "#0f1b2d",   # fondo oscuro azul noche
    "panel":     "#162236",   # paneles
    "card":      "#1e2f45",   # tarjetas
    "accent":    "#c9a84c",   # dorado Da Vinci
    "accent2":   "#e8c97a",   # dorado claro
    "text":      "#e8e0d0",   # pergamino
    "text_dim":  "#8a9bb0",   # texto apagado
    "green":     "#4caf8f",
    "orange":    "#e0943a",
    "red":       "#e05050",
    "blue":      "#4a90d9",
    "purple":    "#9b72cf",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─────────────────────────────────────────────
# GRÁFICOS
# ─────────────────────────────────────────────

def _mpl_style():
    plt.rcParams.update({
        "figure.facecolor": COLORS["panel"],
        "axes.facecolor":   COLORS["card"],
        "axes.edgecolor":   COLORS["accent"],
        "axes.labelcolor":  COLORS["text"],
        "xtick.color":      COLORS["text_dim"],
        "ytick.color":      COLORS["text_dim"],
        "text.color":       COLORS["text"],
        "grid.color":       "#2a3d55",
        "grid.linewidth":   0.6,
        "font.family":      "sans-serif",
    })


def build_chart_composicion(fig, res: dict):
    """Gráfico de dona — composición corporal 4 componentes."""
    fig.clear()
    _mpl_style()
    mg  = max(res.get("masa_grasa", 0), 0)
    mo  = max(res.get("masa_osea", 0), 0)
    mm  = max(res.get("masa_muscular", 0), 0)
    mr  = max(res.get("masa_residual", 0), 0)
    vals = [mg, mo, mm, mr]
    labels = ["Grasa", "Ósea", "Muscular", "Residual"]
    colors = [COLORS["orange"], COLORS["purple"], COLORS["blue"], COLORS["green"]]

    total = sum(vals)
    if total <= 0:
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center",
                color=COLORS["text_dim"], fontsize=11)
        ax.axis("off")
        return

    ax = fig.add_subplot(111)
    wedges, texts, autotexts = ax.pie(
        vals, labels=None, colors=colors,
        autopct="%1.1f%%", startangle=140,
        wedgeprops=dict(width=0.55, edgecolor=COLORS["panel"], linewidth=2),
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color(COLORS["bg"])
        at.set_fontweight("bold")

    ax.legend(
        wedges, [f"{l}\n{v:.1f} kg ({v/total*100:.1f}%)" for l, v in zip(labels, vals)],
        loc="lower center", bbox_to_anchor=(0.5, -0.22),
        ncol=2, fontsize=7.5,
        framealpha=0, labelcolor=COLORS["text"],
    )
    ax.set_title("Composición Corporal", color=COLORS["accent"],
                 fontsize=10, fontweight="bold", pad=8)


def build_chart_pliegues(fig, datos: dict):
    """Gráfico de barras horizontales — pliegues cutáneos."""
    fig.clear()
    _mpl_style()
    keys   = ["bicipital","tricipital","subescapular","suprailiaco","abdominal","muslo","pantorrilla"]
    labels = ["Bicipital","Tricipital","Subescap.","Sup. Iliaco","Abdominal","Muslo","Pantorrilla"]
    vals = []
    for k in keys:
        try:
            vals.append(float(datos.get(k, 0) or 0))
        except ValueError:
            vals.append(0)

    ax = fig.add_subplot(111)
    y = np.arange(len(labels))
    bars = ax.barh(y, vals, color=COLORS["blue"], edgecolor=COLORS["panel"],
                   height=0.6, alpha=0.85)
    # gradient color by value
    max_v = max(vals) if max(vals) > 0 else 1
    for bar, v in zip(bars, vals):
        ratio = v / max_v
        r = int(0x4a + ratio * (0xe0 - 0x4a))
        g = int(0x90 + ratio * (0x50 - 0x90))
        b = int(0xd9 + ratio * (0x50 - 0xd9))
        bar.set_color(f"#{r:02x}{g:02x}{b:02x}")
        ax.text(v + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}", va="center", fontsize=7.5, color=COLORS["text"])

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("mm", fontsize=8)
    ax.set_title("Pliegues Cutáneos", color=COLORS["accent"],
                 fontsize=10, fontweight="bold")
    ax.grid(axis="x", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=1.2)


def build_chart_imc(fig, res: dict):
    """Medidor tipo velocímetro para el IMC."""
    fig.clear()
    _mpl_style()
    imc = res.get("imc", 0) or 0

    ax = fig.add_subplot(111, aspect="equal")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.3, 1.4)
    ax.axis("off")

    # Arco de fondo por zonas
    zonas = [
        (10, 18.5, "#4a90d9", "Bajo"),
        (18.5, 25, "#4caf8f", "Normal"),
        (25, 30, "#e0943a", "Sobrepeso"),
        (30, 40, "#e05050", "Obesidad"),
    ]
    import matplotlib.patches as patches
    for z_min, z_max, color, lbl in zonas:
        theta1 = 180 - (z_min - 10) / 30 * 180
        theta2 = 180 - (z_max - 10) / 30 * 180
        arc = patches.Wedge((0, 0), 1.0, theta2, theta1,
                             width=0.3, color=color, alpha=0.85)
        ax.add_patch(arc)
        mid_theta = math.radians((theta1 + theta2) / 2)
        tx = 1.18 * math.cos(mid_theta)
        ty = 1.18 * math.sin(mid_theta)
        ax.text(tx, ty, lbl, ha="center", va="center",
                fontsize=6.5, color=COLORS["text"], fontweight="bold")

    # Aguja
    imc_clamp = max(10, min(40, imc))
    angle_deg = 180 - (imc_clamp - 10) / 30 * 180
    angle_rad = math.radians(angle_deg)
    ax.annotate("", xy=(0.72 * math.cos(angle_rad), 0.72 * math.sin(angle_rad)),
                xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=COLORS["accent2"],
                                lw=2.5, mutation_scale=14))
    circle = plt.Circle((0, 0), 0.07, color=COLORS["accent"], zorder=5)
    ax.add_patch(circle)

    ax.text(0, -0.18, f"IMC: {imc:.1f}", ha="center", va="center",
            fontsize=12, fontweight="bold", color=COLORS["accent2"])
    clasif = res.get("clasificacion_imc", "")
    ax.text(0, -0.3, clasif, ha="center", va="center",
            fontsize=9, color=COLORS["text_dim"])
    ax.set_title("Índice de Masa Corporal", color=COLORS["accent"],
                 fontsize=10, fontweight="bold", pad=4)


# ─────────────────────────────────────────────
# INTERFAZ GRÁFICA — VITRUVIO
# ─────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VITRUVIO — Evaluación Antropométrica")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg"])
        self.resizable(True, True)
        self._resultados = {}
        self._build_ui()

    # ── Layout ──────────────────────────────────
    def _build_ui(self):
        self._build_header()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(8, 0))
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Columna izquierda — formulario
        left = ctk.CTkFrame(body, fg_color=COLORS["panel"], corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.scroll = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                             scrollbar_button_color=COLORS["accent"])
        self.scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Columna derecha — tabs (resultados + gráficos)
        right = ctk.CTkFrame(body, fg_color=COLORS["panel"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._build_right_panel(right)

        self._build_inputs(self.scroll)
        self._build_buttons()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORS["card"], height=62, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Logo text
        logo = ctk.CTkFrame(hdr, fg_color="transparent")
        logo.pack(side="left", padx=18, pady=8)
        ctk.CTkLabel(logo, text="𝑽𝑰𝑻𝑹𝑼𝑽𝑰𝑶",
                     font=ctk.CTkFont(family="Georgia", size=22, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo,
                     text="Ficha de Evaluación Antropométrica  ·  inspirado en el Hombre de Vitruvio",
                     font=ctk.CTkFont(size=9),
                     text_color=COLORS["text_dim"]).pack(anchor="w")

        # Fecha
        import datetime
        ctk.CTkLabel(hdr,
                     text=datetime.date.today().strftime("%d / %m / %Y"),
                     font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_dim"]).pack(side="right", padx=18)

    # ── Panel derecho con tabs ──────────────────
    def _build_right_panel(self, parent):
        self._tabview = ctk.CTkTabview(parent,
                                       fg_color=COLORS["panel"],
                                       segmented_button_fg_color=COLORS["card"],
                                       segmented_button_selected_color=COLORS["accent"],
                                       segmented_button_selected_hover_color=COLORS["accent2"],
                                       segmented_button_unselected_color=COLORS["card"],
                                       segmented_button_unselected_hover_color="#2a3d55",
                                       text_color=COLORS["text"],
                                       border_width=0)
        self._tabview.pack(fill="both", expand=True, padx=6, pady=6)

        tab_res    = self._tabview.add("📊  Resultados")
        tab_comp   = self._tabview.add("🥧  Composición")
        tab_plieg  = self._tabview.add("📐  Pliegues")
        tab_imc    = self._tabview.add("⚖  IMC")
        tab_form   = self._tabview.add("📖  Fórmulas")

        self._build_results_tab(tab_res)
        self._build_chart_tab(tab_comp, "comp")
        self._build_chart_tab(tab_plieg, "plieg")
        self._build_chart_tab(tab_imc, "imc")
        self._build_formulas_tab(tab_form)

    def _build_results_tab(self, parent):
        self._res_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                                   scrollbar_button_color=COLORS["accent"])
        self._res_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self._res_labels = {}

        grupos = [
            ("Frecuencia Cardíaca", [
                ("FCM calculada", "fcm", "lpm"),
            ]),
            ("Pliegues & Grasa", [
                ("Suma pliegues", "suma_pliegues", "mm"),
                ("Densidad Corporal", "densidad_corporal", "g/cm³"),
                ("Grasa Corporal", "grasa_pct", "%"),
                ("Clasif. Grasa", "clasificacion_grasa", ""),
            ]),
            ("4 Componentes (Matiegka)", [
                ("Masa Grasa", "masa_grasa", "kg"),
                ("% Grasa (Faulkner)", "masa_grasa_pct", "%"),
                ("Masa Ósea", "masa_osea", "kg"),
                ("% Ósea", "masa_osea_pct", "%"),
                ("Masa Muscular", "masa_muscular", "kg"),
                ("% Muscular", "masa_muscular_pct", "%"),
                ("Masa Residual", "masa_residual", "kg"),
                ("% Residual", "masa_residual_pct", "%"),
            ]),
            ("Índices Corporales", [
                ("IMC", "imc", "kg/m²"),
                ("Clasif. IMC", "clasificacion_imc", ""),
                ("ICC", "icc", ""),
                ("Tipo Obesidad", "tipo_obesidad", ""),
            ]),
            ("Metabolismo y Condición", [
                ("TMB", "tmb", "kcal/día"),
                ("Ruffier-Dickson", "ruffier_dickson", ""),
                ("Clasif. Ruffier", "ruffier_clasif", ""),
            ]),
        ]
        for grupo_title, campos in grupos:
            # encabezado grupo
            gh = ctk.CTkFrame(self._res_scroll, fg_color=COLORS["card"], corner_radius=6)
            gh.pack(fill="x", padx=2, pady=(8, 1))
            ctk.CTkLabel(gh, text=grupo_title,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=COLORS["accent"]).pack(anchor="w", padx=10, pady=3)

            for lbl_text, key, unit in campos:
                row = ctk.CTkFrame(self._res_scroll,
                                   fg_color=COLORS["card"], corner_radius=4)
                row.pack(fill="x", padx=2, pady=1)
                ctk.CTkLabel(row, text=lbl_text,
                             font=ctk.CTkFont(size=10),
                             text_color=COLORS["text_dim"],
                             width=170, anchor="w").pack(side="left", padx=10, pady=4)
                val_lbl = ctk.CTkLabel(row, text="—",
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       text_color=COLORS["text"])
                val_lbl.pack(side="left")
                if unit:
                    ctk.CTkLabel(row, text=f" {unit}",
                                 font=ctk.CTkFont(size=9),
                                 text_color=COLORS["text_dim"]).pack(side="left")
                self._res_labels[key] = val_lbl

    def _build_formulas_tab(self, parent):
        """Pestaña para ver y cambiar las fórmulas usadas en cada cálculo."""
        intro = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=8)
        intro.pack(fill="x", padx=6, pady=(6, 4))
        ctk.CTkLabel(intro,
                     text="Selecciona la variante de fórmula para cada cálculo."
                          "  Los cambios se aplican al presionar  Calcular.",
                     font=ctk.CTkFont(size=9), text_color=COLORS["text_dim"],
                     wraplength=520, justify="left").pack(anchor="w", padx=10, pady=6)

        self._formula_vars = {}   # {group_key: StringVar}
        self._formula_desc_labels = {}  # {group_key: CTkLabel}
        self._formula_eq_labels   = {}  # {group_key: CTkLabel}

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                        scrollbar_button_color=COLORS["accent"])
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        for gkey, gdata in FORMULA_OPTS.items():
            # Card por grupo
            card = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=8)
            card.pack(fill="x", padx=4, pady=6)

            # Encabezado
            hdr = ctk.CTkFrame(card, fg_color=COLORS["accent"], corner_radius=6)
            hdr.pack(fill="x", padx=4, pady=(4, 0))
            ctk.CTkLabel(hdr, text=gdata["label"],
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COLORS["bg"]).pack(anchor="w", padx=10, pady=3)

            # Dropdown
            sel_row = ctk.CTkFrame(card, fg_color="transparent")
            sel_row.pack(fill="x", padx=8, pady=(6, 2))
            ctk.CTkLabel(sel_row, text="Método activo:",
                         font=ctk.CTkFont(size=10), text_color=COLORS["text_dim"],
                         width=110).pack(side="left")
            opts = list(gdata["options"].keys())
            var = tk.StringVar(value=gdata["default"])
            self._formula_vars[gkey] = var

            def _make_callback(k, v, gd):
                def _cb(choice):
                    info = gd["options"][choice]
                    self._formula_desc_labels[k].configure(
                        text=f"  {info['desc']}")
                    self._formula_eq_labels[k].configure(
                        text=f"  {info['eq']}")
                    ref_lbl = self._formula_ref_labels[k]
                    ref_lbl.configure(text=f"  Referencia: {info['ref']}")
                return _cb

            combo = ctk.CTkOptionMenu(
                sel_row, variable=var, values=opts, width=320,
                fg_color=COLORS["bg"],
                button_color=COLORS["accent"],
                button_hover_color=COLORS["accent2"],
                dropdown_fg_color=COLORS["card"],
                text_color=COLORS["text"],
                command=_make_callback(gkey, var, gdata),
            )
            combo.pack(side="left", padx=(6, 0))

            # Ecuación
            default_info = gdata["options"][gdata["default"]]
            eq_lbl = ctk.CTkLabel(card,
                                  text=f"  {default_info['eq']}",
                                  font=ctk.CTkFont(family="Courier", size=10),
                                  text_color=COLORS["accent2"],
                                  justify="left", anchor="w", wraplength=500)
            eq_lbl.pack(fill="x", padx=4, pady=(4, 0))
            self._formula_eq_labels[gkey] = eq_lbl

            # Descripción
            desc_lbl = ctk.CTkLabel(card,
                                    text=f"  {default_info['desc']}",
                                    font=ctk.CTkFont(size=9),
                                    text_color=COLORS["text"],
                                    justify="left", anchor="w", wraplength=500)
            desc_lbl.pack(fill="x", padx=4, pady=(2, 0))
            self._formula_desc_labels[gkey] = desc_lbl

            # Referencia
            ref_lbl = ctk.CTkLabel(card,
                                   text=f"  Referencia: {default_info['ref']}",
                                   font=ctk.CTkFont(size=8),
                                   text_color=COLORS["text_dim"],
                                   justify="left", anchor="w", wraplength=500)
            ref_lbl.pack(fill="x", padx=4, pady=(1, 6))
            if not hasattr(self, "_formula_ref_labels"):
                self._formula_ref_labels = {}
            self._formula_ref_labels[gkey] = ref_lbl

    def _build_chart_tab(self, parent, chart_id: str):
        fig = Figure(figsize=(5.5, 4.2), dpi=96)
        fig.patch.set_facecolor(COLORS["panel"])
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.get_tk_widget().configure(bg=COLORS["panel"])
        setattr(self, f"_fig_{chart_id}", fig)
        setattr(self, f"_canvas_{chart_id}", canvas)

    # ── Helpers formulario ──────────────────────
    def _section(self, parent, title):
        f = ctk.CTkFrame(parent, fg_color=COLORS["accent"], corner_radius=6)
        f.pack(fill="x", padx=2, pady=(10, 2))
        ctk.CTkLabel(f, text=title,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COLORS["bg"]).pack(anchor="w", padx=10, pady=4)

    def _row(self, parent, label, key, default="", width=130):
        frm = ctk.CTkFrame(parent, fg_color="transparent")
        frm.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(frm, text=label, width=185, anchor="w",
                     font=ctk.CTkFont(size=10),
                     text_color=COLORS["text"]).pack(side="left")
        var = tk.StringVar(value=str(default))
        entry = ctk.CTkEntry(frm, textvariable=var, width=width,
                             fg_color=COLORS["card"],
                             border_color=COLORS["accent"],
                             text_color=COLORS["text"])
        entry.pack(side="left", padx=(4, 0))
        self._vars[key] = var
        return var

    def _row_combo(self, parent, label, key, options, default=0):
        frm = ctk.CTkFrame(parent, fg_color="transparent")
        frm.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(frm, text=label, width=185, anchor="w",
                     font=ctk.CTkFont(size=10),
                     text_color=COLORS["text"]).pack(side="left")
        var = tk.StringVar(value=options[default])
        combo = ctk.CTkOptionMenu(frm, variable=var, values=options, width=155,
                                  fg_color=COLORS["card"],
                                  button_color=COLORS["accent"],
                                  button_hover_color=COLORS["accent2"],
                                  dropdown_fg_color=COLORS["card"],
                                  text_color=COLORS["text"])
        combo.pack(side="left", padx=(4, 0))
        self._vars[key] = var
        return var

    # ── Formulario de inputs ────────────────────
    def _build_inputs(self, parent):
        self._vars = {}

        self._section(parent, "Datos Personales")
        self._row(parent, "Nombre completo:", "nombre", "Andrés Osorio", width=190)
        self._row(parent, "Ocupación:", "ocupacion", "Trabajador/Estudiante", width=190)
        self._row(parent, "Edad (años):", "edad", 33)
        self._row_combo(parent, "Sexo:", "sexo", ["Masculino", "Femenino"])
        self._row(parent, "Peso (kg):", "peso", 79)
        self._row(parent, "Talla (m):", "talla", 1.69)
        self._row(parent, "FC Reposo (lpm):", "fcr", 65)
        self._row(parent, "PA (mmHg):", "pa", "110/60", width=100)
        self._row(parent, "Factor de actividad:", "factor_actividad", "1.78 Moderada", width=160)
        self._row_combo(parent, "Biotipo:", "biotipo",
                        ["Endomorfo", "Mesomorfo", "Ectomorfo", "Mixto"])

        self._section(parent, "Pliegues Cutáneos (mm)")
        for lbl, key, val in [
            ("Bicipital:", "bicipital", 4), ("Tricipital:", "tricipital", 9),
            ("Subescapular:", "subescapular", 17), ("Supra Iliaco:", "suprailiaco", 22),
            ("Abdominal:", "abdominal", 21), ("Muslo:", "muslo", 13),
            ("Pantorrilla:", "pantorrilla", 6),
        ]:
            self._row(parent, lbl, key, val)

        self._section(parent, "Diámetros Óseos (cm)")
        for lbl, key, val in [
            ("Húmeral:", "humeral", 6.9), ("Femoral:", "femoral", 9.3),
            ("Muñeca:", "muneca", 6.5),
        ]:
            self._row(parent, lbl, key, val)

        self._section(parent, "Perímetros Corporales (cm)")
        for lbl, key, val in [
            ("Brazo relajado:", "brazo_relajado", 32.1), ("Brazo en tensión:", "brazo_tension", 34.4),
            ("Antebrazo:", "antebrazo", 24.3), ("Tórax:", "torax", 98.3),
            ("Cintura:", "cintura", 91.4), ("C. Umbilical:", "c_umbilical", 93.1),
            ("Cadera:", "cadera", 103), ("Muslo:", "muslo_p", 50.1),
            ("Pantorrilla:", "pantorrilla_p", 36),
        ]:
            self._row(parent, lbl, key, val)

        self._section(parent, "Test Ruffier-Dickson (opcional)")
        ctk.CTkLabel(parent,
                     text="  Dejar en 0 si no se realiza el test",
                     font=ctk.CTkFont(size=9), text_color=COLORS["text_dim"]).pack(anchor="w", padx=6)
        self._row(parent, "FC post-esfuerzo (lpm):", "fc_post", 0)
        self._row(parent, "FC recuperación (lpm):", "fc_rec", 0)

    # ── Botonera inferior ───────────────────────
    def _build_buttons(self):
        bar = ctk.CTkFrame(self, fg_color=COLORS["card"], height=56, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        btn_cfg = dict(height=36, font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8)
        ctk.CTkButton(bar, text="  Calcular", command=self._calcular,
                      width=160, fg_color=COLORS["accent"],
                      hover_color=COLORS["accent2"],
                      text_color=COLORS["bg"], **btn_cfg).pack(side="left", padx=14, pady=10)
        ctk.CTkButton(bar, text="  Exportar CSV", command=self._export_csv,
                      width=150, fg_color="#2a5c38",
                      hover_color=COLORS["green"], **btn_cfg).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(bar, text="  Exportar PDF", command=self._export_pdf,
                      width=150, fg_color="#5c1a1a",
                      hover_color=COLORS["red"], **btn_cfg).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(bar, text="  Limpiar", command=self._limpiar,
                      width=120, fg_color="#3a2a1a",
                      hover_color="#6d4c41", **btn_cfg).pack(side="left", padx=4, pady=10)

        # crédito
        ctk.CTkLabel(bar,
                     text="VITRUVIO  ·  ISAK · Durnin-Womersley · Rose & Gurfinkel · Harris-Benedict",
                     font=ctk.CTkFont(size=8), text_color=COLORS["text_dim"]).pack(side="right", padx=14)

    # ── Acciones ────────────────────────────────
    def _get_datos(self) -> dict:
        return {k: v.get() for k, v in self._vars.items()}

    def _get_config(self) -> dict:
        return {k: v.get() for k, v in self._formula_vars.items()}

    def _calcular(self):
        datos = self._get_datos()
        res = calcular(datos, self._get_config())
        if "_error" in res:
            messagebox.showerror("Error en cálculo",
                                 f"Verifica que todos los campos numéricos sean válidos.\n\nDetalle: {res['_error']}")
            return
        self._resultados = res
        self._update_results(res)
        self._update_charts(datos, res)

    def _update_results(self, res: dict):
        clasif_colors = {
            "Normal": COLORS["green"], "Bajo peso": COLORS["blue"],
            "Sobrepeso": COLORS["orange"], "Obesidad I": COLORS["red"],
            "Obesidad II": COLORS["red"], "Obesidad III": COLORS["red"],
            "Atlético": COLORS["green"], "Óptimo": COLORS["green"],
            "Aceptable": COLORS["orange"], "Exceso": COLORS["red"],
            "Muy bajo": COLORS["blue"],
        }
        for key, lbl in self._res_labels.items():
            val = res.get(key)
            if val is None:
                lbl.configure(text="N/D", text_color=COLORS["text_dim"])
            else:
                text = str(val)
                color = clasif_colors.get(str(val), COLORS["text"])
                lbl.configure(text=text, text_color=color)

    def _update_charts(self, datos: dict, res: dict):
        build_chart_composicion(self._fig_comp, res)
        self._canvas_comp.draw()

        build_chart_pliegues(self._fig_plieg, datos)
        self._canvas_plieg.draw()

        build_chart_imc(self._fig_imc, res)
        self._canvas_imc.draw()

    def _export_csv(self):
        if not self._resultados:
            self._calcular()
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="vitruvio_ficha.csv",
            title="Guardar CSV")
        if not path:
            return
        exportar_csv(self._get_datos(), self._resultados, path)
        messagebox.showinfo("VITRUVIO", f"CSV guardado en:\n{path}")

    def _export_pdf(self):
        if not self._resultados:
            self._calcular()
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="vitruvio_ficha.pdf",
            title="Guardar PDF")
        if not path:
            return
        exportar_pdf(self._get_datos(), self._resultados, path)
        messagebox.showinfo("VITRUVIO", f"PDF guardado en:\n{path}")

    def _limpiar(self):
        for k, v in self._vars.items():
            v.set("0" if k in ("fc_post", "fc_rec") else "")
        for lbl in self._res_labels.values():
            lbl.configure(text="—", text_color=COLORS["text"])
        self._resultados = {}
        # limpiar gráficos
        for chart_id in ("comp", "plieg", "imc"):
            fig = getattr(self, f"_fig_{chart_id}")
            fig.clear()
            ax = fig.add_subplot(111)
            ax.set_facecolor(COLORS["card"])
            ax.text(0.5, 0.5, "Ingresa datos y presiona Calcular",
                    ha="center", va="center",
                    color=COLORS["text_dim"], fontsize=9)
            ax.axis("off")
            getattr(self, f"_canvas_{chart_id}").draw()


if __name__ == "__main__":
    app = App()
    app.mainloop()
