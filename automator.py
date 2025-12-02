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

# Enable High DPI Awareness to ensure correct coordinates
try:
    auto.SetProcessDpiAwareness(2) # Process_PerMonitorDpiAware
except Exception:
    pass # Ignore if not supported (e.g. older Windows)

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

    def evaluate_condition(self, condition):
        """Evaluates a condition string like '{status} == 'OK''."""
        # Replace variables
        if '{' in condition and '}' in condition:
            for var_name, var_val in self.variables.items():
                condition = condition.replace(f"{{{var_name}}}", str(var_val))
        
        # Safety check: only allow simple comparisons
        # This is a basic implementation. For production, use a safer parser.
        try:
            # We use eval() here for flexibility, but it's risky if inputs are untrusted.
            # Assuming CSVs are trusted.
            return eval(condition)
        except Exception as e:
            self.logger.error(f"Condition evaluation failed: {condition} - {e}")
            return False

    def find_matching_end(self, start_index, start_type):
        """Finds the matching EndIf/Else/EndLoop for a given start action."""
        nesting = 0
        for i in range(start_index + 1, len(self.actions)):
            act = self.actions[i].get('Action', '')
            
            if start_type == 'If':
                if act == 'If':
                    nesting += 1
                elif act == 'EndIf':
                    if nesting == 0:
                        return i
                    nesting -= 1
                elif act == 'Else':
                    if nesting == 0:
                        return i
            
            elif start_type == 'Loop':
                if act == 'Loop':
                    nesting += 1
                elif act == 'EndLoop':
                    if nesting == 0:
                        return i
                    nesting -= 1
        return -1

    def run(self):
        i = 0
        loop_stack = [] # Stores (start_index, loop_info)
        
        while i < len(self.actions):
            action = self.actions[i]
            self.logger.info(f"--- Action {i+1} ---")
            target_app = action.get('TargetApp', '')
            key = action.get('Key', '')
            act_type = action.get('Action', '')
            value = action.get('Value', '')

            # Variable substitution for Value (except for control flow which handles it specifically)
            if act_type not in ['If', 'Loop', 'SetVariable']:
                 if '{' in value and '}' in value:
                    for var_name, var_val in self.variables.items():
                        value = value.replace(f"{{{var_name}}}", str(var_val))

            self.logger.info(f"Target: {target_app}, Action: {act_type}, Value: {value}")
            
            # --- Control Flow ---
            if act_type == 'If':
                condition = value
                result = self.evaluate_condition(condition)
                self.logger.info(f"Condition '{condition}' evaluated to: {result}")
                
                if result:
                    # Continue to next action (True block)
                    i += 1
                else:
                    # Jump to Else or EndIf
                    jump_to = self.find_matching_end(i, 'If')
                    if jump_to == -1:
                        self.logger.error("Missing matching EndIf/Else for If")
                        break
                    
                    # If we jumped to Else, we need to execute the Else block next (so i = jump_to + 1)
                    # But wait, if we jump to Else, the next iteration will process 'Else' action?
                    # No, 'Else' action itself should just jump to EndIf if encountered naturally.
                    # If we jump TO Else, we want to enter the block AFTER Else.
                    
                    next_act = self.actions[jump_to].get('Action', '')
                    if next_act == 'Else':
                        i = jump_to + 1
                    else: # EndIf
                        i = jump_to + 1
                continue

            elif act_type == 'Else':
                # If we hit Else naturally, it means we executed the True block.
                # So we must skip to EndIf.
                # We need to find the EndIf corresponding to the If that started this block.
                # But we don't have a reference to the start If here easily unless we track stack.
                # Alternatively, we can just scan forward for EndIf, respecting nesting.
                # Since we are inside an Else block (conceptually), we search for EndIf.
                # But wait, 'Else' is at the same nesting level as 'If'.
                
                # Scan forward for EndIf
                jump_to = self.find_matching_end(i, 'If') # Reuse If logic? No, If logic looks for Else/EndIf.
                # We need a finder that looks for EndIf only.
                
                nesting = 0
                found = -1
                for j in range(i + 1, len(self.actions)):
                    act = self.actions[j].get('Action', '')
                    if act == 'If':
                        nesting += 1
                    elif act == 'EndIf':
                        if nesting == 0:
                            found = j
                            break
                        nesting -= 1
                
                if found != -1:
                    i = found + 1
                else:
                    self.logger.error("Missing matching EndIf for Else")
                    break
                continue

            elif act_type == 'EndIf':
                # Just continue
                i += 1
                continue

            elif act_type == 'Loop':
                # Check if this loop is already active
                active_loop = None
                if loop_stack and loop_stack[-1][0] == i:
                    active_loop = loop_stack[-1]
                
                if active_loop:
                    # Re-eval condition
                    condition = value
                    # If value is a number, it's a count loop
                    if value.isdigit():
                         # Count is handled in state
                         pass # Logic below
                    else:
                         # Condition loop
                         pass
                else:
                    # New loop entry
                    pass

                # Unified Loop Logic
                # If value is digit -> Count loop.
                # Else -> Condition loop.
                
                should_loop = False
                
                # Expand variables in value for evaluation
                eval_value = value
                if '{' in eval_value and '}' in eval_value:
                    for var_name, var_val in self.variables.items():
                        eval_value = eval_value.replace(f"{{{var_name}}}", str(var_val))

                if eval_value.isdigit():
                    max_count = int(eval_value)
                    # Check stack
                    if loop_stack and loop_stack[-1][0] == i:
                        # Increment counter
                        loop_stack[-1][1]['current'] += 1
                        if loop_stack[-1][1]['current'] < max_count:
                            should_loop = True
                        else:
                            should_loop = False
                            loop_stack.pop() # Loop finished
                    else:
                        # First entry
                        if max_count > 0:
                            should_loop = True
                            loop_stack.append((i, {'type': 'count', 'current': 0, 'max': max_count}))
                        else:
                            should_loop = False
                else:
                    # Condition loop
                    result = self.evaluate_condition(value) # Use original value with vars
                    if result:
                        should_loop = True
                        if not (loop_stack and loop_stack[-1][0] == i):
                            loop_stack.append((i, {'type': 'condition'}))
                    else:
                        should_loop = False
                        if loop_stack and loop_stack[-1][0] == i:
                            loop_stack.pop()

                if should_loop:
                    i += 1
                else:
                    # Jump to EndLoop
                    jump_to = self.find_matching_end(i, 'Loop')
                    if jump_to == -1:
                        self.logger.error("Missing matching EndLoop")
                        break
                    i = jump_to + 1
                continue

            elif act_type == 'EndLoop':
                # Jump back to Loop start
                if loop_stack:
                    start_index = loop_stack[-1][0]
                    i = start_index
                else:
                    self.logger.error("EndLoop without active Loop")
                    i += 1
                continue

            # --- Normal Action ---
            try:
                self.execute_action(target_app, key, act_type, value)
            except Exception as e:
                self.logger.error(f"Action failed: {e}")
                self.capture_screenshot(f"error_action_{i+1}")
                # sys.exit(1)
            
            i += 1

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
            
            if not element.IsKeyboardFocusable:
                self.logger.warning(f"Element '{element.Name}' is not keyboard focusable. Focus might not work.")
                
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

        elif act_type == "SetVariable":
            if self.dry_run:
                self.logger.info(f"[Dry-run] Would set variable based on: {value}")
                return

            # Parse value: "var_name = expression" or just "var_name" (if getting from somewhere else? No, SetVariable implies setting)
            # Or "var_name = value"
            if "=" in value:
                parts = value.split("=", 1)
                var_name = parts[0].strip()
                expr = parts[1].strip()
                
                # Evaluate expression if it contains variables or math
                # Simple substitution first
                if '{' in expr and '}' in expr:
                    for v_name, v_val in self.variables.items():
                        expr = expr.replace(f"{{{v_name}}}", str(v_val))
                
                try:
                    # Try to eval as python expression (for math)
                    # If it fails (e.g. string), keep as string
                    # But eval('string') fails if not quoted.
                    # Let's try to eval, if NameError/SyntaxError, treat as string.
                    # But "1 + 1" should be 2.
                    val = eval(expr)
                except:
                    val = expr
                
                self.variables[var_name] = val
                self.logger.info(f"Set variable '{var_name}' to '{val}'")
            else:
                self.logger.warning(f"Invalid SetVariable format: {value}. Expected 'name = value'")

        else:
            self.logger.warning(f"Unknown action: {act_type}")

    def find_window(self, target_app):
        self.logger.debug(f"Searching for window '{target_app}'...")
        
        # Explicit Regex Mode
        if target_app.startswith("regex:"):
            pattern = target_app[6:] # Strip 'regex:'
            self.logger.debug(f"Using regex pattern: {pattern}")
            win = auto.WindowControl(searchDepth=1, RegexName=pattern)
            if win.Exists(maxSearchSeconds=1):
                return win
            return None

        # Standard Mode (Exact match first, then partial regex fallback)
        win = auto.WindowControl(searchDepth=1, Name=target_app)
        if win.Exists(maxSearchSeconds=1):
            return win
        
        # Fallback: Partial match using RegexName
        # Note: This might be risky if target_app contains regex special chars, 
        # but it's the existing behavior for "partial match".
        # Ideally we should escape it, but for backward compatibility we keep it simple or escape.
        # Let's escape it to be safe for "partial match" logic if it wasn't intended as regex.
        safe_name = re.escape(target_app)
        win = auto.WindowControl(searchDepth=1, RegexName=f".*{safe_name}.*")
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
                regex_name_match = re.search(r"\bRegexName='([^']*)'", props_str)
                id_match = re.search(r"\bAutomationId='([^']*)'", props_str)
                class_match = re.search(r"\bClassName='([^']*)'", props_str)
                index_match = re.search(r"\bfoundIndex=(\d+)", props_str)
                depth_match = re.search(r"\bsearchDepth=(\d+)", props_str)
                
                if name_match:
                    search_params["Name"] = name_match.group(1)
                if regex_name_match:
                    search_params["RegexName"] = regex_name_match.group(1)
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
