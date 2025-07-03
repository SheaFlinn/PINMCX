def format_outcome(outcome: bool) -> str:
    """
    Convert a boolean outcome to its display string representation.
    
    Args:
        outcome: Boolean value representing the outcome
        
    Returns:
        str: "YES" if outcome is True, "NO" if outcome is False
        
    Raises:
        TypeError: If outcome is not a boolean
    """
    if not isinstance(outcome, bool):
        raise TypeError("Outcome must be a boolean value")
        
    return "YES" if outcome else "NO"

# Add type hints for easier usage
def format_outcome_display(outcome: bool) -> str:
    """
    Same as format_outcome but with a more descriptive name for display purposes.
    """
    return format_outcome(outcome)
