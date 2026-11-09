"""
Retrain the DWCS/UFC signing model with one command.

    python retrain.py            # retrain, log the run, keep the new model only if it isn't worse
    python retrain.py --force    # keep the new model even if its score dropped

When to run it:
  1. After re-checking outcomes (some "not signed" fighters get the call later: flip 0 -> 1 in the CSV)
  2. After adding a new batch of verified fighters (stats as of their snapshot bout)

Every run is appended to retrain_log.csv (date, fighters, signed, AUC, kept or not),
so you can see whether new data made the model better or worse.
"""
import sys, json, datetime as dt
from pathlib import Path
import numpy as np, pandas as pd, joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score

HERE = Path(__file__).parent
DATA, LOG, MODEL = HERE / 'dwcs_prospects_172.csv', HERE / 'retrain_log.csv', HERE / 'model.joblib'
FEATS = ['wins', 'losses', 'fights', 'win_pct', 'undefeated', 'finish_rate', 'win_streak', 'title_win', 'age']
TOLERANCE = 0.02   # a drop smaller than this is treated as noise, not a regression


def load():
    df = pd.read_csv(DATA)
    df['fights'] = df.wins + df.losses + df.draws
    df['win_pct'] = np.where(df.fights > 0, df.wins / df.fights * 100, np.nan)
    df['undefeated'] = (df.losses == 0).astype(int)
    return df[FEATS], df.signed


def build():
    return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                         LogisticRegression(C=0.5, max_iter=1000))


def main(force=False):
    X, y = load()
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=42)
    auc = cross_val_score(build(), X, y, cv=cv, scoring='roc_auc')
    run = {'date': dt.date.today().isoformat(), 'fighters': len(y), 'signed': int(y.sum()),
           'auc': round(auc.mean(), 3), 'auc_low': round(np.percentile(auc, 5), 3),
           'auc_high': round(np.percentile(auc, 95), 3)}

    prev = pd.read_csv(LOG).iloc[-1] if LOG.exists() and LOG.stat().st_size else None
    prev_kept = None
    if prev is not None:
        kept = pd.read_csv(LOG).query('kept == True')
        prev_kept = kept.iloc[-1] if len(kept) else None
    worse = prev_kept is not None and run['auc'] < prev_kept['auc'] - TOLERANCE
    run['kept'] = force or not worse

    if run['kept']:
        joblib.dump({'model': build().fit(X, y), 'features': FEATS, 'trained': run['date']}, MODEL)
    pd.DataFrame([run]).to_csv(LOG, mode='a', header=not LOG.exists(), index=False)

    print(f"{run['fighters']} fighters ({run['signed']} signed)  AUC {run['auc']}  "
          f"(5th-95th pct {run['auc_low']}-{run['auc_high']})")
    if prev_kept is not None:
        print(f"Last kept model: AUC {prev_kept['auc']} on {prev_kept['fighters']} fighters ({prev_kept['date']})")
    print('Saved model.joblib' if run['kept'] else
          f'NOT saved: AUC dropped more than {TOLERANCE}. Check the new data, or rerun with --force.')


if __name__ == '__main__':
    main(force='--force' in sys.argv)
