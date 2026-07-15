import sqlite3
import os

DB_PATH = "../data/playbook.db"

def init_database():
    # Ensure a fresh database for testing
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            rule_text TEXT NOT NULL
        )
    """)
    
    # Seed enterprise compliance rules
    rules = [
        (
            "liability", 
            "The company's aggregate liability shall not exceed 1x the total fees paid in the 12 months preceding the incident. Unlimited liability clauses are strictly forbidden."
        ),
        (
            "governing_law", 
            "All contracts must be governed exclusively by the laws of the State of Delaware, without regard to conflict of laws principles."
        ),
        (
            "payment_terms", 
            "Standard payment terms are Net-30 days from the invoice date. Any terms extending past Net-45 require CFO sign-off."
        ),
        (
            "data_privacy", 
            "All vendor contracts must include a standard Data Processing Addendum (DPA) compliant with GDPR and CCPA. Vendor must notify of breaches within 24 hours."
        ),
        (
            "termination", 
            "The company must retain the right to terminate for convenience with 30 days written notice. Auto-renewal clauses must be modified to require written opt-in."
        )
    ]
    
    cursor.executemany(
        "INSERT INTO contract_rules (category, rule_text) VALUES (?, ?)", 
        rules
    )
    
    conn.commit()
    conn.close()
    print(f"Successfully initialized and seeded {DB_PATH} on persistent storage.")

if __name__ == "__main__":
    init_database()