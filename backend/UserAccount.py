import os
import json
import hashlib

ACCOUNTS_PATH = "database/accounts.txt"

def hash_password(password):
    """Hashes a password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_accounts():
    """Loads all registered user accounts from the database."""
    if not os.path.exists(ACCOUNTS_PATH):
        return {}
    with open(ACCOUNTS_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_accounts(accounts):
    """Saves the dictionary of accounts to the database file."""
    os.makedirs("database", exist_ok=True)
    with open(ACCOUNTS_PATH, "w") as f:
        json.dump(accounts, f, indent=4)

def register_user(username, password):
    """Registers a new user account if the username doesn't already exist."""
    username = username.strip()
    password = password.strip()

    if not username or not password:
        return False, "Username and password cannot be empty."

    accounts = load_accounts()

    if username in accounts:
        return False, "Username already exists. Choose another."

    accounts[username] = hash_password(password)
    save_accounts(accounts)
    return True, "Registration successful!"

def verify_user(username, password):
    """Verifies user login credentials."""
    username = username.strip()
    password = password.strip()

    accounts = load_accounts()

    if username not in accounts:
        return False, "Username not found."

    if accounts[username] == hash_password(password):
        return True, "Login successful!"
    else:
        return False, "Incorrect password."