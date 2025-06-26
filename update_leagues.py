from app import db, create_app
from app.models import League, LeagueMember, LeagueEvent, User
from datetime import datetime
import json

def calculate_league_points(user):
    """Calculate league points for a user based on their achievements"""
    points = 0
    
    # Prediction accuracy points
    points += user.reliability_index * 100
    
    # Points won in markets
    points += user.points * 0.1  # 10% of total points
    
    # Prediction volume points
    points += user.predictions_count * 5  # 5 points per prediction
    
    # Trading volume points
    trade_count = sum(
        1 for event in user.market_events
        if event.event_type == 'trade_executed'
    )
    points += trade_count * 2  # 2 points per trade
    
    # Liquidity provision points
    liquidity_count = len({
        event.market_id for event in user.market_events
        if event.event_type == 'liquidity_provided'
    })
    points += liquidity_count * 10  # 10 points per market with liquidity
    
    return int(points)

def update_league_rankings():
    """Update league rankings and distribute rewards"""
    app = create_app()
    with app.app_context():
        print("Updating league rankings...")
        
        # Get all leagues
        leagues = League.query.all()
        
        for league in leagues:
            print(f"Updating {league.name} rankings...")
            
            # Get all members of the league
            members = LeagueMember.query.filter_by(league_id=league.id).all()
            
            # Calculate points for each member
            member_points = []
            for member in members:
                points = calculate_league_points(member.user)
                member_points.append((member, points))
            
            # Sort members by points (descending)
            member_points.sort(key=lambda x: x[1], reverse=True)
            
            # Update rankings and points
            for i, (member, points) in enumerate(member_points, 1):
                # Calculate rank change
                rank_change = member.current_rank - i
                
                # Update member's points and rank
                member.points = points
                member.current_rank = i
                
                # Log the rank change event
                event = LeagueEvent(
                    league_id=league.id,
                    user_id=member.user_id,
                    event_type='rank_change',
                    details={
                        'old_rank': member.current_rank,
                        'new_rank': i,
                        'points': points,
                        'rank_change': rank_change
                    }
                )
                db.session.add(event)
            
            # Distribute rewards based on rank
            for i, (member, points) in enumerate(member_points, 1):
                reward = 0
                
                # Top 10% get 10x rewards
                if i <= len(member_points) * 0.1:
                    reward = points * 0.1
                # Next 20% get 5x rewards
                elif i <= len(member_points) * 0.3:
                    reward = points * 0.05
                # Rest get 2x rewards
                else:
                    reward = points * 0.02
                
                if reward > 0:
                    # Update user's points
                    member.user.points += reward
                    
                    # Log the reward event
                    event = LeagueEvent(
                        league_id=league.id,
                        user_id=member.user_id,
                        event_type='reward_earned',
                        details={
                            'rank': i,
                            'reward': reward,
                            'reason': 'weekly_ranking'
                        }
                    )
                    db.session.add(event)
            
            db.session.commit()
            print(f"Updated {len(member_points)} members in {league.name}")
        
        print("League rankings update complete!")

if __name__ == '__main__':
    update_league_rankings()
