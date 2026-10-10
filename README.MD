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

To publish the web app with Streamlit Community Cloud:

1. Push this repository to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/).
3. Create an app from `PRANEEL-CRICKET/cryptananalysis`, branch `main`, file
   `app.py`.

### Desktop app

```powershell
python app_desktop.py
```

The desktop app saves practice history locally to `data/progress.json`.

## Tests

```powershell
python -m pytest
```