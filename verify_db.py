from database import get_all_pis
import sys

try:
    pis = get_all_pis()
    print(f"Found {len(pis)} PIs")
    if pis:
        first_pi = pis[0]
        print(f"First PI keys: {list(first_pi.keys())}")
        if 'items' in first_pi:
            print(f"Items found: {len(first_pi['items'])}")
            print("Status: SUCCESS - Code on disk is correct.")
        else:
            print("Status: FAILURE - 'items' key missing from PI dict.")
    else:
        print("Status: FAILURE - No PIs found.")

except Exception as e:
    print(f"Error: {e}")
