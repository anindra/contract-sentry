from pydantic import BaseModel, Field
from typing import Literal

# 1. Input Contract
class RuleQuery(BaseModel):
    category: Literal["liability", "governing_law", "payment_terms", "data_privacy", "termination"] = Field(
        description="The specific category of legal compliance rules to fetch from the enterprise playbook."
    )

# 2. Output Contract
class RuleResponse(BaseModel):
    category: str
    rule_text: str
    status: Literal["FOUND", "NOT_FOUND"]