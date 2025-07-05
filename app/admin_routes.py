from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.contract import ContractDraft
from app.models.published_contract import Contract
from app import db

admin = Blueprint('admin', __name__)

# GET /admin/contracts: Show all ContractDrafts (pending approval)
@admin.route('/contracts')
def contract_drafts():
    drafts = ContractDraft.query.all()
    return render_template('admin_contracts.html', drafts=drafts)

# POST /admin/contracts/<draft_id>/publish: Publish draft
@admin.route('/contracts/<int:draft_id>/publish', methods=['POST'])
def publish_draft(draft_id):
    draft = ContractDraft.query.get_or_404(draft_id)
    contract = draft.to_contract()
    db.session.add(contract)
    db.session.delete(draft)
    db.session.commit()
    flash('Draft published successfully.', 'success')
    return redirect(url_for('admin.contract_drafts'))

# POST /admin/contracts/<draft_id>/reject: Delete draft
@admin.route('/contracts/<int:draft_id>/reject', methods=['POST'])
def reject_draft(draft_id):
    draft = ContractDraft.query.get_or_404(draft_id)
    db.session.delete(draft)
    db.session.commit()
    flash('Draft rejected and deleted.', 'info')
    return redirect(url_for('admin.contract_drafts'))

# GET /admin/published: Show all published Contracts
@admin.route('/published')
def published_contracts():
    contracts = Contract.query.all()
    return render_template('admin_published.html', contracts=contracts)

