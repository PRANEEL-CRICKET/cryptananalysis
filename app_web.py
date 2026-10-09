from datetime import datetime
from time import time, time_ns

import streamlit as st

from cryptarithm.generator import generate_puzzle
from cryptarithm.solver import (
    check_solution,
    parse_puzzle,
    solution_steps,
    solve,
)


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


def _generate_game_puzzle(difficulty):
    current = st.session_state.get("challenge")
    if current is not None and current["outcome"] is None:
        return
    st.session_state.game_question = generate_puzzle(difficulty)
    st.session_state.challenge = None


def _start_web_challenge(equation, difficulty):
    current = st.session_state.get("challenge")
    if current is not None and current["outcome"] is None:
        return

    previous = st.session_state.get("challenge")
    if previous is not None and previous["outcome"] is not None:
        st.session_state.challenge = None

    try:
        result = solve(equation, strategy="mrv_fc", max_solutions=2)
    except ValueError as error:
        st.error(f"Invalid puzzle: {error}")
        return

    if not result.solutions:
        st.error(
            "No solution exists: no digit assignment satisfies the "
            "distinct-digit, leading-letter, and column-carry constraints. "
            "Check the shared letters for a contradiction."
        )
        return

    seconds = {"Easy": 300, "Medium": 600, "Hard": 1800}[difficulty]
    st.session_state.challenge = {
        "id": time_ns(),
        "equation": equation,
        "difficulty": difficulty,
        "deadline": time() + seconds,
        "result": result,
        "outcome": None,
    }


def _complete_web_challenge(solved, reason):
    challenge = st.session_state.challenge
    if challenge["outcome"] is not None:
        return

    result = challenge["result"]
    outcome = "solved" if solved else "unsolved"
    challenge["outcome"] = outcome
    challenge["reason"] = reason
    st.session_state.practice_history.append(
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "equation": challenge["equation"],
            "solved": solved,
            "letter_count": len(result.puzzle.letters),
            "difficulty": challenge["difficulty"],
            "source": "challenge",
            "reason": reason,
        }
    )


def _render_web_challenge_solution(challenge):
    result = challenge["result"]
    mapping = result.solutions[0]
    addends = [
        int("".join(str(mapping[letter]) for letter in word))
        for word in result.puzzle.addends
    ]
    answer = int(
        "".join(str(mapping[letter]) for letter in result.puzzle.result)
    )

    if challenge["outcome"] == "solved":
        st.success("Correct! This challenge is in your Solved set.")
    else:
        st.warning(
            f"This challenge is in your Unsolved set. "
            f"{challenge['reason']}"
        )

    st.markdown("#### Solution cards")
    card_columns = st.columns(5)
    for index, letter in enumerate(result.puzzle.letters):
        with card_columns[index % len(card_columns)]:
            with st.container(border=True):
                st.markdown(f"### {letter}")
                st.markdown(f"## {mapping[letter]}")

    st.markdown("#### Answer check")
    st.code(f"{' + '.join(map(str, addends))} = {answer}")
    st.markdown("#### Column-by-column solution")
    for step in solution_steps(result.puzzle, mapping):
        st.write(f"- {step}")

    if result.explanation:
        with st.expander("Solver search trace"):
            for step in result.explanation:
                st.write(f"- {step}")


@st.fragment(run_every="1s")
def _render_web_challenge_timer():
    challenge = st.session_state.get("challenge")
    if challenge is None or challenge["outcome"] is not None:
        return

    remaining = max(0, int(challenge["deadline"] - time() + 0.999))
    if remaining == 0:
        _complete_web_challenge(False, "Time expired.")
        st.rerun(scope="app")
        return

    st.metric(
        "Time remaining",
        f"{remaining // 60:02d}:{remaining % 60:02d}",
    )


