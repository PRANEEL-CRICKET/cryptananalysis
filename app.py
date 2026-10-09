import tkinter as tk
from tkinter import messagebox, ttk

from cryptarithm.generator import generate_puzzle
from cryptarithm.progress import (
    load_progress,
    record_attempt,
    suggested_difficulty,
)
from cryptarithm.solver import parse_puzzle, solve


# ---------- App actions ----------

def solve_puzzle():
    equation = puzzle_entry.get().strip()

    if not equation:
        messagebox.showwarning("Puzzle needed", "Enter an equation first.")
        return

    try:
        result = solve(equation, strategy="mrv_fc", max_solutions=2)
    except ValueError as error:
        messagebox.showerror("Invalid puzzle", str(error))
        set_status("Please check the puzzle format.")
        return

    clear_text(solve_output)

    if not result.solutions:
        solve_output.insert(tk.END, "No solution found.\n")
    else:
        mapping = result.solutions[0]

        solve_output.insert(tk.END, "LETTER MAPPING\n", "heading")
        solve_output.insert(tk.END, "─" * 42 + "\n")

        for letter, digit in sorted(mapping.items()):
            solve_output.insert(tk.END, f"  {letter}   →   {digit}\n")

        def number_for(word):
            return int("".join(str(mapping[letter]) for letter in word))

        addends = [number_for(word) for word in result.puzzle.addends]
        answer = number_for(result.puzzle.result)

        solve_output.insert(tk.END, "\nANSWER CHECK\n", "heading")
        solve_output.insert(
            tk.END,
            f"  {' + '.join(map(str, addends))} = {answer}\n",
        )

        if len(result.solutions) > 1:
            solve_output.insert(
                tk.END,
                "\nAt least two solutions exist; showing the first.\n",
            )

    solve_output.insert(tk.END, "\nSEARCH DETAILS\n", "heading")
    solve_output.insert(
        tk.END,
        f"  Nodes: {result.nodes:,}\n"
        f"  Backtracks: {result.backtracks:,}\n"
        f"  Time: {result.elapsed_seconds * 1000:.2f} ms\n",
    )

    if result.explanation:
        solve_output.insert(tk.END, "\nEXPLANATION\n", "heading")
        for step in result.explanation:
            solve_output.insert(tk.END, f"  • {step}\n")

    set_status("Puzzle solved. Record your own practice result when ready.")


def create_puzzle():
    try:
        equation = generate_puzzle(difficulty_box.get())
    except ValueError as error:
        messagebox.showerror("Could not generate puzzle", str(error))
        return

    puzzle_entry.delete(0, tk.END)
    puzzle_entry.insert(0, equation)
    clear_text(solve_output)
    solve_output.insert(
        tk.END,
        "Puzzle ready!\n\nTry solving it yourself, then record your result "
        "using the buttons below.",
    )
    set_status(f"{difficulty_box.get()} puzzle generated.")


def record_my_result(solved):
    equation = puzzle_entry.get().strip()

    if not equation:
        messagebox.showwarning("Puzzle needed", "Enter an equation first.")
        return

    try:
        puzzle = parse_puzzle(equation)
    except ValueError as error:
        messagebox.showerror("Invalid puzzle", str(error))
        return

    letter_count = len(puzzle.letters)
    if letter_count <= 4:
        level = "Easy"
    elif letter_count <= 7:
        level = "Medium"
    else:
        level = "Hard"

    record_attempt(
        equation,
        solved,
        letter_count=letter_count,
        difficulty=level,
    )

    message = (
        "Your result was recorded: solved."
        if solved
        else "Your result was recorded: needs more practice."
    )
    set_status(message)
    refresh_dashboard()


def compare_strategies():
    equation = puzzle_entry.get().strip()

    if not equation:
        messagebox.showwarning("Puzzle needed", "Enter an equation first.")
        return

    strategies = [
        ("backtracking", "Basic backtracking"),
        ("mrv", "MRV"),
        ("mrv_fc", "MRV + forward checking"),
    ]

    clear_text(research_output)
    research_output.insert(tk.END, "Strategy comparison\n", "heading")
    research_output.insert(tk.END, f"Puzzle: {equation}\n\n")
    research_output.insert(
        tk.END,
        f"{'Strategy':<28} {'Solutions':>9} {'Nodes':>11} "
        f"{'Backtracks':>12} {'Time ms':>10}\n",
    )
    research_output.insert(tk.END, "─" * 76 + "\n")

    try:
        for strategy, label in strategies:
            result = solve(equation, strategy=strategy, max_solutions=2)
            research_output.insert(
                tk.END,
                f"{label:<28} "
                f"{len(result.solutions):>9} "
                f"{result.nodes:>11,} "
                f"{result.backtracks:>12,} "
                f"{result.elapsed_seconds * 1000:>10.2f}\n",
            )
    except ValueError as error:
        messagebox.showerror("Invalid puzzle", str(error))
        set_status("Please check the puzzle format.")
        return

    research_output.insert(
        tk.END,
        "\nTip: compare several puzzles before drawing conclusions "
        "from a single benchmark.",
    )
    set_status("Strategy comparison complete.")


