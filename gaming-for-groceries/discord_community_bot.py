import sys
import json
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# GG LOOP Discord Community Engine Spec
COMMUNITY_CONFIG = {
    "guild_name": "GG LOOP Community & Tournaments",
    "founder": "Jayson Quindao (@djjrip)",
    "official_website": "https://djjrip.github.io/gaming-for-groceries/",
    "bracket_engine": "https://djjrip.github.io/gaming-for-groceries/bracket.html",
    "community_hub": "https://djjrip.github.io/gaming-for-groceries/community.html",
    "sponsor_media_kit": "https://djjrip.github.io/gaming-for-groceries/sponsor.html",
    "prize_pool_breakdown": {
        "1st_place": "$150 Grocery Gift Card (H-E-B, Kroger, Whole Foods)",
        "2nd_place": "$75 Grocery Gift Card",
        "3rd_place": "$40 Grocery Gift Card"
    },
    "channels": [
        {"name": "📢│announcements", "purpose": "Official tournament dates, rule changes, sponsor highlights"},
        {"name": "🏆│live-brackets", "purpose": "Live updates from djjrip.github.io/gaming-for-groceries/bracket.html"},
        {"name": "♟️│chess-arena", "purpose": "Lichess game links, Blitz tournaments, tactic discussions"},
        {"name": "🎯│fps-valorant", "purpose": "Custom 10-man lobbies, aim duel brackets, team finding"},
        {"name": "🃏│tcg-tabletop", "purpose": "Partner store meetups, deck lists, regional qualifiers"},
        {"name": "💼│sponsors-partners", "purpose": "DFW local brands, discount codes (e.g. GGLOOP20), venue announcements"}
    ]
}

def print_community_manifest():
    print("========================================================")
    print("🎮 GG LOOP DISCORD & COMMUNITY ARCHITECTURE")
    print("========================================================\n")
    print(f"Community: {COMMUNITY_CONFIG['guild_name']}")
    print(f"Founder: {COMMUNITY_CONFIG['founder']}")
    print(f"Portal: {COMMUNITY_CONFIG['community_hub']}")
    print(f"Brackets: {COMMUNITY_CONFIG['bracket_engine']}\n")
    print("--- CHANNEL SPECIFICATION ---")
    for ch in COMMUNITY_CONFIG["channels"]:
        print(f"  • {ch['name']} — {ch['purpose']}")
    print("\n--- REWARD MATRIX ---")
    for rank, reward in COMMUNITY_CONFIG["prize_pool_breakdown"].items():
        print(f"  • {rank.upper()}: {reward}")
    print("\n✅ COMMUNITY ENGINE MANIFEST INITIALIZED!")

if __name__ == '__main__':
    print_community_manifest()
