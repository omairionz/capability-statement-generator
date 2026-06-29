# pdf_builder.py

import os
os.environ["G_MESSAGES_DEBUG"] = "none"
from pathlib import Path
from weasyprint import HTML
from src.models import FirmProfile

TEMPLATE_PATH = Path("prompts/templates/capability_statement.html")
OUTPUT_PATH = Path("outputs")

def build_pdf(firm: FirmProfile, output_path: Path, save_preview: bool = True) -> None:
    html = _render_html(firm)
    if save_preview:
        preview_path = OUTPUT_PATH / "preview.html"
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview_path.write_text(html, encoding="utf-8")
        print(f"Preview saved to: {preview_path}")
    HTML(string=html).write_pdf(output_path)
    print(f"PDF saved to: {output_path}")

def _render_html(firm: FirmProfile):
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    executive_summary_html = _render_executive_summary(firm)
    capabilities_html = _render_capabilities(firm)
    differentiators_html = _render_differentiators(firm)
    certifications_html = _render_certifications(firm)
    naics_html = _render_naics(firm)
    clients_html = _render_clients(firm)
    partners_html = _render_partners(firm)
    vehicles_html = _render_vehicles(firm)
    header_contact_html = _render_header_contact(firm)
    id_codes_html = _render_id_codes(firm)

    hq = firm.company_identity.headquarters
    address = f"{hq.street}, {hq.city}, {hq.state} {hq.zip}"

    company_info = (
        f'<div class="identifiers">'
        f'<div><span class="label">Location:</span> {address}</div>'
        f'<div><span class="label">Email:</span> {firm.company_identity.general_email or ""}</div>'
        f'<div><span class="label">Phone:</span> {firm.company_identity.general_phone or ""}</div>'
        f'{id_codes_html}'
        f'</div>'
    )

    display = firm.company_identity.display_name
    left_col = (
        _section("Executive Summary", executive_summary_html)
        + _section("Core Capabilities", capabilities_html)
        + _section(f"Why {display}?", differentiators_html)
    )
    right_col = (
        _section("Company Information", company_info, accent=True)
        + _section("Certifications", certifications_html, accent=True)
        + _section("NAICS Codes", naics_html, accent=True)
        + _section("Contract Vehicles", vehicles_html, accent=True)
        + _section("Partners", partners_html, accent=True)
    )
    clients_title = "Clients Served"
    if firm.clients_served.partial_list:
        clients_title += " (Partial List)"
    clients_block = _section(clients_title, clients_html)

    html = template
    html = html.replace("{{ display_name }}", display)
    html = html.replace("{{ tagline }}", firm.company_identity.tagline or "")
    html = html.replace("{{ primary_color }}", firm.brand_assets.primary_color)
    html = html.replace("{{ accent_color }}", firm.brand_assets.accent_color)
    html = html.replace("{{ header_contact }}", header_contact_html)
    html = html.replace("{{ left_col }}", left_col)
    html = html.replace("{{ right_col }}", right_col)
    html = html.replace("{{ clients_block }}", clients_block)
    html = html.replace("{{ address }}", address)
    html = html.replace("{{ email }}", firm.company_identity.general_email or "")
    html = html.replace("{{ phone }}", firm.company_identity.general_phone or "")

    return html

def _render_executive_summary(firm: FirmProfile) -> str:
    es = firm.executive_summary
    parts = []
    first_para = " ".join(filter(None, [
        f"{firm.company_identity.legal_name} is {es.who_they_are}," if es.who_they_are else "",
        es.mission_commitment or "",
        es.positioning_statement or "",
        es.value_proposition or "",
    ]))
    if first_para.strip():
        parts.append(f"<p>{first_para}</p>")
    second_para = " ".join(filter(None, [
        es.voice_passion or "",
        es.closing_line or "",
    ]))
    if second_para.strip():
        parts.append(f"<p>{second_para}</p>")
    for para in es.additional_paragraphs:
        parts.append(f"<p>{para}</p>")
    return "".join(parts)

def _render_capabilities(firm: FirmProfile) -> str:
    # If NO capability area has services (e.g. FedScale), render a simple bulleted list.
    any_services = any(cap.services for cap in firm.core_capabilities)
    if not any_services:
        items = "".join(f"<li>{cap.area}</li>" for cap in firm.core_capabilities)
        return f"<ul class='cap-bullets'>{items}</ul>"

    # Otherwise, render boxed cards two-per-row.
    has_any_services = any(cap.services for cap in firm.core_capabilities)
    cells = []
    for cap in firm.core_capabilities:
        if has_any_services:
            inner = f"<div class='capability-area'>{cap.area}</div>"
            if cap.services:
                inner += "<ul>"
                for service in cap.services:
                    inner += f"<li>{service}</li>"
                inner += "</ul>"
            cells.append(f"<div class='cap-card'>{inner}</div>")
        else:
            # No firm has services -> render areas as a simple bulleted card
            cells.append(f"<div class='cap-card cap-card-flat'><div class='capability-area'>&bull; {cap.area}</div></div>")

    html = "<div class='cap-grid'>"
    for i in range(0, len(cells), 2):
        html += "<div class='cap-row'>"
        html += f"<div class='cap-cell'>{cells[i]}</div>"
        if i + 1 < len(cells):
            html += f"<div class='cap-cell'>{cells[i+1]}</div>"
        else:
            html += "<div class='cap-cell'></div>"
        html += "</div>"
    html += "</div>"
    return html

