from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime 
import os
import sys
import logging

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from award_badges import award_badges
from update_leagues import update_league_rankings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_scheduler():
    """Create and configure the scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule badge awards daily at midnight
    scheduler.add_job(
        award_badges,
        CronTrigger(hour=0, minute=0),
        id='award_badges',
        name='Award badges to users'
    )
    
    # Schedule league updates weekly on Sunday at midnight
    scheduler.add_job(
        update_league_rankings,
        CronTrigger(day_of_week='sun', hour=0, minute=0),
        id='update_leagues',
        name='Update league rankings and distribute rewards'
    )
    
    return scheduler

def main():
    """Main function to start the scheduler"""
    try:
        # Create Flask app context
        app = create_app()
        with app.app_context():
            # Create and start scheduler
            scheduler = create_scheduler()
            scheduler.start()
            
            # Keep the script running
            try:
                while True:
                    pass
            except (KeyboardInterrupt, SystemExit):
                # Shutdown scheduler gracefully
                scheduler.shutdown()
                logger.info("Scheduler shutdown complete")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")

if __name__ == '__main__':
    main()
