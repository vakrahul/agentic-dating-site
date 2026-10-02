import asyncio
import sys
sys.path.insert(0, 'backend')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.scrapers.instagram import fetch_instagram
from app.scrapers.linkedin import fetch_linkedin


async def test():
    # Test Instagram
    print("=== INSTAGRAM TEST ===")
    try:
        ig = await fetch_instagram("https://www.instagram.com/garyvee/")
        bio = (ig.get("biography") or "")[:60]
        posts = ig.get("latest_posts") or []
        print(f"OK: @{ig.get('username')} | followers: {ig.get('followers')} | posts scraped: {len(posts)}")
        print(f"   bio: {bio}")
        if posts:
            print(f"   sample post caption: {str(posts[0].get('caption',''))[:80]}")
    except Exception as e:
        print(f"FAIL: {e}")

    # Test LinkedIn
    print("\n=== LINKEDIN TEST ===")
    try:
        li = await fetch_linkedin("https://www.linkedin.com/in/garyvaynerchuk/")
        print(f"OK: name={li.get('name')} | headline={str(li.get('headline',''))[:60]}")
    except Exception as e:
        print(f"FAIL: {e}")


if __name__ == "__main__":
    asyncio.run(test())