def _render_differentiators(firm: FirmProfile) -> str:
    if not firm.differentiators:
        return ""
    html = "<ul>"
    for d in firm.differentiators:
        html += f"<li>{d}</li>"
    html += "</ul>"
    return html

def _render_certifications(firm: FirmProfile) -> str:
    html = "<ul>"
    for cert in firm.certifications.primary:
        expiry = f" — expires {cert.expires}" if cert.expires else ""
        html += f"<li><strong>{cert.name}</strong>{expiry}</li>"
    for cert in firm.certifications.list_based:
        html += f"<li>{cert.name}</li>"
        if cert.supplement:
            html += "<ul>"
            for s in cert.supplement:
                html += f"<li>{s}</li>"
            html += "</ul>"
    html += "</ul>"
    return html

def _render_naics(firm: FirmProfile) -> str:
    if not firm.naics_codes.codes:
        return ""
    regular = [c for c in firm.naics_codes.codes if not c.wildcard]
    wildcards = [c for c in firm.naics_codes.codes if c.wildcard]
    ordered = regular + wildcards

    # When descriptions are hidden, render as a compact comma-separated block
    # instead of a tall single-column list.
    if not firm.naics_codes.show_description:
        codes = ", ".join(c.code for c in ordered)
        return f'<div class="naics-inline">{codes}</div>'

    html = "<ul>"
    for code in ordered:
        html += f"<li>{code.code}: {code.description}</li>"
    html += "</ul>"
    return html

def _client_list_html(clients: list) -> str:
    # If many clients, split into two side-by-side sub-columns to save vertical space.
    if len(clients) > 8:
        mid = (len(clients) + 1) // 2
        left = "".join(f"<li>{c}</li>" for c in clients[:mid])
        right = "".join(f"<li>{c}</li>" for c in clients[mid:])
        return (
            '<div class="client-split">'
            f'<ul>{left}</ul><ul>{right}</ul>'
            '</div>'
        )
    return "<ul>" + "".join(f"<li>{c}</li>" for c in clients) + "</ul>"

def _render_clients(firm: FirmProfile) -> str:
    cs = firm.clients_served
    html = ""
    # Both narrative lines together, above the lists.
    narrative = " ".join(filter(None, [cs.intro_text or "", cs.validation_text or ""]))
    if narrative.strip():
        html += f"<p class='clients-narrative'><em>{narrative}</em></p>"
    html += '<div class="clients-columns">'
    if cs.government:
        html += f'<div><div class="client-head">U.S. Government</div><div class="client-box">{_client_list_html(cs.government)}</div></div>'
    if cs.commercial:
        html += f'<div><div class="client-head">Commercial</div><div class="client-box">{_client_list_html(cs.commercial)}</div></div>'
    html += "</div>"
    return html

def _render_partners(firm: FirmProfile) -> str:
    if not firm.partners:
        return ""
    html = "<ul>"
    for partner in firm.partners:
        if partner.relationship:
            html += f"<li>{partner.name} — {partner.relationship}</li>"
        else:
            html += f"<li>{partner.name}</li>"
    html += "</ul>"
    return html

def _render_vehicles(firm: FirmProfile) -> str:
    if not firm.contract_vehicles:
        return ""
    html = "<ul>"
    for v in firm.contract_vehicles:
        line = v.name
        if v.identifier:
            line += f" — {v.identifier}"
        if v.note:
            line += f" ({v.note})"
        html += f"<li>{line}</li>"
    html += "</ul>"
    return html

def _section(title: str, content: str, accent: bool = False) -> str:
    """Wrap content in a section with a header. Returns empty string if content is empty,
    which suppresses the header for sections a firm doesn't have."""
    if not content or not content.strip():
        return ""
    cls = "section-header accent" if accent else "section-header"
    return f'<div class="{cls}">{title}</div>{content}'


def _render_header_contact(firm: FirmProfile) -> str:
    if not firm.contacts:
        return ""
    html = ""
    for contact in firm.contacts:
        html += f'<div class="hc-name">{contact.name}</div>'
        html += f'<div class="hc-title">{contact.title}</div>'
        if contact.phone:
            html += f'<div class="hc-line">{contact.phone}</div>'
        if contact.email:
            html += f'<div class="hc-line">{contact.email}</div>'
    return html

def _render_id_codes(firm: FirmProfile) -> str:
    ids = firm.identifiers
    html = ""
    if ids.cage:
        html += f'<div><span class="label">CAGE:</span> {ids.cage}</div>'
    if ids.duns:
        html += f'<div><span class="label">DUNS:</span> {ids.duns}</div>'
    if ids.uei:
        html += f'<div><span class="label">UEI:</span> {ids.uei}</div>'
    if ids.dnb_open_ratings:
        html += f'<div><span class="label">D&B Rating:</span> {ids.dnb_open_ratings}</div>'
    return html