# ---------- Learning dashboard ----------

def refresh_dashboard():
    if "attempts_value" not in globals():
        return

    history = load_progress()
    total = len(history)
    solved = sum(bool(item.get("solved", False)) for item in history)
    needs_practice = total - solved
    accuracy = (solved / total * 100) if total else 0

    attempts_value.config(text=str(total))
    solved_value.config(text=str(solved))
    practice_value.config(text=str(needs_practice))
    accuracy_value.config(text=f"{accuracy:.0f}%")
    level_value.config(text=suggested_difficulty())

    draw_learning_graph(history)


def draw_learning_graph(history):
    graph.delete("all")
    width = graph.winfo_width()
    height = graph.winfo_height()

    if width < 120 or height < 120:
        return

    if not history:
        graph.create_text(
            width / 2,
            height / 2,
            text="Record a few practice results to see your learning graph.",
            font=("Segoe UI", 11),
            fill="#64748b",
        )
        return

    factor = graph_factor.get()
    values = []

    if factor == "Practice accuracy":
        for index in range(len(history)):
            recent = history[max(0, index - 4):index + 1]
            score = (
                sum(bool(item.get("solved", False)) for item in recent)
                / len(recent)
                * 100
            )
            values.append(score)
        y_label = "Accuracy (%)"
        maximum = 100

    elif factor == "Puzzle size":
        for item in history:
            count = item.get("letter_count", 0)
            if not count:
                try:
                    count = len(parse_puzzle(item["equation"]).letters)
                except (ValueError, KeyError):
                    count = 0
            values.append(count)
        y_label = "Distinct letters"
        maximum = max(values) if values else 1

    elif factor == "Solved puzzles":
        running = 0
        for item in history:
            running += int(bool(item.get("solved", False)))
            values.append(running)
        y_label = "Solved"
        maximum = max(values) if values else 1

    else:
        running = 0
        for item in history:
            running += int(not bool(item.get("solved", False)))
            values.append(running)
        y_label = "Needs practice"
        maximum = max(values) if values else 1

    maximum = max(maximum, 1)
    left, right = 58, width - 22
    top, bottom = 38, height - 40
    chart_width = right - left
    chart_height = bottom - top

    graph.create_text(
        width / 2,
        16,
        text=factor,
        font=("Segoe UI", 11, "bold"),
        fill="#334155",
    )
    graph.create_text(
        15,
        height / 2,
        text=y_label,
        angle=90,
        font=("Segoe UI", 8),
        fill="#64748b",
    )

    for tick in range(5):
        value = maximum * tick / 4
        y = bottom - chart_height * tick / 4
        graph.create_line(left, y, right, y, fill="#e2e8f0")
        graph.create_text(
            left - 8,
            y,
            text=f"{value:.0f}",
            anchor="e",
            font=("Segoe UI", 8),
            fill="#64748b",
        )

    graph.create_line(left, top, left, bottom, fill="#94a3b8")
    graph.create_line(left, bottom, right, bottom, fill="#94a3b8")

    points = []
    count = len(values)

    for index, value in enumerate(values):
        x = (
            left + chart_width / 2
            if count == 1
            else left + chart_width * index / (count - 1)
        )
        y = bottom - chart_height * value / maximum
        points.append((x, y))

    for first, second in zip(points, points[1:]):
        graph.create_line(
            first[0],
            first[1],
            second[0],
            second[1],
            fill="#6d43c0",
            width=3,
        )

    for index, (x, y) in enumerate(points):
        graph.create_oval(
            x - 4,
            y - 4,
            x + 4,
            y + 4,
            fill="#6d43c0",
            outline="white",
            width=1,
        )

        if index == 0 or index == count - 1 or count <= 5:
            graph.create_text(
                x,
                bottom + 15,
                text=str(index + 1),
                font=("Segoe UI", 8),
                fill="#64748b",
            )

    graph.create_text(
        width / 2,
        height - 10,
        text="Practice attempt",
        font=("Segoe UI", 8),
        fill="#64748b",
    )


def show_dashboard_tab(_event=None):
    if notebook.select() == str(learning_tab):
        refresh_dashboard()


