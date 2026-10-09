from cryptarithm.solver import solve


def test_send_more_money():
    result = solve("SEND + MORE = MONEY")

    assert result.solutions

    mapping = result.solutions[0]
    send = int("".join(str(mapping[letter]) for letter in "SEND"))
    more = int("".join(str(mapping[letter]) for letter in "MORE"))
    money = int("".join(str(mapping[letter]) for letter in "MONEY"))

    assert send + more == money
    assert len(set(mapping.values())) == len(mapping)