# Capability Statement Generator

> Created by @omairionz

A tool that generates opportunity-tailored federal capability statements from structured firm profiles.

---

## Architecture

This tool uses a **decomposed-prompt pipeline**, not a single monolithic call, since different tailoring decisions require different reasoning contexts and produce different structured outputs.

- **Tier 1 — Generic Generation**: Loads a structured firm profile from YAML, validates it with Pydantic, serializes it to JSON, and passes it to Claude with an engineered prompt that produces a complete capability statement in Markdown. Any firm profile in the correct schema generates a clean statement with zero code changes.
- **Tier 2 — Opportunity-Aware Tailoring**: Given a federal opportunity description (Sources Sought, RFP excerpt, SAM.gov listing), runs four specialized Claude calls — each handling one tailoring decision — that produce structured JSON outputs validated by Pydantic invariant checks before being applied to the firm profile:
  - **Past Performance Reordering**: Ranks and features the most opportunity-relevant past contracts.
  - **Capability Reordering**: Surfaces the most aligned capability areas for the opportunity's mission.
  - **Value Proposition Rewrite**: Rewrites the firm's positioning sentence with opportunity-specific language while preserving factual substance.
  - **Differentiator Rewording**: Selectively rewords up to two generic differentiators with opportunity-specific keywords, leaving accomplishment-based claims untouched.
- **Tier 3 — PDF Generation**: Builds a polished, branded, one-page PDF capability statement directly from the `FirmProfile` object using an HTML + CSS template rendered by WeasyPrint. Features per-firm brand color theming, two-column layout with boxed capability cards, adaptive section rendering (sections with no data for a given firm suppress themselves entirely), and a fixed footer.
- **Tier 4 — Streamlit UI + RAG** *(in progress)*: A web interface for non-technical BD directors, plus embedding-based retrieval over larger past performance libraries.

All four tailoring prompts include explicit invariant rules ("do not add IDs not present in the input," "reword at most two differentiators," "never reword factual accomplishments") and rationale fields for auditability. The tailoring pipeline was validated against two structurally different imaginary federal opportunities, producing visibly different outputs from the same firm profile.

## Getting Started

#### Prerequisites

1. Install GTK3 Runtime (required by WeasyPrint on Windows):

   Download and run the installer from the [GTK for Windows Runtime Environment](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases). Accept defaults. Restart your terminal after installation.

   > Mac and Linux users do not need this step.

2. Install dependencies:

```
uv pip install -r requirements.txt
```

#### Configure API Keys

Create a `.env` file at the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

- [Get Anthropic API key](https://platform.claude.com/settings/keys)

> This project uses the **Anthropic API** exclusively for all LLM calls.

#### Adding Firm Data

Firm profiles and past performance libraries are stored as YAML files. Create one for each firm you want to generate statements for:

```
data/
├── firm_profiles/
│   └── your_firm.yaml          # Company identity, capabilities, certifications, NAICS, etc.
├── past_performance/
│   └── your_firm.yaml          # Past contract entries with IDs, agencies, values, tags
└── opportunities/
    └── your_opportunity.txt    # Plain-text opportunity description
```

See the included `itdc.yaml` and `fedscale.yaml` for complete schema examples. Both cover different data profiles — ITDC has sub-services under each capability area; FedScale has capability areas only — demonstrating how the schema and template adapt to different firm structures.

## Running the Project

#### CLI

Run `verify_data.py` from the project root, changing the `FIRM_NAME` and `OPPORTUNITY` constants at the top of the file to target different firms and opportunities:

```
python verify_data.py
```

This will:
- Load and validate the firm profile and past performance library
- Run all four Tier 2 tailoring calls against the specified opportunity
- Generate a tailored Markdown capability statement
- Generate a tailored PDF capability statement
- Save all outputs and tailoring rationale JSON files to `outputs/`

#### Suppress GTK Warnings (Windows)

To suppress harmless GTK startup warnings on Windows, add the following environment variable before running:

```
set G_MESSAGES_DEBUG=none && python verify_data.py
```

Or set `G_MESSAGES_DEBUG=none` permanently in your Windows environment variables.

## Output

Each run produces the following files inside `outputs/`:

```
outputs/
├── {firm}.pdf                            # Tailored PDF capability statement
├── {firm}.md                             # Tailored Markdown capability statement
├── {firm}-past-performance-library.json  # Reordered past performance library
├── {firm}-past-performance-tailoring.json # AI's reordering rationale
├── {firm}-capabilities-tailoring.json   # AI's capability ordering rationale
├── {firm}-differentiators-tailoring.json # AI's rewording decisions and rationale
└── {firm}-positioning-tailoring.json    # AI's value proposition rewrite and rationale
```

The rationale JSON files record which tailoring decisions were made and why — useful for auditing and for understanding what the tool changed versus preserved.

> [!NOTE]
> Only .pdf output is visible for repository navigation ease.

## Project Structure

```
capability-statement-generator/
├── data/
│   ├── firm_profiles/         # Firm profile YAML files (schema source of truth)
│   ├── opportunities/         # Plain-text opportunity descriptions
│   └── past_performance/      # Past performance library YAML files
├── examples/                  # Real-world capability statement examples (reference only)
├── outputs/                   # Generated files land here (gitignored)
├── prompts/
│   ├── tailoring_prompts/     # Four specialized tailoring prompts (one per decision)
│   ├── templates/             # HTML + CSS template for PDF generation
│   └── generate_statement.md  # Tier 1 Markdown generation prompt
├── src/
│   ├── models.py              # Pydantic models for firm profiles and tailoring outputs
│   ├── loaders.py             # YAML → Pydantic validation functions
│   ├── generator.py           # Tier 1: Claude call → Markdown
│   ├── tailor.py              # Tier 2: four-prompt tailoring orchestrator
│   ├── pdf_builder.py         # Tier 3: FirmProfile → HTML → PDF via WeasyPrint
│   ├── retriever.py           # Tier 4: RAG over past performance library (planned)
│   └── app.py                 # Tier 4: Streamlit UI (planned)
├── verify_data.py             # End-to-end test and run script
├── .env                       # API keys (gitignored)
└── requirements.txt
```

## Credits

Built by **[@omairionz](https://github.com/omairionz)**.

Developed with Claude Chat (Anthropic) as a pair programming collaborator.

Architecture decisions, data modeling, prompt engineering, and tailoring design by the author.

> Federal GovCon domain research — capability statement structure, BD workflow, set-aside certifications, NAICS codes, and past performance conventions — conducted independently by the author using real publicly available capability statements from federal small businesses.
