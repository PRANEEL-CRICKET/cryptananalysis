import pytest

from cryptarithm.generator import generate_puzzle
from cryptarithm.solver import parse_puzzle, solve, words_share_letters


@pytest.mark.parametrize("difficulty", ["Easy", "Medium", "Hard"])
def test_generator_returns_solvable_interlocked_puzzle(difficulty):
    puzzle = generate_puzzle(difficulty, seed=5)

    assert "+" in puzzle
    assert "=" in puzzle

    result = solve(puzzle, max_solutions=1)
    assert result.solutions
    parsed = parse_puzzle(puzzle)
    assert words_share_letters((*parsed.addends, parsed.result))