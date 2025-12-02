import uiautomation as auto
import pprint

print("uiautomation version:", auto.VERSION if hasattr(auto, 'VERSION') else "Unknown")
print("\nAttributes containing 'Dpi':")
for attr in dir(auto):
    if 'dpi' in attr.lower():
        print(attr)

print("\nAll attributes:")
pprint.pprint(dir(auto))
