import base64
import html as html_module
import math
from collections import defaultdict

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# ================= MINIMIZATION LOGIC ================= #

def get_partitions(states, alphabet, final_states, trans_dict):
    final_set = set(final_states)
    non_final = sorted([s for s in states if s not in final_set])
    final = sorted([s for s in final_states])

    partitions = []
    if non_final:
        partitions.append(tuple(non_final))
    if final:
        partitions.append(tuple(final))

    history = [list(partitions)]

    while True:
        new_partitions = []

        for group in partitions:
            if len(group) <= 1:
                new_partitions.append(group)
                continue

            split_map = {}

            for state in group:
                behavior = []
                for char in alphabet:
                    dest = trans_dict.get((state, char))
                    dest_idx = -1
                    for idx, p in enumerate(partitions):
                        if dest in p:
                            dest_idx = idx
                            break
                    behavior.append(dest_idx)

                key = tuple(behavior)
                if key not in split_map:
                    split_map[key] = []
                split_map[key].append(state)

            for subgroup in split_map.values():
                new_partitions.append(tuple(sorted(subgroup)))

        new_partitions = sorted(new_partitions)

        if new_partitions == partitions:
            history.append(list(partitions))
            break

        partitions = new_partitions
        history.append(list(partitions))

    return history


def parse_transitions(t_raw):
    trans_dict = {}
    parts = t_raw.split(",")
    temp = []
    current = ""

    for p in parts:
        current += p
        if ")" in p:
            temp.append(current.strip())
            current = ""
        else:
            current += ","

    for unit in temp:
        if "->" not in unit:
            continue
        try:
            left, target = unit.split("->")
            left = left.replace("(", "").replace(")", "")
            s, char = left.split(",")
            trans_dict[(s.strip(), char.strip())] = target.strip()
        except Exception:
            continue

    return trans_dict


def _svg_text(s: str) -> str:
    return html_module.escape(str(s), quote=True)


