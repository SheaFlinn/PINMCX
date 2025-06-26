import unittest
from datetime import datetime, timedelta
from app import create_app
from app.models import User, db
from app.services import PointsService

class TestPointsService(unittest.TestCase):
    def setUp(self):
        """Setup test environment with in-memory SQLite"""
        self.app = create_app("testing")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            current_streak=0,
            longest_streak=0,
            last_check_in_date=None,
            xp=0
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        """Cleanup after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_award_xp_streak_bonus(self):
        """Test XP streak bonus calculation"""
        base_xp = 100

        # Day 1: First award (no streak)
        PointsService.award_xp(self.user, base_xp)
        self.assertEqual(self.user.xp, base_xp)  # 100 * 1.0 = 100
        self.assertEqual(self.user.current_streak, 1)
        self.assertEqual(self.user.longest_streak, 1)

        # Simulate next day by setting last_check_in_date to yesterday
        self.user.last_check_in_date -= timedelta(days=1)
        db.session.commit()

        # Day 2: Second award (streak bonus applies)
        PointsService.award_xp(self.user, base_xp)
        self.assertEqual(self.user.xp, base_xp + base_xp * 1.1)  # 100 + 110 = 210
        self.assertEqual(self.user.current_streak, 2)
        self.assertEqual(self.user.longest_streak, 2)

        # Test missed day (reset streak)
        # Set last check-in to 2 days ago
        self.user.last_check_in_date = datetime.utcnow() - timedelta(days=2)
        db.session.commit()

        PointsService.award_xp(self.user, base_xp)
        self.assertEqual(self.user.xp, base_xp + base_xp * 1.1 + base_xp)  # 100 + 110 + 100 = 310
        self.assertEqual(self.user.current_streak, 1)
        self.assertEqual(self.user.longest_streak, 2)  # Longest streak remains 2

        # Test streak cap (should max at 2.0 multiplier)
        for i in range(10):  # Simulate 10 consecutive days
            # Set last_check_in_date to yesterday to simulate a new consecutive day
            self.user.last_check_in_date = datetime.utcnow().date() - timedelta(days=1)
            db.session.commit()
            PointsService.award_xp(self.user, base_xp)

        # After 10 consecutive days, streak should be 11 and XP should be maxed at 2.0 multiplier
        self.assertEqual(self.user.current_streak, 11)
        self.assertEqual(self.user.longest_streak, 11)
        # XP should be 310 from setup + 10-day streak bonuses capped at 2.0x
        looped_bonus = sum([base_xp * min(1.0 + 0.1 * (i + 1), 2.0) for i in range(10)])
        expected_xp = 310 + looped_bonus
        self.assertEqual(self.user.xp, expected_xp)

    def test_award_xp_same_day(self):
        """Test that XP is not awarded multiple times in the same day"""
        base_xp = 100
        PointsService.award_xp(self.user, base_xp)
        
        # Try to award XP again on the same day
        PointsService.award_xp(self.user, base_xp)
        
        # XP should remain the same
        self.assertEqual(self.user.xp, base_xp)  # Only 100 XP awarded
        self.assertEqual(self.user.current_streak, 1)
        self.assertEqual(self.user.longest_streak, 1)
