#!/usr/bin/env python3
"""
Institutional Gamification System - Civic Engagement Analytics

Comprehensive gamification and user engagement system for Memphis civic prediction market.
Tracks user behavior, streaks, achievements, and civic engagement metrics.

Features:
- XP/Points system with civic engagement weighting
- Streak tracking and habit formation analytics
- Achievement badges and milestone recognition
- Leaderboards and community engagement metrics
- Institutional-grade analytics and reporting

Version: July_27_2025v1_InstitutionalGamification
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class UserEngagementMetrics:
    """User engagement and gamification metrics"""
    user_id: str
    total_xp: int
    current_streak: int
    longest_streak: int
    total_predictions: int
    correct_predictions: int
    civic_engagement_score: float
    last_activity: str
    achievements: List[str]
    level: int
    rank: str

@dataclass
class Achievement:
    """Achievement definition"""
    achievement_id: str
    name: str
    description: str
    category: str  # PREDICTION, STREAK, CIVIC, COMMUNITY
    criteria: Dict[str, Any]
    xp_reward: int
    badge_icon: str
    rarity: str  # COMMON, RARE, EPIC, LEGENDARY

class InstitutionalGamificationSystem:
    """Institutional-grade gamification and engagement system"""
    
    def __init__(self, db_path: str = "mcx_points.db"):
        self.db_path = db_path
        
        # Initialize database
        self._init_gamification_database()
        
        # Initialize logging
        self._init_gamification_logging()
        
        # Load achievements
        self.achievements = self._load_achievements()
        
        # XP and level configuration
        self.xp_config = {
            'prediction_made': 10,
            'correct_prediction': 50,
            'streak_bonus_multiplier': 1.5,
            'civic_engagement_bonus': 25,
            'daily_login': 5,
            'first_prediction_of_day': 15,
            'community_interaction': 20
        }
        
        self.level_thresholds = [
            100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000  # Levels 1-10
        ]
        
        self.rank_titles = [
            "Civic Newcomer", "Local Observer", "Community Participant", "Civic Enthusiast",
            "Memphis Insider", "Policy Tracker", "Civic Expert", "Community Leader",
            "Memphis Oracle", "Civic Legend"
        ]
        
    def _init_gamification_database(self):
        """Initialize gamification database tables"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create user engagement metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_engagement_metrics (
                user_id TEXT PRIMARY KEY,
                total_xp INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                civic_engagement_score REAL DEFAULT 0.0,
                last_activity TEXT,
                level INTEGER DEFAULT 1,
                rank TEXT DEFAULT 'Civic Newcomer',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id TEXT,
                achievement_id TEXT,
                earned_at TEXT,
                xp_awarded INTEGER,
                PRIMARY KEY (user_id, achievement_id)
            )
        ''')
        
        # Create daily activity table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_activity (
                user_id TEXT,
                activity_date TEXT,
                predictions_made INTEGER DEFAULT 0,
                xp_earned INTEGER DEFAULT 0,
                streak_day INTEGER DEFAULT 0,
                civic_actions INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, activity_date)
            )
        ''')
        
        # Create leaderboard snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                snapshot_date TEXT,
                leaderboard_type TEXT,
                leaderboard_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _init_gamification_logging(self):
        """Initialize gamification logging"""
        
        self.gamification_logger = logging.getLogger('institutional_gamification')
        self.gamification_logger.setLevel(logging.INFO)
        
        # Create file handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'gamification.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.gamification_logger.addHandler(file_handler)
        
    def _load_achievements(self) -> List[Achievement]:
        """Load achievement definitions"""
        
        return [
            Achievement(
                achievement_id="first_prediction",
                name="First Prediction",
                description="Made your first civic prediction",
                category="PREDICTION",
                criteria={"total_predictions": 1},
                xp_reward=25,
                badge_icon="🎯",
                rarity="COMMON"
            ),
            Achievement(
                achievement_id="prediction_streak_7",
                name="Week Warrior",
                description="Made predictions for 7 consecutive days",
                category="STREAK",
                criteria={"current_streak": 7},
                xp_reward=100,
                badge_icon="🔥",
                rarity="RARE"
            ),
            Achievement(
                achievement_id="prediction_streak_30",
                name="Monthly Master",
                description="Made predictions for 30 consecutive days",
                category="STREAK",
                criteria={"current_streak": 30},
                xp_reward=500,
                badge_icon="💎",
                rarity="EPIC"
            ),
            Achievement(
                achievement_id="civic_expert",
                name="Civic Expert",
                description="Achieved 80%+ accuracy on civic predictions",
                category="CIVIC",
                criteria={"accuracy_rate": 0.8, "min_predictions": 20},
                xp_reward=300,
                badge_icon="🏛️",
                rarity="EPIC"
            ),
            Achievement(
                achievement_id="memphis_oracle",
                name="Memphis Oracle",
                description="Achieved 90%+ accuracy on 100+ predictions",
                category="CIVIC",
                criteria={"accuracy_rate": 0.9, "min_predictions": 100},
                xp_reward=1000,
                badge_icon="👁️",
                rarity="LEGENDARY"
            ),
            Achievement(
                achievement_id="community_leader",
                name="Community Leader",
                description="Top 10 on monthly leaderboard",
                category="COMMUNITY",
                criteria={"monthly_rank": 10},
                xp_reward=200,
                badge_icon="👑",
                rarity="RARE"
            )
        ]
        
    def award_xp(self, user_id: str, action: str, amount: Optional[int] = None, 
                 contract_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> int:
        """Award XP to user for specific action"""
        
        if amount is None:
            amount = self.xp_config.get(action, 0)
        
        # Get current user metrics
        metrics = self.get_user_metrics(user_id)
        
        # Apply streak bonus if applicable
        if action in ['correct_prediction', 'prediction_made'] and metrics.current_streak > 0:
            streak_bonus = int(amount * (self.xp_config['streak_bonus_multiplier'] - 1) * min(metrics.current_streak / 10, 1))
            amount += streak_bonus
        
        # Update user XP
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_engagement_metrics 
            SET total_xp = total_xp + ?, updated_at = ?
            WHERE user_id = ?
        ''', (amount, datetime.utcnow().isoformat(), user_id))
        
        if cursor.rowcount == 0:
            # Create new user record
            cursor.execute('''
                INSERT INTO user_engagement_metrics 
                (user_id, total_xp, last_activity, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update level and rank
        self._update_user_level(user_id)
        
        # Check for new achievements
        self._check_achievements(user_id)
        
        self.gamification_logger.info(f"Awarded {amount} XP to user {user_id} for {action}")
        
        return amount
        
    def update_prediction_stats(self, user_id: str, is_correct: bool, contract_id: str):
        """Update user prediction statistics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update prediction counts
        if is_correct:
            cursor.execute('''
                UPDATE user_engagement_metrics 
                SET total_predictions = total_predictions + 1,
                    correct_predictions = correct_predictions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ?
            ''', (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), user_id))
            
            # Award XP for correct prediction
            self.award_xp(user_id, 'correct_prediction', contract_id=contract_id)
        else:
            cursor.execute('''
                UPDATE user_engagement_metrics 
                SET total_predictions = total_predictions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ?
            ''', (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        # Update civic engagement score
        self._update_civic_engagement_score(user_id)
        
    def update_streak(self, user_id: str, activity_date: Optional[str] = None) -> int:
        """Update user activity streak"""
        
        if activity_date is None:
            activity_date = datetime.utcnow().date().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current metrics
        cursor.execute('''
            SELECT current_streak, longest_streak, last_activity 
            FROM user_engagement_metrics 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if not result:
            # Create new user record
            cursor.execute('''
                INSERT INTO user_engagement_metrics 
                (user_id, current_streak, longest_streak, last_activity, updated_at)
                VALUES (?, 1, 1, ?, ?)
            ''', (user_id, activity_date, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            return 1
        
        current_streak, longest_streak, last_activity = result
        
        if last_activity:
            last_date = datetime.fromisoformat(last_activity).date()
            current_date = datetime.fromisoformat(activity_date).date()
            
            if current_date == last_date:
                # Same day, no streak change
                conn.close()
                return current_streak
            elif current_date == last_date + timedelta(days=1):
                # Consecutive day, increment streak
                new_streak = current_streak + 1
                new_longest = max(longest_streak, new_streak)
            else:
                # Streak broken, reset to 1
                new_streak = 1
                new_longest = longest_streak
        else:
            # First activity
            new_streak = 1
            new_longest = 1
        
        # Update streak
        cursor.execute('''
            UPDATE user_engagement_metrics 
            SET current_streak = ?, longest_streak = ?, last_activity = ?, updated_at = ?
            WHERE user_id = ?
        ''', (new_streak, new_longest, activity_date, datetime.utcnow().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        # Award streak bonus XP
        if new_streak > 1:
            streak_xp = min(new_streak * 5, 50)  # Cap at 50 XP
            self.award_xp(user_id, 'streak_bonus', amount=streak_xp)
        
        return new_streak
        
    def _update_user_level(self, user_id: str):
        """Update user level based on XP"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT total_xp FROM user_engagement_metrics WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            total_xp = result[0]
            
            # Calculate level
            level = 1
            for threshold in self.level_thresholds:
                if total_xp >= threshold:
                    level += 1
                else:
                    break
            
            # Get rank title
            rank = self.rank_titles[min(level - 1, len(self.rank_titles) - 1)]
            
            # Update level and rank
            cursor.execute('''
                UPDATE user_engagement_metrics 
                SET level = ?, rank = ?, updated_at = ?
                WHERE user_id = ?
            ''', (level, rank, datetime.utcnow().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
    def _update_civic_engagement_score(self, user_id: str):
        """Update civic engagement score based on activity"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT total_predictions, correct_predictions, current_streak 
            FROM user_engagement_metrics 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if result:
            total_predictions, correct_predictions, current_streak = result
            
            # Calculate engagement score
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            activity_factor = min(total_predictions / 100, 1.0)  # Normalize to 100 predictions
            streak_factor = min(current_streak / 30, 1.0)  # Normalize to 30 days
            
            engagement_score = (accuracy * 0.4 + activity_factor * 0.4 + streak_factor * 0.2) * 100
            
            cursor.execute('''
                UPDATE user_engagement_metrics 
                SET civic_engagement_score = ?, updated_at = ?
                WHERE user_id = ?
            ''', (engagement_score, datetime.utcnow().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
    def _check_achievements(self, user_id: str):
        """Check and award new achievements"""
        
        metrics = self.get_user_metrics(user_id)
        
        for achievement in self.achievements:
            # Check if user already has this achievement
            if achievement.achievement_id in metrics.achievements:
                continue
            
            # Check achievement criteria
            if self._meets_achievement_criteria(metrics, achievement):
                self._award_achievement(user_id, achievement)
                
    def _meets_achievement_criteria(self, metrics: UserEngagementMetrics, achievement: Achievement) -> bool:
        """Check if user meets achievement criteria"""
        
        criteria = achievement.criteria
        
        if 'total_predictions' in criteria:
            if metrics.total_predictions < criteria['total_predictions']:
                return False
        
        if 'current_streak' in criteria:
            if metrics.current_streak < criteria['current_streak']:
                return False
        
        if 'accuracy_rate' in criteria:
            accuracy = metrics.correct_predictions / metrics.total_predictions if metrics.total_predictions > 0 else 0
            if accuracy < criteria['accuracy_rate']:
                return False
            
            if 'min_predictions' in criteria and metrics.total_predictions < criteria['min_predictions']:
                return False
        
        return True
        
    def _award_achievement(self, user_id: str, achievement: Achievement):
        """Award achievement to user"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Record achievement
        cursor.execute('''
            INSERT OR IGNORE INTO user_achievements 
            (user_id, achievement_id, earned_at, xp_awarded)
            VALUES (?, ?, ?, ?)
        ''', (user_id, achievement.achievement_id, datetime.utcnow().isoformat(), achievement.xp_reward))
        
        if cursor.rowcount > 0:
            # Award XP
            self.award_xp(user_id, 'achievement', amount=achievement.xp_reward)
            
            self.gamification_logger.info(f"User {user_id} earned achievement: {achievement.name}")
        
        conn.commit()
        conn.close()
        
    def get_user_metrics(self, user_id: str) -> UserEngagementMetrics:
        """Get user engagement metrics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT total_xp, current_streak, longest_streak, total_predictions,
                   correct_predictions, civic_engagement_score, last_activity, level, rank
            FROM user_engagement_metrics 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            # Get user achievements
            cursor.execute('''
                SELECT achievement_id FROM user_achievements WHERE user_id = ?
            ''', (user_id,))
            
            achievements = [row[0] for row in cursor.fetchall()]
            
            metrics = UserEngagementMetrics(
                user_id=user_id,
                total_xp=result[0],
                current_streak=result[1],
                longest_streak=result[2],
                total_predictions=result[3],
                correct_predictions=result[4],
                civic_engagement_score=result[5],
                last_activity=result[6] or "",
                achievements=achievements,
                level=result[7],
                rank=result[8]
            )
        else:
            # Return default metrics for new user
            metrics = UserEngagementMetrics(
                user_id=user_id,
                total_xp=0,
                current_streak=0,
                longest_streak=0,
                total_predictions=0,
                correct_predictions=0,
                civic_engagement_score=0.0,
                last_activity="",
                achievements=[],
                level=1,
                rank="Civic Newcomer"
            )
        
        conn.close()
        return metrics
        
    def get_leaderboard(self, leaderboard_type: str = "xp", limit: int = 50) -> List[Dict[str, Any]]:
        """Get leaderboard rankings"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if leaderboard_type == "xp":
            order_by = "total_xp DESC"
        elif leaderboard_type == "streak":
            order_by = "current_streak DESC, total_xp DESC"
        elif leaderboard_type == "accuracy":
            order_by = "(CAST(correct_predictions AS REAL) / NULLIF(total_predictions, 0)) DESC, total_predictions DESC"
        elif leaderboard_type == "civic_engagement":
            order_by = "civic_engagement_score DESC"
        else:
            order_by = "total_xp DESC"
        
        cursor.execute(f'''
            SELECT user_id, total_xp, current_streak, total_predictions, correct_predictions,
                   civic_engagement_score, level, rank
            FROM user_engagement_metrics 
            WHERE total_predictions > 0
            ORDER BY {order_by}
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for i, row in enumerate(results, 1):
            accuracy = row[4] / row[3] if row[3] > 0 else 0
            
            leaderboard.append({
                'rank': i,
                'user_id': row[0],
                'total_xp': row[1],
                'current_streak': row[2],
                'total_predictions': row[3],
                'correct_predictions': row[4],
                'accuracy': accuracy,
                'civic_engagement_score': row[5],
                'level': row[6],
                'rank_title': row[7]
            })
        
        return leaderboard
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get gamification system statistics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user counts
        cursor.execute('SELECT COUNT(*) FROM user_engagement_metrics')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_engagement_metrics WHERE total_predictions > 0')
        active_users = cursor.fetchone()[0]
        
        # Get engagement stats
        cursor.execute('SELECT AVG(civic_engagement_score) FROM user_engagement_metrics WHERE total_predictions > 0')
        avg_engagement = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT MAX(current_streak) FROM user_engagement_metrics')
        max_streak = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(total_predictions) FROM user_engagement_metrics')
        total_predictions = cursor.fetchone()[0] or 0
        
        # Get achievement stats
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_achievements')
        users_with_achievements = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_achievements')
        total_achievements_earned = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'avg_civic_engagement_score': avg_engagement,
            'max_current_streak': max_streak,
            'total_predictions_made': total_predictions,
            'users_with_achievements': users_with_achievements,
            'total_achievements_earned': total_achievements_earned,
            'available_achievements': len(self.achievements)
        }

# Global gamification system instance
institutional_gamification_system = InstitutionalGamificationSystem()

def award_xp(user_id: str, action: str, amount: Optional[int] = None, 
             contract_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> int:
    """Convenience function for awarding XP"""
    return institutional_gamification_system.award_xp(user_id, action, amount, contract_id, details)

def update_prediction_stats(user_id: str, is_correct: bool, contract_id: str):
    """Convenience function for updating prediction stats"""
    institutional_gamification_system.update_prediction_stats(user_id, is_correct, contract_id)

def get_user_metrics(user_id: str) -> UserEngagementMetrics:
    """Convenience function for getting user metrics"""
    return institutional_gamification_system.get_user_metrics(user_id)
