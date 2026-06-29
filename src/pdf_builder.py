# pdf_builder.py

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
    contacts_html = _render_contacts(firm)
    id_codes_html = _render_id_codes(firm)

    hq = firm.company_identity.headquarters
    address = f"{hq.street}, {hq.city}, {hq.state} {hq.zip}"

    html = template
    html = html.replace("{{ address }}", address)
    html = html.replace("{{ email }}", firm.company_identity.general_email or "")
    html = html.replace("{{ phone }}", firm.company_identity.general_phone or "")
    html = html.replace("{{ founded }}", str(firm.company_identity.founded) if firm.company_identity.founded else "")

    html = html.replace("{{ firm_type }}", firm.company_identity.firm_type or "")
    html = html.replace("{{ legal_name }}", firm.company_identity.legal_name or "")
    html = html.replace("{{ display_name }}", firm.company_identity.display_name)
    html = html.replace("{{ tagline }}", firm.company_identity.tagline or "")
    html = html.replace("{{ primary_color }}", firm.brand_assets.primary_color)
    html = html.replace("{{ accent_color }}", firm.brand_assets.accent_color)
    html = html.replace("{{ id_codes }}", id_codes_html)

    html = html.replace("{{ executive_summary }}", executive_summary_html)
    html = html.replace("{{ capabilities }}", capabilities_html)
    html = html.replace("{{ differentiators }}", differentiators_html)
    html = html.replace("{{ certifications }}", certifications_html)
    html = html.replace("{{ naics }}", naics_html)
    html = html.replace("{{ clients }}", clients_html)
    html = html.replace("{{ partners }}", partners_html)
    html = html.replace("{{ vehicles }}", vehicles_html)
    html = html.replace("{{ contacts }}", contacts_html)

    return html

# ==================================================================
# ====================== SUB HELPER METHODS ========================
# ==================================================================

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

def _render_executive_summary(firm: FirmProfile) -> str:
    es = firm.executive_summary
    parts = []
    
    # First paragraph: identity fields
    first_para = " ".join(filter(None, [
        f"{firm.company_identity.display_name} is {es.who_they_are}," if es.who_they_are else "",
        es.mission_commitment or "",
        es.positioning_statement or "",
        es.value_proposition or "",
    ]))
    if first_para.strip():
        parts.append(f"<p>{first_para}</p>")
    
    # Second paragraph: passion + closing
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
    html = ""
    for cap in firm.core_capabilities:
        html += f"<div class='capability-area'>{cap.area}</div>"
        if cap.services:
            html += "<ul>"
            for service in cap.services:
                html += f"<li>{service}</li>"
            html += "</ul>"
    return html

def _render_differentiators(firm: FirmProfile) -> str:
    if not firm.differentiators:
        return ""  # FedScale — nothing to render
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
    html = "<ul>"
    regular = [c for c in firm.naics_codes.codes if not c.wildcard]
    wildcards = [c for c in firm.naics_codes.codes if c.wildcard]
    for code in regular + wildcards:
        if firm.naics_codes.show_description:
            html += f"<li>{code.code}: {code.description}</li>"
        else:
            html += f"<li>{code.code}</li>"
    html += "</ul>"
    return html

def _render_clients(firm: FirmProfile) -> str:
    cs = firm.clients_served
    html = ""
    partial = " <em>(partial list)</em>" if cs.partial_list else ""
    if cs.intro_text:
        html += f"<p><em>{cs.intro_text}</em></p>"
    if cs.government:
        html += f"<h4>U.S. Government{partial}</h4><ul>"
        for client in cs.government:
            html += f"<li>{client}</li>"
        html += "</ul>"
    if cs.commercial:
        html += "<h4>Commercial</h4><ul>"
        for client in cs.commercial:
            html += f"<li>{client}</li>"
        html += "</ul>"
    if cs.validation_text:
        html += f"<p><em>{cs.validation_text}</em></p>"
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

def _render_contacts(firm: FirmProfile) -> str:
    if not firm.contacts:
        return ""
    html = "<ul>"
    for contact in firm.contacts:
        html += f"<li><strong>{contact.name}</strong> — {contact.title}"
        if contact.phone:
            html += f"<br>{contact.phone}"
        if contact.email:
            html += f"<br>{contact.email}"
        html += "</li>"
    html += "</ul>"
    return html