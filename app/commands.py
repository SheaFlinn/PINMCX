import click
from flask import current_app
from app import create_app, db
from app.models import User, Badge, NewsSource

def register_commands(app):
    app.cli.add_command(seed_db)

@click.command('seed-db')
def seed_db():
    app = create_app()
    with app.app_context():
        # Handle admin user
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.set_password('adminpassword')
        else:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('adminpassword')
            db.session.add(admin)

        # Seed news sources
        from app.models import NewsSource

        default_sources = [
            {"name": "Daily Memphian", "url": "https://dailymemphian.com", "selector": ".headline", "domain_tag": "local", "source_weight": 1.0},
            {"name": "WREG", "url": "https://wreg.com", "selector": ".entry-title", "domain_tag": "crime", "source_weight": 0.9},
            {"name": "MLK50", "url": "https://mlk50.com", "selector": "h2.title", "domain_tag": "justice", "source_weight": 0.8},
            {"name": "Commercial Appeal", "url": "https://commercialappeal.com", "selector": "h3.headline", "domain_tag": "metro", "source_weight": 1.0},
        ]

        for source in default_sources:
            existing = NewsSource.query.filter_by(name=source["name"]).first()
            if not existing:
                db.session.add(NewsSource(**source))

        # Seed badges
        default_badges = [
            {'type': 'starter', 'name': 'Starter', 'description': 'First steps', 'icon': 'starter.png'},
            {'type': 'streak7', 'name': 'One Week Streak', 'description': 'Checked in 7 days in a row', 'icon': 'streak_7.png'},
            {'type': 'daily_streak_5', 'name': '5-Day Streak', 'description': 'Checked in for 5 days in a row', 'icon': 'streak_5.png'},
            {'type': 'daily_streak_10', 'name': '10-Day Streak', 'description': 'Checked in for 10 days in a row', 'icon': 'streak_10.png'},
            {'type': 'daily_streak_30', 'name': '30-Day Streak', 'description': 'Checked in for 30 days in a row', 'icon': 'streak_30.png'},
            {'type': 'xp_100', 'name': 'XP 100', 'description': 'Earned 100 XP', 'icon': 'xp_100.png'},
            {'type': 'xp_500', 'name': 'XP 500', 'description': 'Earned 500 XP', 'icon': 'xp_500.png'},
            {'type': 'xp_1000', 'name': 'XP 1000', 'description': 'Earned 1000 XP', 'icon': 'xp_1000.png'},
        ]
        
        # First update any existing badges with None icons
        for badge in Badge.query.all():
            if badge.icon is None:
                matching_badge = next((b for b in default_badges if b['type'] == badge.type), None)
                if matching_badge:
                    badge.icon = matching_badge['icon']
                    db.session.add(badge)

        # Then add any missing badges
        for badge_data in default_badges:
            if not Badge.query.filter_by(type=badge_data['type']).first():
                badge = Badge(**badge_data)
                db.session.add(badge)
        
        db.session.commit()
        click.echo('Database seeded.')
