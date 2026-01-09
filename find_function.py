
import os

def check_file(filename):
    print(f"Checking {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if 'def get_purchase_requisitions' in line:
                    print(f"FOUND get_purchase_requisitions at line {i+1}")
                if 'def create_ocu' in line:
                    print(f"FOUND create_ocu at line {i+1}")
                if 'def create_purchase_requisition' in line:
                    print(f"FOUND create_purchase_requisition at line {i+1}")
    except Exception as e:
        print(f"Error: {e}")

check_file('database.py')