def set_status(message):
    status_text.set(message)


def clear_text(widget):
    widget.delete("1.0", tk.END)


def make_text_area(parent, height=18):
    frame = ttk.Frame(parent, style="Card.TFrame")

    text = tk.Text(
        frame,
        height=height,
        wrap="word",
        font=("Consolas", 10),
        background="#ffffff",
        foreground="#1e293b",
        relief="flat",
        padx=14,
        pady=12,
        insertbackground="#1e293b",
    )
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)

    text.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    text.tag_configure(
        "heading",
        font=("Segoe UI", 10, "bold"),
        foreground="#5b36a8",
    )
    return frame, text


# ---------- Window and visual style ----------

root = tk.Tk()
root.title("Cryptarithm Lab")
root.geometry("1020x760")
root.minsize(760, 600)
root.configure(background="#f3f5fa")

style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure("TFrame", background="#f3f5fa")
style.configure("Card.TFrame", background="#ffffff")
style.configure("TLabel", background="#f3f5fa", foreground="#263248")
style.configure(
    "Title.TLabel",
    background="#f3f5fa",
    foreground="#182235",
    font=("Segoe UI", 21, "bold"),
)
style.configure(
    "Subtitle.TLabel",
    background="#f3f5fa",
    foreground="#64748b",
    font=("Segoe UI", 10),
)
style.configure(
    "CardTitle.TLabel",
    background="#ffffff",
    foreground="#64748b",
    font=("Segoe UI", 9),
)
style.configure(
    "Metric.TLabel",
    background="#ffffff",
    foreground="#27324a",
    font=("Segoe UI", 16, "bold"),
)
style.configure(
    "TButton",
    padding=(12, 8),
    font=("Segoe UI", 9, "bold"),
)
style.configure(
    "Primary.TButton",
    background="#6741b8",
    foreground="#ffffff",
)
style.map(
    "Primary.TButton",
    background=[("active", "#56359c"), ("pressed", "#472c83")],
)
style.configure(
    "TNotebook",
    background="#f3f5fa",
    borderwidth=0,
)
style.configure(
    "TNotebook.Tab",
    padding=(16, 9),
    font=("Segoe UI", 9, "bold"),
)
style.configure(
    "TLabelframe",
    background="#ffffff",
    foreground="#334155",
)
style.configure(
    "TLabelframe.Label",
    background="#ffffff",
    foreground="#475569",
    font=("Segoe UI", 9, "bold"),
)

page = ttk.Frame(root, padding=(22, 18))
page.pack(fill="both", expand=True)

header = ttk.Frame(page)
header.pack(fill="x", pady=(0, 14))

ttk.Label(
    header,
    text="Cryptarithm Lab",
    style="Title.TLabel",
).pack(anchor="w")

ttk.Label(
    header,
    text="Solve puzzles, compare search strategies, and follow your progress.",
    style="Subtitle.TLabel",
).pack(anchor="w", pady=(3, 0))

notebook = ttk.Notebook(page)
notebook.pack(fill="both", expand=True)

solve_tab = ttk.Frame(notebook, padding=16)
research_tab = ttk.Frame(notebook, padding=16)
learning_tab = ttk.Frame(notebook, padding=16)

notebook.add(solve_tab, text="  Solve & Practice  ")
notebook.add(research_tab, text="  Research  ")
notebook.add(learning_tab, text="  Learning Dashboard  ")

# ---------- Solve & Practice tab ----------

ttk.Label(
    solve_tab,
    text="Your puzzle",
    font=("Segoe UI", 13, "bold"),
).pack(anchor="w")

ttk.Label(
    solve_tab,
    text="Use addition format, for example: SEND + MORE = MONEY",
    style="Subtitle.TLabel",
).pack(anchor="w", pady=(2, 9))

puzzle_entry = ttk.Entry(solve_tab, font=("Segoe UI", 12))
puzzle_entry.pack(fill="x", pady=(0, 12))
puzzle_entry.insert(0, "SEND + MORE = MONEY")

action_row = ttk.Frame(solve_tab)
action_row.pack(fill="x", pady=(0, 12))

ttk.Label(action_row, text="Puzzle size:").pack(side="left", padx=(0, 6))

difficulty_box = ttk.Combobox(
    action_row,
    values=["Easy", "Medium", "Hard"],
    state="readonly",
    width=10,
)
difficulty_box.set("Easy")
difficulty_box.pack(side="left", padx=(0, 12))

ttk.Button(
    action_row,
    text="Generate puzzle",
    command=create_puzzle,
).pack(side="left", padx=(0, 8))

