from datetime import datetime, timedelta
from app.extensions import db
from app.models import User, Market, Prediction, MarketEvent
from typing import Union, Optional

class PointsService:
    @staticmethod
    def _get_user(user_id_or_obj):
        """Helper method to get user from either ID or User object"""
        if isinstance(user_id_or_obj, User):
            return user_id_or_obj
        elif isinstance(user_id_or_obj, int):
            return db.session.get(User, user_id_or_obj)
        raise ValueError("Input must be a User object or user ID")

    @staticmethod
    def award_xp(user_id: int, amount: int) -> Optional[int]:
        """Add XP to user by ID"""
        user = db.session.get(User, user_id)
        if user:
            user.xp = (user.xp or 0) + amount
            db.session.commit()
            return user.xp
        return None

    @staticmethod
    def get_user_xp(user_id: int) -> Optional[int]:
        """Get user's XP points by ID"""
        user = db.session.get(User, user_id)
        return user.xp if user else None

    @staticmethod
    def get_user_streak(user_id: int) -> Optional[dict]:
        """Get user's streak information
        
        Returns:
            dict: {
                "current_streak": int,
                "longest_streak": int,
                "last_check_in": datetime
            }
            None: if user not found
        """
        user = db.session.get(User, user_id)
        if user:
            return {
                "current_streak": user.current_streak,
                "longest_streak": user.longest_streak,
                "last_check_in": user.last_check_in_date
            }
        return None

    @staticmethod
    def get_total_points(user_id_or_obj: Union[User, int]) -> Optional[int]:
        """Get user's total points (regular points + liquidity buffer)"""
        user = PointsService._get_user(user_id_or_obj)
        if not user:
            return None
        return user.points + user.lb_deposit

    @staticmethod
    def predict(user_id: int, market_id: int, choice: str, stake_amount: int) -> Optional[dict]:
        """Create a new prediction for a user
        
        Args:
            user_id: ID of the user making the prediction
            market_id: ID of the market being predicted on
            choice: Prediction choice ('YES' or 'NO')
            stake_amount: Amount of points to stake
            
        Returns:
            dict: {
                "success": bool,
                "prediction_id": int,
                "remaining_points": int,
                "message": str
            } or None if validation fails
        """
        # Validate choice
        if choice not in ['YES', 'NO']:
            return {
                "success": False,
                "message": "Invalid choice. Must be 'YES' or 'NO'"
            }

        # Fetch user
        user = db.session.get(User, user_id)
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        # Fetch market
        market = db.session.get(Market, market_id)
        if not market:
            return {
                "success": False,
                "message": "Market not found"
            }

        # Validate market state
        if market.resolved:
            return {
                "success": False,
                "message": "Market is resolved and cannot accept new predictions"
            }

        # Validate points
        if user.points < stake_amount:
            return {
                "success": False,
                "message": "Insufficient points",
                "required_points": stake_amount,
                "available_points": user.points
            }

        # Deduct points
        user.points -= stake_amount

        # Calculate price based on market state
        if choice == 'YES':
            # For YES predictions, price is stake amount (simplified for now)
            price = stake_amount
        else:
            # For NO predictions, price is negative stake amount
            price = -stake_amount

        # Create prediction
        prediction = Prediction(
            user_id=user_id,
            market_id=market_id,
            outcome=True if choice == 'YES' else False,
            shares=stake_amount,
            shares_purchased=stake_amount,
            stake=stake_amount,
            price=price,
            created_at=datetime.utcnow()
        )

        db.session.add(prediction)
        db.session.commit()

        # Log prediction event
        prediction.log_prediction_event()

        return {
            "success": True,
            "prediction_id": prediction.id,
            "remaining_points": user.points,
            "message": "Prediction created successfully",
            "price": price
        }

    @staticmethod
    def resolve_market(market_id: int, winning_choice: str) -> Optional[dict]:
        """
        Resolve a market and award points to winners.
        
        Args:
            market_id: ID of the market to resolve
            winning_choice: 'YES' or 'NO'
        
        Returns:
            dict: {
                "market_id": int,
                "winning_choice": str,
                "winners": list[int]
            } or None if market is invalid or already resolved
        """
        # Validate winning choice
        if winning_choice not in ['YES', 'NO']:
            return None

        # Get market
        market = db.session.get(Market, market_id)
        if not market:
            return None

        # Check if market is already resolved
        if market.resolved:
            return None

        # Resolve market
        market.resolved = True
        market.resolved_outcome = winning_choice
        market.resolved_at = datetime.utcnow()

        # Get all predictions for this market
        predictions = db.session.query(Prediction).filter_by(market_id=market_id).all()
        winners = []

        # Process each prediction
        for prediction in predictions:
            # Only award points for correct predictions
            if (prediction.outcome and winning_choice == 'YES') or (not prediction.outcome and winning_choice == 'NO'):
                user = db.session.get(User, prediction.user_id)
                if user:
                    # Double the stake amount as reward
                    reward = prediction.stake * 2
                    user.points += reward
                    winners.append(user.id)

                    # Create prediction resolution event
                    event = MarketEvent(
                        market_id=market_id,
                        user_id=user.id,
                        event_type='prediction_resolved',
                        description=f'Prediction {prediction.id} resolved correctly with outcome {winning_choice}',
                        event_data={
                            'prediction_id': prediction.id,
                            'outcome': winning_choice,
                            'points_awarded': reward,
                            'xp_awarded': False  # XP is awarded separately through market.award_xp_for_predictions()
                        }
                    )
                    db.session.add(event)

        # Commit changes
        db.session.commit()

        return {
            "market_id": market_id,
            "winning_choice": winning_choice,
            "winners": winners
        }
