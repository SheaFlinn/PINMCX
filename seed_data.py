from app import db, create_app
from app.models import Badge, League
import json

def seed_badges():
    """Seed the database with initial badges"""
    badges = [
        {
            'name': 'Master Predictor',
            'description': 'Achieve 90%+ prediction accuracy',
            'icon': 'master_predictor.png',
            'category': 'Prediction',
            'requirements': {'reliability': 0.9},
            'rarity': 'Legendary'
        },
        {
            'name': 'Expert Forecaster',
            'description': 'Achieve 80-89% prediction accuracy',
            'icon': 'expert_forecaster.png',
            'category': 'Prediction',
            'requirements': {'reliability': 0.8},
            'rarity': 'Epic'
        },
        {
            'name': 'Trading Pro',
            'description': 'Execute 1000+ trades',
            'icon': 'trading_pro.png',
            'category': 'Trading',
            'requirements': {'trades': 1000},
            'rarity': 'Rare'
        },
        {
            'name': 'Liquidity Provider',
            'description': 'Provide liquidity to 10+ markets',
            'icon': 'liquidity_provider.png',
            'category': 'Trading',
            'requirements': {'markets': 10},
            'rarity': 'Uncommon'
        },
        {
            'name': 'Community Leader',
            'description': 'Invite 10+ users to the platform',
            'icon': 'community_leader.png',
            'category': 'Community',
            'requirements': {'invites': 10},
            'rarity': 'Rare'
        }
    ]
    
    for badge_data in badges:
        badge = Badge(**badge_data)
        db.session.add(badge)
    
    db.session.commit()
    print(f"Created {len(badges)} badges")

def seed_leagues():
    """Seed the database with initial leagues"""
    leagues = [
        {
            'name': 'Bronze League',
            'description': 'Entry-level competitive league for new players',
            'tier': 1,
            'requirements': {
                'points': 1000,
                'predictions': 50,
                'reliability': 0.7
            },
            'max_members': 50
        },
        {
            'name': 'Silver League',
            'description': 'Intermediate league for experienced players',
            'tier': 2,
            'requirements': {
                'points': 5000,
                'predictions': 100,
                'reliability': 0.75
            },
            'max_members': 30
        },
        {
            'name': 'Gold League',
            'description': 'Advanced league for top players',
            'tier': 3,
            'requirements': {
                'points': 10000,
                'predictions': 200,
                'reliability': 0.8
            },
            'max_members': 20
        },
        {
            'name': 'Platinum League',
            'description': 'Elite league for expert players',
            'tier': 4,
            'requirements': {
                'points': 25000,
                'predictions': 500,
                'reliability': 0.85
            },
            'max_members': 10
        },
        {
            'name': 'Diamond League',
            'description': 'The most prestigious league for master players',
            'tier': 5,
            'requirements': {
                'points': 50000,
                'predictions': 1000,
                'reliability': 0.9
            },
            'max_members': 5
        }
    ]
    
    for league_data in leagues:
        league = League(**league_data)
        db.session.add(league)
    
    db.session.commit()
    print(f"Created {len(leagues)} leagues")

def main():
    app = create_app()
    with app.app_context():
        print("Seeding database...")
        seed_badges()
        seed_leagues()
        print("Database seeding complete!")

if __name__ == '__main__':
    main()
