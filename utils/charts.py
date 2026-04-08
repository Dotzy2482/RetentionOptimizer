import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

# Turkish character support - use a font that has Turkish glyphs
_FONT_FAMILY = "Segoe UI"
matplotlib.rcParams["font.family"] = _FONT_FAMILY
matplotlib.rcParams["axes.unicode_minus"] = False


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
    ax.set_title("Loyalty Score Dağılımı", fontsize=12, fontweight="bold")
    ax.set_xlabel("Loyalty Score")
    ax.set_ylabel("Müşteri Sayısı")
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
    fig.colorbar(scatter, ax=ax, label="Recency (gün)")
    ax.set_title("RFM: Frequency vs Monetary", fontsize=12, fontweight="bold")
    ax.set_xlabel("Frequency (sipariş sayısı)")
    ax.set_ylabel("Monetary (toplam harcama)")
    ax.grid(alpha=0.3)
    fig.tight_layout()


def segment_pie(labels, sizes, fig: Figure):
    fig.clear()
    ax = fig.add_subplot(111)
    colors = ["#e74c3c", "#f39c12", "#3498db", "#2ecc71", "#9b59b6",
              "#1abc9c", "#e67e22", "#34495e"]
    ax.pie(
        sizes, labels=labels, autopct="%1.1f%%",
        colors=colors[:len(labels)], startangle=90,
        textprops={"fontsize": 9},
    )
    ax.set_title("Segment Dağılımı", fontsize=12, fontweight="bold")
    fig.tight_layout()


# ── Segmentation view charts ─────────────────────────────────────

SEGMENT_COLORS = {
    "Low Engagement": "#e74c3c",
    "At Risk": "#f39c12",
    "Active Customer": "#3498db",
    "High Value Loyal": "#2ecc71",
}


def segment_rfm_bar(seg_stats, fig: Figure):
    """Three separate subplots for Recency, Frequency, Monetary per segment."""
    fig.clear()

    labels = seg_stats["segment_label"].tolist()
    colors = [SEGMENT_COLORS.get(l, "#7f8c8d") for l in labels]
    x = np.arange(len(labels))

    metrics = [
        ("avg_recency", "Ort. Recency (gün)"),
        ("avg_frequency", "Ort. Frequency"),
        ("avg_monetary", "Ort. Monetary"),
    ]

    for i, (col, ylabel) in enumerate(metrics):
        ax = fig.add_subplot(1, 3, i + 1)
        ax.set_facecolor("#ffffff")
        ax.bar(x, seg_stats[col], color=colors, alpha=0.85, edgecolor="#2c3e50")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6, rotation=20, ha="right")
        ax.set_ylabel(ylabel, fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Segment Bazlı Ortalama RFM", fontsize=12, fontweight="bold")
    fig.tight_layout()


def segment_scatter(frequency, monetary, segment_labels, fig: Figure):
    """Frequency vs Monetary scatter colored by segment, with log scale."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor("#ffffff")

    import numpy as _np

    unique_labels = sorted(set(segment_labels))
    for label in unique_labels:
        mask = [s == label for s in segment_labels]
        freq = _np.array([f for f, m in zip(frequency, mask) if m])
        mon = _np.array([mo for mo, m in zip(monetary, mask) if m])
        color = SEGMENT_COLORS.get(label, "#7f8c8d")
        ax.scatter(freq, mon, c=color, label=label, alpha=0.5, s=15, edgecolors="none")

    ax.set_title("Frequency vs Monetary (Segment)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Frequency")
    ax.set_ylabel("Monetary")
    # Use log scale to spread out compressed points
    ax.set_yscale("symlog", linthresh=100)
    ax.set_xscale("symlog", linthresh=5)
    ax.legend(fontsize=8, loc="upper left")
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

    colors = ["#3498db" if v < 0.15 else "#e74c3c" for v in values]
    ax.barh(names, values, color=colors, edgecolor="#2c3e50", alpha=0.85)
    ax.set_title("Feature Importance", fontsize=12, fontweight="bold")
    ax.set_xlabel("Importance")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
