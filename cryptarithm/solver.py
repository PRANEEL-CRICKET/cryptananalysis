from dataclasses import dataclass
import re
from time import perf_counter


@dataclass(frozen=True)
class Puzzle:
    addends: tuple[str, ...]
    result: str
    letters: tuple[str, ...]
    leading: frozenset[str]


@dataclass
class SolveResult:
    puzzle: Puzzle
    solutions: list[dict[str, int]]
    nodes: int
    backtracks: int
    elapsed_seconds: float
    explanation: list[str]
    strategy: str


def words_share_letters(words: tuple[str, ...]) -> bool:
    """Return whether any two words share a letter."""
    return any(
        set(first) & set(second)
        for index, first in enumerate(words)
        for second in words[index + 1:]
    )


def parse_puzzle(equation: str) -> Puzzle:
    """Parse a puzzle like SEND + MORE = MONEY."""
    if equation.count("=") != 1:
        raise ValueError("The equation must contain exactly one '=' sign.")

    left, right = equation.split("=")
    addends = tuple(word.strip().upper() for word in left.split("+"))
    result = right.strip().upper()
    words = (*addends, result)

    if any(not re.fullmatch(r"[A-Z]+", word) for word in words):
        raise ValueError(
            "Use letters A-Z, with addends separated by '+' and one '='."
        )

    letters = tuple(dict.fromkeys("".join(words)))

    if len(letters) > 10:
        raise ValueError(
            f"A decimal puzzle can use at most 10 distinct letters; "
            f"this puzzle has {len(letters)}."
        )

    maximum_sum = sum(10 ** len(word) - 1 for word in addends)
    maximum_result_length = len(str(maximum_sum))
    if len(result) > maximum_result_length:
        longest_addend = max(map(len, addends))
        raise ValueError(
            f"The result has {len(result)} letters, but these addends can "
            f"sum to at most {maximum_result_length} digits. For two "
            f"addends, the result can be at most one letter longer than "
            f"the longest addend ({longest_addend} letters)."
        )

    if not words_share_letters(words):
        raise ValueError(
            "The words do not share any letters, so the puzzle has no "
            "interlocking letter constraints. Share at least one letter "
            "between two words."
        )

    leading = frozenset(word[0] for word in words if len(word) > 1)

    return Puzzle(
        addends=addends,
        result=result,
        letters=letters,
        leading=leading,
    )


def word_value(word: str, assignment: dict[str, int]) -> int:
    """Convert a word to its number using the current letter mapping."""
    return int("".join(str(assignment[letter]) for letter in word))


def check_solution(puzzle: Puzzle, assignment: dict[str, int]) -> bool:
    """Return whether an assignment is a valid solution for a puzzle."""
    if set(assignment) != set(puzzle.letters):
        return False

    digits = list(assignment.values())
    if any(type(digit) is not int or not 0 <= digit <= 9 for digit in digits):
        return False
    if len(set(digits)) != len(digits):
        return False
    if any(assignment[letter] == 0 for letter in puzzle.leading):
        return False

    return sum(
        word_value(word, assignment)
        for word in puzzle.addends
    ) == word_value(puzzle.result, assignment)


def solution_steps(puzzle: Puzzle, assignment: dict[str, int]) -> list[str]:
    """Describe the column addition and carry for a valid assignment."""
    width = max(
        max(len(word) for word in puzzle.addends),
        len(puzzle.result),
    )
    carry = 0
    steps = []

    for column in range(width):
        addend_letters = [
            word[-1 - column]
            for word in puzzle.addends
            if column < len(word)
        ]
        addend_total = sum(assignment[letter] for letter in addend_letters)
        column_total = addend_total + carry
        result_letter = (
            puzzle.result[-1 - column]
            if column < len(puzzle.result)
            else None
        )
        next_carry = column_total // 10
        column_names = ("Units", "Tens", "Hundreds")
        column_name = (
            column_names[column]
            if column < len(column_names)
            else f"10^{column}"
        )
        addend_values = " + ".join(
            f"{letter}={assignment[letter]}" for letter in addend_letters
        )
        result_label = (
            f"{result_letter}={assignment[result_letter]}"
            if result_letter is not None
            else "no result digit"
        )
        if not addend_letters:
            steps.append(f"Final carry: {carry}; {result_label}.")
            carry = 0
            continue
        steps.append(
            f"{column_name} column: {addend_values} + carry {carry} = "
            f"{column_total}; {result_label}; carry {next_carry}."
        )
        carry = next_carry

    return steps


