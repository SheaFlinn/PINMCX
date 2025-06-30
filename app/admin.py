from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
import json
import os
from datetime import datetime, timedelta
from . import db
from .models import Market, Prediction, User, MarketEvent, League, NewsSource, NewsHeadline
from .forms import MarketForm, PredictionForm, NewsSourceForm, LBForm, LeagueForm
from sqlalchemy import func
import logging

# Create admin blueprint
bp = Blueprint('admin', __name__, url_prefix='/admin')

class AdminModelView(ModelView):
    """Base ModelView for admin interface"""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

class UserModelView(AdminModelView):
    """Custom ModelView for User model"""
    column_list = ('username', 'email', 'is_admin', 'points', 'lb_deposit', 'reliability_index', 'xp', 'current_streak', 'longest_streak', 'last_active')
    column_searchable_list = ('username', 'email')
    column_filters = ('is_admin', 'last_active')
    form_columns = ('username', 'email', 'is_admin', 'points', 'lb_deposit', 'reliability_index', 'xp', 'current_streak')

class MarketModelView(AdminModelView):
    """Custom ModelView for Market model"""
    column_list = ('title', 'description', 'resolution_date', 'resolution_method', 'domain', 'resolved', 'resolved_outcome', 'resolved_at', 'created_at')
    column_searchable_list = ('title', 'description')
    column_filters = ('resolved', 'resolution_date', 'created_at')
    form_columns = ('title', 'description', 'resolution_date', 'resolution_method', 'domain', 'resolved', 'resolved_outcome')

class PredictionModelView(AdminModelView):
    """Custom ModelView for Prediction model"""
    column_list = ('user', 'market', 'outcome', 'amount', 'created_at')
    column_filters = ('outcome', 'created_at')
    form_columns = ('user', 'market', 'outcome', 'amount')

class MarketEventModelView(AdminModelView):
    """Custom ModelView for MarketEvent model"""
    column_list = ('market', 'event_type', 'description', 'created_at')
    column_filters = ('event_type', 'created_at')
    form_columns = ('market', 'event_type', 'description', 'event_data')

class NewsSourceModelView(AdminModelView):
    """Custom ModelView for NewsSource model"""
    column_list = ('name', 'url', 'selector', 'domain_tag', 'source_weight', 'active')
    column_searchable_list = ('name', 'url')
    column_filters = ('active', 'domain_tag')
    form_columns = ('name', 'url', 'selector', 'domain_tag', 'source_weight', 'active')

class NewsHeadlineModelView(AdminModelView):
    """Custom ModelView for NewsHeadline model"""
    column_list = ('title', 'url', 'date_added', 'date_published', 'source_id')
    column_searchable_list = ('title', 'url')
    column_filters = ('date_added', 'date_published', 'source_id')
    form_columns = ('title', 'url', 'date_added', 'date_published', 'source_id')

class LeagueModelView(AdminModelView):
    """Custom ModelView for League model"""
    column_list = ('name', 'description', 'min_xp')
    column_searchable_list = ('name', 'description')
    form_columns = ('name', 'description', 'min_xp')

# Admin index view with custom access control
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

# Initialize admin with custom index view
admin = Admin(name='Prediction Market Admin', template_mode='bootstrap4', index_view=MyAdminIndexView())

# Register all custom ModelViews with admin
admin.add_view(UserModelView(User, db.session))
admin.add_view(MarketModelView(Market, db.session))
admin.add_view(PredictionModelView(Prediction, db.session))
admin.add_view(MarketEventModelView(MarketEvent, db.session))
admin.add_view(NewsSourceModelView(NewsSource, db.session))
admin.add_view(NewsHeadlineModelView(NewsHeadline, db.session))
admin.add_view(LeagueModelView(League, db.session))

def parse_reddit_drafts():
    drafts = []
    try:
        draft_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'drafts', 'refined_reddit_drafts.json')
        if os.path.exists(draft_file):
            logging.info(f"Loading Reddit drafts from: {draft_file}")
            with open(draft_file, 'r') as f:
                raw = json.load(f)
                logging.info(f"Found {len(raw)} Reddit draft entries")
                
                # Try to get Reddit NewsSource
                source = NewsSource.query.filter_by(name="Reddit").first()
                if not source:
                    logging.info("Creating Reddit NewsSource since it's missing")
                    source = NewsSource(
                        name="Reddit",
                        url="https://reddit.com",
                        selector="h3",
                        domain_tag="community",
                        source_weight=0.6,
                        active=True
                    )
                    db.session.add(source)
                    db.session.commit()
                    logging.info("Created Reddit NewsSource successfully")
                
                for entry in raw:
                    # Create draft with required fields
                    title = entry.get('title')
                    if not title or not title.strip():
                        title = "Untitled"
                    
                    draft = {
                        'headline': title,
                        'source': source.name,
                        'domain': entry.get("domain", "community"),
                        'resolution_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        'original_headline': entry.get("original_headline"),
                        'refined_title': entry.get("refined_title"),
                        'relevance_score': entry.get("relevance_score", 0.0),
                        'created_at': entry.get("created_at"),
                        'is_reddit': True  # Add flag to identify Reddit drafts
                    }
                    drafts.append(draft)
                    logging.debug(f"Processed draft: {draft['headline']} (domain: {draft['domain']})")
        
        logging.info(f"Successfully processed {len(drafts)} Reddit drafts")
        return drafts
    except json.JSONDecodeError:
        logging.warning("Reddit drafts file is empty or invalid JSON")
        return []
    except Exception as e:
        logging.error(f"Error loading Reddit drafts: {e}")
        return []

