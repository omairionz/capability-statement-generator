"""
Throwaway script to verify the loader + model pipeline works end-to-end.
Run from the project root:    python verify_data.py

Change FIRM_NAME below to test against a different firm profile.
"""

from pathlib import Path

from src.loaders import (
    load_firm_profile,
    load_past_performance,
    load_opportunity,
)
from src.generator import generate_markdown_capability_statement
from src.tailor import tailor
import json

# Single point of control — swap firms by changing this one line.
FIRM_NAME = "itdc"  # {"fedscale", "itdc"}
OPPORTUNITY = "epa-data-modernization-sources-sought"

firm = load_firm_profile(f"data/firm_profiles/{FIRM_NAME}.yaml")
pp_path = Path(f"data/past_performance/pp-{FIRM_NAME}.yaml")
opportunity_text = load_opportunity(f"data/opportunities/{OPPORTUNITY}.txt")

def main() -> None:
    # Load the firm profile
    print("=" * 60)
    print(f"FIRM PROFILE — {FIRM_NAME.upper()}")
    print("=" * 60)
    print(f"Name:        {firm.company_identity.legal_name}")
    print(f"Display:     {firm.company_identity.display_name}")
    print(f"Founded:     {firm.company_identity.founded}")
    print(f"HQ:          {firm.company_identity.headquarters.city}, "
          f"{firm.company_identity.headquarters.state}")
    print(f"Firm type:   {firm.company_identity.firm_type}")
    print()
    print(f"Capability areas ({len(firm.core_capabilities)}):")
    for area in firm.core_capabilities:
        services_count = len(area.services) if area.services else 0
        print(f"  - {area.area} ({services_count} services)")
    print()
    diffs = len(firm.differentiators) if firm.differentiators else 0
    gov = len(firm.clients_served.government) if firm.clients_served.government else 0
    com = len(firm.clients_served.commercial) if firm.clients_served.commercial else 0
    print(f"Differentiators: {diffs}")
    print(f"NAICS codes:     {len(firm.naics_codes.codes)} "
          f"(show_description={firm.naics_codes.show_description})")
    print(f"Contacts:        {len(firm.contacts)}")
    print(f"Gov clients:     {gov}")
    print(f"Commercial:      {com}")
    print(f"Primary certs:   {len(firm.certifications.primary)}")
    print(f"Listed certs:    {len(firm.certifications.list_based)}")
    print(f"Partners:        {len(firm.partners)}")
    print(f"Vehicles:        {len(firm.contract_vehicles)}")

    pp_library = load_past_performance(pp_path)
    print()
    print("=" * 60)
    print("PAST PERFORMANCE")
    print("=" * 60)
    print(f"Total entries: {len(pp_library.past_performance)}")
    for entry in pp_library.past_performance:
        value_str = f"${entry.contract_value.amount:,}"
        print(f"  [{entry.id}] {entry.title} — {entry.role} — {value_str}")

    # Load the opportunity
    print()
    print("=" * 60)
    print("OPPORTUNITY")
    print("=" * 60)
    print(f"Length: {len(opportunity_text)} characters")
    print(f"Preview: {opportunity_text[:200]}...")

    # Generate the capability statement
    print()
    print("=" * 60)
    print(f"GENERATING {FIRM_NAME.upper()} CAPABILITY STATEMENT")
    print("=" * 60)
    markdown = generate_markdown_capability_statement(firm)
    print(markdown)

    output_path_md = Path(f"outputs/{FIRM_NAME}.md")
    output_path_md.parent.mkdir(parents=True, exist_ok=True)
    output_path_md.write_text(markdown, encoding="utf-8")
    print()
    print(f"Saved to: {output_path_md}")

    pp_library, pp_tailored_model, firm_profile, cc_tailored_model= tailor(firm, pp_library, opportunity_text) # Returns tailored PastPerformanceLibrary and PastPerformanceTailoring

    # Tailoring Past performance
    print()
    print("=" * 60)
    print(f"GENERATING TAILORED PAST PERFORMANCE")
    print("=" * 60)
    for entry in pp_library.past_performance:
        tag = "⭐ FEATURED" if entry.id in pp_tailored_model.featured_ids else ""
        print(f"{tag} - {entry.id} - {entry.title}")

    output_path_library = Path(f"outputs/{FIRM_NAME}-past-performance-library.json")
    output_path_library.parent.mkdir(parents=True, exist_ok=True)
    output_path_library.write_text(json.dumps(pp_library.model_dump(), indent=2), encoding="utf-8")

    output_path_pp_tailoring = Path(f"outputs/{FIRM_NAME}-past-performance-tailoring.json")
    output_path_pp_tailoring.parent.mkdir(parents=True, exist_ok=True)
    output_path_pp_tailoring.write_text(json.dumps(pp_tailored_model.model_dump(), indent=2), encoding="utf-8")

    # Tailor core capabilities
    print()
    print("=" * 60)
    print(f"GENERATING TAILORED CORE CAPABILITIES")
    print("=" * 60)
    for entry in firm_profile.core_capabilities:
        print(f"{entry.area}")
        for service in entry.services:
            print(f"  - {service}")
    
    output_path_firm_capabilities = Path(f"outputs/{FIRM_NAME}-firm-capabilities.json")
    output_path_firm_capabilities.parent.mkdir(parents=True, exist_ok=True)
    output_path_firm_capabilities.write_text(json.dumps([c.model_dump() for c in firm_profile.core_capabilities], indent=2), encoding="utf-8")

    output_path_cc_tailoring = Path(f"outputs/{FIRM_NAME}-capabilities-tailoring.json")
    output_path_cc_tailoring.parent.mkdir(parents=True, exist_ok=True)
    output_path_cc_tailoring.write_text(json.dumps(cc_tailored_model.model_dump(), indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()