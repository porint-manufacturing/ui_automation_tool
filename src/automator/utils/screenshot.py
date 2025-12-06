"""
Screenshot Utilities

Handles screenshot capture functionality.
"""

import logging
import os
import datetime
import uiautomation as auto


def capture_screenshot(name_prefix, dry_run=False):
    """
    Capture a screenshot of the entire screen.
    
    Args:
        name_prefix: Prefix for the screenshot filename
        dry_run: If True, only log the action without capturing
        
    Returns:
        str: Path to saved screenshot, or None if failed/dry-run
    """
    logger = logging.getLogger(__name__)
    
    if dry_run:
        logger.info(f"[Dry-run] Would capture screenshot: {name_prefix}")
        return None
    
    try:
        if not os.path.exists("errors"):
            os.makedirs("errors")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"errors/{name_prefix}_{timestamp}.png"
        
        # Capture full screen
        auto.GetRootControl().CaptureToImage(filename)
        logger.info(f"Screenshot saved to: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return None
