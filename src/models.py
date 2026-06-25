"""
Pydantic models for the capability statement generator.

Each class describes the shape of a section of input data. Loading a YAML
file via these models gives you validated Python objects with autocomplete
and clear errors if anything is missing or malformed.

There are two top-level models:
    FirmProfile          -> matches data/firm_profiles/*.yaml
    PastPerformanceLibrary -> matches data/past_performance/*.yaml
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

# ***** FIRM PROFILE *****

class Headquarters(BaseModel):
    """Address of the firm."""
    street: str
    city: str
    state: str
    zip: str


class CompanyIdentity(BaseModel):
    """Basic firm information. With exception of CAGE, DUNS, and UEI numbers."""
    legal_name: str
    display_name: str
    tagline: Optional[str] = None
    founded: Optional[int] = None  # not always on the cap statement (FedScale)
    headquarters: Headquarters
    general_email: str
    general_phone: str
    fax: Optional[str] = None
    website: Optional[str] = None
    firm_type: str


class ExecutiveSummary(BaseModel):
    """
    Narrative components of the cap statement opening.

    All fields are optional because firms vary in how they structure their
    summary. Use the named fields for the common beats; use
    additional_paragraphs for content that doesn't fit any named slot.

    Tier 2 tailoring targets the named fields specifically. Content placed
    in additional_paragraphs is preserved verbatim and not rewritten.
    """
    who_they_are: Optional[str] = None
    mission_commitment: Optional[str] = None
    positioning_statement: Optional[str] = None  # renamed from track_record_framing
    value_proposition: Optional[str] = None
    voice_passion: Optional[str] = None
    closing_line: Optional[str] = None
    additional_paragraphs: list[str] = Field(default_factory=list)


class CoreCapabilities(BaseModel):
    """One capability area, optionally with a list of sub-services. area: str -- services: Optional[list[str]] = None"""
    area: str
    services: Optional[list[str]] = None  # FedScale lists areas without sub-services

class PrimaryCertification(BaseModel):
    """
    Major prominent certification (e.g. SBA 8(a), HUBZone, EDWOSB).
    Renamed from 'icon_based' since not all entries in this category
    necessarily have an icon — EDWOSB on FedScale's statement has none.
    """
    name: str
    expires: Optional[str] = None


class ListedCertification(BaseModel):
    """
    Smaller technical/professional certification, possibly with
    supplementary detail (versions, levels, appraisals).
    """
    name: str
    supplement: Optional[list[str]] = None


class Certifications(BaseModel):
    primary: list[PrimaryCertification] = Field(default_factory=list)
    list_based: list[ListedCertification] = Field(default_factory=list)


class NAICSCode(BaseModel):
    """A NAICS code entry. wildcard=True for family codes like 236xxx."""
    code: str
    description: str
    wildcard: bool = False


class NAICSCodes(BaseModel):
    """
    The full NAICS code section. show_description controls whether the
    generator renders descriptions alongside codes — some firms (FedScale)
    only display the codes themselves.
    """
    show_description: bool = True
    codes: list[NAICSCode] = Field(default_factory=list)


class Identifiers(BaseModel):
    duns: Optional[str] = None
    cage: Optional[str] = None
    uei: Optional[str] = None
    dnb_open_ratings: Optional[str] = None


class Contact(BaseModel):
    name: str
    title: str
    phone: Optional[str] = None
    email: Optional[str] = None


class ClientsServed(BaseModel):
    """
    Clients grouped by sector.

    intro_text and validation_text capture narrative content that
    appears physically near the client list on the source statement
    (e.g. FedScale's "team has proven experience..." paragraph and
    "earned a strong client satisfaction rating" line).
    """
    partial_list: bool = False
    intro_text: Optional[str] = None
    validation_text: Optional[str] = None
    government: Optional[list[str]] = None
    commercial: Optional[list[str]] = None


class Partner(BaseModel):
    name: str
    relationship: Optional[str] = None


class ContractVehicle(BaseModel):
    name: str
    identifier: Optional[str] = None
    note: Optional[str] = None


class TechnicalExpertise(BaseModel):
    processes: Optional[list[str]] = None
    devops_and_delivery: Optional[list[str]] = None
    cloud_and_development: Optional[list[str]] = None
    data_platforms: Optional[list[str]] = None


class BrandAssets(BaseModel):
    logo_path: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None


class FirmProfile(BaseModel):
    """
    The full firm profile. Top-level model loaded from
    data/firm_profiles/*.yaml.
    """
    company_identity: CompanyIdentity
    executive_summary: ExecutiveSummary
    core_capabilities: list[CoreCapabilities] = Field(default_factory=list)
    differentiators: Optional[list[str]] = None
    certifications: Certifications
    naics_codes: NAICSCodes
    identifiers: Identifiers
    contacts: list[Contact] = Field(default_factory=list)
    clients_served: ClientsServed
    partners: list[Partner] = Field(default_factory=list)
    contract_vehicles: list[ContractVehicle] = Field(default_factory=list)
    technical_expertise: TechnicalExpertise = Field(default_factory=TechnicalExpertise)
    brand_assets: BrandAssets = Field(default_factory=BrandAssets)


# ***** PAST PERFORMANCE LIBRARY *****

class ContractValue(BaseModel):
    amount: int
    currency: str = "USD"
    approximate: bool = False
    represents: str = "total contract"


class PeriodOfPerformance(BaseModel):
    start_year: int
    end_year: Optional[int] = None
    ongoing: bool = False


class PastPerformanceEntry(BaseModel):
    id: str
    title: str
    client: str
    sector: Literal["government", "commercial"]
    role: Literal["prime", "subcontractor"]
    prime_contractor: Optional[str] = None
    contract_value: ContractValue
    period_of_performance: PeriodOfPerformance
    description: str
    tags: list[str] = Field(default_factory=list)

class PastPerformanceLibrary(BaseModel):
    past_performance: list[PastPerformanceEntry]

# ***** TAILORING PROFILE *****

class PastPerformanceTailoring(BaseModel):
    featured_ids: list[str] = Field(default_factory=list)
    remaining_ids: list[str] = Field(default_factory=list)
    rationale: str

class CapabilityTailoring(BaseModel):
    ordered_capability_areas: list[str] = Field(default_factory=list)
    rationale: str

class DifferentiatorDecision(BaseModel):
    original: str
    rewritten: str
    was_changed: bool = False # if False, origional = rewritten
    rationale: Optional[str] = None

class DifferentiatorsTailoring(BaseModel):
    decisions: list[DifferentiatorDecision] = Field(default_factory=list)
    overall_rationale: str

class PositioningTailoring(BaseModel):
    tailored_value_proposition: str
    tailored_closing_line: str
    rationale: str