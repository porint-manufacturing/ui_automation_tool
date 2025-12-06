"""
Focus Management Utilities

Handles UI element focus setting with Win32 API fallback for legacy applications.
"""

import logging
import ctypes
import uiautomation as auto


class FocusManager:
    """Manages UI element focus with fallback mechanisms."""
    
    def __init__(self, force_run=False):
        """
        Initialize FocusManager.
        
        Args:
            force_run: If True, continue execution even if focus fails
        """
        self.force_run = force_run
        self.logger = logging.getLogger(__name__)
    
    def set_focus_win32(self, element):
        """
        Set focus using Win32 API.
        
        Args:
            element: UI Automation element
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            hwnd = element.NativeWindowHandle
            if hwnd:
                user32 = ctypes.windll.user32
                user32.SetFocus(hwnd)
                self.logger.info(f"Focus set using Win32 API (HWND: {hwnd})")
                return True
            else:
                self.logger.warning("No NativeWindowHandle available for Win32 SetFocus")
                return False
        except Exception as e:
            self.logger.warning(f"Win32 SetFocus failed: {e}")
            return False
    
    def set_focus_with_fallback(self, element, element_desc="element"):
        """
        Set focus with UI Automation first, then Win32 API fallback.
        
        Args:
            element: UI Automation element
            element_desc: Description of element for logging
            
        Raises:
            RuntimeError: If focus fails and force_run is False
        """
        # Try UI Automation SetFocus first
        try:
            element.SetFocus()
            self.logger.info(f"Focus set on {element_desc} using UI Automation")
            return
        except Exception as e:
            self.logger.warning(f"UI Automation SetFocus failed for {element_desc}: {e}")
        
        # Fallback to Win32 API
        if self.set_focus_win32(element):
            return
        
        # Both methods failed
        error_msg = f"Failed to set focus on {element_desc} (both UI Automation and Win32 API failed)"
        if self.force_run:
            self.logger.warning(f"{error_msg}. Continuing due to --force-run flag.")
        else:
            raise RuntimeError(error_msg)
