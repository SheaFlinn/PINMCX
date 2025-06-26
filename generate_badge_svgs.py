import os

BADGE_DIR = "static/badges"

BADGES = {
    "master_predictor.svg": """<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#FFD700" stroke="#000" stroke-width="2"/>
    <path d="M50 25 L75 50 L50 75 L25 50 Z" fill="#000"/>
    <text x="50" y="55" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Master</text>
    <text x="50" y="70" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Predictor</text>
</svg>""",
    "expert_forecaster.svg": """<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#4CAF50" stroke="#000" stroke-width="2"/>
    <path d="M50 25 L75 50 L50 75 L25 50 Z" fill="#000"/>
    <path d="M50 30 L50 70" stroke="#000" stroke-width="2"/>
    <text x="50" y="55" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Expert</text>
    <text x="50" y="70" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Forecaster</text>
</svg>""",
    "trading_pro.svg": """<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#2196F3" stroke="#000" stroke-width="2"/>
    <path d="M25 50 L75 50" stroke="#000" stroke-width="2"/>
    <path d="M50 25 L50 75" stroke="#000" stroke-width="2"/>
    <text x="50" y="55" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Trading</text>
    <text x="50" y="70" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Pro</text>
</svg>""",
    "liquidity_provider.svg": """<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#00BCD4" stroke="#000" stroke-width="2"/>
    <circle cx="50" cy="50" r="25" fill="#000"/>
    <text x="50" y="55" font-family="Arial" font-size="12" fill="#FFF" text-anchor="middle">Liquidity</text>
    <text x="50" y="70" font-family="Arial" font-size="12" fill="#FFF" text-anchor="middle">Provider</text>
</svg>""",
    "community_leader.svg": """<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#9C27B0" stroke="#000" stroke-width="2"/>
    <path d="M50 25 L75 50 L50 75 L25 50 Z" fill="#000"/>
    <text x="50" y="55" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Community</text>
    <text x="50" y="70" font-family="Arial" font-size="12" fill="#000" text-anchor="middle">Leader</text>
</svg>"""
}

os.makedirs(BADGE_DIR, exist_ok=True)

for filename, content in BADGES.items():
    path = os.path.join(BADGE_DIR, filename)
    with open(path, "w") as f:
        f.write(content)
    print(f"✔ Created {filename}")

