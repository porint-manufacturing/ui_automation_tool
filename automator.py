import sys
import csv
import time
import subprocess
import re
import argparse
import logging
import os
import datetime
import uiautomation as auto

class Automator:
    def __init__(self, action_files, log_file=None, log_level="INFO", dry_run=False):
        self.actions = []
        self.variables = {}
        self.aliases = {}
        self.dry_run = dry_run
        
        # Configure logging
        level = getattr(logging, log_level.upper(), logging.INFO)
        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers,
            force=True # Reconfigure if already configured
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure action_files is a list
        if isinstance(action_files, str):
            self.action_files = [action_files]
        else:
            self.action_files = action_files
            
        if self.dry_run:
            self.logger.info("=== DRY RUN MODE ENABLED ===")

    def load_aliases(self, alias_files):
        """Loads aliases from one or more CSV files."""
        if isinstance(alias_files, str):
            alias_files = [alias_files]
            
        for alias_file in alias_files:
            self.logger.info(f"Loading aliases from {alias_file}...")
            try:
                with open(alias_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        alias = row.get("AliasName")
                        path = row.get("RPA_Path")
                        if alias and path:
                            if alias in self.aliases:
                                self.logger.warning(f"Duplicate alias '{alias}' found in {alias_file}. Overwriting.")
                            self.aliases[alias] = path
            except Exception as e:
                self.logger.error(f"Error loading aliases from {alias_file}: {e}")
                sys.exit(1)
        self.logger.info(f"Loaded {len(self.aliases)} aliases total.")

    def load_actions(self):
        for csv_file in self.action_files:
            self.logger.info(f"Loading actions from {csv_file}...")
            try:
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Resolve alias if present
                        key = row.get("Key", "")
                        if key and key in self.aliases:
                            self.logger.debug(f"Resolved alias '{key}' -> '{self.aliases[key]}'")
                            row["Key"] = self.aliases[key]
                        
                        self.actions.append(row)
            except FileNotFoundError:
                self.logger.error(f"File not found: {csv_file}")
                sys.exit(1)
            except Exception as e:
                self.logger.error(f"Error loading actions from {csv_file}: {e}")
                sys.exit(1)
        self.logger.info(f"Loaded {len(self.actions)} actions total.")

    def run(self):
        for i, action in enumerate(self.actions):
            self.logger.info(f"--- Action {i+1} ---")
            target_app = action.get('TargetApp', '')
            key = action.get('Key', '')
            act_type = action.get('Action', '')
            value = action.get('Value', '')

            # 変数置換
            if '{' in value and '}' in value:
                for var_name, var_val in self.variables.items():
                    value = value.replace(f"{{{var_name}}}", str(var_val))

            self.logger.info(f"Target: {target_app}, Action: {act_type}, Value: {value}")
            
            try:
                self.execute_action(target_app, key, act_type, value)
            except Exception as e:
                self.logger.error(f"Action failed: {e}")
                self.capture_screenshot(f"error_action_{i+1}")
                # sys.exit(1)

    def capture_screenshot(self, name_prefix):
        """Captures a screenshot of the entire screen."""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would capture screenshot: {name_prefix}")
            return

        try:
            if not os.path.exists("errors"):
                os.makedirs("errors")
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"errors/{name_prefix}_{timestamp}.png"
            
            # Capture full screen
            auto.GetRootControl().CaptureToImage(filename)
            self.logger.info(f"Screenshot saved to: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")

    def execute_action(self, target_app, key, act_type, value):
        if act_type == "Launch":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would launch: {value}")
                return
            self.logger.info(f"Launching {value}...")
            subprocess.Popen(value, shell=True)
            return

        if act_type == "Wait":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would wait: {value} seconds")
                return
            self.logger.info(f"Waiting {value} seconds...")
            time.sleep(float(value))
            return

        window = self.find_window(target_app)
        if not window:
            if self.dry_run:
                self.logger.warning(f"[Dry-run] Window '{target_app}' not found. Subsequent actions might fail.")
                return
            raise Exception(f"Window '{target_app}' not found.")

        if act_type == "Focus":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would focus window: {target_app}")
                return
            window.SetFocus()
            return

        element = window
        if key:
            element = self.find_element_by_path(window, key)
            if not element:
                if self.dry_run:
                     self.logger.warning(f"[Dry-run] Element not found for key: {key}")
                     return
                raise Exception(f"Element not found for key: {key}")
            if self.dry_run:
                self.logger.info(f"[Dry-run] Element found: {element.Name} ({element.ControlTypeName})")

        if act_type == "Click":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would click element: {element.Name}")
                return
            self.logger.info(f"Clicking element '{element.Name}'...")
            try:
                invoke = element.GetPattern(auto.PatternId.InvokePattern)
                if invoke:
                    self.logger.debug("Using InvokePattern...")
                    invoke.Invoke()
                else:
                    element.Click()
            except Exception as e:
                self.logger.warning(f"Invoke failed, falling back to Click: {e}")
                element.Click()

        elif act_type == "GetValue":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would get value from element: {element.Name} and store in '{value}'")
                self.variables[value] = "[DryRunValue]"
                return

            val = element.Name
            try:
                pattern = element.GetPattern(auto.PatternId.ValuePattern)
                if pattern:
                    val = pattern.Value
            except Exception as e:
                self.logger.warning(f"Failed to get ValuePattern: {e}")

            if not val or val == element.Name:
                try:
                    pattern = element.GetPattern(auto.PatternId.TextPattern)
                    if pattern:
                        val = pattern.DocumentRange.GetText(-1)
                except Exception as e:
                    self.logger.warning(f"Failed to get TextPattern: {e}")
            
            self.logger.info(f"Got value: '{val}'. Storing in variable '{value}'")
            self.variables[value] = val

        elif act_type == "Input":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would input text '{value}' into element: {element.Name}")
                return

            self.logger.info(f"Inputting text: {value}")
            success = False
            if isinstance(element, (auto.EditControl, auto.DocumentControl)):
                try:
                    if element.GetPattern(auto.PatternId.ValuePattern):
                        element.SetValue(value)
                        success = True
                except Exception as e:
                    self.logger.warning(f"SetValue failed: {e}")
            
            if not success:
                self.logger.debug("Fallback to SendKeys...")
                element.SetFocus()
                auto.SendKeys(value)

        elif act_type == "SendKeys":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would send keys '{value}' to element: {element.Name}")
                return

            self.logger.info(f"Sending keys: {value}")
            element.SetFocus()
            time.sleep(0.5)
            auto.SendKeys(value)

        elif act_type == "SetClipboard":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would set clipboard to: {value}")
                return

            text_to_copy = value.replace("{ENTER}", "\r\n")
            self.logger.info(f"Setting clipboard: {text_to_copy}")
            auto.SetClipboardText(text_to_copy)

        elif act_type == "GetClipboard":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would get clipboard text and store in '{value}'")
                self.variables[value] = "[DryRunClipboard]"
                return

            val = auto.GetClipboardText()
            self.logger.info(f"Got clipboard text: '{val}'. Storing in variable '{value}'")
            self.variables[value] = val

        elif act_type == "VerifyValue":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would verify value of element: {element.Name} against '{value}'")
                return

            current_val = element.Name
            try:
                pattern = element.GetPattern(auto.PatternId.ValuePattern)
                if pattern and pattern.Value:
                    current_val = pattern.Value
            except Exception:
                pass

            if not current_val:
                try:
                    pattern = element.GetPattern(auto.PatternId.TextPattern)
                    if pattern:
                        current_val = pattern.DocumentRange.GetText(-1)
                except Exception:
                    pass
            
            # The original code had an empty 'if not key: pass' block here.
            # The new code replaces the verification logic from here.
            
            # New verification logic for VerifyValue
            current_val = element.Name # This line seems redundant if current_val was already set above
            try:
                pattern = element.GetPattern(auto.PatternId.ValuePattern)
                if pattern:
                    current_val = pattern.Value
            except:
                pass
                
            if current_val == value:
                self.logger.info(f"Verification PASSED: Value is '{current_val}'")
            else:
                self.logger.error(f"Verification FAILED: Expected '{value}', got '{current_val}'")
                raise Exception(f"Verification failed. Expected '{value}', got '{current_val}'")

        elif act_type == "WaitUntilVisible":
            timeout = float(value) if value else 10.0
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would wait until element is visible: {key} (Timeout: {timeout}s)")
                return

            self.logger.info(f"Waiting until visible: {key} (Timeout: {timeout}s)...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Use a custom find method or just try/except with find_element_by_path
                # Since find_element_by_path logs errors/warnings, we might want to suppress them here or just accept them.
                # To avoid spamming logs, we can check existence manually or modify find_element_by_path.
                # For simplicity, let's just try to find it.
                try:
                    # We need to find the element dynamically each time
                    found = self.find_element_by_path(window, key)
                    if found and found.Exists(maxSearchSeconds=0):
                        self.logger.info(f"Element became visible.")
                        return
                except:
                    pass
                time.sleep(0.5)
            raise Exception(f"Timeout waiting for element to be visible: {key}")

        elif act_type == "FocusElement":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would focus element: {element.Name}")
                return
            self.logger.info(f"Focusing element '{element.Name}'...")
            element.SetFocus()

        elif act_type == "WaitUntilEnabled":
            timeout = float(value) if value else 10.0
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would wait until element is enabled: {key} (Timeout: {timeout}s)")
                return

            self.logger.info(f"Waiting until enabled: {key} (Timeout: {timeout}s)...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    found = self.find_element_by_path(window, key)
                    if found and found.Exists(maxSearchSeconds=0) and found.IsEnabled:
                        self.logger.info(f"Element became enabled.")
                        return
                except:
                    pass
                time.sleep(0.5)
            raise Exception(f"Timeout waiting for element to be enabled: {key}")

        elif act_type == "WaitUntilGone":
            timeout = float(value) if value else 10.0
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would wait until element is gone: {key} (Timeout: {timeout}s)")
                return

            self.logger.info(f"Waiting until gone: {key} (Timeout: {timeout}s)...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    found = self.find_element_by_path(window, key)
                    if not found or not found.Exists(maxSearchSeconds=0):
                        self.logger.info(f"Element is gone.")
                        return
                except:
                    # If find raises exception (e.g. parent gone), then it's gone
                    self.logger.info(f"Element is gone (exception).")
                    return
                time.sleep(0.5)
            raise Exception(f"Timeout waiting for element to be gone: {key}")

        elif act_type == "VerifyVariable":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would verify variable '{key}' against '{value}'")
                return

            var_name = key
            expected_val = value
            actual_val = self.variables.get(var_name, '')
            self.logger.info(f"Verifying variable '{var_name}': Expected='{expected_val}', Actual='{actual_val}'")
            
            expected_normalized = expected_val.replace('\\r', '\r').replace('\\n', '\n')
            actual_normalized = str(actual_val).replace('\r\n', '\n')
            expected_normalized = expected_normalized.replace('\r\n', '\n')

            if expected_normalized != actual_normalized:
                 raise Exception(f"Verification failed! Expected '{expected_normalized}' but got '{actual_normalized}'")
            self.logger.info("Verification passed.")

        elif act_type == "Paste":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would paste from clipboard to element: {element.Name}")
                return

            self.logger.info("Pasting from clipboard...")
            element.SetFocus()
            time.sleep(0.5)
            auto.SendKeys('{Ctrl}v')

        elif act_type == "Exit":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would exit window: {target_app}")
                return

            self.logger.info(f"Exiting {target_app}...")
            try:
                pattern = window.GetPattern(auto.PatternId.WindowPattern)
                if pattern:
                    pattern.Close()
                else:
                    window.SetFocus()
                    auto.SendKeys('{Alt}{F4}')
            except Exception as e:
                self.logger.error(f"Failed to exit window: {e}")

        else:
            self.logger.warning(f"Unknown action: {act_type}")

    def find_window(self, target_app):
        self.logger.debug(f"Searching for window '{target_app}'...")
        win = auto.WindowControl(searchDepth=1, Name=target_app)
        if win.Exists(maxSearchSeconds=1):
            return win
        
        win = auto.WindowControl(searchDepth=1, RegexName=f".*{target_app}.*")
        if win.Exists(maxSearchSeconds=1):
            return win
            
        return None

    def find_element_by_path(self, root, path_string):
        parts = [p.strip() for p in path_string.split('->')]
        current = root
        
        for part in parts:
            if not part:
                continue
            
            match = re.match(r"(\w+)(?:\((.*)\))?", part)
            if not match:
                self.logger.error(f"Invalid path part format: {part}")
                return None
            
            control_type = match.group(1)
            props_str = match.group(2)
            
            search_params = {"ControlTypeName": control_type}
            found_index = 1

            if props_str:
                name_match = re.search(r"\bName='([^']*)'", props_str)
                id_match = re.search(r"\bAutomationId='([^']*)'", props_str)
                class_match = re.search(r"\bClassName='([^']*)'", props_str)
                index_match = re.search(r"\bfoundIndex=(\d+)", props_str)
                depth_match = re.search(r"\bsearchDepth=(\d+)", props_str)
                
                if name_match:
                    search_params["Name"] = name_match.group(1)
                if id_match:
                    search_params["AutomationId"] = id_match.group(1)
                if class_match:
                    search_params["ClassName"] = class_match.group(1)
                if index_match:
                    found_index = int(index_match.group(1))
                if depth_match:
                    search_params["searchDepth"] = int(depth_match.group(1))

            self.logger.debug(f"Searching descendant: {search_params} (Index: {found_index}) under {current.Name}...")
            
            target = current.Control(
                foundIndex=found_index,
                **search_params
            )
            
            if not target.Exists(maxSearchSeconds=2):
                self.logger.warning(f"Not found: {part}")
                return None
            
            current = target
            
        return current

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automator: Execute UI automation from CSV.")
    parser.add_argument("csv_files", nargs='+', default=["actions.csv"], help="Path to the actions CSV file(s).")
    parser.add_argument("--aliases", nargs='+', help="Path to the aliases CSV file(s).")
    parser.add_argument("--log-file", help="Path to the log file.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level.")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no side effects).")
    
    args = parser.parse_args()
    
    app = Automator(args.csv_files, log_file=args.log_file, log_level=args.log_level, dry_run=args.dry_run)
    
    if args.aliases:
        app.load_aliases(args.aliases)
        
    app.load_actions()
    app.run()
