from pydantic import ValidationError
from app.gateway import RuleQuery, fetch_playbook_rule

def run_tests():
    print("--- SCENARIO 1: Valid Execution Flow ---")
    try:
        # Simulate the LLM successfully choosing a correct category
        valid_input = {"category": "liability"}
        validated_query = RuleQuery(**valid_input)
        
        result = fetch_playbook_rule(validated_query)
        print(f"Status: {result.status}")
        print(f"Category: {result.category}")
        print(f"Rule Text: {result.rule_text}\n")
    except Exception as e:
        print(f"Scenario 1 Failed: {e}\n")


    print("--- SCENARIO 2: Typo / Unsupported Category Deflected ---")
    try:
        # Simulate an LLM hallucinating an invalid category name
        invalid_input = {"category": "intellectual_property"}
        print("Attempting to parse invalid category...")
        RuleQuery(**invalid_input)
    except ValidationError as e:
        print("Success: Pydantic blocked the execution before it hit the database!")
        print(f"Validation Error Details:\n{e}\n")


    print("--- SCENARIO 3: Prompt Injection Deflected ---")
    try:
        # Simulate a malicious contract trying to inject SQL commands
        injection_attack = {"category": "liability'; DROP TABLE contract_rules; --"}
        print("Attempting to parse prompt injection attack string...")
        RuleQuery(**injection_attack)
    except ValidationError as e:
        print("Success: Pydantic successfully blocked the injection attempt!")
        print(f"Validation Error Details:\n{e}\n")

if __name__ == "__main__":
    run_tests()