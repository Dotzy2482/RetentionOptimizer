import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

# ── Design tokens (aligned with styles.qss) ──────────────────
_FONT = "Segoe UI"
matplotlib.rcParams["font.family"] = _FONT
matplotlib.rcParams["axes.unicode_minus"] = False

_PRIMARY = "#7C3AED"
_PRIMARY_LIGHT = "#A78BFA"
_PRIMARY_LIGHTER = "#DDD6FE"
_SUCCESS = "#059669"
_WARNING = "#F59E0B"
_DANGER = "#DC2626"
_TEXT = "#1C1C1E"
_TEXT_SEC = "#6B7280"
_SURFACE = "#FFFFFF"
_BG = "#F2F2F7"
_GRID = "#E5E7EB"

SEGMENT_COLORS = {
    "Low Engagement": _DANGER,
    "At Risk": _WARNING,
    "Active Customer": _PRIMARY_LIGHT,
    "High Value Loyal": _SUCCESS,
}

_SEGMENT_ORDER = ["Low Engagement", "At Risk", "Active Customer", "High Value Loyal"]


def _style_ax(ax):
    """Clean axis styling — no top/right spines, subtle grid."""
    ax.set_facecolor(_SURFACE)
    ax.tick_params(colors=_TEXT_SEC, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(_GRID)
        ax.spines[spine].set_linewidth(0.8)


def create_canvas(width=6, height=4, dpi=100) -> tuple[Figure, FigureCanvas]:
    """Create a matplotlib Figure + Qt canvas pair."""
    fig = Figure(figsize=(width, height), dpi=dpi)
    fig.set_facecolor(_BG)
    canvas = FigureCanvas(fig)
    return fig, canvas


# ── Dashboard charts ──────────────────────────────────────────

def loyalty_histogram(scores, fig: Figure):
    fig.clear()
    ax = fig.add_subplot(111)
    _style_ax(ax)
    ax.hist(scores, bins=20, color=_PRIMARY_LIGHT, edgecolor=_PRIMARY,
            alpha=0.75, linewidth=0.8)
    ax.set_title("Loyalty Score Dagilimi", fontsize=13, fontweight="bold",
                 color=_TEXT, pad=10)
    ax.set_xlabel("Loyalty Score", fontsize=10, color=_TEXT_SEC)
    ax.set_ylabel("Musteri Sayisi", fontsize=10, color=_TEXT_SEC)
    ax.grid(axis="y", alpha=0.3, color=_GRID, linewidth=0.5)
    fig.tight_layout(pad=1.5)


def rfm_scatter(frequency, monetary, recency, fig: Figure):
    fig.clear()
    ax = fig.add_subplot(111)
    _style_ax(ax)
    scatter = ax.scatter(
        frequency, monetary,
        c=recency, cmap="PuRd", alpha=0.55, s=16, edgecolors="none",
    )
    cbar = fig.colorbar(scatter, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label("Recency (gun)", fontsize=9, color=_TEXT_SEC)
    cbar.ax.tick_params(colors=_TEXT_SEC, labelsize=8)
    ax.set_title("RFM: Frequency vs Monetary", fontsize=13, fontweight="bold",
                 color=_TEXT, pad=10)
    ax.set_xlabel("Frequency (siparis)", fontsize=10, color=_TEXT_SEC)
    ax.set_ylabel("Monetary (toplam)", fontsize=10, color=_TEXT_SEC)
    ax.grid(alpha=0.3, color=_GRID, linewidth=0.5)
    fig.tight_layout(pad=1.5)


def segment_pie(labels, sizes, fig: Figure):
    """Donut chart with external legend — no inline labels to prevent overlap."""
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor(_BG)

    colors = [SEGMENT_COLORS.get(lbl, _TEXT_SEC) for lbl in labels]

    wedges, _, autotexts = ax.pie(
        sizes, autopct="%1.1f%%", colors=colors, startangle=90,
        pctdistance=0.78,
        wedgeprops={"edgecolor": _SURFACE, "linewidth": 2.5, "width": 0.55},
        textprops={"fontsize": 9, "color": _TEXT},
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_fontweight("bold")
        at.set_color(_TEXT)

    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.92, 0.5),
              fontsize=9, frameon=False, labelcolor=_TEXT)
    ax.set_title("Segment Dagilimi", fontsize=13, fontweight="bold",
                 color=_TEXT, pad=8)
    fig.tight_layout(pad=1.0, rect=[0, 0, 0.75, 1])


# ── Segmentation view charts ─────────────────────────────────

def segment_rfm_bar(seg_stats, fig: Figure):
    """Three subplots: Recency, Frequency, Monetary per segment."""
    fig.clear()

    labels = seg_stats["segment_label"].tolist()
    short = []
    for l in labels:
        if l == "Low Engagement":
            short.append("Low\nEngage")
        elif l == "At Risk":
            short.append("At\nRisk")
        elif l == "Active Customer":
            short.append("Active\nCust")
        elif l == "High Value Loyal":
            short.append("High\nValue")
        else:
            short.append(l[:8])

    colors = [SEGMENT_COLORS.get(l, _TEXT_SEC) for l in labels]
    x = np.arange(len(labels))

    metrics = [
        ("avg_recency", "Ort. Recency (gun)"),
        ("avg_frequency", "Ort. Frequency"),
        ("avg_monetary", "Ort. Monetary"),
    ]

    for i, (col, ylabel) in enumerate(metrics):
        ax = fig.add_subplot(1, 3, i + 1)
        _style_ax(ax)
        bars = ax.bar(x, seg_stats[col], color=colors, alpha=0.85,
                      edgecolor=_SURFACE, linewidth=0.5, width=0.65)
        ax.set_xticks(x)
        ax.set_xticklabels(short, fontsize=7.5, color=_TEXT_SEC)
        ax.set_ylabel(ylabel, fontsize=9, color=_TEXT_SEC)
        ax.grid(axis="y", alpha=0.3, color=_GRID, linewidth=0.5)

        for bar in bars:
            h = bar.get_height()
            txt = f"{h:,.0f}" if h >= 100 else f"{h:.1f}"
            ax.text(bar.get_x() + bar.get_width() / 2, h,
                    txt, ha="center", va="bottom", fontsize=7, color=_TEXT_SEC)

    fig.suptitle("Segment Bazli Ortalama RFM", fontsize=13,
                 fontweight="bold", color=_TEXT, y=0.98)
    fig.tight_layout(pad=1.5, rect=[0, 0, 1, 0.93])


def segment_scatter(frequency, monetary, segment_labels, fig: Figure):
    """Frequency vs Monetary scatter colored by segment."""
    fig.clear()
    ax = fig.add_subplot(111)
    _style_ax(ax)

    unique_labels = sorted(
        set(segment_labels),
        key=lambda s: _SEGMENT_ORDER.index(s) if s in _SEGMENT_ORDER else 99,
    )
    for label in unique_labels:
        mask = [s == label for s in segment_labels]
        freq = np.array([f for f, m in zip(frequency, mask) if m])
        mon = np.array([mo for mo, m in zip(monetary, mask) if m])
        color = SEGMENT_COLORS.get(label, _TEXT_SEC)
        ax.scatter(freq, mon, c=color, label=label, alpha=0.45, s=14,
                   edgecolors="none")

    ax.set_title("Frequency vs Monetary (Segment)", fontsize=13,
                 fontweight="bold", color=_TEXT, pad=10)
    ax.set_xlabel("Frequency", fontsize=10, color=_TEXT_SEC)
    ax.set_ylabel("Monetary", fontsize=10, color=_TEXT_SEC)
    ax.set_yscale("symlog", linthresh=100)
    ax.set_xscale("symlog", linthresh=5)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9, edgecolor=_GRID)
    ax.grid(alpha=0.3, color=_GRID, linewidth=0.5)
    fig.tight_layout(pad=1.5)


# ── Churn / Prediction view charts ───────────────────────────

def feature_importance_bar(importances: dict, fig: Figure):
    """Horizontal bar chart for feature importances."""
    fig.clear()
    ax = fig.add_subplot(111)
    _style_ax(ax)

    sorted_items = sorted(importances.items(), key=lambda x: x[1])
    names = [k for k, v in sorted_items]
    values = [v for k, v in sorted_items]

    colors = [_PRIMARY_LIGHTER if v < 0.15 else _PRIMARY for v in values]
    ax.barh(names, values, color=colors, edgecolor=_SURFACE, alpha=0.85,
            linewidth=0.5, height=0.6)
    ax.set_title("Feature Importance", fontsize=13, fontweight="bold",
                 color=_TEXT, pad=10)
    ax.set_xlabel("Importance", fontsize=10, color=_TEXT_SEC)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="x", alpha=0.3, color=_GRID, linewidth=0.5)

    for i, v in enumerate(values):
        ax.text(v + 0.008, i, f"{v:.3f}", ha="left", va="center",
                fontsize=8, color=_TEXT_SEC)

    fig.tight_layout(pad=1.5)
