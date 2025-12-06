import subprocess
import time
import uiautomation as auto
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inspector import Inspector

def verify_inspector_logic():
    print("Launching Calculator...")
    subprocess.Popen("calc.exe")
    time.sleep(2)
    
    try:
        calc_window = auto.WindowControl(searchDepth=1, Name="電卓")
        if not calc_window.Exists(maxSearchSeconds=3):
            calc_window = auto.WindowControl(searchDepth=1, RegexName=".*Calculator.*") # Fallback for English
        
        if not calc_window.Exists():
            print("Calculator window not found.")
            return False

        print("Calculator found. Inspecting elements...")
        inspector = Inspector()  # Modern mode by default

        # 1. Inspect '5' button
        print("\n--- Inspecting Button '5' ---")
        btn_5 = calc_window.ButtonControl(Name="5")
        if btn_5.Exists():
            path = inspector.get_rpa_path(btn_5)
            print(f"Generated Path: {path}")
            # Modern mode should use AutomationId or Name
            if "AutomationId" in path or "Name" in path:
                print("SUCCESS: AutomationId or Name is present (modern mode).")
            else:
                print("FAILURE: Neither AutomationId nor Name found.")
                return False
        else:
            print("Button '5' not found.")
            return False

        # 2. Inspect Hamburger Menu (Navigation)
        print("\n--- Inspecting Hamburger Menu (Navigation) ---")
        nav_btn = calc_window.ButtonControl(AutomationId="TogglePaneButton")
        if not nav_btn.Exists():
             nav_btn = calc_window.ButtonControl(Name="ナビゲーションを開く")

        if nav_btn.Exists():
            path = inspector.get_rpa_path(nav_btn)
            print(f"Generated Path: {path}")
            # Verify it works for menu/button
            if "ButtonControl" in path:
                 print("SUCCESS: Identified as ButtonControl.")
            else:
                print("FAILURE: Not identified as ButtonControl.")
                return False
        else:
            print("Hamburger menu button not found.")
            return False

        print("\nInspector Verification: PASS")
        return True
        
    finally:
        # Close calculator
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'CalculatorApp.exe'], 
                          capture_output=True, timeout=5)
        except:
            pass

if __name__ == "__main__":
    success = verify_inspector_logic()
    sys.exit(0 if success else 1)
