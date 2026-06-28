# tailor.py

from dotenv import load_dotenv
load_dotenv() # Loaded first

import re
import os # OpenRouter capability
import json
from pathlib import Path
#from langchain_openai import ChatOpenAI # OpenRouter capability
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from src.models import FirmProfile, PastPerformanceLibrary, PastPerformanceTailoring, CapabilityTailoring, DifferentiatorsTailoring, PositioningTailoring

# OPEN ROUTER
# llm = ChatOpenAI(
#     model="anthropic/claude-sonnet-4-6",
#     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
#     openai_api_base="https://openrouter.ai/api/v1",
#     max_tokens=2000
# )

llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=2000)

PAST_PERFORMANCE_PROMPT = Path("prompts/tailoring_prompts/tailor_past_performance.md")
CAPABILITIES_PROMPT = Path("prompts/tailoring_prompts/tailor_capabilities.md")
DIFFERENTIATORS_PROMPT = Path("prompts/tailoring_prompts/tailor_differentiators.md")
POSITIONING_PROMPT = Path("prompts/tailoring_prompts/tailor_positioning.md") # value_proposition of Executive Summary

def _call_tailoring_prompt(system_prompt_path: Path, user_content: str, pydantic_model):
    """Runs LLM calls and JSON parsing. Returns Tailoring Objects."""
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ])

    try:
        parsed_dict = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if not match:
            raise ValueError(
                f"Claude did not return valid JSON. Raw response:\n\n{response.content}"
            )
        print("⚠️ Warning! JSON parse failed; recovered via regex fallback")
        parsed_dict = json.loads(match.group())
    
    return pydantic_model.model_validate(parsed_dict)

def tailor(firm: FirmProfile, library: PastPerformanceLibrary, opportunity_text: str):
    """Master tailoring method. Returns FirmProfile, PastPerformanceLibrary, 
    PP Tailoring, Capabilities Tailoring, Differentiators Tailoring, 
    & Positioning Tailoring Objects."""

    # ====== 1. Past Performance (pp) ===========================================
    pp_user_content = f"OPPORTUNITY TEXT:\n\n{opportunity_text}\n\nPAST PERFORMANCE LIBRARY:\n\n{library.model_dump_json(indent=2)}"
    # Validate JSON shape with Pydantic Model
    pp_tailoring = _call_tailoring_prompt(PAST_PERFORMANCE_PROMPT, pp_user_content, PastPerformanceTailoring)
    # Validate Tailoring Library with actual Past Performance Library and against invariants
    _validate_pp_tailoring_invariants(pp_tailoring, library)
    # Applied ordering
    pp_library_final = _apply_past_performance_ordering(pp_tailoring, library)

    # ====== 2. Core Capabilities (cc) ==========================================
    cc_user_content = f"OPPORTUNITY TEXT:\n\n{opportunity_text}\n\nCAPABILITIES:\n\n{json.dumps([c.model_dump() for c in firm.core_capabilities], indent=2)}"
    cc_tailoring = _call_tailoring_prompt(CAPABILITIES_PROMPT, cc_user_content, CapabilityTailoring)
    _validate_capabilities_tailoring_invariants(cc_tailoring, firm)
    tailored_firm_profile = _apply_capabilities_ordering(cc_tailoring, firm)

    # ====== 3. Differentiators (d) =============================================
    if tailored_firm_profile.differentiators:
        d_user_content = f"OPPORTUNITY TEXT:\n\n{opportunity_text}\n\nDIFFERENTIATORS:\n\n{json.dumps(tailored_firm_profile.differentiators, indent=2)}"   
        d_tailoring = _call_tailoring_prompt(DIFFERENTIATORS_PROMPT, d_user_content, DifferentiatorsTailoring)
        _validate_differentiators_tailoring_invariants(d_tailoring, tailored_firm_profile)
        tailored_firm_profile = _apply_differentiators_rewording(d_tailoring, tailored_firm_profile)
    else:
        d_tailoring = None
        
    # ====== 4. Positioning (pos) ===============================================
    pos_user_content = f"OPPORTUNITY TEXT:\n\n{opportunity_text}\n\nPOSITIONING:\n\n{json.dumps(tailored_firm_profile.executive_summary.value_proposition, indent=2)}"
    pos_tailoring = _call_tailoring_prompt(POSITIONING_PROMPT, pos_user_content, PositioningTailoring)
    _validate_positioning_tailoring_invariants(pos_tailoring, tailored_firm_profile)
    tailored_firm_profile = _apply_positioning_rewording(pos_tailoring, tailored_firm_profile)

    # ++++++++ RETURN STATEMENT ++++++++++
    return tailored_firm_profile, pp_library_final, pp_tailoring, cc_tailoring, d_tailoring, pos_tailoring

#=====================================================================================================
#========================================== HELPER METHODS ===========================================
#=====================================================================================================

# _____1. Past Performance _____________________________________________

