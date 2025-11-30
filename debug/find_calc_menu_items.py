import subprocess
import time
import uiautomation as auto
from inspector import Inspector

def find_menu_items():
    print("Launching Calculator...")
    subprocess.Popen("calc.exe")
    time.sleep(2)
    
    calc_window = auto.WindowControl(searchDepth=1, Name="電卓")
    if not calc_window.Exists(maxSearchSeconds=3):
        calc_window = auto.WindowControl(searchDepth=1, RegexName=".*Calculator.*")
    
    if not calc_window.Exists():
        print("Calculator window not found.")
        return

    inspector = Inspector()

    # 1. Click Hamburger Menu
    print("\n--- Clicking Hamburger Menu ---")
    nav_btn = calc_window.ButtonControl(AutomationId="TogglePaneButton")
    if not nav_btn.Exists():
         nav_btn = calc_window.ButtonControl(Name="ナビゲーションを開く")
    
    if nav_btn.Exists():
        nav_btn.Click()
        time.sleep(2) # Wait for animation
        
        print("Dumping all descendants (depth 5)...")
        # Use WalkControl to traverse
        def walk(control, depth):
            if depth > 5: return
            try:
                children = control.GetChildren()
                for child in children:
                    print(f"{'  '*depth} {child.ControlTypeName} - Name='{child.Name}' - ID='{child.AutomationId}'")
                    walk(child, depth+1)
            except:
                pass

        walk(calc_window, 0)

if __name__ == "__main__":
    find_menu_items()
