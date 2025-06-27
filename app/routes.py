from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file, Response
from flask_login import login_user, login_required, logout_user, current_user
from . import db
import config
from .models import User, Market, Prediction, NewsSource, LiquidityProvider, MarketEvent, Badge, UserBadge
from .forms import LoginForm, RegisterForm, MarketForm, PredictionForm, NewsSourceForm, LBForm
from datetime import datetime
import logging
import csv
from io import StringIO, BytesIO
import json

logging.basicConfig(level=logging.INFO)

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
        logging.info(f"Login attempt for username: {form.username.data}")
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            logging.info(f"Found user {user.username} in database")
            if user.check_password(form.password.data):
                logging.info(f"Password check succeeded for user {user.username}")
                login_user(user)
                return redirect(url_for('main.index'))
            else:
                logging.info(f"Password check failed for user {user.username}")
        else:
            logging.info(f"User {form.username.data} not found in database")
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check for existing user
        user_by_email = User.query.filter_by(email=form.email.data).first()
        user_by_username = User.query.filter_by(username=form.username.data).first()
        
        error = False
        if user_by_email:
            flash('Email address already registered.', 'error')
            error = True
        if user_by_username:
            flash('Username already taken.', 'error')
            error = True
        
        if error:
            return render_template('register.html', form=form)

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

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/create_market', methods=['GET', 'POST'])
@login_required
def create_market():
    try:
        if not current_user.is_admin:
            flash('Market creation is only available to administrators', 'error')
            return redirect(url_for('main.index'))
        
        form = MarketForm()
        if form.validate_on_submit():
            market = Market(
                title=form.title.data,
                description=form.description.data,
                resolution_date=datetime.strptime(form.resolution_date.data, '%Y-%m-%d'),
                resolution_method=form.resolution_method.data,
                source_url=form.source_url.data,
                yes_pool=500,  # Initialize with 50/50 odds
                no_pool=500    # Initialize with 50/50 odds
            )
            
            db.session.add(market)
            db.session.commit()
            flash('Market created successfully!')
            return redirect(url_for('main.index'))
        
        return render_template('create_market.html', form=form)
    except SQLAlchemyError as e:
        app.logger.error(f"Database error in market creation: {str(e)}", exc_info=True)
        flash('Database error occurred. Please try again later.', 'error')
        return redirect(url_for('main.index'))
    except AttributeError as e:
        app.logger.error(f"Attribute error in market creation: {str(e)}", exc_info=True)
        flash('Invalid market data. Please check your inputs.', 'error')
        return redirect(url_for('main.index'))
    except ValueError as e:
        app.logger.error(f"Value error in market creation: {str(e)}", exc_info=True)
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        return redirect(url_for('main.create_market'))

@main.route('/market/<int:market_id>')
@login_required
def market(market_id):
    market = Market.query.get_or_404(market_id)
    predictions = Prediction.query.filter_by(market_id=market_id).all()
    
    # Add reliability index directly to predictions
    for prediction in predictions:
        prediction.reliability_index = prediction.user.reliability_index if prediction.user.reliability_index else None
    
    form = PredictionForm()
    return render_template('market.html', 
                         market=market,
                         predictions=predictions,
                         form=form)

@main.route('/market/<int:market_id>/predict', methods=['POST'])
@login_required
def place_prediction(market_id):
    try:
        market = Market.query.get_or_404(market_id)
        form = PredictionForm()
        
        if form.validate_on_submit():
            price = market.place_prediction(
                user=current_user,
                outcome=form.outcome.data.upper(),
                amount=form.points_staked.data
            )
            flash(f'Prediction made successfully! Price: {price} points')
            return redirect(url_for('main.market', market_id=market_id))
        
        # If validation failed, re-render the market page with form errors
        return render_template('market.html', market=market, form=form)
    except SQLAlchemyError as e:
        app.logger.error(f"Database error in prediction: {str(e)}", exc_info=True)
        flash('Database error occurred. Please try again later.', 'error')
        return redirect(url_for('main.market', market_id=market_id))
    except AttributeError as e:
        app.logger.error(f"Attribute error in prediction: {str(e)}", exc_info=True)
        flash('Invalid market or user data. Please refresh the page.', 'error')
        return redirect(url_for('main.market', market_id=market_id))

