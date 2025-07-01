from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Market
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    markets = Market.query.filter_by(resolved=False).all()
    return render_template('index.html', markets=markets)

@main.route('/market/<int:market_id>')
def view_market(market_id):
    market = Market.query.get_or_404(market_id)
    return render_template('market.html', market=market)

@main.route('/resolve/<int:market_id>', methods=['POST'])
@login_required
def resolve_market(market_id):
    if not current_user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for('main.index'))

    outcome = request.form.get('outcome')
    if outcome not in ['YES', 'NO']:
        flash("Invalid outcome", "danger")
        return redirect(url_for('main.view_market', market_id=market_id))

    market = Market.query.get_or_404(market_id)
    market.resolve(outcome)
    db.session.commit()
    flash("Market resolved", "success")
    return redirect(url_for('main.view_market', market_id=market_id))
