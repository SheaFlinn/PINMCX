import json
import os
from typing import List, Dict

def load_draft_contracts() -> List[Dict]:
    """Load draft contracts from JSON file"""
    try:
        with open("draft_contracts.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error loading JSON: {e}")
        return []

def generate_prompt(draft: Dict) -> str:
    """Generate a prompt for refining a contract"""
    return f"""Original Headline: {draft['original_headline']}

Source: {draft['source_name']}
Article Date: {draft['source_date']}

Original Question: {draft['title']}

Please refine this question to be more precise, clear, and balanced. The question should:
1. Be specific about what is being predicted
2. Have a clear timeframe
3. Avoid ambiguous language
4. Be neutral and unbiased
5. Be verifiable

Refined Question:"""

def print_prompts(drafts: List[Dict]):
    """Print prompts for all drafts"""
    for draft in drafts:
        print("\n" + "="*80 + "\n")
        print(generate_prompt(draft))
        print("\n" + "-"*80 + "\n")

def export_prompts(drafts: List[Dict], output_file: str):
    """Export prompts to a text file"""
    with open(output_file, "w") as f:
        for draft in drafts:
            f.write("\n" + "="*80 + "\n")
            f.write(generate_prompt(draft))
            f.write("\n" + "-"*80 + "\n")

def main():
    """Main function"""
    drafts = load_draft_contracts()
    
    if not drafts:
        print("No draft contracts found.")
        return
    
    print(f"Found {len(drafts)} draft contracts.")
    
    # Print prompts directly
    print("\nPrinting prompts to console:")
    print_prompts(drafts)
    
    # Export to file
    output_file = "contract_prompts.txt"
    export_prompts(drafts, output_file)
    print(f"\nPrompts exported to {output_file}")

if __name__ == '__main__':
    main()
