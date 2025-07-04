from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.draft_contract import DraftContract
from app.models import NewsSource
from app import db

admin = Blueprint('admin', __name__)

@admin.route('/admin')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for('main.index'))

    drafts = ContractDraft.query.all()
    sources = NewsSource.query.all()
    return render_template('admin/dashboard.html', drafts=drafts, sources=sources)

@admin.route('/admin/publish/<int:draft_id>', methods=['POST'])
@login_required
def publish_draft(draft_id):
    if not current_user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for('main.index'))

    # Assume ContractDraft has .to_contract() method or similar
    draft = ContractDraft.query.get_or_404(draft_id)
    market = draft.to_contract()
    db.session.add(market)
    db.session.commit()

    db.session.delete(draft)
    db.session.commit()

    flash("Draft published successfully", "success")
    return redirect(url_for('admin.dashboard'))
