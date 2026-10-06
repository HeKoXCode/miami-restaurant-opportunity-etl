"""Native high-resolution figures shared by the notebook and published exports."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch, Rectangle

from src.reporting import (
    build_preference_value_view,
    build_premium_view,
    build_price_competition_view,
    build_sensitivity_view,
    build_stratum_view,
)

NAVY, BLUE, ORANGE, INK, MUTED = "#12344D", "#2F75B5", "#D97A00", "#172C3E", "#536879"
PUBLIC_NAMES = [
    "01_customer_value_premium",
    "02_value_by_stratum",
    "03_preference_value",
    "04_demand_vs_coverage",
    "05_competition_by_price",
    "06_threshold_sensitivity",
]


def build_figures(report):
    plt.rcdefaults()
    # Stable SVG IDs let the public verification detect genuine visual drift.
    plt.rcParams["svg.hashsalt"] = "miami-educational-report-v1"
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 15,
            "axes.labelcolor": INK,
            "text.color": INK,
            "axes.edgecolor": "#D7E0E8",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.spines.bottom": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "path",
        }
    )

    def figure(n, title, subtitle):
        fig, ax = plt.subplots(figsize=(12, 7.6))
        fig.patch.set_facecolor("white")
        fig.subplots_adjust(left=0.16, right=0.93, bottom=0.25, top=0.73)
        fig.text(
            0.06,
            0.944,
            f"MIAMI ETL  /  CASO EDUCATIVO  /  {n:02d}",
            fontsize=12,
            color=BLUE,
            weight="bold",
        )
        fig.text(0.06, 0.873, title, fontsize=24, weight="bold", color=NAVY)
        fig.text(0.06, 0.812, subtitle, fontsize=13, color=MUTED)
        fig.text(
            0.06,
            0.075,
            "Fuente: tablas finales del caso educativo | run_id: 1aa6a2953069e064",
            fontsize=10,
            color=MUTED,
        )
        fig.text(
            0.06,
            0.040,
            "Percy I. Marzoratti Hill  |  No representa un censo del mercado ni una recomendación de inversión.",
            fontsize=10,
            color=MUTED,
        )
        return fig, ax

    figures = []
    names = []

    def keep(fig, name):
        figures.append(fig)
        names.append(name)

    fig, ax = figure(
        1,
        "El valor estimado se concentra en clientes premium",
        "Comparación de participación en clientes y gasto estimado, no ingresos observados.",
    )
    v = build_premium_view(report.customer_value).reindex(["No", "Sí"])
    y = np.arange(2)
    ax.barh(y + 0.17, v.iloc[:, 0] * 100, height=0.29, color=BLUE, label="Clientes")
    ax.barh(y - 0.17, v.iloc[:, 1] * 100, height=0.29, color=ORANGE, label="Gasto estimado")
    for i in range(2):
        for offset, col in [(0.17, 0), (-0.17, 1)]:
            value = v.iloc[i, col] * 100
            ax.text(
                value + 1.4, i + offset, f"{value:.1f}%", va="center", fontsize=16, weight="bold"
            )
    ax.set(
        yticks=y,
        yticklabels=["Sin premium", "Con premium"],
        xlim=(0, 94),
        xlabel="Participación (%)",
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, 1.16), ncol=2, frameon=False, fontsize=13)
    ax.xaxis.grid(True, alpha=0.16)
    ax.set_axisbelow(True)
    keep(fig, "miami_01_premium")

    fig, ax = figure(
        2,
        "Muy Alto reúne el 56,5% del gasto estimado",
        "Una segmentación ayuda a priorizar una validación; no demuestra rentabilidad.",
    )
    v = build_stratum_view(report.customer_value)
    y = np.arange(len(v))
    ax.barh(y + 0.17, v.customer_share * 100, height=0.29, color=BLUE, label="Clientes")
    ax.barh(y - 0.17, v.spend_share * 100, height=0.29, color=ORANGE, label="Gasto estimado")
    for i, (_, row) in enumerate(v.iterrows()):
        for off, key in [(0.17, "customer_share"), (-0.17, "spend_share")]:
            value = row[key] * 100
            ax.text(value + 1, i + off, f"{value:.1f}%", va="center", fontsize=13)
    ax.set(yticks=y, yticklabels=v.segment, xlim=(0, 68), xlabel="Participación (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, 1.16), ncol=2, frameon=False, fontsize=13)
    ax.xaxis.grid(True, alpha=0.16)
    ax.set_axisbelow(True)
    keep(fig, "miami_02_segmentacion")

    fig, ax = figure(
        3,
        "Mariscos y Vegetariano concentran señales de valor",
        "Ticket × frecuencia = gasto estimado por período; moneda y periodicidad no especificadas.",
    )
    v = build_preference_value_view(report.preference_opportunity)
    colors = [
        "#8896A3"
        if row.customer_preference == "Otro"
        else ORANGE
        if row.customer_preference in ["Mariscos", "Vegetariano"]
        else BLUE
        for _, row in v.iterrows()
    ]
    ax.barh(v.customer_preference, v.estimated_period_spend / 1000, color=colors, height=0.58)
    for i, (_, row) in enumerate(v.iterrows()):
        ax.text(
            row.estimated_period_spend / 1000 + 2,
            i,
            f"{row.estimated_period_spend / 1000:.1f} mil  |  n={row.customer_count:,}",
            va="center",
            fontsize=12,
        )
    ax.set(xlim=(0, 242), xlabel="Unidades de gasto estimado por período (miles)")
    ax.xaxis.grid(True, alpha=0.16)
    ax.set_axisbelow(True)
    fig.text(
        0.17,
        0.132,
        "Otro: calidad baja por preferencias imputadas; no concluyente para priorización.",
        fontsize=11,
        color=MUTED,
    )
    keep(fig, "miami_03_valor_preferencia")

    signal_colors = {
        "Brecha de cobertura observada": ORANGE,
        "Cobertura observada equilibrada": "#168B85",
        "Oferta observada amplia": "#C5A443",
        "No concluyente": "#8896A3",
    }
    fig, ax = figure(
        4,
        "Una brecha observada no equivale a una inversión",
        "3.183 clientes Miami frente a 186 restaurantes de la muestra Yelp; escenario Base.",
    )
    for _, row in report.preference_opportunity.iterrows():
        x, y = row.observed_restaurant_coverage * 100, row.customer_share * 100
        col = signal_colors.get(row.coverage_signal, "#8896A3")
        ax.scatter(
            x,
            y,
            s=200 + row.estimated_period_spend / 450,
            color=col,
            edgecolor="white",
            linewidth=1.5,
            zorder=3,
        )
        offsets = {
            "Vegetariano": (-15, 13),
            "Mariscos": (11, 10),
            "Vegano": (10, 7),
            "Pescado": (-12, -20),
            "Carnes": (11, 8),
            "Otro": (-14, 10),
        }
        dx, dy = offsets[row.customer_preference]
        ax.annotate(
            row.customer_preference,
            (x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="right" if dx < 0 else "left",
            fontsize=13,
        )
    ax.plot([0, 50], [0, 50], ls="--", color="#8191A0", lw=1)
    ax.set(
        xlim=(0, 50),
        ylim=(0, 36),
        xlabel="Cobertura por categoría en la muestra Yelp (%)",
        ylabel="Participación de clientes (%)",
    )
    ax.grid(alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend(
        handles=[
            Patch(facecolor=col, label=label)
            for col, label in [
                (ORANGE, "Brecha"),
                ("#168B85", "Equilibrio"),
                ("#C5A443", "Oferta amplia"),
                ("#8896A3", "No concluyente"),
            ]
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.16),
        ncol=4,
        frameon=False,
        fontsize=10,
    )
    fig.text(
        0.17,
        0.135,
        "Tamaño: gasto estimado. Categorías solapadas; la cobertura no es cuota de mercado.",
        fontsize=11,
        color=MUTED,
    )
    keep(fig, "miami_04_demanda_cobertura")

    fig, ax = figure(
        5,
        "El precio observado añade una dimensión al caso",
        "Conteos por preferencia y nivel de precio Yelp, no disposición a pagar.",
    )
    v = build_price_competition_view(report.restaurant_competition)
    ax.set_xlim(-0.5, 4.5)
    ax.set_ylim(5.5, -0.5)
    for i in range(6):
        for j in range(5):
            val = int(v.iloc[i, j])
            col = plt.cm.Blues(0.08 + 0.85 * val / max(v.to_numpy().max(), 1))
            ax.add_patch(
                Rectangle((j - 0.48, i - 0.48), 0.96, 0.96, facecolor=col, edgecolor="white")
            )
            ax.text(
                j,
                i,
                str(val),
                ha="center",
                va="center",
                fontsize=17,
                color="white" if val > 20 else INK,
                weight="bold",
            )
    ax.set(xticks=range(5), xticklabels=v.columns, yticks=range(6), yticklabels=v.index)
    ax.tick_params(length=0, pad=10)
    fig.text(
        0.17,
        0.135,
        "Las categorías pueden solaparse; un restaurante puede contarse en más de una fila.",
        fontsize=11,
        color=MUTED,
    )
    keep(fig, "miami_05_competencia_precio")

    fig, ax = figure(
        6,
        "La señal cambia al exigir mayor robustez",
        "Mariscos y Vegetariano pasan de brecha a equilibrio en el escenario Conservador.",
    )
    v = build_sensitivity_view(report.preference_sensitivity)
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(5.5, -0.5)
    labels = {
        "Brecha de cobertura observada": "Brecha",
        "Cobertura observada equilibrada": "Equilibrio",
        "Oferta observada amplia": "Oferta amplia",
        "No concluyente": "No concluyente",
    }
    for i in range(6):
        for j in range(3):
            signal = v.iloc[i, j]
            col = signal_colors.get(signal, "#8896A3")
            ax.add_patch(
                Rectangle(
                    (j - 0.48, i - 0.48), 0.96, 0.96, facecolor=col, alpha=0.17, edgecolor="white"
                )
            )
            ax.text(
                j,
                i,
                labels.get(signal, signal),
                ha="center",
                va="center",
                fontsize=13,
                weight="bold",
            )
    ax.set(
        xticks=range(3),
        xticklabels=[
            "Conservador\nBrecha ≥ 1,50",
            "Base\nBrecha ≥ 1,25",
            "Exploratorio\nBrecha ≥ 1,10",
        ],
        yticks=range(6),
        yticklabels=v.index,
    )
    ax.tick_params(length=0, pad=10)
    fig.text(
        0.17,
        0.133,
        "Índice: participación de clientes / cobertura de categoría. Umbrales completos en GitHub.",
        fontsize=11,
        color=MUTED,
    )
    keep(fig, "miami_06_sensibilidad")
    return figures, PUBLIC_NAMES


def export_figures(report, assets_dir, pdf_path=None):
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    figures, names = build_figures(report)
    for fig, name in zip(figures, names):
        fig.savefig(assets_dir / f"{name}.png", dpi=250, facecolor="white")
        fig.savefig(assets_dir / f"{name}.svg", facecolor="white", metadata={"Date": None})
        svg_path = assets_dir / f"{name}.svg"
        svg_path.write_text(
            "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines())
            + "\n",
            encoding="utf-8",
        )
    if pdf_path is not None:
        pdf_path = Path(pdf_path)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        with PdfPages(
            pdf_path,
            metadata={
                "Title": "Miami ETL - Evidencia del caso educativo",
                "Author": "Percy Ignacio Marzoratti Hill",
                "CreationDate": None,
                "ModDate": None,
            },
        ) as pdf:
            for fig in figures:
                pdf.savefig(fig)
    for fig in figures:
        plt.close(fig)