def _validate_pp_tailoring_invariants(tailoring: PastPerformanceTailoring, library: PastPerformanceLibrary) -> None:
    """Past Performance ID invariants validation"""
    library_ids = {entry.id for entry in library.past_performance}
    featured_ids = tailoring.featured_ids
    remaining_ids = tailoring.remaining_ids

    # Invariant 1: Each ID must be in the library.
    output_ids = set(featured_ids) | set(remaining_ids)
    invented_ids = output_ids - library_ids
    if invented_ids:
        raise ValueError(
            f"Tailoring returned IDs not present in the library: {sorted(invented_ids)}. "
            f"Library contains: {sorted(library_ids)}"
        )
    
    # Invariant 2: No duplicates between featured_ids and remaining_ids
    duplicates = set(featured_ids) & set(remaining_ids)
    if duplicates:
        raise ValueError(
            f"Tailoring placed the same ID(s) in both featured and remaining: "
            f"{sorted(duplicates)}"
        )

    # Invariant 3: every library ID must appear in exactly one list
    missing_ids = library_ids - output_ids
    if missing_ids:
        raise ValueError(
            f"Tailoring omitted library IDs that should appear in one of the lists: "
            f"{sorted(missing_ids)}"
        )

    # Also catch within-list duplicates, which would otherwise be hidden by sets
    if len(featured_ids) != len(set(featured_ids)):
        raise ValueError(
            f"featured_ids contains duplicates: {featured_ids}"
        )
    if len(remaining_ids) != len(set(remaining_ids)):
        raise ValueError(
            f"remaining_ids contains duplicates: {remaining_ids}"
        )

def _apply_past_performance_ordering(tailoring: PastPerformanceTailoring, library: PastPerformanceLibrary):
    """Does the reordering of past performances."""
    reordered = []

    for featured in tailoring.featured_ids:
        for entry in library.past_performance:
            if entry.id == featured:
                reordered.append(entry)

    for remaining in tailoring.remaining_ids:
        for entry in library.past_performance:
            if entry.id == remaining:
                reordered.append(entry)

    return PastPerformanceLibrary(past_performance=reordered)

# _____ 2. Core Capabilities ____________________________________________

def _validate_capabilities_tailoring_invariants(tailoring: CapabilityTailoring, firm: FirmProfile):
    """Core capabilities variants check."""
    capability_entries = {entry.area for entry in firm.core_capabilities}
    ordered_capability_areas = tailoring.ordered_capability_areas

    # Invariant 1. Each ordered_capability_areas must be inside firm.core_capabilities.area.
    output_ids = set(ordered_capability_areas)
    invented_ids = output_ids - capability_entries
    if invented_ids:
        raise ValueError(
            f"Tailoring returned capability areas not present in the library: {sorted(invented_ids)}. "
            f"Original capability entries contains: {sorted(capability_entries)}"
        )
    
    # Invariant 2. Each ordered_capability_areas must appear exactly once.
    if len(ordered_capability_areas) != len(set(ordered_capability_areas)):
        raise ValueError(
            f"ordered_capability_areas contains duplicates: {ordered_capability_areas}"
        )
    
    # Invariant 3: every firm capability must appear in the output
    missing_areas = capability_entries - output_ids
    if missing_areas:
        raise ValueError(
            f"Tailoring omitted capability areas that must appear in output: {sorted(missing_areas)}"
        )
    
def _apply_capabilities_ordering(tailoring: CapabilityTailoring, firm: FirmProfile):
    """Reorders core capabilities. Returns FirmProfile."""
    reordered = []
    for tailored_entry in tailoring.ordered_capability_areas:
        for capability in firm.core_capabilities:
            if tailored_entry == capability.area:
                reordered.append(capability)
    return firm.model_copy(update={"core_capabilities": reordered}, deep=True)

# _____ 3. Differentiators ____________________________________________

def _validate_differentiators_tailoring_invariants(tailoring: DifferentiatorsTailoring, firm: FirmProfile):
    differentiators = set(firm.differentiators) if firm.differentiators else set()
    original_differentiators = {entry.original for entry in tailoring.decisions}

    # Invariant 1: every differentiator must match a tailoring.original
    missing = differentiators - original_differentiators
    if missing:
        raise ValueError(
            f"Decisions are missing entries for these differentiators: {sorted(missing)}"
        )
    
    # Invariant 2: Check count
    if len(firm.differentiators) != len(tailoring.decisions):
        raise ValueError(
            f"Expected {len(firm.differentiators)} objects. Got {len(tailoring.decisions)} instead."
        )    
    
    # Invariant 3: At most 2 differentiators were rewritten
    count = 0
    for entry in tailoring.decisions:
        if entry.was_changed:
            count += 1
    if count > 2:
        raise ValueError(
            f"Expected 2 changes. Instead got {count} changes."
        )
    
    # Invariant 4: Check for duplicates
    original_list = [entry.original for entry in tailoring.decisions]
    if len(original_list) != len(set(original_list)):
        raise ValueError(
            f"Decisions contain duplicate originals: {original_list}"
        )

    # Invariant 5: was_changed=False means original == rewritten
    for decision in tailoring.decisions:
        if not decision.was_changed and decision.original != decision.rewritten:
            raise ValueError(
                f"Decision marked was_changed=False but text differs.\n"
                f"  original:  '{decision.original}'\n"
                f"  rewritten: '{decision.rewritten}'"
            )

def _apply_differentiators_rewording(tailoring: DifferentiatorsTailoring, firm: FirmProfile):
    """Rewords differentiators. Returns FirmProfile."""
    reworded = []
    for tailored_entry in tailoring.decisions:
        reworded.append(tailored_entry.rewritten)
    return firm.model_copy(update={"differentiators": reworded}, deep=True)

# _____ 4. Positioning ____________________________________________

def _validate_positioning_tailoring_invariants(tailoring: PositioningTailoring, firm: FirmProfile):
    print("TODO")

def _apply_positioning_rewording(tailoring: PositioningTailoring, firm: FirmProfile):
    print("TODO")