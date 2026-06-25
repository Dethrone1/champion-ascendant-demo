# Champion Ascendant

MMA analytics platform that scores unsigned fighters on how ready they are to
get signed by a major promotion. Built around ASCENT, a scoring model I
developed from several years of real ONE Championship and DWCS signing data.

This is the public portfolio version of the project. The scoring model itself
is proprietary and is not included here — the calculator on this build runs a
simplified placeholder formula so the interface still works. See "Scoring model"
below.

## What it does

The site ranks unsigned MMA prospects on a 0–100 signing-readiness score across
two pathways — ONE Championship and Dana White's Contender Series. Each pathway
weights fighter stats differently because the two promotions sign different
kinds of fighters. The calculator takes a fighter's stats (finish rate, win
rate, age, promotion, region, etc.) and returns a score with a component
breakdown so you can see why the number came out the way it did.

There's also a prospects page listing scored fighters.

## Stack

- Backend: Python / Flask
- Frontend: HTML, CSS, vanilla JavaScript (no framework)
- Hosting: Railway

The scoring runs client-side in JavaScript. Flask serves two routes and the
page templates.

## Structure

```
app.py            Flask app and routes
templates/
  index.html      Calculator + methodology page
  prospects.html  Ranked prospect list
requirements.txt  Python dependencies
railway.json      Deployment config
```

## Running locally

```
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Scoring model

The real ASCENT model — the component weights, promotion pipeline tables,
weight-class normalization, and bonus logic — is proprietary and kept private,
since I treat this project as a potential product. The calculator in this public
repo uses a simplified placeholder so the UI is fully interactive; its scores
are illustrative and do not reflect the production model.

I'm happy to walk through the real architecture and modeling approach in an
interview.
