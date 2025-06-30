from app import db, create_app
from app.models import Badge, League
import json
import os

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

def create_test_contracts():
    """Create test contract data for the trade engine."""
    contracts = [
        {
            "id": "contract_123",
            "title": "Test Contract 1",
            "description": "A test contract for trading",
            "total_yes": 0,
            "total_no": 0,
            "odds_yes": 0.5,
            "odds_no": 0.5,
            "status": "active"
        },
        {
            "id": "contract_456",
            "title": "Test Contract 2",
            "description": "Another test contract",
            "total_yes": 0,
            "total_no": 0,
            "odds_yes": 0.5,
            "odds_no": 0.5,
            "status": "active"
        }
    ]
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname("live/priced_contracts.json"), exist_ok=True)
    
    # Save contracts
    with open("live/priced_contracts.json", 'w') as f:
        json.dump(contracts, f, indent=2)
    
    print("✅ Created test contracts:")
    for contract in contracts:
        print(f"- Contract ID: {contract['id']}")
        print(f"  Title: {contract['title']}")
        print(f"  Initial Odds: YES={contract['odds_yes']}, NO={contract['odds_no']}\n")

def main():
    app = create_app()
    with app.app_context():
        print("Seeding database...")
        seed_badges()
        seed_leagues()
        print("Database seeding complete!")
        create_test_contracts()

if __name__ == '__main__':
    main()
