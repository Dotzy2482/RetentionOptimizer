import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


def create_canvas(width=6, height=4, dpi=100) -> tuple[Figure, FigureCanvas]:
    """Create a matplotlib Figure + Qt canvas pair."""
    fig = Figure(figsize=(width, height), dpi=dpi)
    fig.set_facecolor("#f5f6fa")
    canvas = FigureCanvas(fig)
    return fig, canvas


def loyalty_histogram(scores, fig: Figure):
    """Draw loyalty score distribution histogram."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor("#ffffff")

    ax.hist(scores, bins=20, color="#3498db", edgecolor="#2c3e50", alpha=0.85)
    ax.set_title("Loyalty Score Dagilimi", fontsize=12, fontweight="bold")
    ax.set_xlabel("Loyalty Score")
    ax.set_ylabel("Musteri Sayisi")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()


def rfm_scatter(frequency, monetary, recency, fig: Figure):
    """Draw Frequency vs Monetary scatter, colored by Recency."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor("#ffffff")

    scatter = ax.scatter(
        frequency, monetary,
        c=recency, cmap="RdYlGn_r", alpha=0.6, s=20, edgecolors="none",
    )
    fig.colorbar(scatter, ax=ax, label="Recency (gun)")
    ax.set_title("RFM: Frequency vs Monetary", fontsize=12, fontweight="bold")
    ax.set_xlabel("Frequency (siparis sayisi)")
    ax.set_ylabel("Monetary (toplam harcama)")
    ax.grid(alpha=0.3)
    fig.tight_layout()


def segment_pie(labels, sizes, fig: Figure):
    """Draw segment distribution pie chart."""
    fig.clear()
    ax = fig.add_subplot(111)

    colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6",
              "#1abc9c", "#e67e22", "#34495e"]
    ax.pie(
        sizes, labels=labels, autopct="%1.1f%%",
        colors=colors[:len(labels)], startangle=90,
        textprops={"fontsize": 9},
    )
    ax.set_title("Segment Dagilimi", fontsize=12, fontweight="bold")
    fig.tight_layout()