@main.route('/market/<int:market_id>/resolve', methods=['POST'])
@login_required
def resolve_market(market_id):
    try:
        if not current_user.is_admin:
            flash('Market resolution is only available to administrators', 'error')
            return redirect(url_for('main.index'))
        
        market = Market.query.get_or_404(market_id)
        outcome = request.form.get('outcome')
        
        if outcome not in ['YES', 'NO']:
            flash('Invalid outcome specified', 'error')
            return redirect(url_for('main.market', market_id=market_id))
        
        market.resolved = True
        market.resolved_outcome = outcome
        market.resolved_at = datetime.utcnow()
        
        # Award XP for predictions
        market.award_xp_for_predictions()
        
        db.session.commit()
        flash('Market resolved successfully!')
        return redirect(url_for('main.market', market_id=market_id))
    except SQLAlchemyError as e:
        app.logger.error(f"Database error in market resolution: {str(e)}", exc_info=True)
        flash('Database error occurred. Please try again later.', 'error')
        return redirect(url_for('main.market', market_id=market_id))
    except AttributeError as e:
        app.logger.error(f"Attribute error in market resolution: {str(e)}", exc_info=True)
        flash('Invalid market data. Please refresh the page.', 'error')
        return redirect(url_for('main.market', market_id=market_id))

@main.route('/market/<int:market_id>/trade', methods=['POST'])
@login_required
def trade(market_id):
    """Handle market trades"""
    market = Market.query.get_or_404(market_id)
    
    # Check if market is resolved
    if market.resolved_outcome is not None:
        return jsonify({'error': 'Market is already resolved'}), 400
        
    data = request.get_json()
    
    # Validate trade amount
    amount = float(data.get('amount', 0))
    if amount < config.MIN_TRADE_SIZE or amount > config.MAX_TRADE_SIZE:
        return jsonify({'error': f'Trade amount must be between {config.MIN_TRADE_SIZE} and {config.MAX_TRADE_SIZE} points'}), 400
        
    # Check if trade would exceed pool cap
    total_pool = market.yes_pool + market.no_pool
    if total_pool + amount > config.CONTRACT_POOL_CAP:
        return jsonify({'error': f'Market pool cap reached. Total pool cannot exceed {config.CONTRACT_POOL_CAP} points'}), 400
        
    try:
        # Execute trade
        trade_result = market.trade(amount, data.get('outcome', True))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'price': trade_result['price'],
            'shares': trade_result['shares'],
            'total_pool': total_pool + amount
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/market/<int:market_id>/liquidity', methods=['POST'])
@login_required
def provide_liquidity(market_id):
    """
    Handle liquidity provision for a market.
    
    Expected JSON payload:
    {
        "action": "provide" | "withdraw",
        "points": float  # Points to provide/withdraw
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    action = data.get('action')
    points = data.get('points')
    
    if not action or not points:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if action not in ['provide', 'withdraw']:
        return jsonify({'error': 'Invalid action'}), 400
    
    market = Market.query.get_or_404(market_id)
    
    try:
        if action == 'provide':
            if current_user.points < points:
                return jsonify({'error': 'Insufficient points'}), 400
                
            # Calculate shares based on current liquidity pool size
            total_shares = sum(lp.shares for lp in market.liquidity_providers)
            if total_shares == 0:
                shares = points / market.liquidity_pool
            else:
                shares = (points / market.liquidity_pool) * total_shares
                
            # Create or update liquidity provider position
            lp = LiquidityProvider.query.filter_by(
                market_id=market_id,
                user_id=current_user.id
            ).first()
            
            if lp:
                lp.shares += shares
            else:
                lp = LiquidityProvider(
                    market_id=market_id,
                    user_id=current_user.id,
                    shares=shares
                )
                db.session.add(lp)
                
            # Update market pools
            market.yes_pool += points / 2
            market.no_pool += points / 2
            market.liquidity_pool += points
            
            # Update user points
            current_user.points -= points
            
            # Log the event
            event = MarketEvent(
                market=market,
                event_type='liquidity_provided',
                user=current_user,
                details={
                    'points': points,
                    'shares': shares,
                    'total_shares': total_shares + shares
                }
            )
            db.session.add(event)
            
        else:  # withdraw
            lp = LiquidityProvider.query.filter_by(
                market_id=market_id,
                user_id=current_user.id
            ).first()
            
            if not lp:
                return jsonify({'error': 'No liquidity position found'}), 400
                
            if lp.shares < points:
                return jsonify({'error': 'Cannot withdraw more than your share'}), 400
                
            # Calculate points to withdraw based on share percentage
            total_shares = sum(lp.shares for lp in market.liquidity_providers)
            share_percentage = lp.shares / total_shares
            points_to_withdraw = share_percentage * points
            
            # Update liquidity provider shares
            lp.shares -= points
            if lp.shares <= 0:
                db.session.delete(lp)
                
            # Update market pools
            market.yes_pool -= points_to_withdraw / 2
            market.no_pool -= points_to_withdraw / 2
            market.liquidity_pool -= points_to_withdraw
            
            # Update user points
            current_user.points += points_to_withdraw
            
            # Log the event
            event = MarketEvent(
                market=market,
                event_type='liquidity_withdrawn',
                user=current_user,
                details={
                    'points': points_to_withdraw,
                    'shares': points,
                    'total_shares': total_shares - points
                }
            )
            db.session.add(event)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'shares': lp.shares if lp else 0,
            'market': {
                'yes_pool': market.yes_pool,
                'no_pool': market.no_pool,
                'liquidity_pool': market.liquidity_pool
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/wallet')
@login_required
def wallet():
    """Show user's wallet and badges"""
    user = current_user
    
    # Get user's badges with creation dates
    badges = user.badges_sorted
    
    return render_template('wallet.html', 
        user=user,
        badges=badges
    )

