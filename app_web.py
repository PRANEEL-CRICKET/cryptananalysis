from datetime import datetime

import streamlit as st

from cryptarithm.generator import generate_puzzle
from cryptarithm.solver import parse_puzzle, solve


def _suggested_difficulty(history):
    recent = history[-5:]
    if len(recent) < 3:
        return "Easy"

    success_rate = sum(bool(attempt["solved"]) for attempt in recent) / len(
        recent
    )
    if success_rate >= 0.8:
        return "Hard"
    if success_rate >= 0.5:
        return "Medium"
    return "Easy"


def _generate_puzzle(difficulty):
    st.session_state.equation = generate_puzzle(difficulty)
    st.session_state.solve_requested = False


st.set_page_config(page_title="Cryptarithm Lab", page_icon="🔢", layout="wide")
st.title("Cryptarithm Lab")
st.caption(
    "Solve addition cryptarithms, generate practice puzzles, and compare "
    "search strategies."
)

if "practice_history" not in st.session_state:
    st.session_state.practice_history = []

with st.sidebar:
    st.subheader("Puzzle")
    equation = st.text_input(
        "Enter an equation",
        value=st.session_state.get("equation", "SEND + MORE = MONEY"),
        key="equation",
        help="Use letters A-Z, '+' between addends, and one '=' sign.",
    )
    if st.button("Solve puzzle", type="primary", width="stretch"):
        st.session_state.solve_requested = True

    st.divider()
    st.subheader("Generate a puzzle")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    st.button(
        "Generate puzzle",
        width="stretch",
        on_click=_generate_puzzle,
        args=(difficulty,),
    )

solve_tab, practice_tab, compare_tab, progress_tab = st.tabs(
    ["Solve", "Practice", "Compare strategies", "Progress"]
)

with solve_tab:
    st.subheader("Solve a cryptarithm")
    st.write(f"**Current puzzle:** `{equation}`")
    if st.session_state.pop("solve_requested", False):
        try:
            result = solve(equation, strategy="mrv_fc", max_solutions=2)
        except ValueError as error:
            st.error(str(error))
        else:
            if not result.solutions:
                st.warning("No solution found.")
            else:
                mapping = result.solutions[0]
                st.markdown("#### Letter mapping")
                st.dataframe(
                    [
                        {"Letter": letter, "Digit": digit}
                        for letter, digit in sorted(mapping.items())
                    ],
                    hide_index=True,
                    width="stretch",
                )

                addends = [
                    int("".join(str(mapping[letter]) for letter in word))
                    for word in result.puzzle.addends
                ]
                answer = int(
                    "".join(
                        str(mapping[letter]) for letter in result.puzzle.result
                    )
                )
                st.markdown("#### Answer check")
                st.code(f"{' + '.join(map(str, addends))} = {answer}")
                if len(result.solutions) > 1:
                    st.info("At least two solutions exist; showing the first.")

            st.markdown("#### Search details")
            metric_columns = st.columns(3)
            metric_columns[0].metric("Nodes", f"{result.nodes:,}")
            metric_columns[1].metric("Backtracks", f"{result.backtracks:,}")
            metric_columns[2].metric(
                "Time", f"{result.elapsed_seconds * 1000:.2f} ms"
            )
            if result.explanation:
                with st.expander("Solver explanation"):
                    for step in result.explanation:
                        st.write(f"- {step}")

with practice_tab:
    st.subheader("Record your practice result")
    st.write("Try the puzzle yourself, then record how it went.")
    result_columns = st.columns(2)
    if result_columns[0].button(
        "I solved it", type="primary", width="stretch"
    ):
        solved_by_user = True
    elif result_columns[1].button(
        "I need more practice", width="stretch"
    ):
        solved_by_user = False
    else:
        solved_by_user = None

    if solved_by_user is not None:
        try:
            puzzle = parse_puzzle(equation)
        except ValueError as error:
            st.error(str(error))
        else:
            letter_count = len(puzzle.letters)
            level = (
                "Easy"
                if letter_count <= 4
                else "Medium"
                if letter_count <= 7
                else "Hard"
            )
            st.session_state.practice_history.append(
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "equation": equation,
                    "solved": solved_by_user,
                    "letter_count": letter_count,
                    "difficulty": level,
                }
            )
            st.success("Your practice result was recorded for this session.")

with compare_tab:
    st.subheader("Compare solving strategies")
    st.write(f"**Current puzzle:** `{equation}`")
    if st.button("Run comparison"):
        try:
            comparison_results = [
                (
                    label,
                    solve(equation, strategy=strategy, max_solutions=2),
                )
                for strategy, label in [
                    ("backtracking", "Basic backtracking"),
                    ("mrv", "MRV"),
                    ("mrv_fc", "MRV + forward checking"),
                ]
            ]
        except ValueError as error:
            st.error(str(error))
        else:
            st.dataframe(
                [
                    {
                        "Strategy": label,
                        "Solutions": len(result.solutions),
                        "Nodes": result.nodes,
                        "Backtracks": result.backtracks,
                        "Time (ms)": round(result.elapsed_seconds * 1000, 2),
                    }
                    for label, result in comparison_results
                ],
                hide_index=True,
                width="stretch",
            )
            st.caption(
                "Compare multiple puzzles before drawing conclusions from a "
                "single benchmark."
            )

with progress_tab:
    history = st.session_state.practice_history
    total = len(history)
    solved_count = sum(bool(attempt["solved"]) for attempt in history)
    accuracy = solved_count / total * 100 if total else 0

    st.subheader("Learning dashboard")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Attempts", total)
    metric_columns[1].metric("Solved", solved_count)
    metric_columns[2].metric("Needs practice", total - solved_count)
    metric_columns[3].metric("Accuracy", f"{accuracy:.0f}%")

    if not history:
        st.info("Record a practice result to start your progress chart.")
    else:
        factor = st.selectbox(
            "Progress measure",
            [
                "Practice accuracy",
                "Puzzle size",
                "Solved puzzles",
                "Needs practice",
            ],
        )
        values = []
        if factor == "Practice accuracy":
            for index in range(total):
                recent = history[max(0, index - 4):index + 1]
                values.append(
                    sum(bool(attempt["solved"]) for attempt in recent)
                    / len(recent)
                    * 100
                )
        elif factor == "Puzzle size":
            values = [attempt["letter_count"] for attempt in history]
        else:
            solved_running = 0
            needs_practice_running = 0
            for attempt in history:
                solved_running += int(bool(attempt["solved"]))
                needs_practice_running += int(not bool(attempt["solved"]))
                values.append(
                    solved_running
                    if factor == "Solved puzzles"
                    else needs_practice_running
                )

        st.line_chart({factor: values}, x_label="Practice attempt")
        st.caption(
            f"Suggested next difficulty: "
            f"**{_suggested_difficulty(history)}**"
        )
        with st.expander("Practice history"):
            st.dataframe(
                [
                    {
                        "Time": attempt["time"],
                        "Puzzle": attempt["equation"],
                        "Result": (
                            "Solved" if attempt["solved"] else "Needs practice"
                        ),
                        "Difficulty": attempt["difficulty"],
                    }
                    for attempt in reversed(history)
                ],
                hide_index=True,
                width="stretch",
            )