@st.fragment
def _render_web_challenge_inputs():
    challenge = st.session_state.get("challenge")
    if challenge is None or challenge["outcome"] is not None:
        return

    st.write(f"**Challenge:** `{challenge['equation']}`")
    st.caption(
        "Each letter is one card. Assign a different digit to every letter; "
        "leading letters cannot be zero."
    )

    card_columns = st.columns(5)
    entries = {}
    for index, letter in enumerate(challenge["result"].puzzle.letters):
        with card_columns[index % len(card_columns)]:
            with st.container(border=True):
                st.markdown(f"### {letter}")
                entries[letter] = st.text_input(
                    f"Digit for {letter}",
                    max_chars=1,
                    placeholder="0-9",
                    key=f"challenge-{challenge['id']}-{letter}",
                    label_visibility="collapsed",
                )
    submitted = st.button(
        "Check my answer",
        type="primary",
        width="stretch",
        key=f"check-challenge-{challenge['id']}",
    )

    if submitted:
        if time() >= challenge["deadline"]:
            _complete_web_challenge(False, "Time expired.")
        else:
            answer_mapping = {}
            if all(
                len(digit) == 1 and digit in "0123456789"
                for digit in entries.values()
            ):
                answer_mapping = {
                    letter: int(digit) for letter, digit in entries.items()
                }
            solved = check_solution(
                challenge["result"].puzzle,
                answer_mapping,
            )
            _complete_web_challenge(
                solved,
                "Correct answer."
                if solved
                else "The digit assignment was incorrect or incomplete.",
            )

        st.rerun(scope="app")


def _render_web_challenge():
    challenge = st.session_state.get("challenge")
    if challenge is None:
        st.info("Start a challenge to see the letter cards and timer.")
        return

    if challenge["outcome"] is not None:
        _render_web_challenge_solution(challenge)
        return

    _render_web_challenge_timer()
    _render_web_challenge_inputs()


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

solve_tab, practice_tab, game_tab, compare_tab, progress_tab = st.tabs(
    ["Solve", "Practice", "Fun Games", "Compare strategies", "Progress"]
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
                st.warning(
                    "No solution exists: no digit assignment satisfies the "
                    "distinct-digit, leading-letter, and column-carry "
                    "constraints. Check the shared letters for a "
                    "contradiction."
                )
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

with game_tab:
    st.subheader("Timed letter-card challenge")
    st.write(
        "Practice a cryptarithm by assigning a digit to each letter before "
        "the timer runs out. A correct answer goes into Solved; an incorrect "
        "answer or timeout goes into Unsolved with the worked solution."
    )
    difficulty_options = {
        "Easy": "5 minutes",
        "Medium": "10 minutes",
        "Hard": "30 minutes",
    }
    game_difficulty = st.selectbox(
        "Challenge difficulty",
        list(difficulty_options),
        key="game_difficulty",
        format_func=lambda level: f"{level} — {difficulty_options[level]}",
    )
    game_question = st.text_input(
        "Your cryptarithm (or generate one below)",
        value="SEND + MORE = MONEY",
        key="game_question",
        help="Use letters A-Z, '+' between addends, and one '=' sign.",
    )
    game_actions = st.columns(2)
    game_actions[0].button(
        "Generate challenge puzzle",
        width="stretch",
        on_click=_generate_game_puzzle,
        args=(game_difficulty,),
        disabled=(
            st.session_state.get("challenge") is not None
            and st.session_state.challenge["outcome"] is None
        ),
    )
    if game_actions[1].button(
        "Start challenge",
        type="primary",
        width="stretch",
        disabled=(
            st.session_state.get("challenge") is not None
            and st.session_state.challenge["outcome"] is None
        ),
    ):
        _start_web_challenge(game_question.strip(), game_difficulty)

    st.caption(
        "Rules: at most 10 distinct letters; the result cannot exceed the "
        "maximum possible sum length; at least two words must share a letter. "
        "Leading letters cannot be zero."
    )
    _render_web_challenge()

    challenge_history = [
        attempt
        for attempt in st.session_state.practice_history
        if attempt.get("source") == "challenge"
    ]
    solved_history = [
        attempt for attempt in challenge_history if attempt["solved"]
    ]
    unsolved_history = [
        attempt for attempt in challenge_history if not attempt["solved"]
    ]
    category_columns = st.columns(2)
    category_columns[0].subheader(f"Solved ({len(solved_history)})")
    category_columns[0].write(
        [attempt["equation"] for attempt in solved_history]
        or ["No solved challenges yet."]
    )
    category_columns[1].subheader(f"Unsolved ({len(unsolved_history)})")
    category_columns[1].write(
        [
            f"{attempt['equation']} — {attempt['reason']}"
            for attempt in unsolved_history
        ]
        or ["No unsolved challenges yet."]
    )

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
