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
            f'<div style="background:#fdf2f4;border:1px solid #e8b4bc;border-radius:10px;'
            f'padding:14px 18px;font-size:15px;color:#8b2c3a;line-height:1.5;">Error: {str(e)}</div>'
        )