@main.route('/wallet/deposit', methods=['POST'])
@login_required
def deposit_lb():
    form = LBForm()
    if form.validate_on_submit():
        if current_user.deposit_to_lb(form.amount.data):
            db.session.commit()
            flash(f'Successfully deposited {form.amount.data} points to your Liquidity Buffer')
        else:
            flash('Invalid deposit amount')
    return redirect(url_for('main.wallet'))

@main.route('/wallet/withdraw', methods=['POST'])
@login_required
def withdraw_lb():
    form = LBForm()
    if form.validate_on_submit():
        if current_user.withdraw_from_lb(form.amount.data):
            db.session.commit()
            flash(f'Successfully withdrew {form.amount.data} points from your Liquidity Buffer')
        else:
            flash('Invalid withdrawal amount')
    return redirect(url_for('main.wallet'))

@main.route('/manage_sources', methods=['GET', 'POST'])
@login_required
def manage_sources():
    form = NewsSourceForm()
    if form.validate_on_submit():
        source = NewsSource(
            name=form.name.data,
            url=form.url.data,
            selector=form.selector.data,
            date_selector=form.date_selector.data,
            active=form.active.data
        )
        db.session.add(source)
        db.session.commit()
        flash('News source created successfully!', 'success')
        return redirect(url_for('main.manage_sources'))
    
    sources = NewsSource.query.all()
    return render_template('manage_sources.html', sources=sources, form=form)

