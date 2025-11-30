import sys
import csv
import time
import subprocess
import re
import argparse
import uiautomation as auto

class Automator:
    def __init__(self):
        self.actions = []
        self.variables = {}
        self.aliases = {}


    def load_aliases(self, alias_file):
        """Loads aliases from a CSV file."""
        print(f"Loading aliases from {alias_file}...")
        try:
            with open(alias_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    alias = row.get("AliasName")
                    path = row.get("RPA_Path")
                    if alias and path:
                        if alias in self.aliases:
                            print(f"Warning: Duplicate alias '{alias}' found. Overwriting.")
                        self.aliases[alias] = path
            print(f"Loaded {len(self.aliases)} aliases.")
        except Exception as e:
            print(f"Error loading aliases: {e}")
            sys.exit(1)

    def load_actions(self, csv_file):
        print(f"Loading actions from {csv_file}...")
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Resolve alias if present
                    key = row.get("Key", "") # Use .get to handle missing 'Key' gracefully
                    if key and key in self.aliases: # Check if key exists and is an alias
                        print(f"  Resolved alias '{key}' -> '{self.aliases[key]}'")
                        row["Key"] = self.aliases[key]
                    
                    self.actions.append(row)
            print(f"Loaded {len(self.actions)} actions.")
        except FileNotFoundError:
            print(f"Error: File not found: {csv_file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading actions: {e}")
            sys.exit(1)

    def run(self):
        for i, action in enumerate(self.actions):
            print(f"\n--- Action {i+1} ---")
            target_app = action.get('TargetApp', '')
            key = action.get('Key', '')
            act_type = action.get('Action', '')
            value = action.get('Value', '')

            # 変数置換 ({var_name} -> value)
            if '{' in value and '}' in value:
                for var_name, var_val in self.variables.items():
                    value = value.replace(f"{{{var_name}}}", str(var_val))

            print(f"Target: {target_app}, Action: {act_type}, Value: {value}")
            
            try:
                self.execute_action(target_app, key, act_type, value)
            except Exception as e:
                print(f"Action failed: {e}")
                # Continue or stop? For now, let's stop on critical error or just print
                # sys.exit(1)

    def execute_action(self, target_app, key, act_type, value):
        # 1. Launch
        if act_type == "Launch":
            print(f"Launching {value}...")
            subprocess.Popen(value, shell=True)
            return

        # 2. Wait
        if act_type == "Wait":
            print(f"Waiting {value} seconds...")
            time.sleep(float(value))
            return

        # 3. Find Window
        window = self.find_window(target_app)
        if not window:
            raise Exception(f"Window '{target_app}' not found.")

        # 4. Focus Window
        if act_type == "Focus":
            window.SetFocus()
            return

        # 5. Find Element (if Key is provided)
        element = window
        if key:
            element = self.find_element_by_path(window, key)
            if not element:
                raise Exception(f"Element not found for key: {key}")

        # 6. Interact
        if act_type == "Click":
            print(f"Clicking element '{element.Name}'...")
            try:
                invoke = element.GetPattern(auto.PatternId.InvokePattern)
                if invoke:
                    print("  Using InvokePattern...")
                    invoke.Invoke()
                else:
                    element.Click()
            except Exception as e:
                print(f"  Invoke failed, falling back to Click: {e}")
                element.Click()
        elif act_type == "GetValue":
            # 値を取得して変数に保存
            # ValuePatternがあればそれ、なければName
            val = element.Name
            
            # Try ValuePattern
            try:
                pattern = element.GetPattern(auto.PatternId.ValuePattern)
                if pattern:
                    val = pattern.Value
            except Exception as e:
                print(f"Warning: Failed to get ValuePattern: {e}")

            # Try TextPattern if Value is empty or same as Name (heuristic)
            if not val or val == element.Name:
                try:
                    pattern = element.GetPattern(auto.PatternId.TextPattern)
                    if pattern:
                        val = pattern.DocumentRange.GetText(-1)
                except Exception as e:
                    print(f"Warning: Failed to get TextPattern: {e}")
            
            print(f"Got value: '{val}'. Storing in variable '{value}'")
            self.variables[value] = val

        elif act_type == "Input":
            print(f"Inputting text: {value}")
            # Try to set value using ValuePattern first if applicable
            success = False
            if isinstance(element, (auto.EditControl, auto.DocumentControl)):
                try:
                    # Check if it supports ValuePattern
                    if element.GetPattern(auto.PatternId.ValuePattern):
                        element.SetValue(value)
                        success = True
                except Exception as e:
                    print(f"  SetValue failed: {e}")
            
            if not success:
                print("  Fallback to SendKeys...")
                element.SetFocus()
                auto.SendKeys(value)

        elif act_type == "SendKeys":
            print(f"Sending keys: {value}")
            element.SetFocus()
            time.sleep(0.5) # Focus wait
            auto.SendKeys(value)

        elif act_type == "SetClipboard":
            # {ENTER} などのプレースホルダーを置換
            text_to_copy = value.replace("{ENTER}", "\r\n")
            print(f"Setting clipboard: {text_to_copy}")
            auto.SetClipboardText(text_to_copy)

        elif act_type == "GetClipboard":
            # クリップボードからテキストを取得して変数に保存
            val = auto.GetClipboardText()
            print(f"Got clipboard text: '{val}'. Storing in variable '{value}'")
            self.variables[value] = val

        elif act_type == "VerifyValue":
            # 値を取得して比較
            # Valueが {var_name} の場合は変数の値と比較
            expected_val = value
            if '{' in value and '}' in value:
                 # 簡易的な変数展開（完全一致のみ対応）
                 # Inputのような部分置換ではなく、値そのものが変数参照である場合を想定
                 # しかし、今回は "Formula: ..." という文字列と比較したいので、
                 # execute_actionに来る前に run() で既に置換されているはず。
                 pass

            # 要素の値を取得（Name, ValuePattern, TextPattern）
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
            
            # もし要素が見つからない/値がない場合でも、変数の値と比較したい場合があるかも？
            # 今回は "GetClipboard" で変数に入れた値と比較したい。
            # その場合、VerifyValueのターゲットは要素ではなく "Variable" になるべきだが、
            # CSVフォーマット上 Key が必須。
            # そこで、Keyが空の場合は「変数同士の比較」または「変数と値の比較」とするロジックを追加。
            
            if not key:
                # Keyがない場合、TargetAppも無視して、Valueを "Actual == Expected" の形式でパースするか、
                # あるいは "VerifyVariable" アクションを作るか。
                # ここでは既存の VerifyValue を拡張し、Keyが空なら Value を "VarName==Expected" とみなす...のは複雑。
                # シンプルに、Keyが空なら "Value" は "変数名" とし、その変数の値と... 何を比較する？
                # CSVのValueカラムは1つしかない。
                pass

            print(f"Verifying value: Expected='{value}', Actual='{current_val}'")
            if current_val != value:
                raise Exception(f"Verification failed! Expected '{value}' but got '{current_val}'")
            print("Verification passed.")

        elif act_type == "VerifyVariable":
            # 変数の値を検証
            # Valueは "VarName==ExpectedValue" の形式を想定、あるいは
            # CSVの制約上、Valueには "ExpectedValue" を入れ、Keyに "VarName" を入れるなどの工夫が必要。
            # ここでは Key を変数名、Value を期待値として扱う。
            var_name = key # Keyカラムを変数名として利用
            expected_val = value
            
            actual_val = self.variables.get(var_name, '')
            print(f"Verifying variable '{var_name}':")
            print(f"  Expected: {repr(expected_val)}")
            print(f"  Actual  : {repr(actual_val)}")
            
            # CSVからの読み込みで \r\n が文字として入っている場合の対応
            expected_normalized = expected_val.replace('\\r', '\r').replace('\\n', '\n')
            actual_normalized = str(actual_val).replace('\r\n', '\n')
            expected_normalized = expected_normalized.replace('\r\n', '\n')

            if expected_normalized != actual_normalized:
                 raise Exception(f"Verification failed! Expected '{expected_normalized}' but got '{actual_normalized}'")
            print("Verification passed.")

        elif act_type == "Paste":
            print("Pasting from clipboard...")
            element.SetFocus()
            time.sleep(0.5)
            auto.SendKeys('{Ctrl}v')

        elif act_type == "Exit":
            print(f"Exiting {target_app}...")
            try:
                # Try WindowPattern Close
                pattern = window.GetPattern(auto.PatternId.WindowPattern)
                if pattern:
                    pattern.Close()
                else:
                    # Fallback to Alt+F4
                    window.SetFocus()
                    auto.SendKeys('{Alt}{F4}')
            except Exception as e:
                print(f"Failed to exit window: {e}")

        else:
            print(f"Unknown action: {act_type}")

    def find_window(self, target_app):
        # Try to find by Name (partial match) or ClassName
        # Root is Desktop
        print(f"Searching for window '{target_app}'...")
        # First try exact name
        win = auto.WindowControl(searchDepth=1, Name=target_app)
        if win.Exists(maxSearchSeconds=1):
            return win
        
        # Try regex/partial
        win = auto.WindowControl(searchDepth=1, RegexName=f".*{target_app}.*")
        if win.Exists(maxSearchSeconds=1):
            return win
            
        return None

    def find_element_by_path(self, root, path_string):
        """
        Parses the path string like "ControlTypeName(Prop='Val') -> ..." and traverses the tree.
        """
        parts = [p.strip() for p in path_string.split('->')]
        current = root
        
        for part in parts:
            if not part:
                continue
            
            # Parse "Type(Prop='Val', ...)"
            match = re.match(r"(\w+)(?:\((.*)\))?", part)
            if not match:
                print(f"Invalid path part format: {part}")
                return None
            
            control_type = match.group(1)
            props_str = match.group(2)
            
            # Search params
            search_params = {"ControlTypeName": control_type}
            found_index = 1 # Default to 1st match

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

            print(f"  Searching descendant: {search_params} (Index: {found_index}) under {current.Name}...")
            
            # Use uiautomation's search capability
            # searchDepth=0xFFFFFFFF means search all descendants
            # foundIndex support: GetChildren or FindAll is needed if index > 1, 
            # but uiautomation's Control() method usually returns the first match.
            # To support foundIndex, we might need to use GetChildren or FindAll if foundIndex > 1.
            # However, recursive search with index is tricky.
            # uiautomation supports `foundIndex` argument in GetFirstChild/GetLastChild but not directly in Control() for recursive?
            # Actually Control() has `foundIndex` parameter! Let's check signature.
            # Control(self, searchFromControl=None, searchDepth=0xFFFFFFFF, searchInterval=0.0, foundIndex=1, ... )
            
            target = current.Control(
                foundIndex=found_index,
                **search_params
            )
            
            if not target.Exists(maxSearchSeconds=2):
                print(f"  Not found: {part}")
                return None
            
            current = target
            
        return current

if __name__ == "__main__":
    csv_file = "actions.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    app = Automator(csv_file)
    app.load_actions()
    app.run()
