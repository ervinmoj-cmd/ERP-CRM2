
import os
import sys

# Mock configuration
# We need to load environment or rely on the user providing creds?
# Since we can't interactively ask for password in script, we will try to use the ones from the database if possible.
# But database access requires app context or manual db usage.

# Let's try to just import and run 'fetch_new_emails' with dummy data? No, that won't test connection.
# We'll try to use the same logic as 'sync_client_responses' but print more debug info.

from database import get_user_by_id, get_all_users
from email_reader import fetch_new_emails

# We need a valid user email/password to test.
# I will fetch the first user with smtp credentials from DB.

def test_sync():
    print("Testing email sync connection...")
    users = get_all_users()
    test_user = None
    target_email = "emoreno@inair.com.mx"
    
    for u in users:
        val_email = (u.get('email') or '').strip()
        val_smtp = (u.get('email_smtp') or '').strip()
        if target_email in val_email or target_email in val_smtp:
            if u.get('password_smtp'):
                test_user = u
                break
    
    if not test_user:
        print(f"User {target_email} not found or has no SMTP password.")
        # Fallback to any user
        for u in users:
             if u.get('email_smtp') and u.get('password_smtp'):
                test_user = u
                print(f"Fallback to user: {u['email']}")
                break


    print(f"Testing with user: {test_user['email']}")
    
    try:
        emails = fetch_new_emails(test_user['email_smtp'], test_user['password_smtp'], since_days=1)
        print(f"Successfully fetched {len(emails)} emails.")
        for e in emails[:3]:
            print(f" - {e['subject']} ({e['date']})")
    except Exception as e:
        print(f"Error fetching emails: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync()