@main.route('/sources/<int:source_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_source(source_id):
    source = NewsSource.query.get_or_404(source_id)
    form = NewsSourceForm(obj=source)
    
    if form.validate_on_submit():
        source.name = form.name.data
        source.url = form.url.data
        source.selector = form.selector.data
        source.date_selector = form.date_selector.data
        source.active = form.active.data
        db.session.commit()
        flash('News source updated successfully!', 'success')
        return redirect(url_for('main.manage_sources'))
    
    return render_template('edit_source.html', form=form, source=source)

@main.route('/sources/<int:source_id>/toggle', methods=['POST'])
@login_required
def toggle_source(source_id):
    source = NewsSource.query.get_or_404(source_id)
    logging.info(f'---> Toggling source {source.id}. Current active state: {source.active}')
    source.active = not source.active
    logging.info(f'---> New active state: {source.active}')
    db.session.commit()
    status = "activated" if source.active else "deactivated"
    flash(f'Source "{source.name}" has been {status}.', 'success')
    return redirect(url_for('main.manage_sources'))

@main.route('/sources/<int:source_id>/delete', methods=['POST'])
@login_required
def delete_source(source_id):
    source = NewsSource.query.get_or_404(source_id)
    db.session.delete(source)
    db.session.commit()
    flash('News source deleted successfully!', 'success')
    return redirect(url_for('main.manage_sources'))

@main.route('/scrape_news')
@login_required
def scrape_news():
    return render_template('scrape_news.html')

@main.route('/scrape', methods=['GET'])
@login_required
def scrape():
    try:
        # Get all active news sources
        sources = NewsSource.query.filter_by(active=True).all()
        headlines = []
        
        for source in sources:
            # For each source, scrape headlines using its selector
            try:
                # This would typically use requests and BeautifulSoup
                # For now, we'll simulate with some test data
                test_headlines = [
                    {
                        'title': f'Test Headline {i} from {source.name}',
                        'source': source.name,
                        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                    for i in range(1, 4)  # Simulate 3 headlines per source
                ]
                headlines.extend(test_headlines)
            except Exception as e:
                flash(f'Error scraping from {source.name}: {str(e)}', 'warning')
                continue
        
        return jsonify({
            'headlines': headlines,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@main.route('/resolved-markets')
@login_required
def resolved_markets():
    """Get list of resolved markets"""
    markets = Market.query.filter(Market.resolved_outcome.isnot(None)).all()
    return jsonify({
        'markets': [{
            'id': market.id,
            'title': market.title,
            'resolved_outcome': market.resolved_outcome,
            'resolution_date': market.resolution_date.isoformat() if market.resolution_date else None
        } for market in markets]
    })

@main.route('/leaderboard')
@login_required
def leaderboard():
    """Show top users by XP with badges"""
    # Get top 50 users by XP
    top_users = User.query.order_by(User.xp.desc()).limit(50).all()
    
    # Pre-calculate reliability and badges for each user
    for user in top_users:
        predictions = Prediction.query.filter_by(user_id=user.id).all()
        total_predictions = len(predictions)
        correct_predictions = sum(1 for p in predictions if 
            p.market.resolved_outcome is not None and 
            (p.market.resolved_outcome == (p.prediction_type == 'YES')))
        
        user.reliability = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        user.total_predictions = total_predictions
        
        # Use the new badges_sorted property
        user.badges_sorted = user.badges_sorted[:3]
    
    return render_template('leaderboard.html', users=top_users)

@main.route('/next-market-drop')
@login_required
def next_market_drop():
    """Get next market drop information"""
    # Get the next unresolved market
    next_market = Market.query.filter(Market.resolved_outcome.is_(None)).order_by(Market.created_at).first()
    
    if next_market:
        now = datetime.utcnow()
        time_to_drop = next_market.created_at - now
        hours = time_to_drop.total_seconds() // 3600
        minutes = (time_to_drop.total_seconds() % 3600) // 60
        seconds = time_to_drop.total_seconds() % 60
        
        return jsonify({
            'market_id': next_market.id,
            'title': next_market.title,
            'time_to_drop': {
                'hours': int(hours),
                'minutes': int(minutes),
                'seconds': int(seconds)
            }
        })
    
    return jsonify({
        'error': 'No upcoming markets'
    }), 404

@main.route('/market/<int:market_id>/transcript')
@login_required
def market_transcript(market_id):
    market = Market.query.get_or_404(market_id)
    if not market.resolved:
        abort(404)

    predictions = Prediction.query.filter_by(market_id=market_id).all()
    
    # Get format parameter (default to csv)
    format = request.args.get('format', 'csv').lower()
    
    if format == 'csv':
        # Create CSV output
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Username", "Prediction", "Shares", "Payout", "Reliability Index"])
        
        # Write data rows
        for prediction in predictions:
            writer.writerow([
                prediction.user.username,
                "YES" if prediction.prediction == 1 else "NO",
                f"{prediction.shares:.2f}",
                f"{prediction.payout:.2f}",
                f"{prediction.user.reliability_index:.2f}" if prediction.user.reliability_index else "N/A"
            ])
        
        # Prepare response
        output.seek(0)
        filename = f"transcript_market_{market_id}.csv"
        return send_file(
            BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    elif format == 'json':
        # Create JSON output
        data = []
        for prediction in predictions:
            data.append({
                "username": prediction.user.username,
                "prediction": "YES" if prediction.prediction == 1 else "NO",
                "shares": float(prediction.shares),
                "payout": float(prediction.payout),
                "reliability_index": float(prediction.user.reliability_index) if prediction.user.reliability_index else None
            })
        
        filename = f"transcript_market_{market_id}.json"
        return Response(
            json.dumps(data, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    
    else:
        abort(400)  # Bad request if format is neither csv nor json

@main.route('/market/<int:market_id>/transcript_json')
@login_required
def market_transcript_json(market_id):
    """Download market transcript as JSON"""
    market = Market.query.get_or_404(market_id)
    events = MarketEvent.query.filter_by(market_id=market_id).order_by(MarketEvent.created_at.asc()).all()
    
    transcript = []
    for event in events:
        transcript.append({
            'event_type': event.event_type,
            'description': event.description,
            'event_data': event.event_data,
            'timestamp': event.created_at.isoformat()
        })
    
    # Create JSON response
    json_data = json.dumps(transcript, indent=2)
    
    # Create response with appropriate headers
    response = Response(
        json_data,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=market_{market_id}_transcript.json'
        }
    )
    return response

@main.route('/market/<int:market_id>/prediction_transcript')
@login_required
def prediction_transcript(market_id):
    market = Market.query.get_or_404(market_id)
    if not market.resolved:
        abort(404)

    # Get all predictions for this market
    predictions = Prediction.query.filter_by(market_id=market_id).all()
    
    # Create CSV output
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Username", "Prediction", "Shares", "Average Price", "Payout", "Reliability Index"])
    
    # Write data rows
    for prediction in predictions:
        writer.writerow([
            prediction.user.username,
            "YES" if prediction.prediction == 1 else "NO",
            f"{prediction.shares:.2f}",
            f"{prediction.average_price:.2f}",
            f"{prediction.payout:.2f}",
            f"{prediction.user.reliability_index:.2f}" if prediction.user.reliability_index else "N/A"
        ])
    
    # Prepare response
    output.seek(0)
    filename = f"transcript_market_{market_id}.csv"
    
    return send_file(
        BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@main.route('/admin/debug_reddit_drafts')
@login_required
def debug_reddit_drafts():
    if not current_user.is_admin:
        flash('This route is only available to administrators', 'error')
        return redirect(url_for('main.index'))
    
    try:
        with open('drafts/refined_reddit_drafts.json', 'r') as f:
            drafts = json.load(f)
            
        # Validate drafts structure
        if not isinstance(drafts, list):
            return "Invalid JSON: Expected a list of drafts"
            
        # Create HTML table
        html = """
        <h2>Reddit Drafts Debug View</h2>
        <table border="1">
            <tr>
                <th>Title</th>
                <th>Source</th>
                <th>Relevance Score</th>
            </tr>
        """
        
        for draft in drafts:
            if not isinstance(draft, dict) or 'title' not in draft:
                title = "Untitled"
            else:
                title = draft.get('title', "Untitled")
            
            source = draft.get('source_id', "Reddit")
            relevance = draft.get('relevance_score', 0.0)
            
            html += f"<tr><td>{title}</td><td>{source}</td><td>{relevance}</td></tr>"
        
        html += "</table>"
        
        return html
        
    except FileNotFoundError:
        return "Drafts file not found"
    except json.JSONDecodeError:
        return "Invalid JSON format"
    except Exception as e:
        return f"Error: {str(e)}"
