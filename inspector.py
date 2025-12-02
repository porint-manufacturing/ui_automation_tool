import uiautomation as auto
import time
import keyboard
import argparse
import csv
import datetime
import sys
import io
import ctypes

# Enable High DPI Awareness to ensure correct coordinates
try:
    auto.SetProcessDpiAwareness(2) # Process_PerMonitorDpiAware
except Exception:
    pass

class Inspector:
    def __init__(self, mode="modern", output="clipboard"):
        self.mode = mode
        self.output = output
        self.recorded_items = []
        print(f"UI Inspector initialized (Mode: {mode}, Output: {output})")

    def get_rpa_path(self, control):
        """
        Generates a robust RPA path for the control.
        Uses chained paths (Parent -> Child) to improve performance and uniqueness.
        """
        root = control.GetTopLevelControl()
        if not root:
            return self._generate_segment(control, None)

        # Collect lineage: [Root, ..., Parent, Control]
        # We don't include Root in the path string (it's the TargetApp).
        lineage = []
        current = control
        depth_safety = 0
        while current and depth_safety < 50:
            if auto.ControlsAreSame(current, root):
                break
            lineage.insert(0, current)
            try:
                current = current.GetParentControl()
            except Exception as e:
                print(f"Warning: GetParentControl failed: {e}")
                break
            depth_safety += 1
        
        # Generate path segments
        path_segments = []
        parent = root
        for item in lineage:
            segment = self._generate_segment(item, parent)
            path_segments.append(segment)
            parent = item
            
        return " -> ".join(path_segments)

    def _generate_segment(self, control, parent):
        """Generates a single path segment (Type(Props)) relative to parent."""
        control_type = control.ControlTypeName
        name = control.Name
        automation_id = control.AutomationId
        class_name = control.ClassName
        
        criteria = []
        search_params = {"ControlTypeName": control_type}
        
        # 1. Strategy: AutomationId (Modern)
        if self.mode == "modern" and automation_id:
            criteria.append(f"AutomationId='{automation_id}'")
            search_params["AutomationId"] = automation_id
            
        # 2. Strategy: Name (Modern/Legacy if stable)
        # In legacy mode, we might skip Name if it looks dynamic, but for now we include it if present.
        elif name:
            # Escape single quotes
            safe_name = name.replace("'", "\\'")
            criteria.append(f"Name='{safe_name}'")
            search_params["Name"] = name
            
        # 3. Strategy: ClassName (Legacy)
        if self.mode == "legacy" and class_name:
            criteria.append(f"ClassName='{class_name}'")
            search_params["ClassName"] = class_name
            
        # 4. Strategy: Fallback to ClassName if nothing else
        if not criteria and class_name:
            criteria.append(f"ClassName='{class_name}'")
            search_params["ClassName"] = class_name

        # Calculate foundIndex relative to PARENT
        # This is much faster than searching the whole tree.
        found_index = 1
        
        if parent:
            try:
                count = 0
                found = False
                
                # Use WalkControl with maxDepth=1 to search ONLY direct children.
                # This avoids traversing deep subtrees (like massive lists).
                # Note: WalkControl(root, maxDepth=1) yields root, then children.
                # We skip the first one (parent itself).
                
                gen = auto.WalkControl(parent, maxDepth=1)
                next(gen) # Skip parent
                
                for ctrl, depth in gen:
                    # Check match
                    is_match = (ctrl.ControlTypeName == control_type)
                    if is_match and "AutomationId" in search_params:
                        is_match = (ctrl.AutomationId == search_params["AutomationId"])
                    if is_match and "Name" in search_params:
                        is_match = (ctrl.Name == search_params["Name"])
                    if is_match and "ClassName" in search_params:
                        is_match = (ctrl.ClassName == search_params["ClassName"])
                    
                    if is_match:
                        count += 1
                        if auto.ControlsAreSame(ctrl, control):
                            found_index = count
                            found = True
                            break
                
                if not found:
                    # Fallback: It might not be a direct child if the hierarchy changed dynamically?
                    pass

            except Exception as e:
                # This often happens with transient elements (like menus closing).
                # Defaulting to 1 is usually safe for these unique items.
                print(f"    Warning: Index calculation skipped (defaulting to 1). Reason: {e}")
                found_index = 1

        # Construct path string
        props = criteria
        if found_index > 1 or self.mode == "legacy":
             props.append(f"foundIndex={found_index}")
        
        # If we are chaining (parent exists), we enforce searchDepth=1
        if parent:
            props.append("searchDepth=1")
        
        props_str = ", ".join(props)
        return f"{control_type}({props_str})"

    def run(self):
        print("UI Inspector started.")
        
        if self.output == "interactive_alias":
            self.run_interactive()
        else:
            self.run_normal()

        self.finalize()

    def run_interactive(self):
        print("Interactive Alias Mode")
        print("Type the alias name and press Enter, then click the target element.")
        print("Type 'q' or 'exit' to finish.")
        print("-" * 50)

        while True:
            try:
                alias_name = input("\n[Interactive] Enter Alias Name (or 'q' to finish): ").strip()
            except EOFError:
                break
                
            if alias_name.lower() in ['q', 'exit']:
                break
            
            if not alias_name:
                print("  >> Name cannot be empty.")
                continue

            print(f"  >> Click the element for '{alias_name}' (Press ESC to cancel this item)...")
            
            result = self.wait_for_click()
            if not result:
                print("  >> Cancelled.")
                continue
            
            control, x, y = result
            path = self.get_rpa_path(control)
            print(f"  >> Captured: {path}")
            
            self.recorded_items.append({
                "AliasName": alias_name,
                "RPA_Path": path
            })

    def run_normal(self):
        print("Hover over an element and CLICK (Left Click) to inspect/record.")
        print("Press 'ESC' to finish and output.")
        print("-" * 50)

        last_element = None
        
        while True:
            if keyboard.is_pressed('esc'):
                print("\nFinishing...")
                break
                
            # Check for click (Left Button) using ctypes
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                x, y = auto.GetCursorPos()
                control = auto.ControlFromPoint(x, y)
                
                if control:
                    # Debounce
                    if not last_element or not auto.ControlsAreSame(control, last_element):
                        self.inspect_element(control, x, y)
                        last_element = control
                        while ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                            time.sleep(0.05)
                else:
                    time.sleep(0.1)
            else:
                last_element = None 
                time.sleep(0.05)

    def wait_for_click(self):
        """Waits for a left click and returns (control, x, y). Returns None if ESC is pressed."""
        while True:
            if keyboard.is_pressed('esc'):
                return None
            
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                x, y = auto.GetCursorPos()
                control = auto.ControlFromPoint(x, y)
                # Wait for release to avoid multiple registrations
                while ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                    time.sleep(0.05)
                return control, x, y
            
            time.sleep(0.05)

    def inspect_element(self, control, x, y):
        print(f"\n[Clicked at {x}, {y}] Inspecting...")
        
        # Basic info
        print(f"  Name: {control.Name}")
        print(f"  Type: {control.ControlTypeName}")
        print(f"  Class: {control.ClassName}")
        print(f"  AutoId: {control.AutomationId}")
        
        # Get TargetApp (Window Name)
        # We use the TopLevelControl's Name as the TargetApp identifier.
        # This corresponds to the 'Name' or 'RegexName' used in Automator's find_window.
        root = control.GetTopLevelControl()
        target_app = root.Name if root else "Unknown"
        print(f"  TargetApp: {target_app}")
        
        # Generate Path
        rpa_path = self.get_rpa_path(control)
        print(f"  RPA_Path: {rpa_path}")
        
        # Record
        if self.output in ["csv", "clipboard", "alias"]:
            self.recorded_items.append({
                "TargetApp": target_app,
                "Key": rpa_path,
                "Action": "",
                "Value": ""
            })
            print(f"  -> Recorded ({len(self.recorded_items)} items)")

    def finalize(self):
        if not self.recorded_items:
            print("No items recorded.")
            return

        if self.output == "csv":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inspector_{timestamp}.csv"
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
                writer.writeheader()
                writer.writerows(self.recorded_items)
            print(f"Saved to {filename}")
            
        elif self.output == "clipboard":
            # Generate CSV string
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["TargetApp", "Key", "Action", "Value"])
            writer.writeheader()
            writer.writerows(self.recorded_items)
            csv_content = output.getvalue()
            
            auto.SetClipboardText(csv_content)
            print("Copied CSV content to clipboard.")

        elif self.output in ["alias", "interactive_alias"]:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inspector_{timestamp}_alias.csv"
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["AliasName", "RPA_Path"])
                writer.writeheader()
                
                alias_items = []
                for item in self.recorded_items:
                    if "AliasName" in item:
                        # Interactive mode item
                        alias_items.append(item)
                    else:
                        # Normal mode item (convert Key to RPA_Path)
                        alias_items.append({"AliasName": "", "RPA_Path": item["Key"]})
                
                writer.writerows(alias_items)
            print(f"Saved alias definition to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UI Inspector for Automator")
    parser.add_argument("--mode", choices=["modern", "legacy"], default="modern", help="Inspection mode")
    parser.add_argument("--output", choices=["normal", "csv", "clipboard", "alias", "interactive_alias"], default="clipboard", help="Output mode")
    
    args = parser.parse_args()
    
    inspector = Inspector(mode=args.mode, output=args.output)
    inspector.run()
