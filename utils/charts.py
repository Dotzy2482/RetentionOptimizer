import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


def create_canvas(width=6, height=4, dpi=100) -> tuple[Figure, FigureCanvas]:
    """Create a matplotlib Figure + Qt canvas pair."""
    fig = Figure(figsize=(width, height), dpi=dpi)
    fig.set_facecolor("#f5f6fa")
    canvas = FigureCanvas(fig)
    return fig, canvas


# ── Dashboard charts ──────────────────────────────────────────────

def loyalty_histogram(scores, fig: Figure):
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


# ── Segmentation view charts ─────────────────────────────────────

SEGMENT_COLORS = {
    "Low Engagement": "#e74c3c",
    "Active Customer": "#3498db",
    "High Value Loyal": "#2ecc71",
}


def segment_rfm_bar(seg_stats, fig: Figure):
    """Bar chart showing average RFM values per segment.
    seg_stats: DataFrame with columns segment_label, avg_recency, avg_frequency, avg_monetary
    """
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor("#ffffff")

    labels = seg_stats["segment_label"].tolist()
    x = np.arange(len(labels))
    width = 0.25

    ax.bar(x - width, seg_stats["avg_recency"], width, label="Recency", color="#e74c3c", alpha=0.85)
    ax.bar(x, seg_stats["avg_frequency"], width, label="Frequency", color="#3498db", alpha=0.85)
    # Monetary is too large, use secondary axis
    ax2 = ax.twinx()
    ax2.bar(x + width, seg_stats["avg_monetary"], width, label="Monetary", color="#2ecc71", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Recency / Frequency")
    ax2.set_ylabel("Monetary")
    ax.set_title("Segment Bazli Ortalama RFM", fontsize=12, fontweight="bold")

    # Combined legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

    fig.tight_layout()


def segment_scatter(frequency, monetary, segment_labels, fig: Figure):
    """Frequency vs Monetary scatter colored by segment."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor("#ffffff")

    unique_labels = sorted(set(segment_labels))
    for label in unique_labels:
        mask = [s == label for s in segment_labels]
        freq = [f for f, m in zip(frequency, mask) if m]
        mon = [mo for mo, m in zip(monetary, mask) if m]
        color = SEGMENT_COLORS.get(label, "#7f8c8d")
        ax.scatter(freq, mon, c=color, label=label, alpha=0.5, s=15, edgecolors="none")

    ax.set_title("Frequency vs Monetary (Segment)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Frequency")
    ax.set_ylabel("Monetary")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)
    fig.tight_layout()


# ── Churn / Prediction view charts ───────────────────────────────

def feature_importance_bar(importances: dict, fig: Figure):
    """Horizontal bar chart for feature importances."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor("#ffffff")

    sorted_items = sorted(importances.items(), key=lambda x: x[1])
    names = [k for k, v in sorted_items]
    values = [v for k, v in sorted_items]

    colors = ["#3498db" if v < 0.1 else "#e74c3c" for v in values]
    ax.barh(names, values, color=colors, edgecolor="#2c3e50", alpha=0.85)
    ax.set_title("Feature Importance", fontsize=12, fontweight="bold")
    ax.set_xlabel("Importance")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