def solve(
    equation: str,
    strategy: str = "mrv_fc",
    max_solutions: int = 2,
) -> SolveResult:
    """
    Solve an addition cryptarithm.

    Strategies:
        backtracking: assign letters in their original order
        mrv: choose constrained letters first
        mrv_fc: also reject completed columns that violate carries
    """
    valid_strategies = {"backtracking", "mrv", "mrv_fc"}

    if strategy not in valid_strategies:
        raise ValueError(
            "strategy must be 'backtracking', 'mrv', or 'mrv_fc'."
        )

    if max_solutions < 1:
        raise ValueError("max_solutions must be at least 1.")

    puzzle = parse_puzzle(equation)
    assignment: dict[str, int] = {}
    used_digits: set[int] = set()
    solutions: list[dict[str, int]] = []
    explanation: list[str] = []
    nodes = 0
    backtracks = 0
    start_time = perf_counter()

    def partial_assignment_is_valid() -> bool:
        """Check each column once all its letters have been assigned."""
        width = max(
            max(len(word) for word in puzzle.addends),
            len(puzzle.result),
        )
        carry = 0

        for column in range(width):
            addend_letters = [
                word[-1 - column]
                for word in puzzle.addends
                if column < len(word)
            ]

            result_letter = (
                puzzle.result[-1 - column]
                if column < len(puzzle.result)
                else None
            )

            if any(letter not in assignment for letter in addend_letters):
                break

            if result_letter is not None and result_letter not in assignment:
                break

            column_sum = carry + sum(
                assignment[letter] for letter in addend_letters
            )

            if result_letter is not None:
                if column_sum % 10 != assignment[result_letter]:
                    return False
            elif column_sum % 10 != 0:
                return False

            carry = column_sum // 10

        if len(assignment) == len(puzzle.letters):
            addend_sum = sum(
                word_value(word, assignment)
                for word in puzzle.addends
            )
            return addend_sum == word_value(puzzle.result, assignment)

        return True

    def choose_next_letter() -> str:
        remaining = [
            letter
            for letter in puzzle.letters
            if letter not in assignment
        ]

        if strategy == "backtracking":
            return remaining[0]

        # Prefer letters in the units column, then leading letters,
        # then letters that appear in more words.
        units_letters = {
            word[-1]
            for word in (*puzzle.addends, puzzle.result)
        }

        return min(
            remaining,
            key=lambda letter: (
                letter not in units_letters,
                letter not in puzzle.leading,
                -sum(
                    letter in word
                    for word in (*puzzle.addends, puzzle.result)
                ),
            ),
        )

    def search() -> None:
        nonlocal nodes, backtracks

        if len(solutions) >= max_solutions:
            return

        if len(assignment) == len(puzzle.letters):
            if partial_assignment_is_valid():
                solutions.append(dict(assignment))
            return

        letter = choose_next_letter()

        for digit in range(10):
            if digit in used_digits:
                continue

            if digit == 0 and letter in puzzle.leading:
                continue

            nodes += 1
            assignment[letter] = digit
            used_digits.add(digit)

            if len(explanation) < 18:
                explanation.append(
                    f"Try {letter} = {digit}; used digits: "
                    f"{sorted(used_digits)}."
                )

            if partial_assignment_is_valid():
                search()
            else:
                backtracks += 1
                if len(explanation) < 18:
                    explanation.append(
                        f"Reject {letter} = {digit}: a completed "
                        "column conflicts."
                    )

            used_digits.remove(digit)
            del assignment[letter]

            if len(solutions) >= max_solutions:
                return

    search()

    return SolveResult(
        puzzle=puzzle,
        solutions=solutions,
        nodes=nodes,
        backtracks=backtracks,
        elapsed_seconds=perf_counter() - start_time,
        explanation=explanation,
        strategy=strategy,
    )