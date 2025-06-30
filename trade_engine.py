from app.models import Market, Prediction, User
from app import db
from config import Config

def execute_trade(user: User, market: Market, amount: float, outcome: str):
    if market.resolved:
        raise ValueError("Cannot trade on a resolved market.")

    if amount < Config.MIN_TRADE_SIZE or amount > Config.MAX_TRADE_SIZE:
        raise ValueError("Trade amount out of bounds.")

    # Fee routing
    fee = amount * Config.LIQUIDITY_FEE_RATE
    net_amount = amount - fee
    user.points -= amount
    user.lb_deposit += fee  # Add fee to LB (simplified logic)

    # Pricing
    if outcome == 'YES':
        price = market.yes_pool / market.no_pool
        shares = net_amount / price
        market.yes_pool += net_amount
    elif outcome == 'NO':
        price = market.no_pool / market.yes_pool
        shares = net_amount / price
        market.no_pool += net_amount
    else:
        raise ValueError("Invalid outcome side.")

    # Save prediction
    prediction = Prediction(user_id=user.id, market_id=market.id,
                            prediction=outcome, shares=shares,
                            average_price=price)
    db.session.add(prediction)
    db.session.commit()

    return {
        "price": price,
        "shares": shares,
        "fee_routed_to_LB": fee
    }