# Define available domain categories
DOMAIN_CATEGORIES = [
    'infrastructure',
    'public_safety',
    'housing',
    'education',
    'transportation',
    'environment',
    'economy',
    'health',
    'other'
]

@bp.route('/drafts')
@login_required
def drafts():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Load refined drafts
        drafts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts')
        
        # Load news drafts from JSON
        try:
            news_drafts_path = os.path.join(drafts_dir, "refined_drafts.json")
            with open(news_drafts_path, 'r') as f:
                news_drafts = json.load(f)
                # Ensure all news drafts have valid headlines
                for draft in news_drafts:
                    draft['headline'] = draft.get('headline') or 'Untitled'
                    if not draft['headline'].strip():
                        draft['headline'] = 'Untitled'
        except Exception as e:
            logging.warning(f"Error loading news drafts: {e}")
            news_drafts = []
            
        # Load Reddit drafts
        reddit_drafts = parse_reddit_drafts()
        
        # Load headlines from database
        db_headlines = []
        try:
            # Get all headlines from active news sources
            active_sources = NewsSource.query.filter_by(active=True).all()
            for source in active_sources:
                headlines = NewsHeadline.query.filter_by(source_id=source.id).order_by(NewsHeadline.date_added.desc()).all()
                for headline in headlines:
                    db_headlines.append({
                        'headline': headline.title,
                        'source': source.name,
                        'domain': source.domain_tag,
                        'url': headline.url,
                        'date_added': headline.date_added.isoformat(),
                        'date_published': headline.date_published.isoformat() if headline.date_published else None,
                        'domain_tags': [source.domain_tag] if source.domain_tag else []
                    })
        except Exception as e:
            logging.warning(f"Error loading headlines from DB: {e}")
            
        # Combine all drafts
        all_drafts = news_drafts + reddit_drafts + db_headlines
        
        # Sort drafts by relevance score (highest first), then by date added (newest first)
        all_drafts.sort(key=lambda x: (x.get('relevance_score', 0), 
                                    x.get('date_added', datetime.utcnow().isoformat())), 
                       reverse=True)
        
        # Get all domain categories from NewsSource model
        domain_categories = sorted(set(
            source.domain_tag 
            for source in NewsSource.query.all() 
            if source.domain_tag and source.domain_tag != 'other'
        ))
        
        # Get all active markets for lineage selection
        markets = Market.query.filter_by(resolved=False).order_by(Market.created_at.desc()).all()
        
        # Filter drafts by domain
        domain_filter = request.args.get('domain')
        if domain_filter:
            all_drafts = [draft for draft in all_drafts if draft.get('domain') == domain_filter]
        
        return render_template('admin/drafts.html', 
                            drafts=all_drafts, 
                            domain_categories=domain_categories,
                            markets=markets,
                            domain_filter=domain_filter)
                            
    except Exception as e:
        logging.error(f"Error loading drafts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/approve_draft', methods=['POST'])
@login_required
def approve_draft():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    draft_id = request.form.get('draft_id')
    refined_title = request.form.get('refined_title')
    refined_description = request.form.get('refined_description')
    domain = request.form.get('domain')
    parent_market_id = request.form.get('parent_market_id')  # Optional field for lineage
    
    if domain not in DOMAIN_CATEGORIES:
        return jsonify({'error': 'Invalid domain category'}), 400
    
    try:
        # Load the draft from JSON
        drafts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts')
        json_path = os.path.join(drafts_dir, "draft_contracts.json")
        
        with open(json_path, 'r') as f:
            drafts = json.load(f)
            
        # Find the draft
        draft = None
        for d in drafts:
            if d['original_headline'] == draft_id:
                draft = d
                break
        
        if not draft:
            return jsonify({'error': 'Draft not found'}), 404
        
        # Create the market
        market = Market(
            title=refined_title,
            description=refined_description,
            resolution_date=datetime.strptime(draft['resolution_date'], '%Y-%m-%d'),
            resolution_method=draft['resolution_method'],
            source_url=draft['source_url'],
            domain=domain,
            parent_market_id=parent_market_id if parent_market_id else None,
            original_source=draft['original_source'],
            original_headline=draft['original_headline'],
            original_date=datetime.strptime(draft['original_date'], '%Y-%m-%d %H:%M:%S'),
            scraped_at=datetime.strptime(draft['scraped_at'], '%Y-%m-%dT%H:%M:%SZ'),
            refined_by=current_user.id,
            refined_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        # Log market creation event
        MarketEvent.log_market_creation(market, current_user.id)
        
        # Add to database
        db.session.add(market)
        db.session.commit()
        
        # Remove draft from JSON
        drafts.remove(draft)
        with open(json_path, 'w') as f:
            json.dump(drafts, f, indent=4)
        
        return jsonify({'success': True, 'market_id': market.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/reject_draft', methods=['POST'])
@login_required
def reject_draft():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    draft_id = request.form.get('draft_id')
    rejection_reason = request.form.get('rejection_reason')
    
    if not draft_id:
        return jsonify({'error': 'Draft ID is required'}), 400
    
    try:
        # Load the draft from JSON
        drafts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts')
        json_path = os.path.join(drafts_dir, "draft_contracts.json")
        
        with open(json_path, 'r') as f:
            drafts = json.load(f)
            
        # Find the draft
        draft = None
        for d in drafts:
            if d['original_headline'] == draft_id:
                draft = d
                break
        
        if not draft:
            return jsonify({'error': 'Draft not found'}), 404
        
        # Update the draft with rejection reason
        draft['rejection_reason'] = rejection_reason
        draft['rejected_at'] = datetime.utcnow().isoformat()
        draft['rejected_by'] = current_user.id
        
        # Save the updated drafts
        with open(json_path, 'w') as f:
            json.dump(drafts, f, indent=2)
            
        return jsonify({
            'success': True,
            'message': 'Draft rejected successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@bp.route('/save_draft_field', methods=['POST'])
@login_required
def save_draft_field():
    """Save a field edit for a draft market"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    draft_id = request.form.get('draft_id')
    field = request.form.get('field')
    value = request.form.get('value')
    
    if not all([draft_id, field, value]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        drafts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts')
        json_path = os.path.join(drafts_dir, "draft_contracts.json")
        
        with open(json_path, "r") as f:
            drafts = json.load(f)
        
        draft = next((d for d in drafts if d.get('original_headline') == draft_id), None)
        if not draft:
            return jsonify({'error': 'Draft not found'}), 404
            
        draft[field] = value
        
        with open(json_path, "w") as f:
            json.dump(drafts, f, indent=2)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/resolve')
@login_required
def resolve_markets():
    if not current_user.is_admin:
        abort(403)
    
    unresolved_markets = Market.query.filter_by(resolved=False).all()
    return render_template('admin/resolve_markets.html', markets=unresolved_markets)

@bp.route('/resolve/<int:market_id>', methods=['POST'])
@login_required
def resolve_market(market_id):
    if not current_user.is_admin:
        abort(403)
    
    market = Market.query.get_or_404(market_id)
    outcome = request.form.get('outcome')
    
    if outcome not in ['yes', 'no', 'invalid']:
        flash('Invalid outcome selected', 'error')
        return redirect(url_for('admin.resolve_markets'))
    
    market.resolved = True
    market.resolved_outcome = outcome
    market.resolved_at = datetime.utcnow()
    
    # Award XP for predictions
    market.award_xp_for_predictions()
    
    db.session.commit()
    flash('Market resolved successfully', 'success')
    return redirect(url_for('admin.resolve_markets'))

@bp.route('/resolve_market/<int:market_id>', methods=['POST'])
@login_required
def resolve_market_with_domain(market_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    outcome = request.json.get('outcome')
    if outcome not in ['YES', 'NO']:
        return jsonify({'error': 'Invalid outcome'}), 400

    try:
        market = Market.query.get_or_404(market_id)
        
        # Resolve the market
        market.resolved = True
        market.resolved_outcome = outcome
        market.resolved_at = datetime.utcnow()
        
        # Log resolution event
        MarketEvent.log_market_resolution(market, current_user.id)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/change_lineage/<int:market_id>', methods=['POST'])
@login_required
def change_lineage(market_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    parent_market_id = request.form.get('parent_market_id')
    
    try:
        market = Market.query.get_or_404(market_id)
        
        # Update lineage
        market.parent_market_id = int(parent_market_id) if parent_market_id else None
        
        # Log lineage change event
        MarketEvent.log_lineage_change(market, current_user.id, parent_market_id)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/create_league', methods=['GET', 'POST'])
@login_required
def create_league():
    """Create a new league"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    form = LeagueForm()
    if form.validate_on_submit():
        # Check if league name already exists
        if League.query.filter_by(name=form.name.data).first():
            flash('League name already exists', 'error')
            return render_template('admin/create_league.html', form=form)

        # Create new league
        league = League(
            name=form.name.data,
            description=form.description.data,
            min_xp=form.min_xp.data
        )
        db.session.add(league)
        db.session.commit()
        
        flash('League created successfully', 'success')
        return redirect(url_for('admin.create_league'))

    return render_template('admin/create_league.html', form=form)

@bp.route('/analytics')
@login_required
def analytics():
    """Display platform analytics dashboard"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Calculate statistics
    stats = {
        'total_users': User.query.count(),
        'resolved_markets': Market.query.filter_by(resolved=True).count(),
        'unresolved_markets': Market.query.filter_by(resolved=False).count(),
        'total_predictions': Prediction.query.count(),
        'avg_reliability': db.session.query(func.avg(User.reliability_index)).scalar() or 0,
        'lb_total': db.session.query(func.sum(User.lb_deposit)).scalar() or 0,
        'most_active_market': Market.query.join(Prediction).group_by(Market.id)
            .order_by(func.count(Prediction.id).desc()).first(),
        'most_common_domain': db.session.query(
            Market.domain,
            func.count(Market.domain)
        ).group_by(Market.domain).order_by(func.count(Market.domain).desc()).first()
    }

    return render_template('admin/analytics.html', stats=stats)

@bp.route('/refine_draft', methods=['POST'])
@login_required
def refine_draft():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        headline = data.get('headline')
        source = data.get('source')
        domain = data.get('domain')

        if not all([headline, source, domain]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Clean and format the headline
        clean_headline = headline.strip().replace("\n", " ").replace("\r", " ").strip()
        
        # Generate title (max 150 chars)
        title = f"Will '{clean_headline}' impact {domain} policy in Memphis?"
        if len(title) > 150:
            title = title[:147] + "..."

        # Generate description with improved civic framing
        description = f"""
        The recent headline from {source} raises civic questions about the future of {domain} policy in Memphis. 
        This market invites speculation on the potential civic impacts and policy outcomes related to this event.
        
        Key considerations:
        - Impact on local governance and policy decisions
        - Potential changes to community services or infrastructure
        - Public opinion and civic engagement implications
        """

        return jsonify({
            'title': title,
            'description': description,
            'metadata': {
                'source': source,
                'domain': domain,
                'original_headline': headline,
                'refinement_date': datetime.utcnow().isoformat(),
                'refiner_id': current_user.id if current_user.is_authenticated else None
            }
        })
    except Exception as e:
        logging.error(f"Error refining draft: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/save_refined_draft', methods=['POST'])
@login_required
def save_refined_draft():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        headline = data.get('headline')
        source = data.get('source')
        domain = data.get('domain')
        draft_text = data.get('draft_text')

        if not all([headline, source, domain, draft_text]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Load existing draft contracts
        drafts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts', 'draft_contracts.json')
        existing_drafts = []
        if os.path.exists(drafts_path):
            with open(drafts_path, 'r') as f:
                existing_drafts = json.load(f)

        # Get source URL from database if it exists
        source_url = ''
        if source:
            news_source = NewsSource.query.filter_by(name=source).first()
            if news_source:
                source_url = news_source.url

        # Get original headline and URL from database
        original_headline = headline
        original_url = ''
        news_headline = NewsHeadline.query.filter_by(title=headline).first()
        if news_headline:
            original_headline = news_headline.title
            original_url = news_headline.url

        # Get current user details
        refiner_name = current_user.username if current_user.is_authenticated else 'Anonymous'
        refiner_id = current_user.id if current_user.is_authenticated else None

        # Create new draft with comprehensive metadata
        new_draft = {
            'title': headline,
            'description': draft_text,
            'domain': domain,
            'source_name': source,
            'source_url': source_url,
            'original_headline': original_headline,
            'original_url': original_url,
            'resolution_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'refined_by': refiner_id,
            'refiner_name': refiner_name,
            'refinement_date': datetime.utcnow().isoformat(),
            'refinement_history': [
                {
                    'refiner_id': refiner_id,
                    'refiner_name': refiner_name,
                    'refinement_date': datetime.utcnow().isoformat(),
                    'refinement_type': 'initial',
                    'notes': 'Initial refinement'
                }
            ],
            'status': 'refined',
            'version': 1
        }

        # Add to existing drafts
        existing_drafts.append(new_draft)

        # Save updated drafts
        with open(drafts_path, 'w') as f:
            json.dump(existing_drafts, f, indent=2)

        return jsonify({'message': 'Draft saved successfully'})
    except Exception as e:
        logging.error(f"Error saving refined draft: {e}")
        return jsonify({'error': str(e)}), 500
