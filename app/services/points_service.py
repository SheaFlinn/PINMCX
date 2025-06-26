from app.models import Market, Prediction, User, db

def award_xp_for_resolved_market(market_id):
    # Get the market
    market = Market.query.get(market_id)
    if not market or not market.resolved or not market.correct_outcome:
        return

    # Get all correct predictions
    correct_predictions = Prediction.query.filter_by(
        market_id=market_id,
        prediction=market.correct_outcome
    ).all()

    # Award XP to each correct user
    for prediction in correct_predictions:
        user = User.query.get(prediction.user_id)
        if user:
            user.xp = (user.xp or 0) + 10

    db.session.commit()

