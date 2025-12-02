import sys
import os
import csv
import subprocess
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from automator import Automator
import uiautomation as auto

import logging

def verify_focus_button():
    print("--- Testing FocusElement on Notepad Edit ---")
    
    actions_file = "tests/temp_focus_notepad.csv"
    log_file = "tests/verify_focus_notepad.log"
    
    # Use Notepad
    rows = [
        {"TargetApp": "メモ帳", "Key": "", "Action": "Launch", "Value": "notepad.exe"},
        {"TargetApp": "メモ帳", "Key": "", "Action": "Wait", "Value": "2"},
        # Notepad Edit control
        {"TargetApp": "メモ帳", "Key": "EditControl(ClassName='Edit')", "Action": "FocusElement", "Value": ""},
        {"TargetApp": "メモ帳", "Key": "", "Action": "Wait", "Value": "1"},
        {"TargetApp": "メモ帳", "Key": "", "Action": "Exit", "Value": ""}
    ]
    
    with open(actions_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
        writer.writeheader()
        writer.writerows(rows)
        
    app = Automator([actions_file], log_file=log_file, log_level="DEBUG")
    
    window = None
    try:
        print("Launching Notepad...")
        app.execute_action("メモ帳", "", "Launch", "notepad.exe")
        time.sleep(2)
        
        print("Finding window...")
        # Use regex for Notepad title to be safe
        window = app.find_window("regex:.*(メモ帳|Notepad).*")
        if not window:
            print("FAIL: Notepad window not found")
            return

        # Find the edit control
        # Win11 Notepad might have different structure, try to find by ClassName 'Edit' or 'RichEditD2DPT'
        # Or just use the first EditControl
        edit = window.EditControl()
        if not edit.Exists(maxSearchSeconds=1):
            # Try finding recursively
            edit = window.EditControl(searchDepth=3)
            
        if edit.Exists():
            print(f"Edit control found. IsKeyboardFocusable: {edit.IsKeyboardFocusable}")
            
            # Unfocus it first (focus window title bar or something?)
            # Or just assume it might be focused by default.
            # Let's focus the window itself first (which might focus the edit control anyway).
            window.SetFocus()
            
            print("Executing FocusElement...")
            # We need to construct the key that matches this edit control
            # Let's use the one we found
            # But execute_action needs a string key.
            # Let's use a generic key that should match
            key = f"EditControl(ClassName='{edit.ClassName}')"
            
            app.execute_action("regex:.*(メモ帳|Notepad).*", key, "FocusElement", "")
            time.sleep(1)
            
            focused = auto.GetFocusedControl()
            print(f"Focused Control: {focused.Name} ({focused.ControlTypeName})")
            
            # Check if focused control is the edit control
            # Compare RuntimeId or similar
            if focused.GetRuntimeId() == edit.GetRuntimeId():
                print("PASS: Edit control is focused.")
            else:
                print("FAIL: Edit control is NOT focused.")
        else:
            print("FAIL: Edit control not found for testing.")
            
    except Exception as e:
        print(f"FAIL: Exception {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if window:
            try:
                if window.GetWindowPattern():
                    window.GetWindowPattern().Close()
                else:
                    window.SetFocus()
                    auto.SendKeys('{Alt}{F4}')
            except:
                pass
        
        # Close logger handlers to release file
        for handler in app.logger.handlers[:]:
            handler.close()
            app.logger.removeHandler(handler)
        logging.shutdown()
            
        if os.path.exists(actions_file): os.remove(actions_file)
        # Wait a bit for file release
        time.sleep(0.5)
        if os.path.exists(log_file): 
            try:
                os.remove(log_file)
            except:
                print("Warning: Could not remove log file")

if __name__ == "__main__":
    verify_focus_button()
