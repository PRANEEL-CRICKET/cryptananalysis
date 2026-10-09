from cryptarithm.generator import generate_puzzle
from cryptarithm.solver import solve


def test_generator_returns_solvable_puzzle():
    puzzle = generate_puzzle("Easy", seed=5)

    assert "+" in puzzle
    assert "=" in puzzle

    result = solve(puzzle, max_solutions=1)
    assert result.solutions