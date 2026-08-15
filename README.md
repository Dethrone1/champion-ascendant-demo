# Champion Ascendant

This is the public portfolio version of the project. The live site publishes the full formula; the calculator in this repo runs a simplified placeholder so the interface still works. See "Scoring model" below.

## What it does

The site ranks unsigned MMA prospects on a 0–100 signing-readiness score across two pathways — ONE Championship and Dana White's Contender Series. Each pathway weights fighter stats differently because the two promotions sign different kinds of fighters. The calculator takes a fighter's stats (finish rate, win rate, age, promotion, region, etc.) and returns a score with a component breakdown so you can see why the number came out the way it did.

There are also ranked prospect boards for both pathways.

## Stack

- Backend: Python / Flask
- Frontend: HTML, CSS, vanilla JavaScript (no framework)
- Hosting: Railway

The scoring runs client-side in JavaScript. Flask serves four routes and the page templates.

## Structure

```
app.py                  Flask app and routes
templates/
  index.html            Calculator + methodology page
  prospects.html        ONE ranked prospect list
  dwcs.html             DWCS ranked prospect list
  receipts.html         Scoring receipts
requirements.txt        Python dependencies
railway.json            Deployment config
```

## Running locally

```
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Scoring model

The live site publishes the full ASCENT formula — component weights, promotion pipeline tables, and weight-class normalization — on the Factors page. Nothing is hidden; every score reproduces by hand from published inputs.

This repo is a portfolio snapshot and lags the live build. The calculator here runs a simplified placeholder so the UI is interactive, but its numbers are illustrative and won't match production. Use championascendant.com for real scores.

Happy to walk through the calibration process and the dataset in an interview.
