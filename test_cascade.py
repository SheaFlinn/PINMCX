import json
import os
import subprocess

def create_test_contracts():
    """
    Create sample contracts for testing the cascade.
    Returns a list of test contracts with varying qualities.
    """
    return [
        {
            "title": "The city council will approve new housing regulations by June 2025",
            "city": "Memphis",
            "expected_date": "2025-06-01",
            "department": "City Council",
            "source": "agenda"
        },
        {
            "title": "New transportation plan might be proposed",
            "city": "Memphis",
            "expected_date": "2025-07-01",
            "department": "Transportation",
            "source": "agenda"
        },
        {
            "title": "Budget review scheduled for next month",
            "city": "Memphis",
            "expected_date": "2025-08-01",
            "department": "Finance",
            "source": "agenda"
        }
    ]

def run_cascade():
    """
    Run the full cascade workflow and verify the output.
    """
    # Create test directory structure
    os.makedirs("drafts", exist_ok=True)
    
    # Step 1: Create initial test contracts
    with open("drafts/unpatched_contracts.json", 'w') as f:
        json.dump(create_test_contracts(), f, indent=2)
    
    # Step 2: Run patcher
    print("\n🚀 Running patcher...")
    subprocess.run(["python3", "patcher_api.py", "drafts/unpatched_contracts.json"])
    
    # Step 3: Run weigher
    print("\n🚀 Running weigher...")
    subprocess.run(["python3", "weigher_api.py", "drafts/patched_contracts.json"])
    
    # Step 4: Run balancer
    print("\n🚀 Running balancer...")
    subprocess.run(["python3", "balancer_api.py", "drafts/weighted_contracts.json"])
    
    # Step 5: Verify output
    print("\n🔍 Verifying output...")
    with open("drafts/balanced_contracts.json", 'r') as f:
        balanced_contracts = json.load(f)
    
    for contract in balanced_contracts:
        print(f"\n📄 Contract:")
        print(json.dumps(contract, indent=2))
        
        # Verify required fields
        assert "patched_title" in contract
        assert "weight" in contract
        assert "balanced_title" in contract
        
        # Verify weight is one of the expected values
        assert contract["weight"] in ["strong", "medium", "weak"]
        
        # Verify balanced title is a question
        assert contract["balanced_title"].strip().endswith("?")
        
        # Verify future reference
        assert re.search(r"by \w+ \d{1,2}|before|after|on", contract["balanced_title"], re.IGNORECASE)
        
        # Verify subject/actor
        assert re.search(r"will (the|[A-Z][a-z]+)", contract["balanced_title"])
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    run_cascade()
