import unittest
from app import create_app
from app.models import User, db
from app.services.leaderboard_service import LeaderboardService

class LeaderboardServiceTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users with varying values
        self.users = [
            User(username="xp_user", email="xp@example.com", xp=5000, liquidity_buffer_deposit=1000, reliability_index=0.95),
            User(username="lb_user", email="lb@example.com", xp=3000, liquidity_buffer_deposit=5000, reliability_index=0.85),
            User(username="reliability_user", email="reliability@example.com", xp=4000, liquidity_buffer_deposit=2000, reliability_index=0.98),
            User(username="average_user", email="avg@example.com", xp=2000, liquidity_buffer_deposit=1500, reliability_index=0.88)
        ]
        db.session.add_all(self.users)
        db.session.commit()

    def tearDown(self):
        """Tear down test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_xp_leaderboard(self):
        """Test XP leaderboard ordering"""
        result = LeaderboardService.get_leaderboard()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['username'], "xp_user")
        self.assertEqual(result[0]['metric_value'], 5000)
        self.assertEqual(result[1]['username'], "reliability_user")
        self.assertEqual(result[1]['metric_value'], 4000)

    def test_lb_leaderboard(self):
        """Test LB leaderboard ordering"""
        result = LeaderboardService.get_leaderboard(metric="lb")
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['username'], "lb_user")
        self.assertEqual(result[0]['metric_value'], 5000)
        self.assertEqual(result[1]['username'], "reliability_user")
        self.assertEqual(result[1]['metric_value'], 2000)

    def test_reliability_leaderboard(self):
        """Test reliability leaderboard ordering"""
        result = LeaderboardService.get_leaderboard(metric="reliability")
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['username'], "reliability_user")
        self.assertEqual(result[0]['metric_value'], 0.98)
        self.assertEqual(result[1]['username'], "xp_user")
        self.assertEqual(result[1]['metric_value'], 0.95)

    def test_invalid_metric_fallback(self):
        """Test invalid metric falls back to XP"""
        result = LeaderboardService.get_leaderboard(metric="invalid_metric")
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['username'], "xp_user")
        self.assertEqual(result[0]['metric_value'], 5000)

    def test_limit_applies(self):
        """Test that limit parameter works correctly"""
        result = LeaderboardService.get_leaderboard(limit=2)
        self.assertEqual(len(result), 2)

    def test_case_insensitive_metrics(self):
        """Test that metric is case-insensitive"""
        result = LeaderboardService.get_leaderboard(metric="LB")
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['username'], "lb_user")
        self.assertEqual(result[0]['metric_value'], 5000)

if __name__ == '__main__':
    unittest.main()
