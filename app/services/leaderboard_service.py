from typing import List, Dict, Optional
from app.models import User, db

METRIC_ALIASES = {
    'xp': 'xp',
    'lb': 'liquidity_buffer_deposit',
    'reliability': 'reliability_index'
}

class LeaderboardService:
    """
    Service for managing and retrieving leaderboard data.
    Supports sorting by XP, Liquidity Buffer, and Reliability Index.
    """

    @staticmethod
    def get_leaderboard(metric: str = 'xp', limit: int = 20) -> List[Dict]:
        """
        Get top users sorted by specified metric.

        Args:
            metric: Sorting metric ('xp', 'lb', 'reliability')
            limit: Number of users to return

        Returns:
            List of user dicts containing id, username, and metric_value
        """
        # Normalize metric using aliases and fallback to 'xp' if invalid
        metric = METRIC_ALIASES.get(metric.lower(), 'xp')

        # Query users with their metric value
        query = User.query
        
        # Apply sorting based on metric
        if metric == 'xp':
            query = query.order_by(User.xp.desc())
        elif metric == 'liquidity_buffer_deposit':
            query = query.order_by(User.liquidity_buffer_deposit.desc())
        elif metric == 'reliability_index':
            query = query.order_by(User.reliability_index.desc())

        # Apply limit and get results
        users = query.limit(limit).all()

        # Format results
        return [{
            'id': user.id,
            'username': user.username,
            'metric_value': getattr(user, metric)
        } for user in users]
