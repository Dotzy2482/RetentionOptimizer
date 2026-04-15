import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class _ScrollPassthroughCanvas(FigureCanvas):
    """FigureCanvas that forwards mouse wheel events to its parent.

    Matplotlib's default canvas consumes wheelEvent, which breaks scrolling
    inside a QScrollArea when the cursor is over a chart. Ignoring the event
    lets Qt propagate it up to the enclosing scroll area.
    """

    def wheelEvent(self, event):
        event.ignore()

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
    fig.set_facecolor("white")
    canvas = _ScrollPassthroughCanvas(fig)
    return fig, canvas


def _apply_tight_layout(fig: Figure, **tight_kwargs):
    """Apply tight_layout now AND re-apply whenever the canvas resizes.

    Custom rect-based layouts bake positions at a specific figure size;
    when the canvas is resized (e.g. page switch, window resize) text
    elements keep their physical size and the baked positions become
    wrong. Re-running tight_layout on every resize fixes this.
    """
    try:
        fig.tight_layout(**tight_kwargs)
    except Exception:
        pass

    # Replace any prior resize listener registered by this helper so
    # repeated refreshes don't accumulate callbacks.
    prev_cid = getattr(fig, "_tight_resize_cid", None)
    if prev_cid is not None:
        try:
            fig.canvas.mpl_disconnect(prev_cid)
        except Exception:
            pass

    def _on_resize(_event):
        try:
            fig.tight_layout(**tight_kwargs)
        except Exception:
            pass

    try:
        fig._tight_resize_cid = fig.canvas.mpl_connect("resize_event", _on_resize)
    except Exception:
        fig._tight_resize_cid = None


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
        c=recency, cmap="plasma", alpha=0.70, s=18, edgecolors="none",
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
    """Large donut chart with external legend on the right."""
    fig.clear()
    fig.set_facecolor("white")
    ax = fig.add_subplot(111)
    ax.set_facecolor("white")

    colors = [SEGMENT_COLORS.get(lbl, _TEXT_SEC) for lbl in labels]
    total = sum(sizes)

    wedges, _, autotexts = ax.pie(
        sizes, autopct="%1.1f%%", colors=colors, startangle=90,
        pctdistance=0.78,
        wedgeprops={"edgecolor": "white", "linewidth": 3, "width": 0.45},
        textprops={"fontsize": 12, "color": "white", "fontweight": "bold"},
    )
    for at in autotexts:
        at.set_fontsize(12)
        at.set_fontweight("bold")
        at.set_color("white")

    # Legend with count next to each label
    legend_labels = [f"{lbl}  ({int(s):,} • {s/total*100:.1f}%)"
                     for lbl, s in zip(labels, sizes)]
    ax.legend(wedges, legend_labels,
              loc="center left", bbox_to_anchor=(1.05, 0.5),
              fontsize=11, frameon=False, labelcolor=_TEXT,
              handlelength=1.5, handleheight=1.5, borderaxespad=0)

    ax.set_title("Segment Dagilimi", fontsize=14, fontweight="bold",
                 color=_TEXT, pad=16)
    _apply_tight_layout(fig, pad=2.0, rect=[0.02, 0.02, 0.62, 0.98])


# ── Segmentation view charts ─────────────────────────────────

def segment_rfm_bar(seg_stats, fig: Figure):
    """Three stacked horizontal bar charts — one per RFM metric.

    Stacking vertically (one chart per metric) avoids the mixed-scale
    problem of a single grouped bar chart (recency in days vs monetary
    in currency can differ by 2-3 orders of magnitude).
    """
    fig.clear()
    fig.set_facecolor("white")

    # Preserve segment order so all three subplots align consistently
    df = seg_stats.copy()
    df["_order"] = df["segment_label"].apply(
        lambda s: _SEGMENT_ORDER.index(s) if s in _SEGMENT_ORDER else 99
    )
    df = df.sort_values("_order").reset_index(drop=True)

    labels = df["segment_label"].tolist()
    colors = [SEGMENT_COLORS.get(l, _TEXT_SEC) for l in labels]
    y = np.arange(len(labels))

    metrics = [
        ("avg_recency", "Ortalama Recency (gun)", "{:.0f} gun"),
        ("avg_frequency", "Ortalama Frequency (siparis)", "{:.1f}"),
        ("avg_monetary", "Ortalama Monetary (TL)", "{:,.0f}"),
    ]

    for i, (col, title, fmt) in enumerate(metrics):
        ax = fig.add_subplot(3, 1, i + 1)
        _style_ax(ax)
        ax.set_facecolor("white")

        values = df[col].values
        bars = ax.barh(y, values, color=colors, alpha=0.88,
                       edgecolor="white", linewidth=1.2, height=0.62)

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=10, color=_TEXT)
        ax.tick_params(axis="x", labelsize=10, colors=_TEXT_SEC)
        ax.set_title(title, fontsize=12, fontweight="bold",
                     color=_TEXT, pad=8, loc="left")
        ax.grid(axis="x", alpha=0.3, color=_GRID, linewidth=0.5)
        ax.set_axisbelow(True)

        # Room for value labels on the right
        vmax = float(max(values)) if len(values) else 1.0
        ax.set_xlim(0, vmax * 1.18 if vmax > 0 else 1.0)

        for bar, v in zip(bars, values):
            ax.text(v + vmax * 0.015, bar.get_y() + bar.get_height() / 2,
                    fmt.format(v), ha="left", va="center",
                    fontsize=10, fontweight="bold", color=_TEXT)

    fig.suptitle("Segment Bazli Ortalama RFM", fontsize=14,
                 fontweight="bold", color=_TEXT, y=0.995, x=0.02, ha="left")
    _apply_tight_layout(fig, pad=2.0, h_pad=2.8, rect=[0, 0, 1, 0.955])


def segment_scatter(frequency, monetary, segment_labels, fig: Figure):
    """Frequency vs Monetary scatter colored by segment (log scale)."""
    fig.clear()
    fig.set_facecolor("white")
    ax = fig.add_subplot(111)
    _style_ax(ax)
    ax.set_facecolor("white")
    ax.tick_params(labelsize=10, colors=_TEXT_SEC)

    unique_labels = sorted(
        set(segment_labels),
        key=lambda s: _SEGMENT_ORDER.index(s) if s in _SEGMENT_ORDER else 99,
    )
    for label in unique_labels:
        mask = [s == label for s in segment_labels]
        freq = np.array([f for f, m in zip(frequency, mask) if m])
        mon = np.array([mo for mo, m in zip(monetary, mask) if m])
        color = SEGMENT_COLORS.get(label, _TEXT_SEC)
        ax.scatter(freq, mon, c=color, label=label, alpha=0.55, s=28,
                   edgecolors="white", linewidths=0.4)

    ax.set_title("Frequency vs Monetary (Segment Bazinda)", fontsize=14,
                 fontweight="bold", color=_TEXT, pad=14, loc="left")
    ax.set_xlabel("Frequency (log olcek)", fontsize=11, color=_TEXT_SEC,
                  labelpad=8)
    ax.set_ylabel("Monetary (log olcek)", fontsize=11, color=_TEXT_SEC,
                  labelpad=8)
    ax.set_yscale("symlog", linthresh=100)
    ax.set_xscale("symlog", linthresh=5)

    # Legend outside the plot on the right so points don't get covered
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=11, frameon=False, labelcolor=_TEXT,
              markerscale=2.0, handletextpad=0.8, borderaxespad=0)

    ax.grid(alpha=0.3, color=_GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    _apply_tight_layout(fig, pad=2.0, rect=[0.01, 0.01, 0.82, 0.99])


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
