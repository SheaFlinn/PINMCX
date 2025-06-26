from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime
from app.extensions import db
from app.models import User, Market, Prediction
from app.forms import LoginForm, RegisterForm, MarketForm, PredictionForm

main = Blueprint('main', __name__)

@main.route('/')
def index():
    markets = Market.query.filter_by(resolved=False).all()
    return render_template('index.html', markets=markets)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/create_market', methods=['GET', 'POST'])
@login_required
def create_market():
    if not current_user.is_admin:
        flash('Only administrators can create markets', 'error')
        return redirect(url_for('main.index'))

    form = MarketForm()
    if form.validate_on_submit():
        market = Market(
            title=form.title.data,
            description=form.description.data,
            resolution_date=form.resolution_date.data,
            resolution_method=form.resolution_method.data,
            source_url=form.source_url.data,
            yes_pool=500,
            no_pool=500
        )
        db.session.add(market)
        db.session.commit()
        flash('Market created successfully')
        return redirect(url_for('main.index'))
    return render_template('create_market.html', form=form)

@main.route('/market/<int:market_id>')
@login_required
def view_market(market_id):
    market = Market.query.get_or_404(market_id)
    predictions = Prediction.query.filter_by(market_id=market_id).all()
    form = PredictionForm()
    return render_template('market.html', market=market, predictions=predictions, form=form)

@main.route('/market/<int:market_id>/predict', methods=['POST'])
@login_required
def make_prediction(market_id):
    market = Market.query.get_or_404(market_id)
    form = PredictionForm()

    if form.validate_on_submit():
        try:
            # For now, this simulates prediction entry only
            prediction = Prediction(
                user_id=current_user.id,
                market_id=market.id,
                outcome=form.outcome.data,
                amount=form.points_staked.data,
                created_at=datetime.utcnow()
            )
            db.session.add(prediction)
            db.session.commit()
            flash("Prediction placed successfully!", "success")
            return redirect(url_for('main.view_market', market_id=market_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error placing prediction: {str(e)}", "error")

    return render_template('market.html', market=market, form=form)

@main.route('/market/<int:market_id>/resolve', methods=['POST'])
@login_required
def resolve_market(market_id):
    if not current_user.is_admin:
        flash('Only admins can resolve markets', 'error')
        return redirect(url_for('main.index'))

    market = Market.query.get_or_404(market_id)
    outcome = request.form.get('outcome')

    try:
        market.resolve(outcome)
        flash('Market resolved successfully!', 'success')
    except Exception as e:
        flash(f'Error resolving market: {str(e)}', 'error')

    return redirect(url_for('main.view_market', market_id=mar_
