from app import db, Badge

def create_badges():
    """Create initial badges in the database"""
    badges = [
        {
            'type': 'daily_streak_5',
            'name': '5-Day Streak',
            'description': 'Check in every day for 5 days in a row',
            'icon': 'fa-solid fa-medal'
        },
        {
            'type': 'daily_streak_10',
            'name': '10-Day Streak',
            'description': 'Check in every day for 10 days in a row',
            'icon': 'fa-solid fa-trophy'
        },
        {
            'type': 'daily_streak_30',
            'name': '30-Day Streak',
            'description': 'Check in every day for 30 days in a row',
            'icon': 'fa-solid fa-crown'
        },
        {
            'type': 'first_prediction',
            'name': 'First Prediction',
            'description': 'Made your first market prediction',
            'icon': 'fa-solid fa-dice'
        },
        {
            'type': 'prediction_master',
            'name': 'Prediction Master',
            'description': 'Made 100 predictions',
            'icon': 'fa-solid fa-magic'
        },
        {
            'type': 'accuracy_80',
            'name': 'Precisionist',
            'description': 'Achieved 80% prediction accuracy',
            'icon': 'fa-solid fa-bullseye'
        }
    ]

    for badge_data in badges:
        badge = Badge(
            type=badge_data['type'],
            name=badge_data['name'],
            description=badge_data['description'],
            icon=badge_data['icon']
        )
        db.session.add(badge)
    
    db.session.commit()
    print(f"Successfully created {len(badges)} badges!")

if __name__ == '__main__':
    create_badges()
