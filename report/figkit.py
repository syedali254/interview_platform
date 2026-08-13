"""Layout engine for the dissertation figures.

Written after the first attempt produced figures whose titles collided with the
first row of nodes and whose labels ran past the edges of their boxes. Three
rules are enforced here rather than left to each figure to remember:

  1. The title and subtitle own a reserved band. Content cannot be drawn into
     it — `Canvas.top` is the highest y a figure may use, and it already
     accounts for a subtitle that wraps onto a second line.
  2. Text inside a node is wrapped to the node's width. Box height grows to fit
     the wrapped result, so a long label makes a taller box rather than
     overflowing a fixed one.
  3. Every node registers its bounding box. `Canvas.check()` reports anything
     that leaves the canvas or overlaps a sibling, so a broken layout fails
     loudly at build time instead of quietly in the document.
"""

from __future__ import annotations

import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

# ── Visual grammar ───────────────────────────────────────────────────────
INK = "#1b2733"
MUTED = "#5a6b7b"
RULE = "#c8d2dc"
PAPER = "#ffffff"

PHASE1 = "#1f4e79"   # pre-interview
PHASE2 = "#1e6b4f"   # live interview
PHASE3 = "#9a4415"   # assessment
PHASE4 = "#4c3a8c"   # reporting
NEUTRAL = "#44576a"
ACCENT = "#b4530f"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "path.simplify": False,
})


def tint(hex_colour: str, amount: float):
    """Blend toward white. Alpha would dim the border along with the fill."""
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r + (1 - r) * (1 - amount),
            g + (1 - g) * (1 - amount),
            b + (1 - b) * (1 - amount))


