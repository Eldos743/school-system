"""Небольшие SVG-графики, рисуются на сервере (без JS-библиотек).

Цвета задаются CSS-классами, поэтому графики следуют светлой/тёмной теме.
"""
from markupsafe import Markup, escape


def _fmt(v, fmt):
    return fmt.format(v)


def line_chart(labels, series, y_min, y_max, ticks, fmt="{:.0f}", width=560, height=210, target=None):
    """series: список dict(name, values, cls). values может содержать None."""
    pl, pr, pt, pb = 40, 16, 14, 28
    w, h = width - pl - pr, height - pt - pb
    n = len(labels)

    def x(i):
        return pl + (w * i / (n - 1) if n > 1 else w / 2)

    def y(v):
        return pt + h - (v - y_min) / (y_max - y_min) * h

    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" preserveAspectRatio="xMidYMid meet">']
    for t in ticks:
        out.append(f'<line class="grid" x1="{pl}" x2="{pl + w}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>')
        out.append(f'<text class="tick" x="{pl - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{_fmt(t, fmt)}</text>')
    if target is not None:
        tv, tl = target
        out.append(f'<line class="target" x1="{pl}" x2="{pl + w}" y1="{y(tv):.1f}" y2="{y(tv):.1f}"/>')
        out.append(f'<text class="tick target-l" x="{pl + w}" y="{y(tv) - 5:.1f}" text-anchor="end">{escape(tl)}</text>')
    for i, lab in enumerate(labels):
        out.append(f'<text class="tick" x="{x(i):.1f}" y="{height - 8}" text-anchor="middle">{escape(lab)}</text>')
    for s in series:
        pts = [(x(i), y(v), v) for i, v in enumerate(s["values"]) if v is not None]
        if not pts:
            continue
        cls = s.get("cls", "s1")
        if s.get("area") and len(pts) > 1:
            d = f"M{pts[0][0]:.1f},{pt + h} " + " ".join(f"L{a:.1f},{b:.1f}" for a, b, _ in pts) + f" L{pts[-1][0]:.1f},{pt + h} Z"
            out.append(f'<path class="area {cls}" d="{d}"/>')
        d = " ".join(("M" if j == 0 else "L") + f"{a:.1f},{b:.1f}" for j, (a, b, _) in enumerate(pts))
        out.append(f'<path class="line {cls}" d="{d}"/>')
        for j, (a, b, v) in enumerate(pts):
            last = j == len(pts) - 1
            out.append(f'<circle class="dot {cls}{" end" if last else ""}" cx="{a:.1f}" cy="{b:.1f}" r="{4.5 if last else 3}"><title>{escape(s.get("name", ""))}: {_fmt(v, fmt)}</title></circle>')
            if last and s.get("label_end", True):
                out.append(f'<text class="val {cls}" x="{a - 8:.1f}" y="{b - 9:.1f}" text-anchor="end">{_fmt(v, fmt)}</text>')
    out.append("</svg>")
    return Markup("".join(out))


def column_chart(labels, values, y_max, ticks, fmt="{:.0f}", width=560, height=190, highlight=None, cls="s1"):
    pl, pr, pt, pb = 40, 10, 14, 28
    w, h = width - pl - pr, height - pt - pb
    n = len(values)
    step = w / max(n, 1)
    bw = step * 0.62

    def y(v):
        return pt + h - v / y_max * h

    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" preserveAspectRatio="xMidYMid meet">']
    for t in ticks:
        out.append(f'<line class="grid" x1="{pl}" x2="{pl + w}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>')
        out.append(f'<text class="tick" x="{pl - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{_fmt(t, fmt)}</text>')
    for i, (lab, v) in enumerate(zip(labels, values)):
        x0 = pl + step * i + (step - bw) / 2
        hv = max(v, 0) / y_max * h
        hot = highlight is not None and highlight(v)
        out.append(f'<rect class="bar {cls}{" hot" if hot else ""}" x="{x0:.1f}" y="{pt + h - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" rx="2"><title>{escape(lab)}: {_fmt(v, fmt)}</title></rect>')
        out.append(f'<text class="tick" x="{x0 + bw / 2:.1f}" y="{height - 8}" text-anchor="middle">{escape(lab)}</text>')
    out.append("</svg>")
    return Markup("".join(out))


def spark(values, lo, hi, width=88, height=26, cls="s1"):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return Markup("")
    n = len(vals)
    pad = 3

    def x(i):
        return pad + (width - 2 * pad) * i / (n - 1)

    def y(v):
        span = (hi - lo) or 1
        return height - pad - (v - lo) / span * (height - 2 * pad)

    d = " ".join(("M" if i == 0 else "L") + f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
    return Markup(
        f'<svg class="spark" width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-hidden="true">'
        f'<path class="line {cls}" d="{d}"/><circle class="dot {cls} end" cx="{x(n - 1):.1f}" cy="{y(vals[-1]):.1f}" r="2.8"/></svg>')