ttk.Button(
    action_row,
    text="Solve puzzle",
    style="Primary.TButton",
    command=solve_puzzle,
).pack(side="left")

practice_card = ttk.LabelFrame(
    solve_tab,
    text="Your practice result",
    padding=10,
)
practice_card.pack(fill="x", pady=(0, 12))

ttk.Label(
    practice_card,
    text="Try the puzzle yourself, then record how it went.",
    background="#ffffff",
).pack(side="left", padx=(0, 14))

ttk.Button(
    practice_card,
    text="I solved it",
    command=lambda: record_my_result(True),
).pack(side="left", padx=(0, 8))

ttk.Button(
    practice_card,
    text="I need more practice",
    command=lambda: record_my_result(False),
).pack(side="left")

ttk.Label(
    solve_tab,
    text="Solution and explanation",
    font=("Segoe UI", 11, "bold"),
).pack(anchor="w", pady=(0, 6))

solve_frame, solve_output = make_text_area(solve_tab, height=18)
solve_frame.pack(fill="both", expand=True)

# ---------- Research tab ----------

ttk.Label(
    research_tab,
    text="Solver research",
    font=("Segoe UI", 15, "bold"),
).pack(anchor="w")

ttk.Label(
    research_tab,
    text=(
        "Run the three search strategies on the puzzle in the Solve & Practice tab. "
        "Compare nodes, backtracks, and elapsed time."
    ),
    style="Subtitle.TLabel",
    wraplength=850,
).pack(anchor="w", pady=(4, 12))

ttk.Button(
    research_tab,
    text="Compare strategies for current puzzle",
    style="Primary.TButton",
    command=compare_strategies,
).pack(anchor="w", pady=(0, 12))

research_frame, research_output = make_text_area(research_tab, height=24)
research_frame.pack(fill="both", expand=True)

# ---------- Learning Dashboard tab ----------

ttk.Label(
    learning_tab,
    text="Your learning dashboard",
    font=("Segoe UI", 15, "bold"),
).pack(anchor="w")

ttk.Label(
    learning_tab,
    text="Graphs update when you record a practice result.",
    style="Subtitle.TLabel",
).pack(anchor="w", pady=(3, 10))

metrics = ttk.Frame(learning_tab)
metrics.pack(fill="x", pady=(0, 12))


def make_metric_card(parent, title):
    card = ttk.Frame(parent, style="Card.TFrame", padding=(12, 9))
    card.pack(side="left", fill="both", expand=True, padx=3)

    ttk.Label(
        card,
        text=title,
        style="CardTitle.TLabel",
    ).pack(anchor="w")

    value = ttk.Label(
        card,
        text="0",
        style="Metric.TLabel",
    )
    value.pack(anchor="w", pady=(3, 0))
    return value


attempts_value = make_metric_card(metrics, "Attempts")
solved_value = make_metric_card(metrics, "Solved")
practice_value = make_metric_card(metrics, "Needs practice")
accuracy_value = make_metric_card(metrics, "Accuracy")
level_value = make_metric_card(metrics, "Next level")

graph_controls = ttk.Frame(learning_tab)
graph_controls.pack(fill="x", pady=(0, 8))

ttk.Label(
    graph_controls,
    text="Graph factor:",
).pack(side="left")

graph_factor = ttk.Combobox(
    graph_controls,
    values=[
        "Practice accuracy",
        "Puzzle size",
        "Solved puzzles",
        "Needs practice",
    ],
    state="readonly",
    width=24,
)
graph_factor.set("Practice accuracy")
graph_factor.pack(side="left", padx=8)

graph = tk.Canvas(
    learning_tab,
    background="#ffffff",
    highlightthickness=1,
    highlightbackground="#dce2ec",
)
graph.pack(fill="both", expand=True)

ttk.Label(
    learning_tab,
    text=(
        "Accuracy is a rolling percentage across up to five attempts. "
        "Puzzle size counts distinct letters."
    ),
    style="Subtitle.TLabel",
).pack(anchor="w", pady=(8, 0))

graph_factor.bind(
    "<<ComboboxSelected>>",
    lambda _event: refresh_dashboard(),
)
graph.bind(
    "<Configure>",
    lambda _event: refresh_dashboard(),
)
notebook.bind("<<NotebookTabChanged>>", show_dashboard_tab)

# ---------- Status bar ----------

status_text = tk.StringVar(value="Ready.")
status_bar = ttk.Label(
    page,
    textvariable=status_text,
    style="Subtitle.TLabel",
    anchor="w",
)
status_bar.pack(fill="x", pady=(10, 0))

root.mainloop()