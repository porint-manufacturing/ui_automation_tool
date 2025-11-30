import uiautomation as auto
import time
import sys
import os

def debug_traversal():
    print("Hover over a window and press Enter to debug traversal...")
    input()
    
    target = auto.ControlFromCursor()
    root = target.GetTopLevelControl()
    
    print(f"Target: {target.Name} ({target.ControlTypeName})")
    print(f"Root: {root.Name} ({root.ControlTypeName})")
    
    # Check for FindAll
    print(f"Root has FindAll? {'FindAll' in dir(root)}")
    print(f"Root has WalkControl? {'WalkControl' in dir(auto)}")
    
    # Test WalkControl performance
    print("\nTesting WalkControl...")
    start = time.time()
    count = 0
    found = False
    
    # WalkControl is a generator
    for ctrl, depth in auto.WalkControl(root, maxDepth=0xFFFFFFFF):
        if ctrl.ControlTypeName == target.ControlTypeName:
            count += 1
            if auto.ControlsAreSame(ctrl, target):
                print(f"Found target at index {count}")
                found = True
                break
    
    end = time.time()
    print(f"WalkControl took {end - start:.4f}s")
    
    if not found:
        print("Target not found via WalkControl (traversal limit?)")

if __name__ == "__main__":
    debug_traversal()
