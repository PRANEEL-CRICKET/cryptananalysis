import pytest

from cryptarithm.solver import (
    check_solution,
    parse_puzzle,
    solution_steps,
    solve,
)


def test_send_more_money():
    result = solve("SEND + MORE = MONEY")

    assert result.solutions

    mapping = result.solutions[0]
    send = int("".join(str(mapping[letter]) for letter in "SEND"))
    more = int("".join(str(mapping[letter]) for letter in "MORE"))
    money = int("".join(str(mapping[letter]) for letter in "MONEY"))

    assert send + more == money
    assert len(set(mapping.values())) == len(mapping)
    assert check_solution(result.puzzle, mapping)
    assert len(solution_steps(result.puzzle, mapping)) == len("MONEY")


@pytest.mark.parametrize(
    ("equation", "reason"),
    [
        ("ABCDEFGHIJK + A = B", "at most 10 distinct letters"),
        ("CAT + DOG = ANIMAL", "at most 4 digits"),
        ("ABC + DEF = GHIJ", "do not share any letters"),
    ],
)
def test_rejects_puzzles_that_break_generation_rules(equation, reason):
    with pytest.raises(ValueError, match=reason):
        parse_puzzle(equation)


def test_check_solution_rejects_invalid_digit_assignments():
    puzzle = parse_puzzle("SEND + MORE = MONEY")

    assert not check_solution(puzzle, {"S": 9})