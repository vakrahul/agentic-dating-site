import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

tokens = [
    ("Token 1", os.getenv("APIFY_TOKEN")),
    ("Token 2", os.getenv("APIfY_TOKEN_2")),
]

for name, t in tokens:
    if not t:
        print(f"{name}: NOT SET")
        continue
    c = ApifyClient(t)
    try:
        user = c.user().get()
        print(f"{name}: username={getattr(user, 'username', None)}, id={getattr(user, 'id', None)}, plan={getattr(user, 'plan', None)}")
    except Exception as e:
        print(f"{name} error: {e}")
