"""Minimal stand-in for the figure style used during the analysis session.
The original session used a platform style helper; this reproduces its main settings
(open frame, readable font sizes, no top/right spines) so the notebooks run unchanged."""
import matplotlib as mpl

def apply_figure_style(*, frame="open", font=None, sizes=None, **kwargs):
    s = dict(base=10, small=8.5, title=11)
    if sizes: s.update(sizes)
    mpl.rcParams.update({
        "font.size": s["base"], "axes.titlesize": s["title"], "axes.labelsize": s["base"],
        "xtick.labelsize": s["small"], "ytick.labelsize": s["small"], "legend.fontsize": s["small"],
        "axes.spines.top": frame != "open", "axes.spines.right": frame != "open",
        "savefig.dpi": 200, "savefig.bbox": "tight", "figure.dpi": 110,
    })
    if font: mpl.rcParams["font.family"] = font
