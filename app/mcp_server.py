import sqlite3
import logging
import sys
import os
from typing import Literal
from mcp.server.fastmcp import FastMCP

# CRITICAL FDE GOTCHA: Configure logging to write strictly to stderr. 
# If you write to stdout (like a standard print statement), it will corrupt 
# the JSON-RPC messages MCP uses to talk to the LLM, and the system will crash.
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s: %(message)s")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "playbook.db")

# Initialize the FastMCP server
mcp = FastMCP("ContractSentry Playbook")

@mcp.tool()
def get_compliance_rule(category: Literal["liability", "governing_law", "payment_terms", "data_privacy", "termination"]) -> str:
    """
    Fetches strict enterprise compliance rules from the corporate playbook.
    Use this tool whenever you need to check if a contract clause violates company policy.
    """
    logging.info(f"Tool invoked: LLM requested rule for category: '{category}'")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Secure parameterized query prevents SQL Injection
        cursor.execute(
            "SELECT rule_text FROM contract_rules WHERE category = ?", 
            (category,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            logging.info(f"Database hit: Rule found for {category}")
            return row[0]
        
        logging.warning(f"Database miss: No rule found for {category}")
        return f"No specific rule defined for the category: {category}."
        
    except Exception as e:
        logging.error(f"Database execution error: {e}")
        return "System Error: Could not retrieve the rule from the database due to an internal execution error."

if __name__ == "__main__":
    logging.info("Starting ContractSentry MCP Server on stdio transport...")
    mcp.run()