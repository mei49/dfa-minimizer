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
            # Append stable partition one more time to show Pn = Pn-1
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
    # Last entry is the repeated stable partition
    final_partition = history[-2]  # second-to-last is the actual stable result
    minimal_count = len(final_partition)
    original_count = len(states_list)
    merged = original_count - minimal_count

    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:1rem;">'
    for label, val in [("Steps shown", len(history)), ("Original states", original_count), ("Minimal states", minimal_count)]:
        html += f"""
        <div style="background:#f5f5f3;border-radius:8px;padding:12px 14px;">
          <div style="font-size:12px;color:#888;margin-bottom:3px;">{label}</div>
          <div style="font-size:22px;font-weight:500;">{val}</div>
        </div>"""
    html += "</div>"

    html += """
    <div style="background:#fff;border:0.5px solid rgba(0,0,0,0.12);border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1rem;">
      <p style="font-size:11px;font-weight:500;color:#888;text-transform:uppercase;letter-spacing:.04em;margin-bottom:1rem;">Partition refinement</p>
    """

    for i, step in enumerate(history):
        is_last = (i == len(history) - 1)
        groups = "   ".join(["{" + ", ".join(g) + "}" for g in step])
        border = "" if is_last else "border-bottom:0.5px solid rgba(0,0,0,0.08);"

        if is_last:
            stable_badge = (
                f'<span style="display:inline-block;margin-left:10px;font-size:11px;'
                f'padding:2px 8px;border-radius:6px;background:#e8f5e9;color:#2e7d32;">'
                f'stable — P{i} = P{i-1}</span>'
            )
        else:
            stable_badge = ""

        html += f"""
        <div style="display:flex;align-items:flex-start;gap:14px;padding:10px 0;{border}">
          <span style="font-family:ui-monospace,monospace;font-size:13px;font-weight:500;color:#888;min-width:30px;padding-top:2px;">P{i}</span>
          <span style="font-family:ui-monospace,monospace;font-size:14px;flex:1;">{groups}{stable_badge}</span>
        </div>"""

    html += "</div>"

    if merged > 0:
        html += f'<p style="font-size:13px;color:#888;">{merged} state{"s" if merged > 1 else ""} merged — equivalent under bisimulation.</p>'
    else:
        html += '<p style="font-size:13px;color:#888;">DFA is already minimal — no states can be merged.</p>'

    return html


# ================= ROUTES ================= #

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r") as f:
        return f.read()


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
            f'<div style="background:#fef2f2;border:0.5px solid #fca5a5;border-radius:8px;'
            f'padding:12px 16px;font-size:14px;color:#991b1b;">Error: {str(e)}</div>'
        )