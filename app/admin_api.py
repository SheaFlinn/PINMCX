from flask import Blueprint, jsonify, request, abort
from app.models.contract import ContractDraft
from app.models.published_contract import Contract
from app import db

admin_api = Blueprint('admin_api', __name__, url_prefix='/api/admin')

# GET /contracts: List all ContractDrafts
@admin_api.route('/contracts', methods=['GET'])
def list_contract_drafts():
    drafts = ContractDraft.query.all()
    return jsonify([draft.to_dict() for draft in drafts])

# POST /contracts/<draft_id>/publish: Publish a draft
@admin_api.route('/contracts/<int:draft_id>/publish', methods=['POST'])
def publish_contract_draft(draft_id):
    draft = ContractDraft.query.get(draft_id)
    if not draft:
        abort(404, description="Draft not found.")
    # Move to PublishedContract
    contract = Contract.from_draft(draft)
    db.session.add(contract)
    db.session.delete(draft)
    db.session.commit()
    return jsonify(contract.to_dict())

# POST /contracts/<draft_id>/reject: Delete a draft
@admin_api.route('/contracts/<int:draft_id>/reject', methods=['POST'])
def reject_contract_draft(draft_id):
    draft = ContractDraft.query.get(draft_id)
    if not draft:
        abort(404, description="Draft not found.")
    db.session.delete(draft)
    db.session.commit()
    return jsonify({"status": "deleted"})

# GET /published: List all published contracts
@admin_api.route('/published', methods=['GET'])
def list_published_contracts():
    contracts = Contract.query.all()
    return jsonify([contract.to_dict() for contract in contracts])

# Error handlers
@admin_api.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

@admin_api.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400
