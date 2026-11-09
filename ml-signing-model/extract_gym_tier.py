"""
AI step: classify each fighter's gym (from their Sherdog 'Association' field) into a tier
with a language model.

  2 = elite: a globally known camp that regularly sends fighters to the UFC
      (e.g. American Top Team flagship, Kill Cliff FC, Xtreme Couture, Jackson-Wink,
       City Kickboxing, Allstars, Tiger Muay Thai, Chute Boxe Diego Lima, Nova Uniao)
  1 = established: a recognised team or affiliate with some UFC/major-promotion
      alumni (e.g. an ATT affiliate, Team Nogueira, Phuket Top Team)
  0 = regional: a local gym with little or no UFC pipeline

Results are cached in gym_tiers_cache.json, so the notebook runs without an API key.
The cache in this repo was produced with Claude. To rebuild it:
    pip install anthropic && export ANTHROPIC_API_KEY=...
    python extract_gym_tier.py --rebuild
"""
import json, sys, pandas as pd

CACHE = 'gym_tiers_cache.json'
PROMPT = """You are an MMA scouting analyst. Classify this MMA gym / team affiliation.
Affiliation: "{gym}"
Tiers:
2 = elite: globally known camp that regularly sends fighters to the UFC
1 = established: recognised team or branded affiliate with some UFC/major-promotion alumni
0 = regional: local gym with little or no UFC pipeline
If several gyms are listed, use the highest tier. If you do not recognise the gym, answer 0.
Reply with JSON only: {{"tier": <0|1|2>, "label": "<regional|established|elite>"}}"""

def classify(gym, client):
    msg = client.messages.create(model='claude-haiku-5-5', max_tokens=50,
                                 messages=[{'role': 'user', 'content': PROMPT.format(gym=gym)}])
    return json.loads(msg.content[0].text)

if __name__ == '__main__':
    df = pd.read_csv('dwcs_prospects_172.csv')
    gyms = sorted(g for g in df.gym.dropna().unique() if g)
    cache = {} if '--rebuild' in sys.argv else json.load(open(CACHE))
    todo = [g for g in gyms if g not in cache]
    if todo:
        import anthropic
        client = anthropic.Anthropic()
        for g in todo:
            cache[g] = classify(g, client); print(g, '->', cache[g])
        json.dump(cache, open(CACHE, 'w'), indent=1, ensure_ascii=False)
    print(f'{len(gyms)} gyms, {sum(v["tier"] == 2 for v in cache.values())} elite')