def render_partition_refinement_svg(
    partition,
    trans_dict: dict,
    alphabet: list,
    start_state: str,
    final_set: set,
    step_idx: int,
) -> str:
    """One SVG: equivalence blocks (rounded regions), transitions, start, accepting doubles."""
    r = 18
    pad = 11
    gap_b = 22
    gap_s = 10
    y = 68.0
    x_cur = 20.0

    positions = {}
    rects = []

    for block in partition:
        states = sorted(block)
        n = len(states)
        inner_w = max(0, n * (2 * r + gap_s) - gap_s)
        bw = inner_w + 2 * pad
        bh = 2 * (r + pad)
        rects.append((x_cur, y - r - pad, bw, bh))
        for i, st in enumerate(states):
            cx = x_cur + pad + r + i * (2 * r + gap_s)
            positions[st] = (cx, y)
        x_cur += bw + gap_b

    total_w = max(120, int(math.ceil(x_cur + 14)))
    total_h = 118
    sym_order = {c: i for i, c in enumerate(alphabet)}

    pair_syms = defaultdict(list)
    for (src, sym), dst in trans_dict.items():
        if src in positions and dst in positions:
            pair_syms[(src, dst)].append(sym)
    for k in pair_syms:
        pair_syms[k].sort(key=lambda s: sym_order.get(s, 99))

    def shorten(x1, y1, x2, y2, rr):
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-6:
            return x1, y1, x2, y2
        ux, uy = dx / L, dy / L
        return x1 + ux * rr, y1 + uy * rr, x2 - ux * rr, y2 - uy * rr

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" '
        f'preserveAspectRatio="xMidYMid meet" width="{total_w}" height="{total_h}" '
        f'style="width:100%;height:auto;display:block" role="img" '
        f'aria-label="Partition refinement step {step_idx}">',
        "<defs>",
        f'<marker id="marr{step_idx}" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">',
        '<polygon points="0 0, 6 3, 0 6" fill="#7a5a6a"/>',
        "</marker>",
        "</defs>",
    ]

    for rx, ry, rw, rh in rects:
        parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" rx="10" ry="10" '
            f'fill="#faf0f4" stroke="rgba(122,82,98,0.28)" stroke-width="1.2"/>'
        )

    for (src, dst), syms in sorted(pair_syms.items()):
        x1, y1 = positions[src]
        x2, y2 = positions[dst]
        lab = _svg_text(", ".join(syms))
        if src == dst:
            cx, cy = x1, y1
            path_d = (
                f"M {cx - r * 0.55:.1f} {cy - r:.1f} Q {cx:.1f} {cy - r - 26:.1f} "
                f"{cx + r * 0.55:.1f} {cy - r:.1f}"
            )
            parts.append(
                f'<path d="{path_d}" fill="none" stroke="#7a5a6a" stroke-width="1.3" '
                f'marker-end="url(#marr{step_idx})"/>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{cy - r - 30:.1f}" text-anchor="middle" '
                f'font-family="ui-monospace,system-ui,monospace" font-size="10" fill="#5c4d56">{lab}</text>'
            )
        else:
            sx1, sy1, sx2, sy2 = shorten(x1, y1, x2, y2, r + 1.5)
            parts.append(
                f'<line x1="{sx1:.1f}" y1="{sy1:.1f}" x2="{sx2:.1f}" y2="{sy2:.1f}" '
                f'stroke="#7a5a6a" stroke-width="1.3" marker-end="url(#marr{step_idx})"/>'
            )
            mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2 - 9
            parts.append(
                f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" '
                f'font-family="ui-monospace,system-ui,monospace" font-size="10" fill="#5c4d56">{lab}</text>'
            )

    if start_state in positions:
        sx, sy = positions[start_state]
        sx1 = max(6.0, sx - r - 36.0)
        parts.append(
            f'<line x1="{sx1:.1f}" y1="{sy:.1f}" x2="{sx - r - 2:.1f}" y2="{sy:.1f}" '
            f'stroke="#7a5a6a" stroke-width="1.3" marker-end="url(#marr{step_idx})"/>'
        )
        parts.append(
            f'<text x="{sx1 - 2:.1f}" y="{sy - 10:.1f}" text-anchor="end" '
            f'font-family="system-ui,sans-serif" font-size="9" fill="#8a7a84">start</text>'
        )

    for st in sorted(positions.keys()):
        cx, cy = positions[st]
        if st in final_set:
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#fff" '
                f'stroke="#7a5a6a" stroke-width="1.5"/>'
            )
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 6}" fill="#fff" '
                f'stroke="#7a5a6a" stroke-width="1.5"/>'
            )
        else:
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#fff" '
                f'stroke="#7a5a6a" stroke-width="1.5"/>'
            )
        parts.append(
            f'<text x="{cx:.1f}" y="{cy + 4:.1f}" text-anchor="middle" '
            f'font-family="ui-monospace,system-ui,monospace" font-size="11" font-weight="600" '
            f'fill="#2a2328">{_svg_text(st)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _embed_svg_data_uri(svg_xml: str, alt: str) -> str:
    """Inline SVG via data URI so diagrams show when HTML is injected with innerHTML."""
    b64 = base64.b64encode(svg_xml.encode("utf-8")).decode("ascii")
    safe_alt = html_module.escape(alt, quote=True)
    return (
        f'<img src="data:image/svg+xml;base64,{b64}" alt="{safe_alt}" '
        f'style="width:100%;max-width:100%;height:auto;display:block;min-height:112px;vertical-align:top;" />'
    )


def _block_containing(state, partition):
    for block in partition:
        if state in block:
            return block
    return None


def render_result(
    states_list,
    history,
    start_state: str,
    trans_dict: dict,
    alphabet: list,
    final_list: list,
):
    final_partition = history[-2]
    minimal_count = len(final_partition)
    original_count = len(states_list)
    merged = original_count - minimal_count
    final_set = set(final_list)

    start_block = _block_containing(start_state, final_partition)
    if start_block is None:
        raise ValueError(
            f"Start state {start_state!r} does not appear in the refined partition "
            "(check that it is listed under States)."
        )
    start_class = "{" + ", ".join(sorted(start_block)) + "}"
    safe_start = html_module.escape(start_state)
    safe_class = html_module.escape(start_class)

    html = f"""
    <div style="background:#fff;border:1px solid rgba(122,82,98,0.14);border-radius:13px;padding:0.9rem 1.1rem;margin-bottom:1.1rem;box-shadow:0 1px 2px rgba(90,60,75,0.04);">
      <p style="font-size:13px;color:#2a2328;line-height:1.6;">
        <span style="color:#6e5c67;">Start state</span>
        <code style="font-family:ui-monospace,monospace;background:#f3eaee;padding:2px 7px;border-radius:4px;margin:0 5px 0 4px;">{safe_start}</code>
        <span style="color:#8a7a84;">&rarr;</span>
        <span style="color:#6e5c67;margin-left:6px;">Minimal DFA start (equivalence class)</span>
        <code style="font-family:ui-monospace,monospace;background:#f3eaee;padding:2px 7px;border-radius:4px;margin-left:6px;">{safe_class}</code>
      </p>
    </div>"""

    html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:13px;margin-bottom:1.1rem;">'
    for label, val in [("Steps shown", len(history)), ("Original states", original_count), ("Minimal states", minimal_count)]:
        html += f"""
        <div style="background:#f3eaee;border:1px solid rgba(122,82,98,0.1);border-radius:9px;padding:13px 14px;">
          <div style="font-size:12px;color:#6e5c67;margin-bottom:4px;">{label}</div>
          <div style="font-size:22px;font-weight:600;color:#2a2328;">{val}</div>
        </div>"""
    html += "</div>"

    html += """
    <div style="background:#fff;border:1px solid rgba(122,82,98,0.14);border-radius:13px;padding:1.25rem 1.5rem;margin-bottom:1.1rem;box-shadow:0 1px 2px rgba(90,60,75,0.04);">
      <p style="font-size:11px;font-weight:600;color:#6e5c67;text-transform:uppercase;letter-spacing:.06em;margin-bottom:0.35rem;">Partition refinement</p>
      <p style="font-size:12px;color:#8a7a84;margin-bottom:1rem;line-height:1.45;">Each diagram shows equivalence blocks (shaded regions), your transitions, start arrow, and double circles for accepting states.</p>
    """

    for i, step in enumerate(history):
        is_last = i == len(history) - 1
        groups_display = "   ".join(
            [
                "{" + ", ".join(html_module.escape(str(x)) for x in sorted(t)) + "}"
                for t in step
            ]
        )
        if is_last:
            stable_badge = (
                f'<span style="display:inline-block;margin-left:8px;font-size:11px;'
                f'padding:2px 9px;border-radius:5px;background:#e8f0ea;color:#2d5a3d;">'
                f"stable &mdash; P{i} = P{i - 1}</span>"
            )
        else:
            stable_badge = ""

        step_svg_xml = render_partition_refinement_svg(
            step, trans_dict, alphabet, start_state, final_set, i
        )
        step_diagram = _embed_svg_data_uri(step_svg_xml, f"Partition P{i} diagram")
        border_bottom = "none" if is_last else "1px solid rgba(122,82,98,0.1)"
        html += f"""
        <div style="margin-bottom:1.05rem;padding-bottom:1rem;border-bottom:{border_bottom};">
          <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:0.5rem;">
            <span style="font-family:ui-monospace,monospace;font-size:13px;font-weight:600;color:#8a7a84;">P{i}</span>
            <span style="font-family:ui-monospace,monospace;font-size:13px;color:#2a2328;">{groups_display}{stable_badge}</span>
          </div>
          <div style="background:linear-gradient(180deg,#fefbfc 0%,#faf0f3 100%);border:1px solid rgba(122,82,98,0.12);border-radius:10px;padding:0.5rem 0.35rem;overflow-x:auto;min-height:120px;">
            {step_diagram}
          </div>
        </div>"""

    html += "</div>"

    if merged > 0:
        html += f'<p style="font-size:14px;color:#6e5c67;line-height:1.5;">{merged} state{"s" if merged > 1 else ""} merged &mdash; equivalent under bisimulation.</p>'
    else:
        html += '<p style="font-size:14px;color:#6e5c67;line-height:1.5;">DFA is already minimal &mdash; no states can be merged.</p>'

    return html


# ================= HTML PAGE ================= #

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DFA Minimizer</title>
  <style>
    html { font-size: 90%; }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: linear-gradient(180deg, #faf5f7 0%, #f5eef2 100%);
      color: #2a2328;
      min-height: 100vh;
      padding: 2.25rem 1.125rem;
      font-size: 1rem;
      line-height: 1.5;
    }
    .container { max-width: 684px; margin: 0 auto; }
    h1 {
      font-size: 1.575rem;
      font-weight: 600;
      letter-spacing: -0.02em;
      margin-bottom: 1.575rem;
      color: #2a2328;
    }
    .card {
      background: #fff;
      border: 1px solid rgba(122, 82, 98, 0.14);
      border-radius: 13px;
      padding: 1.575rem 1.8rem;
      margin-bottom: 1.125rem;
      box-shadow: 0 1px 3px rgba(90, 60, 75, 0.06);
    }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
    .field { margin-bottom: 14px; }
    label { display: block; font-size: 0.9375rem; font-weight: 500; color: #5c4d56; margin-bottom: 5px; }
    input[type="text"] {
      width: 100%;
      padding: 10px 13px;
      font-size: 1rem;
      border: 1px solid rgba(122, 82, 98, 0.22);
      border-radius: 9px;
      outline: none;
      background: #fff;
      color: #2a2328;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    input[type="text"]:focus {
      border-color: #8b6a7a;
      box-shadow: 0 0 0 3px rgba(139, 106, 122, 0.16);
    }
    .hint { font-size: 0.875rem; color: #8a7a84; margin-top: 5px; line-height: 1.45; }
    code { font-family: ui-monospace, monospace; background: #f3eaee; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; color: #4a3d44; }
    button[type="submit"] {
      margin-top: 1.2rem;
      padding: 10px 25px;
      font-size: 1rem;
      font-weight: 600;
      background: #6b4d5c;
      color: #fff;
      border: none;
      border-radius: 9px;
      cursor: pointer;
      transition: background 0.15s, transform 0.1s;
    }
    button[type="submit"]:hover { background: #5a4050; }
    button[type="submit"]:active { transform: scale(0.99); }
    #result { max-width: 684px; margin-top: 0.45rem; }
    .footer-id {
      text-align: center;
      margin-top: 2.25rem;
      padding-top: 0.9rem;
      font-size: 0.81rem;
      color: #8a7a84;
      letter-spacing: 0.02em;
    }
  </style>
</head>
<body>
<div class="container">
  <h1>DFA minimizer</h1>

  <div class="card">
    <form id="dfa-form">
      <div class="grid-2">
        <div class="field">
          <label>States</label>
          <input type="text" id="states" placeholder="A, B, C, D" />
        </div>
        <div class="field">
          <label>Alphabet</label>
          <input type="text" id="alphabet" placeholder="0, 1" />
        </div>
      </div>
      <div class="grid-2">
        <div class="field">
          <label>Start state</label>
          <input type="text" id="start_state" name="start_state" placeholder="A" autocomplete="off" />
          <p class="hint">Must match one of the state names exactly (e.g. <code>A</code>).</p>
        </div>
        <div class="field">
          <label>Final states</label>
          <input type="text" id="final" placeholder="C, D" />
        </div>
      </div>
      <div class="field">
        <label>Transitions</label>
        <input type="text" id="transitions" placeholder="(A,0)->B, (A,1)->C, ..." />
        <p class="hint">Format: <code>(state,symbol)->dest</code> separated by commas</p>
      </div>
      <button type="submit">Minimize &rarr;</button>
    </form>
  </div>
  <div id="result"></div>
  <p class="footer-id">SNEHA-2024UCA1890</p>
</div>
<script>
  document.getElementById('dfa-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const body = new URLSearchParams({
      states: document.getElementById('states').value,
      alphabet: document.getElementById('alphabet').value,
      start_state: document.getElementById('start_state').value,
      final: document.getElementById('final').value,
      transitions: document.getElementById('transitions').value,
    });
    const res = await fetch('/minimize', { method: 'POST', body });
    document.getElementById('result').innerHTML = await res.text();
  });
</script>
</body>
</html>"""


# ================= ROUTES ================= #

_HTML_UTF8 = "text/html; charset=utf-8"


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content=HTML_PAGE, media_type=_HTML_UTF8)


@app.post("/minimize", response_class=HTMLResponse)
def minimize(
    states: str = Form(...),
    alphabet: str = Form(...),
    start_state: str = Form(...),
    final: str = Form(""),
    transitions: str = Form(...)
):
    try:
        states_list = [s.strip() for s in states.split(",") if s.strip()]
        alpha_list = [a.strip() for a in alphabet.split(",") if a.strip()]
        final_list = [f.strip() for f in final.split(",") if f.strip()]
        start = start_state.strip()

        if not start:
            raise ValueError("Start state is required.")
        if start not in states_list:
            raise ValueError(
                f"Start state {start!r} must be one of the listed states: {', '.join(states_list)}."
            )

        trans_dict = parse_transitions(transitions)
        history = get_partitions(states_list, alpha_list, final_list, trans_dict)

        return HTMLResponse(
            content=render_result(
                states_list, history, start, trans_dict, alpha_list, final_list
            ),
            media_type=_HTML_UTF8,
        )

    except Exception as e:
        return HTMLResponse(
            content=(
                f'<div style="background:#fdf2f4;border:1px solid #e8b4bc;border-radius:9px;'
                f'padding:13px 16px;font-size:14px;color:#8b2c3a;line-height:1.5;">'
                f"Error: {html_module.escape(str(e))}</div>"
            ),
            media_type=_HTML_UTF8,
        )