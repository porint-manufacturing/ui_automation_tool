import sys
import os
import csv
import subprocess
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inspector import Inspector
from automator import Automator

def verify_inspector_alias_output():
    print("--- Testing Inspector Alias Output ---")
    inspector = Inspector(output="alias")
    # Mock recorded items
    inspector.recorded_items = [
        {"TargetApp": "App1", "Key": "Path1", "Action": "", "Value": ""},
        {"TargetApp": "App1", "Key": "Path2", "Action": "", "Value": ""}
    ]
    inspector.finalize()
    
    # Check for output file
    files = [f for f in os.listdir(".") if f.startswith("inspector_") and f.endswith("_alias.csv")]
    if files:
        latest_file = sorted(files)[-1]
        print(f"Alias CSV created: {latest_file}")
        
        # Verify content
        with open(latest_file, 'r', encoding='utf-8-sig') as f:
            reader = list(csv.DictReader(f))
            if len(reader) == 2 and reader[0]["RPA_Path"] == "Path1" and "AliasName" in reader[0]:
                print("Inspector Alias Output Verification: PASS")
            else:
                print("Inspector Alias Output Verification: FAIL (Content mismatch)")
        
        # Cleanup
        os.remove(latest_file)
    else:
        print("Inspector Alias Output Verification: FAIL (File not created)")

def verify_automator_alias_execution():
    print("\n--- Testing Automator Alias Execution ---")
    
    # Create dummy alias file
    alias_file = "tests/temp_aliases.csv"
    with open(alias_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["AliasName", "RPA_Path"])
        writer.writeheader()
        writer.writerow({"AliasName": "MyAlias", "RPA_Path": "ResolvedPath"})
    
    # Create dummy actions file
    actions_file = "tests/temp_actions.csv"
    with open(actions_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["TargetApp", "Key", "Action", "Value"])
        writer.writeheader()
        writer.writerow({"TargetApp": "Test", "Key": "MyAlias", "Action": "Wait", "Value": "0"})
        
    # Initialize Automator and load
    automator = Automator()
    automator.load_aliases(alias_file)
    automator.load_actions(actions_file)
    
    # Check if alias was resolved in loaded actions
    # automator.actions is a list of dicts
    if automator.actions[0]["Key"] == "ResolvedPath":
        print("Automator Alias Resolution Verification: PASS")
    else:
        print(f"Automator Alias Resolution Verification: FAIL (Expected 'ResolvedPath', got '{automator.actions[0]['Key']}')")

    # Cleanup
    if os.path.exists(alias_file): os.remove(alias_file)
    if os.path.exists(actions_file): os.remove(actions_file)

if __name__ == "__main__":
    verify_inspector_alias_output()
    verify_automator_alias_execution()
