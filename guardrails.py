"""
Marine Corps Operations Assistant (MCOA) - Security Guardrails
"""

from typing import Union, List
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
)
import re


@input_guardrail
async def classification_guardrail(
    context: RunContextWrapper[None], 
    agent: Agent, 
    input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """Validates classification level and blocks unauthorized access."""
    
    # Get the input text
    if isinstance(input, str):
        user_input = input.lower()
    else:
        # Get the last user message
        user_input = ""
        for item in reversed(input):
            if isinstance(item, dict) and item.get("role") == "user":
                user_input = item.get("content", "").lower()
                break
    
    # Check for classification markers in request
    classified_keywords = [
        "classified", "secret", "top secret", "ts/sci", "noforn",
        "crypto", "sigint", "humint"
    ]
    
    for keyword in classified_keywords:
        if keyword in user_input:
            return GuardrailFunctionOutput(
                output_info={
                    "violation": "classification",
                    "keyword": keyword,
                    "message": "Attempted to access classified information"
                },
                tripwire_triggered=True
            )
    
    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False
    )


@input_guardrail
async def pii_protection_guardrail(
    context: RunContextWrapper[None], 
    agent: Agent, 
    input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """Prevents exposure of personally identifiable information."""
    
    # Get the input text
    if isinstance(input, str):
        user_input = input.lower()
    else:
        # Get the last user message
        user_input = ""
        for item in reversed(input):
            if isinstance(item, dict) and item.get("role") == "user":
                user_input = item.get("content", "").lower()
                break
    
    # Check for PII requests
    pii_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        r'\b\d{10}\b',  # DoD ID pattern
        r'social security',
        r'home address',
        r'personal phone',
        r'next of kin',
        r'family member'
    ]
    
    for pattern in pii_patterns:
        if re.search(pattern, user_input):
            return GuardrailFunctionOutput(
                output_info={
                    "violation": "pii",
                    "pattern": pattern,
                    "message": "Request for PII blocked"
                },
                tripwire_triggered=True
            )
    
    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False
    )


@input_guardrail
async def opsec_guardrail(
    context: RunContextWrapper[None], 
    agent: Agent, 
    input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """Ensures operational security in responses."""
    
    # Get the input text
    if isinstance(input, str):
        user_input = input.lower()
    else:
        # Get the last user message
        user_input = ""
        for item in reversed(input):
            if isinstance(item, dict) and item.get("role") == "user":
                user_input = item.get("content", "").lower()
                break
    
    # Check for sensitive operational details
    opsec_violations = [
        "real world", "actual operation", "current deployment",
        "troop movements", "exact coordinates", "real names",
        "actual location", "live operation"
    ]
    
    for violation in opsec_violations:
        if violation in user_input:
            return GuardrailFunctionOutput(
                output_info={
                    "violation": "opsec",
                    "keyword": violation,
                    "message": "OPSEC violation detected"
                },
                tripwire_triggered=True
            )
    
    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False
    )


def get_security_guardrails():
    """Return list of security guardrails for the system."""
    return [
        classification_guardrail,
        pii_protection_guardrail,
        opsec_guardrail
    ]