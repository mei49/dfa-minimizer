import tkinter as tk
import fastapi
from tkinter import messagebox

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


# ================= TRANSITION PARSER ================= #

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


# ================= UI ACTION ================= #

def run_dfa():
    try:
        s_raw = states_e.get().strip()
        a_raw = alpha_e.get().strip()
        f_raw = final_e.get().strip()
        t_raw = trans_e.get().strip()

        if not s_raw or not a_raw or not t_raw:
            raise ValueError("Please fill all required fields!")

        states = [s.strip() for s in s_raw.split(",") if s.strip()]
        alphabet = [a.strip() for a in a_raw.split(",") if a.strip()]
        final_states = [f.strip() for f in f_raw.split(",") if f.strip()]

        trans_dict = parse_transitions(t_raw)

        if not trans_dict:
            raise ValueError("Invalid transition format!\nUse: (A,0)->B")

        history = get_partitions(states, alphabet, final_states, trans_dict)

        res = "MINIMIZATION STEPS:\n" + "-" * 40 + "\n"

        for i, step in enumerate(history):
            groups = ", ".join([f"{{{','.join(g)}}}" for g in step])
            res += f"P{i} : {groups}\n"

        result_label.config(text=res, fg="#2e7d32",
                            font=("Consolas", 10, "bold"))

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ================= UI DESIGN ================= #

root = tk.Tk()
root.title("DFA Visualizer Pro")
root.geometry("500x680")
root.configure(bg="#f0f2f5")

# Header
header = tk.Frame(root, bg="#3f51b5", pady=25)
header.pack(fill="x")

tk.Label(header, text="DFA MINIMIZER",
         font=("Segoe UI", 24, "bold"),
         bg="#3f51b5", fg="white").pack()

tk.Label(header, text="Automata Theory Step-by-Step Tool",
         font=("Segoe UI", 10),
         bg="#3f51b5", fg="#c5cae9").pack()

# Card
card = tk.Frame(root, bg="white", padx=25, pady=25)
card.place(relx=0.5, rely=0.58, anchor="center",
           width=430, height=520)


def add_field(label_text):
    tk.Label(card, text=label_text,
             bg="white",
             font=("Segoe UI", 9, "bold"),
             fg="#444").pack(anchor="w")

    ent = tk.Entry(card,
                   font=("Segoe UI", 11),
                   bd=0,
                   highlightthickness=1,
                   highlightbackground="#ddd",
                   highlightcolor="#3f51b5")

    ent.pack(fill="x", pady=(2, 12), ipady=5)

    return ent


# Inputs (EMPTY NOW ✅)
states_e = add_field("States (comma separated)")
alpha_e = add_field("Alphabet (comma separated)")
final_e = add_field("Final States")

trans_e = add_field("Transitions (Format: (State,Input)->Target)")

# Hint
tk.Label(card,
         text="Example: (A,0)->B, (A,1)->C",
         bg="white",
         fg="gray",
         font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 10))


# Button
btn = tk.Button(card,
                text="MINIMIZE DFA",
                command=run_dfa,
                bg="#4CAF50",
                fg="white",
                font=("Segoe UI", 12, "bold"),
                pady=12,
                bd=0,
                cursor="hand2")

btn.pack(fill="x", pady=10)

# Output
result_label = tk.Label(card,
                        text="Enter inputs and click Minimize...",
                        bg="#f9f9f9",
                        font=("Consolas", 10),
                        fg="#666",
                        wraplength=380,
                        pady=20,
                        justify="left",
                        anchor="nw")

result_label.pack(fill="both", expand=True)

root.mainloop()