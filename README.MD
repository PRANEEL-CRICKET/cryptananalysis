# Cryptarithm Lab

A desktop application for solving and practicing addition cryptarithms such as
`SEND + MORE = MONEY`. It can generate puzzles, display solver details, and
track practice progress locally.

## Requirements

- Python 3
- Tkinter (included with most standard Python installations)

Install the test dependency with:

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python app.py
```

Practice history is saved to `data/progress.json` on this computer and is not
included in Git.

## Tests

```powershell
python -m pytest
```