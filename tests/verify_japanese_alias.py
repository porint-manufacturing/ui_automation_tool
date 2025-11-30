import sys
import os
import csv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from automator import Automator

def verify_japanese_alias():
    print("--- Testing Japanese Alias Support ---")
    
    alias_file = "tests/temp_jp_aliases.csv"
    actions_file = "tests/temp_jp_actions.csv"
    
    # Create alias file with Japanese alias
    with open(alias_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["AliasName", "RPA_Path"])
        writer.writeheader()
        writer.writerow({"AliasName": "メモ帳テキストエリア", "RPA_Path": "DocumentControl(ClassName='RichEditD2DPT')"})
    
    # Create actions file using the Japanese alias
    with open(actions_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
        writer.writeheader()
        writer.writerow({"TargetApp": "Notepad", "Key": "メモ帳テキストエリア", "Action": "Wait", "Value": "0"})
        
    # Initialize Automator
    automator = Automator(actions_file)
    automator.load_aliases(alias_file)
    automator.load_actions()
    
    # Verify resolution
    resolved_key = automator.actions[0]["Key"]
    print(f"Original Key: メモ帳テキストエリア")
    print(f"Resolved Key: {resolved_key}")
    
    if resolved_key == "DocumentControl(ClassName='RichEditD2DPT')":
        print("Japanese Alias Verification: PASS")
    else:
        print("Japanese Alias Verification: FAIL")
        
    # Cleanup
    if os.path.exists(alias_file): os.remove(alias_file)
    if os.path.exists(actions_file): os.remove(actions_file)
    
    return True

if __name__ == "__main__":
    verify_japanese_alias()
