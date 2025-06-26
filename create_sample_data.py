from app import db, create_app
from app.models import User, Market, Prediction, Badge, League, LeagueMember, LeagueEvent
from datetime import datetime, timedelta
import random
import json

def create_sample_users():
    """Create sample users with varying stats"""
    users = [
        {
            'username': 'master_predictor',
            'email': 'master@predictor.com',
            'points': 50000,
            'predictions_count': 1000,
            'reliability_index': 0.92
        },
        {
            'username': 'expert_forecaster',
            'email': 'expert@forecaster.com',
            'points': 25000,
            'predictions_count': 500,
            'reliability_index': 0.85
        },
        {
            'username': 'trading_pro',
            'email': 'trader@pro.com',
            'points': 10000,
            'predictions_count': 200,
            'reliability_index': 0.80
        },
        {
            'username': 'liquidity_provider',
            'email': 'lp@provider.com',
            'points': 5000,
            'predictions_count': 100,
            'reliability_index': 0.75
        },
        {
            'username': 'community_leader',
            'email': 'leader@community.com',
            'points': 2000,
            'predictions_count': 50,
            'reliability_index': 0.70
        }
    ]
    
    for user_data in users:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            points=user_data['points'],
            predictions_count=user_data['predictions_count'],
            reliability_index=user_data['reliability_index']
        )
        user.set_password('password123')  # Set a default password
        db.session.add(user)
    
    db.session.commit()
    print(f"Created {len(users)} sample users")

def create_sample_markets():
    """Create sample markets with varying outcomes"""
    markets = [
        {
            'title': 'Will the city council approve the new public transportation plan?',
            'domain': 'Transportation',
            'resolved_outcome': True,
            'resolved_at': datetime.now() - timedelta(days=7)
        },
        {
            'title': 'Will the new recycling program be implemented?',
            'domain': 'Environment',
            'resolved_outcome': False,
            'resolved_at': datetime.now() - timedelta(days=14)
        },
        {
            'title': 'Will the school board pass the new budget?',
            'domain': 'Education',
            'resolved_outcome': True,
            'resolved_at': datetime.now() - timedelta(days=21)
        }
    ]
    
    for market_data in markets:
        market = Market(
            title=market_data['title'],
            domain=market_data['domain'],
            resolved_outcome=market_data['resolved_outcome'],
            resolved_at=market_data['resolved_at'],
            yes_pool=1000,
            no_pool=1000
        )
        db.session.add(market)
    
    db.session.commit()
    print(f"Created {len(markets)} sample markets")

def create_sample_predictions():
    """Create sample predictions for users"""
    users = User.query.all()
    markets = Market.query.all()
    
    for user in users:
        for market in markets:
            # Randomly decide if user made a prediction
            if random.random() < 0.8:  # 80% chance of making a prediction
                prediction = Prediction(
                    user_id=user.id,
                    market_id=market.id,
                    outcome=random.choice([True, False]),
                    shares=random.randint(1, 100),
                    average_price=random.uniform(0.1, 0.9)
                )
                db.session.add(prediction)
    
    db.session.commit()
    print("Created sample predictions")

def create_sample_league_members():
    """Create sample league members"""
    users = User.query.all()
    leagues = League.query.all()
    
    # Assign users to leagues based on their stats
    for user in users:
        # Find the highest tier league they qualify for
        for league in sorted(leagues, key=lambda l: l.tier, reverse=True):
            requirements = league.requirements
            
            if (user.points >= requirements.get('points', 0) and
                user.predictions_count >= requirements.get('predictions', 0) and
                user.reliability_index >= requirements.get('reliability', 0)):
                
                # Check if league has space
                current_members = LeagueMember.query.filter_by(league_id=league.id).count()
                if current_members < league.max_members:
                    member = LeagueMember(
                        user_id=user.id,
                        league_id=league.id,
                        current_rank=current_members + 1,
                        points=calculate_league_points(user)
                    )
                    db.session.add(member)
                    break
    
    db.session.commit()
    print("Created sample league members")

def calculate_league_points(user):
    """Calculate league points for a user"""
    points = 0
    points += user.reliability_index * 100
    points += user.points * 0.1
    points += user.predictions_count * 5
    return int(points)

def main():
    app = create_app()
    with app.app_context():
        print("Creating sample data...")
        
        # Create sample users
        create_sample_users()
        
        # Create sample markets
        create_sample_markets()
        
        # Create sample predictions
        create_sample_predictions()
        
        # Create sample league members
        create_sample_league_members()
        
        print("Sample data creation complete!")

if __name__ == '__main__':
    main()
