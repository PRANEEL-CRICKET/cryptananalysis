# Cryptarithm Lab

Cryptarithm Lab solves and helps you practice addition cryptarithms such as
`SEND + MORE = MONEY`. It includes a desktop app and a Streamlit web app.

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
python -m streamlit run app_web.py
```

Practice history in the web app is private to the current browser session and
is cleared when that session ends.

To publish the web app with Streamlit Community Cloud:

1. Push this repository to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/).
3. Create an app from `PRANEEL-CRICKET/cryptananalysis`, branch `main`, file
   `app_web.py`.

### Desktop app

```powershell
python app.py
```

The desktop app saves practice history locally to `data/progress.json`.

## Tests

```powershell
python -m pytest
```