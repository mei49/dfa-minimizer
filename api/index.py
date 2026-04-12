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


def render_result(states_list, history):
    final_partition = history[-2]
    minimal_count = len(final_partition)
    original_count = len(states_list)
    merged = original_count - minimal_count

    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:1.25rem;">'
    for label, val in [("Steps shown", len(history)), ("Original states", original_count), ("Minimal states", minimal_count)]:
        html += f"""
        <div style="background:#f3eaee;border:1px solid rgba(122,82,98,0.1);border-radius:10px;padding:14px 16px;">
          <div style="font-size:13px;color:#6e5c67;margin-bottom:4px;">{label}</div>
          <div style="font-size:24px;font-weight:600;color:#2a2328;">{val}</div>
        </div>"""
    html += "</div>"

    html += """
    <div style="background:#fff;border:1px solid rgba(122,82,98,0.14);border-radius:14px;padding:1.4rem 1.65rem;margin-bottom:1.25rem;box-shadow:0 1px 2px rgba(90,60,75,0.04);">
      <p style="font-size:12px;font-weight:600;color:#6e5c67;text-transform:uppercase;letter-spacing:.06em;margin-bottom:1.1rem;">Partition refinement</p>
    """

    for i, step in enumerate(history):
        is_last = (i == len(history) - 1)
        groups = "   ".join(["{" + ", ".join(g) + "}" for g in step])
        border = "" if is_last else "border-bottom:1px solid rgba(122,82,98,0.1);"

        if is_last:
            stable_badge = (
                f'<span style="display:inline-block;margin-left:10px;font-size:12px;'
                f'padding:3px 10px;border-radius:6px;background:#e8f0ea;color:#2d5a3d;">'
                f'stable — P{i} = P{i-1}</span>'
            )
        else:
            stable_badge = ""

        html += f"""
        <div style="display:flex;align-items:flex-start;gap:16px;padding:12px 0;{border}">
          <span style="font-family:ui-monospace,monospace;font-size:14px;font-weight:600;color:#8a7a84;min-width:34px;padding-top:2px;">P{i}</span>
          <span style="font-family:ui-monospace,monospace;font-size:15px;flex:1;color:#2a2328;">{groups}{stable_badge}</span>
        </div>"""

    html += "</div>"

    if merged > 0:
        html += f'<p style="font-size:15px;color:#6e5c67;line-height:1.5;">{merged} state{"s" if merged > 1 else ""} merged — equivalent under bisimulation.</p>'
    else:
        html += '<p style="font-size:15px;color:#6e5c67;line-height:1.5;">DFA is already minimal — no states can be merged.</p>'

    return html


# ================= HTML PAGE ================= #

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DFA Minimizer</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: linear-gradient(180deg, #faf5f7 0%, #f5eef2 100%);
      color: #2a2328;
      min-height: 100vh;
      padding: 2.5rem 1.25rem;
      font-size: 16px;
      line-height: 1.5;
    }
    .container { max-width: 760px; margin: 0 auto; }
    h1 {
      font-size: 1.75rem;
      font-weight: 600;
      letter-spacing: -0.02em;
      margin-bottom: 1.75rem;
      color: #2a2328;
    }
    .card {
      background: #fff;
      border: 1px solid rgba(122, 82, 98, 0.14);
      border-radius: 14px;
      padding: 1.75rem 2rem;
      margin-bottom: 1.25rem;
      box-shadow: 0 1px 3px rgba(90, 60, 75, 0.06);
    }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
    .field { margin-bottom: 16px; }
    label { display: block; font-size: 0.9375rem; font-weight: 500; color: #5c4d56; margin-bottom: 6px; }
    input[type="text"] {
      width: 100%;
      padding: 11px 14px;
      font-size: 1rem;
      border: 1px solid rgba(122, 82, 98, 0.22);
      border-radius: 10px;
      outline: none;
      background: #fff;
      color: #2a2328;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    input[type="text"]:focus {
      border-color: #8b6a7a;
      box-shadow: 0 0 0 3px rgba(139, 106, 122, 0.18);
    }
    .hint { font-size: 0.875rem; color: #8a7a84; margin-top: 6px; line-height: 1.45; }
    code { font-family: ui-monospace, monospace; background: #f3eaee; padding: 2px 7px; border-radius: 5px; font-size: 0.9em; color: #4a3d44; }
    button[type="submit"] {
      margin-top: 1.35rem;
      padding: 11px 28px;
      font-size: 1rem;
      font-weight: 600;
      background: #6b4d5c;
      color: #fff;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      transition: background 0.15s, transform 0.1s;
    }
    button[type="submit"]:hover { background: #5a4050; }
    button[type="submit"]:active { transform: scale(0.99); }
    #result { max-width: 760px; margin-top: 0.5rem; }
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
      <div class="field">
        <label>Final states</label>
        <input type="text" id="final" placeholder="C, D" />
      </div>
      <div class="field">
        <label>Transitions</label>
        <input type="text" id="transitions" placeholder="(A,0)->B, (A,1)->C, ..." />
        <p class="hint">Format: <code>(state,symbol)->dest</code> separated by commas</p>
      </div>
      <button type="submit">Minimize →</button>
    </form>
  </div>
  <div id="result"></div>
</div>
<script>
  document.getElementById('dfa-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const body = new URLSearchParams({
      states: document.getElementById('states').value,
      alphabet: document.getElementById('alphabet').value,
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

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


@app.post("/minimize", response_class=HTMLResponse)
def minimize(
    states: str = Form(...),
    alphabet: str = Form(...),
    final: str = Form(""),
    transitions: str = Form(...)
):
    try:
        states_list = [s.strip() for s in states.split(",") if s.strip()]
        alpha_list = [a.strip() for a in alphabet.split(",") if a.strip()]
        final_list = [f.strip() for f in final.split(",") if f.strip()]

        trans_dict = parse_transitions(transitions)
        history = get_partitions(states_list, alpha_list, final_list, trans_dict)

        return render_result(states_list, history)

    except Exception as e:
        return (
            f'<div style="background:#fdf2f4;border:1px solid #e8b4bc;border-radius:10px;'
            f'padding:14px 18px;font-size:15px;color:#8b2c3a;line-height:1.5;">Error: {str(e)}</div>'
        )