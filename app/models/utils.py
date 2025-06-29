import hashlib

def generate_contract_hash(contract_name: str) -> str:
    """Generate a SHA-256 hash for market integrity verification"""
    return hashlib.sha256(contract_name.encode()).hexdigest()
