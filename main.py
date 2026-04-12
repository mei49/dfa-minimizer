from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# ================= MINIMIZATION LOGIC ================= #

def get_partitions(states, alphabet, final_states, trans_dict):
    non_final = sorted([s for s in states if s not in final_states])
    final = sorted([s for s in final_states])

    partitions = []
    if non_final: partitions.append(tuple(non_final))
    if final: partitions.append(tuple(final))

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

        except:
            continue

    return trans_dict


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

        result = "<h3>Minimization Steps:</h3>"

        for i, step in enumerate(history):
            groups = ", ".join([f"{{{','.join(g)}}}" for g in step])
            result += f"<p>P{i}: {groups}</p>"

        return result

    except Exception as e:
        return f"<h3>Error:</h3><p>{str(e)}</p>"