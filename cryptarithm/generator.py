import random
import string


def generate_puzzle(difficulty="Easy", seed=None):
    """Generate a solvable addition puzzle."""
    widths = {"Easy": 1, "Medium": 2, "Hard": 3}

    if difficulty not in widths:
        raise ValueError("Choose Easy, Medium, or Hard.")

    rng = random.Random(seed)
    digit_to_letter = dict(
        zip(range(10), rng.sample(string.ascii_uppercase, 10))
    )

    width = widths[difficulty]
    smallest = 10 ** (width - 1)
    largest = (10 ** width) - 1

    left = rng.randint(smallest, largest)
    right = rng.randint(smallest, largest)
    total = left + right

    def to_word(number):
        return "".join(digit_to_letter[int(digit)] for digit in str(number))

    return f"{to_word(left)} + {to_word(right)} = {to_word(total)}"