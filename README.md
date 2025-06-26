# MCX Points Platform

A Flask-based prediction market platform with points-based trading and liquidity buffer system.

## Features

- User authentication and authorization
- Prediction markets with automated market maker (AMM)
- Liquidity buffer system with daily yield
- Points-based trading system
- Admin-only market creation
- Customizable news sources
- Gamification features (badges, leagues, and rewards)

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python
from app import db
from app.models import User

db.create_all()

# Create admin user (optional)
admin = User(username='admin', email='admin@example.com', is_admin=True)
admin.set_password('adminpassword')
db.session.add(admin)
db.session.commit()
exit()
```

4. Run the application:
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
flask run --host=0.0.0.0
```

## Project Structure

```
mcx_points/
├── app/
│   ├── __init__.py         # Application initialization
│   ├── models.py           # Database models
│   ├── forms.py            # WTForms forms
│   ├── routes.py           # Route handlers
│   └── static/
│       └── css/
│           └── style.css
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Main page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── wallet.html         # Wallet page
│   ├── badges.html         # Badges page
│   └── manage_sources.html # News sources management
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## Database Models

- `User`: User accounts with points and liquidity buffer
- `Market`: Prediction markets with AMM
- `Prediction`: User predictions on markets
- `NewsSource`: Customizable news sources

## Security Features

- Password hashing using Werkzeug
- CSRF protection via Flask-WTF
- Session management with Flask-Login
- Admin-only market creation
- Input validation for all forms

## Gamification System

The prediction market platform includes a gamification system designed to encourage regular engagement and recognize user achievements. Here are the key features:

### User Streaks
- Users earn streaks by logging in daily
- The system tracks both current streak and longest streak
- A progress bar on the profile page shows streak progress
- Streaks reset if a user misses a day of logging in

### Badges
- Users can earn various badges for different achievements:
  - **5-Day Streak**: Check in every day for 5 days in a row
  - **10-Day Streak**: Check in every day for 10 days in a row
  - **30-Day Streak**: Check in every day for 30 days in a row
  - **First Prediction**: Make your first market prediction
  - **Prediction Master**: Make 100 predictions
  - **Precisionist**: Achieve 80% prediction accuracy
- Badges are displayed with icons and descriptions on the user profile
- Users can track their progress toward earning new badges

### Profile Display
- The user profile shows:
  - Basic user information (username, email, join date)
  - Streak statistics with a progress bar
  - Grid of earned badges with icons
  - Motivational messages for users without badges

### Technical Implementation
- Streak tracking is handled automatically via a `@before_request` hook
- Badge awards are triggered based on achievement criteria
- All gamification data is stored in the database
- The UI is responsive and works well on both desktop and mobile devices

## Gamification Features

### Badges
The platform includes a badge system that rewards users for their achievements. Users can earn badges for:

- Prediction Accuracy
  - Master Predictor (90%+ accuracy)
  - Expert Forecaster (80-89% accuracy)
  - Skilled Predictor (70-79% accuracy)

- Trading Volume
  - Trading Pro (1000+ trades)
  - Active Trader (500-999 trades)
  - Regular Trader (100-499 trades)

- Market Participation
  - Liquidity Provider (Provided liquidity to 10+ markets)
  - Market Maker (Provided liquidity to 5-9 markets)
  - Active Participant (Provided liquidity to 1-4 markets)

- Community Engagement
  - Community Leader (Invited 10+ users)
  - Community Builder (Invited 5-9 users)
  - Community Member (Invited 1-4 users)

### Leagues
Users can join competitive leagues based on their performance. There are five tiers of leagues:

1. **Diamond League**
   - Requirements: 50000+ points, 1000+ predictions, 90%+ accuracy
   - Maximum Members: 5
   - Weekly Rewards: 10x base points

2. **Platinum League**
   - Requirements: 25000+ points, 500+ predictions, 85%+ accuracy
   - Maximum Members: 10
   - Weekly Rewards: 5x base points

3. **Gold League**
   - Requirements: 10000+ points, 200+ predictions, 80%+ accuracy
   - Maximum Members: 20
   - Weekly Rewards: 3x base points

4. **Silver League**
   - Requirements: 5000+ points, 100+ predictions, 75%+ accuracy
   - Maximum Members: 30
   - Weekly Rewards: 2x base points

5. **Bronze League**
   - Requirements: 1000+ points, 50+ predictions, 70%+ accuracy
   - Maximum Members: 50
   - Weekly Rewards: 1x base points

### League Points Calculation
League points are calculated based on:
- Prediction Accuracy (100 points per 1.0 reliability)
- Points Won (10% of total points)
- Prediction Volume (5 points per prediction)
- Trading Volume (2 points per trade)
- Liquidity Provision (10 points per market)

### Weekly Rewards
League rewards are distributed weekly based on rank:
- Top 10%: 10x base points
- Next 20%: 5x base points
- Remaining: 2x base points

### Automated Tasks
The platform includes automated tasks that run:
- Daily: Award badges to qualifying users
- Weekly: Update league rankings and distribute rewards

## Market Trading

### Contract Pool Cap
Markets have a total pool cap of 10,000 points (YES + NO pools combined). When a market reaches this cap:

- Users cannot make new trades
- A banner appears indicating the market is full
- The trading form is disabled
- Users must wait for existing trades to be resolved before new trades can be made

### Trading Rules
- Minimum trade size: 1 point
- Maximum trade size: 1,000 points
- Trades are executed via an Automated Market Maker (AMM)
- Liquidity providers earn a 0.3% fee on trades

## Development Notes

- The application uses SQLite by default
- Debug mode is enabled for development
- All routes are protected with appropriate decorators
- Points calculations include liquidity buffer bonuses
