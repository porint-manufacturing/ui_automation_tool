"""
Element Utilities

Helper functions for UI element path formatting and manipulation.
"""


def format_path_with_alias(path, aliases):
    """
    Format element path with alias resolution for display.
    
    Args:
        path: Element path string
        aliases: Dictionary of alias mappings
        
    Returns:
        str: Formatted path with alias information
    """
    if not path:
        return path
    
    # Check if path starts with an alias
    for alias_name, alias_path in aliases.items():
        if path.startswith(f"${alias_name}"):
            # Show both alias and resolved path
            resolved = path.replace(f"${alias_name}", alias_path, 1)
            return f"{path} (resolved: {resolved})"
    
    return path
