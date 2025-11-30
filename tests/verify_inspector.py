import subprocess
import time
import uiautomation as auto
from inspector import Inspector

def verify_inspector_logic():
    print("Launching Calculator...")
    subprocess.Popen("calc.exe")
    time.sleep(2)
    
    calc_window = auto.WindowControl(searchDepth=1, Name="電卓")
    if not calc_window.Exists(maxSearchSeconds=3):
        calc_window = auto.WindowControl(searchDepth=1, RegexName=".*Calculator.*") # Fallback for English
    
    if not calc_window.Exists():
        print("Calculator window not found.")
        return

    print("Calculator found. Inspecting elements...")
    inspector = Inspector()

    # 1. Inspect '5' button
    print("\n--- Inspecting Button '5' ---")
    btn_5 = calc_window.ButtonControl(Name="5")
    if btn_5.Exists():
        path = inspector.get_rpa_path(btn_5)
        print(f"Generated Path: {path}")
        if "ClassName" in path and "foundIndex" in path:
            print("SUCCESS: ClassName and foundIndex are present.")
        else:
            print("FAILURE: ClassName or foundIndex missing.")
    else:
        print("Button '5' not found.")

    # 2. Inspect Hamburger Menu (Navigation)
    print("\n--- Inspecting Hamburger Menu (Navigation) ---")
    # Usually "Navigation" or "Open Navigation" button
    nav_btn = calc_window.ButtonControl(AutomationId="TogglePaneButton") # Common ID for WinUI nav
    if not nav_btn.Exists():
         nav_btn = calc_window.ButtonControl(Name="ナビゲーションを開く")

    if nav_btn.Exists():
        path = inspector.get_rpa_path(nav_btn)
        print(f"Generated Path: {path}")
        # Verify it works for menu/button
        if "ButtonControl" in path:
             print("SUCCESS: Identified as ButtonControl.")
    else:
        print("Hamburger menu button not found.")

    # 3. Inspect a Menu Item (if possible to open)
    # This is harder to automate reliably without disrupting state, but let's try opening nav
    # print("\n--- Inspecting Menu Item ---")
    # if nav_btn.Exists():
    #     nav_btn.Click()
    #     time.sleep(1)
    #     # Try to find a menu item like "Standard" or "Scientific"
    #     # In WinUI calculator, these are in a list
    #     ...

    print("\nVerification finished.")
    # Close calc
    # calc_window.GetWindowPattern().Close()

if __name__ == "__main__":
    verify_inspector_logic()
