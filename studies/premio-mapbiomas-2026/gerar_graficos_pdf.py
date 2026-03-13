#!/usr/bin/env python3
"""
Geração de figuras com fundo branco para submissão ao Prêmio MapBiomas "Combate ao Desmatamento".

5 figuras:
  Fig 1 — Evolução temporal RO 2015-2024 (IBGE vs MapBiomas vs CONAB)
  Fig 2 — Evolução do gap % em barras (-13% a +81%)
  Fig 3 — Gap municipal (7 municípios RO)
  Fig 4 — DETER 2022-2025 × gap % sobreposição (eixo duplo)
  Fig 5 — Ranking de priorização (top-20, barras empilhadas por 3 componentes, coloridas por tier)

Fundo branco, paleta para impressão, 7"×4.5" @ 200 DPI.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── Dimensões (otimizado para impressão A4) ──────────────────────────
DPI = 200
FIG_W = 7.0
FIG_H = 4.5

# ── Paleta fundo branco ─────────────────────────────────────────────
BG = "#FFFFFF"
BG_AXES = "#FFFFFF"
GRID_COLOR = "#E0E0E0"
TEXT_COLOR = "#1a1a1a"
TICK_COLOR = "#444444"
EDGE_COLOR = "#CCCCCC"

COLOR_IBGE = "#2166AC"
COLOR_MB = "#D6604D"
COLOR_CONAB = "#1B7837"
COLOR_GAP = "#B2182B"
COLOR_NEG = "#D6604D"
COLOR_ACCENT = "#7B3294"
COLOR_DETER = "#E66101"

plt.rcParams.update(
    {
        "figure.facecolor": BG,
        "axes.facecolor": BG_AXES,
        "axes.edgecolor": EDGE_COLOR,
        "axes.labelcolor": TEXT_COLOR,
        "text.color": TEXT_COLOR,
        "xtick.color": TICK_COLOR,
        "ytick.color": TICK_COLOR,
        "grid.color": GRID_COLOR,
        "grid.alpha": 0.7,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Helvetica", "Arial"],
        "font.size": 11,
    }
)

OUT_DIR = Path(__file__).parent

# ── Dados (atualizados via IBGE SIDRA + MapBiomas Col.10 + DETER, março 2026) ──

YEARS = list(range(2015, 2025))

IBGE_RO = [
    234_152,
    291_953,
    331_329,
    385_000,
    396_779,
    439_943,
    490_934,
    532_359,
    589_263,
    634_079,
]
MB_RO = [
    268_000,
    310_000,
    336_000,
    345_000,
    348_000,
    338_000,
    352_000,
    349_000,
    348_000,
    350_398,
]

# Municipal (7 municípios, ordenados por gap% decrescente, IBGE > 10k ha)
# Dados: IBGE PAM 2024 (SIDRA tab.5457) × MapBiomas Col.10 2024 Soja+OLT
MUNICIPIOS = [
    ("Itapuã do\nOeste", 23_500, 3_125),
    ("Nova\nMamoré", 11_551, 1_897),
    ("Porto\nVelho", 46_994, 15_720),
    ("Rio\nCrespo", 35_494, 12_731),
    ("Candeias do\nJamari", 30_894, 11_303),
    ("Alto\nParaíso", 29_566, 13_026),
    ("Machadinho\nD'Oeste", 15_500, 6_962),
]

# DETER 2022-2025 (km²) para municípios de RO — top 15 por desmatamento
# Fonte: INPE DETER via agrobr.desmatamento.deter(uf='RO', data_inicio='2022-01-01', data_fim='2025-12-31')
# Gap: (IBGE−MB)/MB×100, mostrado apenas onde MB > 1000 ha (None = MB muito pequeno ou gap ≤ 0)
DETER_OVERLAP = [
    ("Porto Velho", 1_947, 199),
    ("Vilhena", 1_102, None),  # gap −9% (MB > IBGE)
    ("Guajará-\nMirim", 970, None),  # MB < 1k ha
    ("Espigão\nD'Oeste", 563, 42),
    ("Candeias do\nJamari", 531, 173),
    ("Pimenteiras\ndo Oeste", 393, 37),
    ("Cujubim", 350, 105),
    ("Nova\nMamoré", 328, 509),
    ("Machadinho\nD'Oeste", 291, 123),
    ("Pimenta\nBueno", 267, 15),
    ("Costa\nMarques", 238, None),  # MB < 1k ha
    ("S.Franc.\nGuaporé", 214, 203),
    ("Itapuã do\nOeste", 184, 652),
    ("A.Floresta\nD'Oeste", 170, 68),
    ("Chupinguaia", 164, 27),
]


def fmt_k(x: float, _pos: int | None = None) -> str:
    return f"{x / 1000:.0f}k"


# ═══════════════════════════════════════════════════════════════════════
# FIGURA 1: Evolução Temporal RO (2015-2024)
# ═══════════════════════════════════════════════════════════════════════
def fig_temporal() -> None:
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.subplots_adjust(top=0.86, bottom=0.16, left=0.12, right=0.95)

    ax.fill_between(
        YEARS,
        IBGE_RO,
        MB_RO,
        where=[i >= m for i, m in zip(IBGE_RO, MB_RO)],
        alpha=0.12,
        color=COLOR_GAP,
        label="_nolegend_",
    )
    ax.fill_between(
        YEARS,
        IBGE_RO,
        MB_RO,
        where=[i < m for i, m in zip(IBGE_RO, MB_RO)],
        alpha=0.12,
        color=COLOR_MB,
        label="_nolegend_",
    )

    ax.plot(
        YEARS,
        IBGE_RO,
        "o-",
        color=COLOR_IBGE,
        linewidth=2.5,
        markersize=6,
        label="IBGE PAM (pesquisa)",
        zorder=5,
    )
    ax.plot(
        YEARS,
        MB_RO,
        "s-",
        color=COLOR_MB,
        linewidth=2.5,
        markersize=6,
        label="MapBiomas Col.10 (satélite)",
        zorder=5,
    )

    ax.plot(
        2024,
        716_900,
        "D",
        color=COLOR_CONAB,
        markersize=10,
        zorder=6,
        label="CONAB 2025/26",
    )
    ax.annotate(
        "716.900 ha\nCONAB 2025/26",
        xy=(2024, 716_900),
        xytext=(2020.2, 730_000),
        fontsize=9,
        color=COLOR_CONAB,
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": COLOR_CONAB, "lw": 1.2},
    )

    ax.axvline(x=2018, color=COLOR_ACCENT, linestyle="--", alpha=0.4, linewidth=1)
    crossover_y = (IBGE_RO[3] + MB_RO[3]) / 2
    ax.annotate(
        "Inversão\n2018",
        xy=(2018, crossover_y),
        xytext=(2016.2, 530_000),
        fontsize=9,
        color=COLOR_ACCENT,
        fontweight="bold",
        ha="center",
        arrowprops={"arrowstyle": "->", "color": COLOR_ACCENT, "lw": 1.2},
    )

    gap_2024 = IBGE_RO[-1] - MB_RO[-1]
    mid_y = (IBGE_RO[-1] + MB_RO[-1]) / 2
    ax.annotate(
        f"Gap: +{gap_2024 / 1000:.0f}k ha\n(+81%)",
        xy=(2023.8, mid_y),
        xytext=(2021, mid_y - 30_000),
        fontsize=10,
        color=COLOR_GAP,
        fontweight="bold",
        zorder=10,
        bbox={
            "boxstyle": "round,pad=0.4",
            "fc": BG,
            "ec": COLOR_GAP,
            "alpha": 0.95,
            "linewidth": 1.5,
        },
        arrowprops={"arrowstyle": "->", "color": COLOR_GAP, "lw": 1.5},
    )

    ax.annotate(
        "MapBiomas permanece\nna faixa ~340–350k ha",
        xy=(2021, MB_RO[6]),
        xytext=(2018.5, 250_000),
        fontsize=8.5,
        color=COLOR_MB,
        fontstyle="italic",
        arrowprops={"arrowstyle": "->", "color": COLOR_MB, "lw": 1},
    )

    ax.set_ylabel("Área de soja (hectares)", fontsize=11)
    fig.suptitle(
        "Figura 1 — Rondônia: evolução temporal IBGE vs MapBiomas (2015–2024)",
        fontsize=12,
        fontweight="bold",
        y=0.95,
    )
    ax.set_xticks(YEARS)
    ax.set_xticklabels([str(y) for y in YEARS], fontsize=9, rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.tick_params(axis="y", labelsize=9)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.8, edgecolor="#ccc")
    ax.grid(True, axis="y", linewidth=0.5)
    ax.set_xlim(2014.5, 2024.8)
    ax.set_ylim(180_000, 780_000)

    fig.text(
        0.50,
        0.02,
        "Fontes: IBGE SIDRA (tab.5457) · MapBiomas Collection 10 · CONAB 5º Lev. 2025/26",
        ha="center",
        fontsize=8,
        color="#888",
    )

    path = OUT_DIR / "fig_1_temporal_ro.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=BG, edgecolor="none")
    print(f"  OK {path.name}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURA 2: Evolução do Gap % (-13% a +81%)
# ═══════════════════════════════════════════════════════════════════════
def fig_gap_evolution() -> None:
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.subplots_adjust(top=0.86, bottom=0.16, left=0.12, right=0.95)

    gaps = [(i - m) / m * 100 for i, m in zip(IBGE_RO, MB_RO)]

    bar_colors = [COLOR_NEG if g < 0 else COLOR_GAP for g in gaps]
    ax.bar(YEARS, gaps, color=bar_colors, width=0.7, edgecolor=EDGE_COLOR, linewidth=0.5)

    ax.axhline(y=0, color=TEXT_COLOR, linewidth=0.8, alpha=0.4)

    for year, gap in zip(YEARS, gaps):
        va = "bottom" if gap >= 0 else "top"
        offset = 3 if gap >= 0 else -3
        ax.text(
            year,
            gap + offset,
            f"{gap:+.0f}%",
            ha="center",
            va=va,
            fontsize=9,
            fontweight="bold",
            color=TEXT_COLOR,
        )

    ax.annotate(
        "2018: IBGE ultrapassa\nMapBiomas pela 1ª vez",
        xy=(2018, gaps[3]),
        xytext=(2020.5, 70),
        fontsize=9,
        color=COLOR_ACCENT,
        fontweight="bold",
        ha="center",
        arrowprops={"arrowstyle": "->", "color": COLOR_ACCENT, "lw": 1.2},
    )

    ax.set_ylabel("Gap IBGE vs MapBiomas (%)", fontsize=11)
    fig.suptitle(
        "Figura 2 — De −13% a +81% em 10 anos: evolução do gap em Rondônia",
        fontsize=12,
        fontweight="bold",
        y=0.95,
    )
    ax.set_xticks(YEARS)
    ax.set_xticklabels([str(y) for y in YEARS], fontsize=9, rotation=45, ha="right")
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(True, axis="y", linewidth=0.5)
    ax.set_ylim(-25, 100)

    fig.text(
        0.50,
        0.02,
        "Gap = (IBGE − MapBiomas) / MapBiomas × 100  |  RO, soja, classes Soja+OLT",
        ha="center",
        fontsize=8,
        color="#888",
    )

    path = OUT_DIR / "fig_2_gap_evolucao.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=BG, edgecolor="none")
    print(f"  OK {path.name}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURA 3: Gap Municipal (7 municípios RO)
# ═══════════════════════════════════════════════════════════════════════
def fig_municipal() -> None:
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.subplots_adjust(top=0.86, bottom=0.18, left=0.12, right=0.95)

    names = [m[0] for m in MUNICIPIOS]
    ibge_vals = np.array([m[1] for m in MUNICIPIOS], dtype=float)
    mb_vals = np.array([m[2] for m in MUNICIPIOS], dtype=float)
    gaps_pct = (ibge_vals - mb_vals) / mb_vals * 100

    x = np.arange(len(names))
    width = 0.36

    ax.bar(
        x - width / 2,
        ibge_vals,
        width,
        label="IBGE PAM",
        color=COLOR_IBGE,
        edgecolor=EDGE_COLOR,
        linewidth=0.5,
    )
    ax.bar(
        x + width / 2,
        mb_vals,
        width,
        label="MapBiomas Col.10",
        color=COLOR_MB,
        edgecolor=EDGE_COLOR,
        linewidth=0.5,
    )

    for i in range(len(names)):
        y_top = ibge_vals[i]
        color = COLOR_GAP if gaps_pct[i] > 150 else TEXT_COLOR
        ax.text(
            x[i],
            y_top + 2_000,
            f"+{gaps_pct[i]:.0f}%",
            ha="center",
            fontsize=9,
            fontweight="bold",
            color=color,
        )

    ax.axvspan(1.5, 2.5, alpha=0.06, color=COLOR_ACCENT)
    ax.annotate(
        "Porto Velho:\nÁrea 100% amazônica",
        xy=(2, ibge_vals[2]),
        xytext=(4.5, max(ibge_vals) * 0.9),
        fontsize=8.5,
        color=COLOR_ACCENT,
        fontweight="bold",
        ha="center",
        bbox={
            "boxstyle": "round,pad=0.3",
            "fc": BG,
            "ec": COLOR_ACCENT,
            "alpha": 0.9,
            "linewidth": 1,
        },
        arrowprops={"arrowstyle": "->", "color": COLOR_ACCENT, "lw": 1.2},
    )

    ax.set_ylabel("Área de soja (hectares)", fontsize=11)
    fig.suptitle(
        "Figura 3 — Gap por município em Rondônia (2024)",
        fontsize=12,
        fontweight="bold",
        y=0.95,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8.5, rotation=30, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
    ax.tick_params(axis="y", labelsize=9)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.8, edgecolor="#ccc")
    ax.grid(True, axis="y", linewidth=0.5)
    ax.set_ylim(0, max(ibge_vals) * 1.15)

    fig.text(
        0.50,
        0.02,
        "Fonte: IBGE SIDRA (tab.5457) · MapBiomas Collection 10  |  Municípios selecionados de RO",
        ha="center",
        fontsize=8,
        color="#888",
    )

    path = OUT_DIR / "fig_3_municipal_ro.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=BG, edgecolor="none")
    print(f"  OK {path.name}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURA 4: DETER 2022-2025 × gap % sobreposição (eixo duplo)
# ═══════════════════════════════════════════════════════════════════════
def fig_deter_overlap() -> None:
    fig, ax1 = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.subplots_adjust(top=0.84, bottom=0.20, left=0.10, right=0.88)

    names = [d[0] for d in DETER_OVERLAP]
    deter_vals = [d[1] for d in DETER_OVERLAP]
    gap_vals = [d[2] for d in DETER_OVERLAP]

    x = np.arange(len(names))

    ax1.bar(
        x,
        deter_vals,
        color=COLOR_DETER,
        alpha=0.75,
        edgecolor=EDGE_COLOR,
        linewidth=0.5,
        width=0.6,
        label="DETER km² (2022–2025)",
    )

    ax1.set_ylabel("Desmatamento DETER (km²)", fontsize=10, color=COLOR_DETER)
    ax1.tick_params(axis="y", labelsize=8, colors=COLOR_DETER)

    ax2 = ax1.twinx()

    gap_x = []
    gap_y = []
    for i, g in enumerate(gap_vals):
        if g is not None:
            gap_x.append(i)
            gap_y.append(g)

    ax2.plot(
        gap_x,
        gap_y,
        "D-",
        color=COLOR_GAP,
        markersize=8,
        linewidth=2,
        zorder=6,
        label="Gap soja IBGE vs MB (%)",
    )
    for gx, gy in zip(gap_x, gap_y):
        ax2.annotate(
            f"+{gy}%",
            xy=(gx, gy),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color=COLOR_GAP,
        )

    ax2.set_ylabel("Gap de classificação de soja (%)", fontsize=10, color=COLOR_GAP)
    ax2.tick_params(axis="y", labelsize=8, colors=COLOR_GAP)
    ax2.set_ylim(0, 720)

    for i, g in enumerate(gap_vals):
        if g is not None:
            ax1.axvspan(i - 0.35, i + 0.35, alpha=0.06, color=COLOR_GAP, zorder=0)

    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=7.5, rotation=45, ha="right")
    ax1.grid(True, axis="y", linewidth=0.5, alpha=0.5)

    fig.suptitle(
        "Figura 4 — Desmatamento DETER × gap de classificação de soja em Rondônia",
        fontsize=11.5,
        fontweight="bold",
        y=0.96,
    )
    fig.text(
        0.49,
        0.87,
        "Cruzamento descritivo: municípios com alto DETER e gap de soja > 50% destacados",
        ha="center",
        fontsize=9,
        color=COLOR_GAP,
        fontstyle="italic",
    )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper center",
        fontsize=8,
        framealpha=0.9,
        edgecolor="#ccc",
    )

    fig.text(
        0.50,
        0.02,
        "Fontes: INPE DETER (2022–2025) · IBGE SIDRA (tab.5457) · MapBiomas Col.10  |  Top 15 municípios RO por desmatamento",
        ha="center",
        fontsize=7.5,
        color="#888",
    )

    path = OUT_DIR / "fig_4_deter_gap_overlap.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=BG, edgecolor="none")
    print(f"  OK {path.name}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURA 5: Ranking de Priorização para Recalibração (top-20)
# ═══════════════════════════════════════════════════════════════════════

COLOR_TIER_ALTA = "#B2182B"
COLOR_TIER_MEDIA = "#F4A582"
COLOR_TIER_BAIXA = "#D1E5F0"

COLOR_COMP_GAP_REL = "#2166AC"
COLOR_COMP_GAP_ABS = "#4393C3"
COLOR_COMP_DETER = "#E66101"


def fig_ranking() -> None:
    """Fig 5 — Barras horizontais empilhadas do ranking de priorização (top-20)."""
    ranking_csv = OUT_DIR / "ranking_results.csv"
    if not ranking_csv.exists():
        print(
            "  SKIP fig_5 — ranking_results.csv não encontrado (rode ranking_priorizacao.py primeiro)"
        )
        return

    all_rows = []
    with open(ranking_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for r in reader:
            all_rows.append(r)
            if len(all_rows) >= 20:
                break

    tier_order = {"Alta": 0, "Média": 1, "Baixa": 2}
    rows = sorted(all_rows, key=lambda r: (tier_order.get(r["tier"], 9), -float(r["score"])))

    names = [r["municipio"].replace(" - RO", "") for r in rows]
    rp_rel = [float(r["rp_gap_rel"]) for r in rows]
    rp_abs = [float(r["rp_gap_abs"]) for r in rows]
    rp_det = [float(r["rp_deter"]) for r in rows]
    tiers = [r["tier"] for r in rows]
    scores = [float(r["score"]) for r in rows]

    names = names[::-1]
    rp_rel = rp_rel[::-1]
    rp_abs = rp_abs[::-1]
    rp_det = rp_det[::-1]
    tiers = tiers[::-1]
    scores = scores[::-1]

    fig, ax = plt.subplots(figsize=(FIG_W, 5.2))
    fig.subplots_adjust(top=0.88, bottom=0.12, left=0.28, right=0.92)

    y = np.arange(len(names))
    bar_h = 0.65

    ax.barh(
        y,
        rp_rel,
        bar_h,
        label="Gap relativo (%)",
        color=COLOR_COMP_GAP_REL,
        edgecolor="white",
        linewidth=0.3,
    )
    ax.barh(
        y,
        rp_abs,
        bar_h,
        left=rp_rel,
        label="Gap absoluto (ha)",
        color=COLOR_COMP_GAP_ABS,
        edgecolor="white",
        linewidth=0.3,
    )
    ax.barh(
        y,
        rp_det,
        bar_h,
        left=[a + b for a, b in zip(rp_rel, rp_abs)],
        label="DETER (km²)",
        color=COLOR_COMP_DETER,
        edgecolor="white",
        linewidth=0.3,
    )

    tier_color_map = {"Alta": COLOR_TIER_ALTA, "Média": COLOR_TIER_MEDIA, "Baixa": COLOR_TIER_BAIXA}
    for i, tier in enumerate(tiers):
        color = tier_color_map.get(tier, COLOR_TIER_BAIXA)
        ax.barh(i, 0.04, bar_h, left=-0.06, color=color, edgecolor="none")

    for i, s in enumerate(scores):
        ax.text(
            s + 0.04, i, f"{s:.2f}", va="center", fontsize=8, fontweight="bold", color=TEXT_COLOR
        )

    for i in range(1, len(tiers)):
        if tiers[i] != tiers[i - 1]:
            ax.axhline(y=i - 0.5, color="#999", linewidth=0.8, linestyle="--", alpha=0.6)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.set_xlabel("Score (soma dos rank percentiles)", fontsize=10)
    ax.set_xlim(-0.08, 3.15)
    ax.grid(True, axis="x", linewidth=0.5, alpha=0.5)

    fig.suptitle(
        "Figura 5 — Ranking de priorização municipal para recalibração (RO)",
        fontsize=12,
        fontweight="bold",
        y=0.96,
    )

    comp_legend = ax.legend(
        loc="lower right",
        fontsize=8,
        framealpha=0.9,
        edgecolor="#ccc",
        title="Componentes",
        title_fontsize=8,
    )
    ax.add_artist(comp_legend)

    tier_patches = [
        mpatches.Patch(color=COLOR_TIER_ALTA, label="Alta"),
        mpatches.Patch(color=COLOR_TIER_MEDIA, label="Média"),
        mpatches.Patch(color=COLOR_TIER_BAIXA, label="Baixa"),
    ]
    tier_legend = ax.legend(
        handles=tier_patches,
        loc="lower right",
        fontsize=7.5,
        framealpha=0.9,
        edgecolor="#ccc",
        title="Tier",
        title_fontsize=8,
        bbox_to_anchor=(1.0, 0.28),
    )
    ax.add_artist(comp_legend)
    ax.add_artist(tier_legend)

    fig.text(
        0.50,
        0.01,
        "Tier Alta = Q4 em \u22652 componentes e IBGE \u226510.000 ha"
        "  |  Score = rank percentile (gap% + gap ha + DETER km²)"
        "  |  IBGE PAM 2024 · MapBiomas Col.10 · DETER 2022–2025",
        ha="center",
        fontsize=6.5,
        color="#888",
    )

    path = OUT_DIR / "fig_5_ranking_priorizacao.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=BG, edgecolor="none")
    print(f"  OK {path.name}")
    plt.close(fig)


if __name__ == "__main__":
    print("Gerando figuras para submissão 'Combate ao Desmatamento'...\n")
    fig_temporal()
    fig_gap_evolution()
    fig_municipal()
    fig_deter_overlap()
    fig_ranking()
    print(f'\n5 figuras salvas em {OUT_DIR} ({FIG_W}"×{FIG_H}" @ {DPI} DPI)')
