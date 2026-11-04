"""Generic heating-and-transfer process: vessels, pump, exchanger, valves and instrument loops."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing
from esquadro.symbols import exchanger, instrument, pipe, pump, valve, vessel

OUT = Path(__file__).resolve().parent

CAPACITY_M3_H = 12.0
INLET_C = 25.0
OUTLET_C = 80.0
DENSITY = 1000.0
CP_KJ_KG_K = 4.18


def heat_duty_kw() -> float:
    """Q = m cp dT, in kW, for the design flow."""
    mass_kg_s = CAPACITY_M3_H * DENSITY / 3600
    return mass_kg_s * CP_KJ_KG_K * (OUTLET_C - INLET_C)


def draw_flow(d: Drawing, x0: float, y0: float, w: float, h: float) -> None:
    """Lay the train out by columns across the given area; every position comes from it."""
    col = w / 6
    base = y0 + h * 0.55
    tank_h = 56.0
    feed = vessel(d, (x0 + col * 0.6, base), 30, tank_h, "T-101", "Alimentação")
    product = vessel(d, (x0 + col * 5.4, base), 30, tank_h, "T-102", "Produto")
    outlet_y = feed.port("right_low")[1]
    p101 = pump(d, (x0 + col * 1.85, outlet_y), "P-101", "Bomba")
    he_y = base - 10
    he = exchanger(d, (x0 + col * 3.2, he_y), "E-101", "Aquecedor", r=9, tag_offset=2.5)
    fv = valve(d, (x0 + col * 4.25, he_y), "FV-101", actuator=True)
    v101 = valve(d, (x0 + col * 1.3, outlet_y), "V-101")

    pipe(d, feed.port("right_low"), v101.port("in"), arrow=False)
    pipe(d, v101.port("out"), p101.port("in"), arrow=False)
    pipe(d, p101.port("out"), he.port("in"), route="hvh")
    pipe(d, he.port("out"), fv.port("in"))
    pipe(d, fv.port("out"), product.port("left_high"), route="hvh")

    # heating medium stops short of the signal line above it
    x_shell = he.port("shell_in")[0]
    pipe(d, (x_shell, he_y - 26), he.port("shell_in"), kind="thin", label="Vapor", label_side="right")
    pipe(
        d,
        he.port("shell_out"),
        (x_shell, he_y + 38),
        kind="thin",
        label="Condensado",
        label_side="left",
        label_at=0.8,
        arrow_at=0.3,
    )

    signal_y = base - 44
    fit = instrument(d, (x0 + col * 2.6, signal_y), "FT", "101")
    fic = instrument(d, (x0 + col * 4.25, signal_y), "FIC", "101", location="panel")
    pipe(d, fit.port("bottom"), (fit.port("bottom")[0], he_y), kind="thin", arrow=False)
    pipe(d, fit.port("right"), fic.port("left"), kind="signal", arrow=False)
    pipe(d, fic.port("bottom"), fv.port("actuator"), kind="signal", arrow=False)

    ti = instrument(d, (x0 + col * 3.75, base + 20), "TI", "101")
    pipe(d, (ti.port("top")[0], he_y), ti.port("top"), kind="thin", arrow=False)

    lt = instrument(d, (product.port("top")[0], signal_y - 4), "LT", "102")
    pipe(d, lt.port("bottom"), product.port("top"), kind="thin", arrow=False)


def technical() -> Path:
    d = Drawing.sheet(
        "A3",
        mode="industrial",
        title="Fluxo de processo: aquecimento",
        description="Generic process flow: feed vessel, pump, heater, control valve and product vessel.",
        title_block={"number": "EX-003", "drawn": "Esquadro", "date": "2026-11-04", "rev": "0", "projection": None},
    )
    x, y, w, h = d.area
    draw_flow(d, x + 4, y + 8, w - 8, h - 62)

    table_y = y + h - 46
    duty = heat_duty_kw()
    rows = [
        ["Parâmetro", "Valor", "Origem"],
        ["Vazão de projeto", f"{CAPACITY_M3_H:g} m³/h", "parâmetro"],
        ["Temperatura de entrada", f"{INLET_C:g} °C", "parâmetro"],
        ["Temperatura de saída", f"{OUTLET_C:g} °C", "parâmetro"],
        ["Carga térmica (Q = m·cp·dT)", f"{duty:.0f} kW", "calculado"],
    ]
    d.table(x + 4, table_y, rows, (66, 30, 30), row_height=7, align=("start", "end", "start"))
    x1 = x + 146
    d.text((x1, table_y + 5), "LEGENDA", "heading")
    d.line((x1, table_y + 13), (x1 + 16, table_y + 13))
    d.text((x1 + 19, table_y + 13), "Linha de processo", "label", valign="middle")
    d.line((x1, table_y + 21), (x1 + 16, table_y + 21), "thin")
    d.text((x1 + 19, table_y + 21), "Utilidade e tomada de instrumento", "label", valign="middle")
    d.line((x1, table_y + 29), (x1 + 16, table_y + 29), "signal")
    d.text((x1 + 19, table_y + 29), "Sinal de instrumento", "label", valign="middle")
    d.text((x1, table_y + 40), "Simplificado; símbolos não verificados contra ISA-5.1 ou ISO 10628.", "dim")
    return d.save(OUT / "process_flow_technical.svg")


def sketch() -> Path:
    d = Drawing(
        230,
        130,
        "sketch",
        title="Fluxo de processo (croqui)",
        description="Hand-style sketch of a generic heating process.",
    )
    d.text((8, 11), "Aquecimento e transferência: ideia geral", "heading")
    draw_flow(d, 6, 14, 218, 108)
    return d.save(OUT / "process_flow_sketch.svg")


if __name__ == "__main__":
    technical()
    sketch()