class Canvas:
    """A figure with a reserved header and collision checking."""

    def __init__(self, width_in: float, height_in: float, number: int,
                 title: str, subtitle: str = ""):
        self.w = width_in
        self.h = height_in
        self.fig, self.ax = plt.subplots(figsize=(width_in, height_in))
        self.ymax = 100.0 * height_in / width_in
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, self.ymax)
        self.ax.axis("off")
        self.boxes: list[tuple[float, float, float, float, str]] = []
        self.name = f"Figure {number}"
        self._cached_renderer = None

        # ── Header band ──────────────────────────────────────────────────
        title_size = 11.5
        y = self.ymax - 1.2
        self.ax.text(0, y, f"Figure {number}   {title}", ha="left", va="top",
                     fontsize=title_size, color=INK, fontweight="bold")
        y -= self._units_for_lines(1, title_size) + 1.4

        if subtitle:
            sub_size = 7.8
            wrapped = self.wrap(subtitle, 100, sub_size)
            self.ax.text(0, y, wrapped, ha="left", va="top",
                         fontsize=sub_size, color=MUTED, linespacing=1.45)
            y -= self._units_for_lines(wrapped.count("\n") + 1, sub_size) + 1.2

        self.top = y - 1.0          # highest y content may occupy
        self.footer_y = 1.2

    # ── Measurement ──────────────────────────────────────────────────────

    def _pt_to_units(self, points: float) -> float:
        """Convert a point measurement to y-axis units."""
        inches = points / 72.0
        return inches * (100.0 / self.w)

    def _units_for_lines(self, n_lines: int, fontsize: float) -> float:
        return n_lines * self._pt_to_units(fontsize * 1.45)

    def chars_per_width(self, width_units: float, fontsize: float) -> int:
        """How many average characters fit across `width_units` at `fontsize`.

        DejaVu Sans averages close to 0.53 em across mixed-case prose. The
        0.585 used here deliberately over-estimates, so wrapping errs toward a
        narrow line rather than letting a long word graze the box border.
        """
        inches = width_units * (self.w / 100.0)
        char_in = 0.585 * fontsize / 72.0
        return max(6, int(inches / char_in))

    def _wrap_at(self, text: str, chars: int) -> str:
        """Wrap at a character count, honouring newlines the caller wrote.

        Explicit breaks are deliberate structure — the kinds of key held in an
        index, or the score bands on a legend — so each is wrapped on its own
        rather than being flattened into a single paragraph.
        """
        lines = []
        for segment in text.split("\n"):
            if not segment.strip():
                lines.append("")
                continue
            lines.extend(textwrap.wrap(
                segment, width=max(4, chars), break_long_words=False,
                break_on_hyphens=False) or [segment])
        return "\n".join(lines) or text

    def _renderer(self):
        if self._cached_renderer is None:
            self.fig.canvas.draw()
            self._cached_renderer = self.fig.canvas.get_renderer()
        return self._cached_renderer

    def measure(self, line: str, fontsize: float, bold: bool = False) -> float:
        """Width of one rendered line, in x-axis units.

        Estimating from an average character width was the source of every
        overflowing label in the first version of these figures: proportional
        fonts vary far too much between 'illl' and 'WWWW' for a single factor
        to hold. This asks matplotlib what it actually drew.
        """
        if not line:
            return 0.0
        artist = self.ax.text(0, 0, line, fontsize=fontsize,
                              fontweight="bold" if bold else "normal")
        bbox = artist.get_window_extent(renderer=self._renderer())
        artist.remove()
        inv = self.ax.transData.inverted()
        (x0, _), (x1, _) = inv.transform([(bbox.x0, bbox.y0), (bbox.x1, bbox.y1)])
        return abs(x1 - x0)

    def wrap(self, text: str, width_units: float, fontsize: float,
             bold: bool = False) -> str:
        """Wrap so that no rendered line exceeds `width_units`.

        Starts from a character estimate, then measures and narrows until the
        widest line genuinely fits. Converges in two or three passes.
        """
        chars = self.chars_per_width(width_units, fontsize)
        wrapped = self._wrap_at(text, chars)
        for _ in range(12):
            widest = max((self.measure(ln, fontsize, bold)
                          for ln in wrapped.split("\n") if ln), default=0.0)
            if widest <= width_units or chars <= 5:
                return wrapped
            # Scale the character budget by how far over we are, minus one so
            # a pathological line cannot stall the loop.
            chars = max(5, int(chars * width_units / widest) - 1)
            wrapped = self._wrap_at(text, chars)
        return wrapped

    def text_height(self, text: str, width_units: float, fontsize: float) -> float:
        return self._units_for_lines(
            self.wrap(text, width_units, fontsize).count("\n") + 1, fontsize)

    # ── Primitives ───────────────────────────────────────────────────────

    def box(self, x, y, w, colour, title, subtitle=None, *,
            h=None, title_size=8.4, sub_size=7.0, pad=1.9, fill=0.09,
            lw=1.25, radius=1.2, align="center", label=None):
        """A rounded node, sized to its wrapped contents. (x, y) is the centre.

        The usable width depends on alignment: left-aligned text starts at a
        fixed inset from the left border, so it must still stop short of the
        right one. Both margins are subtracted rather than assumed symmetric.
        """
        margin = 1.9 if align == "center" else 2.2
        inner = w - 2 * margin
        t_wrapped = self.wrap(title, inner, title_size, bold=True)
        s_wrapped = self.wrap(subtitle, inner, sub_size) if subtitle else None

        t_h = self._units_for_lines(t_wrapped.count("\n") + 1, title_size)
        s_h = self._units_for_lines(s_wrapped.count("\n") + 1, sub_size) if s_wrapped else 0
        gap = 0.7 if s_wrapped else 0
        needed = t_h + gap + s_h + 2 * pad
        h = max(h or 0, needed)

        self.ax.add_patch(FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            linewidth=lw, edgecolor=colour, facecolor=tint(colour, fill), zorder=3))

        block = t_h + gap + s_h
        cursor = y + block / 2
        tx = x if align == "center" else x - w / 2 + margin
        ha = "center" if align == "center" else "left"

        self.ax.text(tx, cursor, t_wrapped, ha=ha, va="top", fontsize=title_size,
                     color=colour, fontweight="bold", zorder=4, linespacing=1.45)
        if s_wrapped:
            self.ax.text(tx, cursor - t_h - gap, s_wrapped, ha=ha, va="top",
                         fontsize=sub_size, color=MUTED, zorder=4, linespacing=1.45)

        self.boxes.append((x - w / 2, y - h / 2, w, h, label or title[:26]))
        return h

    def band(self, y, h, colour, label, x=0.5, w=99.0, label_size=7.0):
        """A phase swimlane. The label carries an opaque background and sits
        above every routed line, so a rail passing beneath it cannot strike
        through the text."""
        self.ax.add_patch(FancyBboxPatch(
            (x, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.1",
            linewidth=0, facecolor=tint(colour, 0.055), zorder=0))
        self.ax.text(x + 7.5, y + h / 2 + 1.0, label, ha="left", va="bottom",
                     fontsize=label_size, color=colour, fontweight="bold", zorder=6,
                     bbox=dict(boxstyle="round,pad=0.28", fc=PAPER, ec="none"))

    def arrow(self, start, end, colour=NEUTRAL, *, lw=1.15, rad=0.0,
              dashed=False, style="-|>"):
        self.ax.add_patch(FancyArrowPatch(
            start, end, arrowstyle=style, mutation_scale=9, linewidth=lw,
            color=colour, zorder=2, connectionstyle=f"arc3,rad={rad}",
            linestyle="--" if dashed else "-", shrinkA=1.5, shrinkB=1.5))

    def elbow(self, points, colour=NEUTRAL, *, lw=1.05, dashed=False):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.ax.plot(xs[:-1], ys[:-1], color=colour, linewidth=lw, zorder=2,
                     solid_capstyle="round", solid_joinstyle="round",
                     linestyle="--" if dashed else "-")
        self.ax.add_patch(FancyArrowPatch(
            points[-2], points[-1], arrowstyle="-|>", mutation_scale=9,
            linewidth=lw, color=colour, zorder=2,
            linestyle="--" if dashed else "-", shrinkA=0, shrinkB=1.5))

    def label(self, x, y, text, *, size=6.6, colour=MUTED, ha="center",
              va="center", width=None, bold=False, italic=False, boxed=True):
        if width:
            text = self.wrap(text, width, size)
        kw = dict(fc=PAPER, ec="none", pad=0.22) if boxed else None
        self.ax.text(x, y, text, ha=ha, va=va, fontsize=size, color=colour,
                     zorder=5, linespacing=1.4, fontweight="bold" if bold else "normal",
                     style="italic" if italic else "normal",
                     bbox=(dict(boxstyle="round", **kw) if boxed else None))

    def footer(self, text, size=6.8):
        self.ax.text(50, self.footer_y, self.wrap(text, 96, size), ha="center",
                     va="bottom", fontsize=size, color=MUTED, style="italic",
                     linespacing=1.45)

    # ── Validation ───────────────────────────────────────────────────────

    def check(self):
        problems = []
        for x, y, w, h, name in self.boxes:
            if x < -0.5 or x + w > 100.5:
                problems.append(f"{name!r} exceeds width ({x:.1f}..{x + w:.1f})")
            if y < -0.5:
                problems.append(f"{name!r} runs below the canvas (bottom {y:.1f})")
            if y + h > self.top + 0.6:
                problems.append(
                    f"{name!r} intrudes on the header (top {y + h:.1f} > {self.top:.1f})")
        for i, (x1, y1, w1, h1, n1) in enumerate(self.boxes):
            for x2, y2, w2, h2, n2 in self.boxes[i + 1:]:
                ox = min(x1 + w1, x2 + w2) - max(x1, x2)
                oy = min(y1 + h1, y2 + h2) - max(y1, y2)
                if ox > 0.6 and oy > 0.6:
                    problems.append(f"{n1!r} overlaps {n2!r}")
        return problems

    def save(self, path):
        issues = self.check()
        for issue in issues:
            safe = issue.encode("ascii", "replace").decode("ascii")
            print(f"      ! {self.name}: {safe}")
        self.fig.savefig(path, bbox_inches="tight", pad_inches=0.12,
                         facecolor=PAPER)
        plt.close(self.fig)
        return issues
