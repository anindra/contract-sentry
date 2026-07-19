import sqlite3
import os
from typing import Literal
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "playbook.db")

# 1. Input Contract: Defines exactly what parameters the LLM is allowed to generate
class RuleQuery(BaseModel):
    category: Literal["liability", "governing_law", "payment_terms", "data_privacy", "termination"] = Field(
        description="The specific category of legal compliance rules to fetch from the enterprise playbook."
    )

# 2. Output Contract: Guarantees the exact structure returned to the execution context
class RuleResponse(BaseModel):
    category: str
    rule_text: str
    status: Literal["FOUND", "NOT_FOUND"]

# 3. Secure Gateway Function
def fetch_playbook_rule(query: RuleQuery) -> RuleResponse:
    """
    Safely resolves a verified Pydantic query against the SQLite backend
    using parameterized inputs to prevent SQL injection.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Secure Parameterized Query: The input is treated strictly as data, never as executable SQL code
    cursor.execute(
        "SELECT rule_text FROM contract_rules WHERE category = ?", 
        (query.category,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return RuleResponse(
            category=query.category,
            rule_text=row[0],
            status="FOUND"
        )
    
    return RuleResponse(
        category=query.category,
        rule_text="No specific rule defined for this category.",
        status="NOT_FOUND"
    )