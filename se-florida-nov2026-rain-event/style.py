"""Stand-in for the figure-style helpers used in the original session.

The session used a platform plotting helper (apply_figure_style, panel_letter) that is not
public. This file reproduces only what the notebooks call, so the figure cells run; fonts and
spacing may differ slightly from the saved figures in results/figures/.
"""
import matplotlib as mpl


def apply_figure_style(sizes=(8, 7, 6)):
    base, small, tick = sizes
    mpl.rcParams.update({
        "font.size": base, "axes.titlesize": base, "axes.labelsize": base,
        "legend.fontsize": small, "xtick.labelsize": tick, "ytick.labelsize": tick,
        "axes.spines.top": False, "axes.spines.right": False,
        "savefig.bbox": "tight", "figure.dpi": 100,
    })


def panel_letter(ax, letter, case="lower", dx=-0.08, dy=1.04):
    t = letter.lower() if case == "lower" else letter.upper()
    ax.text(dx, dy, t, transform=ax.transAxes, fontsize=10, fontweight="bold",
            va="bottom", ha="right")
