# Cryptarithm Lab

Cryptarithm Lab solves and helps you practice addition cryptarithms such as
`SEND + MORE = MONEY`. Its desktop and Streamlit web apps include a timed
letter-card challenge with Easy (5-minute), Medium (10-minute), and Hard
(30-minute) limits, plus solved and unsolved challenge history.

Puzzle inputs are checked for at most 10 distinct letters, a result length
that can be reached by adding the input words, and shared letters between
words. Leading letters cannot be zero. The challenge checks the submitted
letter-to-digit assignment and shows column/carry steps after each attempt.

## Requirements

- Python 3
- Tkinter (included with most standard Python installations)
- Streamlit (installed from `requirements.txt`)

Install the test dependency with:

```powershell
python -m pip install -r requirements.txt
```

## Run

### Web app

```powershell
python -m streamlit run app.py
```

Practice history in the web app is private to the current browser session and
is cleared when that session ends.

To deploy the web app on [Streamlit Community Cloud](https://share.streamlit.io/):

1. Fork or push this repository to your own GitHub account.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/).
3. Click "New app", select your forked repository and branch (e.g., `main`), and set the main file path to `app.py`.
4. Click "Deploy!" - Streamlit will install dependencies from `requirements.txt` and launch the app.

### Desktop app

```powershell
python app_desktop.py
```

The desktop app saves practice history locally to `data/progress.json`.

## Thinking process and approach

### How the solver works

The solver uses constraint-based backtracking search over digit assignments:

1. **Parse and validate** (`cryptarithm/solver.py`): The puzzle is split into addends and the result (e.g., `SEND + MORE = MONEY`). It validates format, letter uniqueness (max 10 distinct letters), result length feasibility, leading-letter constraints, and that letters are shared between words (to ensure interlocking constraints).
2. **Search strategies** (choose via `solve(..., strategy=...)`):
   - `backtracking`: Assign letters in their original order with basic pruning.
   - `mrv` (Minimum Remaining Values): Prioritize constrained letters first (units column letters, leading letters, and letters appearing in more words) to fail fast.
   - `mrv_fc` (MRV + forward checking): MRV ordering plus column-wise forward checking - after each assignment, verify any column where all addend and result letters are assigned has a consistent carry/mod10; if not, reject early.
3. **Pruning rules**:
   - All letters in a puzzle must get different digits (0-9).
   - Leading letters cannot be 0.
   - After assigning a full column (when all its letters known), `column_sum % 10` must equal the result digit for that column (or be 0 if no result digit), and the carry propagates correctly.
4. **Solution reporting**: The solver returns up to `max_solutions` mappings, search stats (nodes, backtracks, time), a short explanation trace, and the desktop app can show column-by-column carry steps via `solution_steps()`.

### Guide to solving cryptarithms manually

1. **Understand the structure**: Write the addition column by column from right (units) to left, noting carries between columns.
2. **Identify constraints**: List distinct letters, find which are leading (cannot be 0), and note letter frequencies/shared positions.
3. **Start with the units column**: This often has the tightest constraints and no carry-in from the right. Try to deduce possible digit combinations.
4. **Use carry logic**: For each column, `sum of addend digits in column + carry_in ≡ result_digit (mod 10)`, carry_out = floor((sum+carry_in)/10). Carries are 0,1,...,n-1 where n is number of addends.
5. **Apply uniqueness and leading-zero rules**: All assigned digits must be different; first digits of any multi-letter word cannot be 0.
6. **Narrow with arithmetic**: Consider the maximum possible sum of a column to bound carries. Also use the fact that result length can be at most longest addend length + 1.
7. **Try and backtrack**: Make a hypothesis for a constrained letter, propagate implications to other columns, and backtrack if you hit a contradiction.
8. **Verify**: Once you have a full mapping for all letters, compute the actual numbers to confirm the addition holds.

### Tips
- Puzzles in this app require shared letters between words and at most 10 distinct letters (decimal). These constraints are exactly what make them solvable by search.
- Use the "Research" tab to compare strategies and see how pruning affects nodes/backtracks on a given puzzle.

## Tests

```powershell
python -m pytest
```