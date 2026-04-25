# VITRUVIO — Ficha de Evaluación Antropométrica

> Aplicación de escritorio para Windows, inspirada en el **Hombre de Vitruvio** de Leonardo da Vinci.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-darkblue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Características

- Formulario completo de evaluación antropométrica (datos personales, pliegues, diámetros, perímetros)
- Cálculos automáticos:
  - Frecuencia Cardíaca Máxima
  - Densidad Corporal y % Grasa
  - Composición corporal 4 componentes (Rose & Gurfinkel)
  - IMC, ICC, TMB, Ruffier-Dickson
- **Fórmulas intercambiables** — selecciona la variante metodológica para cada cálculo
- Gráficos interactivos: composición corporal (dona), pliegues (barras), IMC (velocímetro)
- Exportar a **CSV** y **PDF**
- Tema oscuro estilo Da Vinci (dorado sobre azul noche)

---

## Fórmulas disponibles

| Cálculo | Opciones |
|---|---|
| Densidad Corporal | Durnin & Womersley (7pl) · Jackson & Pollock 3pl ♂/♀ |
| % Grasa | Siri (1956) · Brozek (1963) |
| FC Máxima | Fox · Tanaka · Nes |
| TMB | Harris-Benedict · Mifflin-St Jeor · OMS/FAO |

---

## Requisitos

```
pip install customtkinter fpdf2 matplotlib numpy openpyxl
```

## Uso

```bash
python app.py
```

---

## Referencias

- ISAK — *International Standards for Anthropometric Assessment*, 2006
- Durnin & Womersley, 1974. *Br J Nutrition* 32:77-97
- Rose & Gurfinkel — Composición corporal 4 componentes
- Harris & Benedict, 1919. *Carnegie Institute of Washington*
- Mifflin et al., 1990. *Am J Clinical Nutrition* 51(2)
- Jackson & Pollock, 1978. *Br J Nutrition* 40:497
- Tanaka et al., 2001. *J Am Coll Cardiology* 37(1)

---

*Autor base: Luis Cruz Saavedra — Asignatura: Musculación*
