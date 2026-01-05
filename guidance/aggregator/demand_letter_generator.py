#!/usr/bin/env python3
"""
Demand Letter Generator for NY Personal Injury Cases

Generates professional demand letters from case summary JSON data.
Supports configurable law firm branding and auto-calculated demand amounts.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class InjurySeverity(Enum):
    """Injury severity classifications for demand calculation."""
    PERMANENT = "permanent"
    DISC_HERNIATION = "disc_herniation"
    RADICULOPATHY = "radiculopathy"
    DISC_BULGING = "disc_bulging"
    SOFT_TISSUE = "soft_tissue"


# Multiplier ranges by injury severity
SEVERITY_MULTIPLIERS = {
    InjurySeverity.PERMANENT: (3.0, 5.0),
    InjurySeverity.DISC_HERNIATION: (2.5, 4.0),
    InjurySeverity.RADICULOPATHY: (2.5, 3.5),
    InjurySeverity.DISC_BULGING: (2.0, 3.0),
    InjurySeverity.SOFT_TISSUE: (1.5, 2.5),
}


class DemandLetterGenerator:
    """
    Generates demand letters for NY Personal Injury cases.

    Input: case_summary.json (output from JSONResultsAggregator)
    Output: Markdown and HTML demand letters
    """

    # Default law firm config when none provided
    DEFAULT_CONFIG = {
        "firm_name": "[LAW FIRM NAME]",
        "firm_address": {
            "street": "[Street Address]",
            "city": "[City]",
            "state": "NY",
            "zip": "[ZIP]"
        },
        "firm_phone": "[Phone]",
        "firm_fax": "[Fax]",
        "firm_email": "[Email]",
        "attorney": {
            "name": "[Attorney Name], Esq.",
            "bar_number": "[Bar Number]",
            "email": "[Attorney Email]",
            "direct_phone": "[Direct Phone]"
        },
        "defaults": {
            "response_deadline_days": 30,
            "certified_mail": True,
            "cc_client": True
        }
    }

    def __init__(self, case_summary_path: str, config_path: Optional[str] = None):
        """
        Initialize the demand letter generator.

        Args:
            case_summary_path: Path to case_summary.json file
            config_path: Optional path to law_firm_config.json
        """
        self.case_summary_path = Path(case_summary_path)
        self.config_path = Path(config_path) if config_path else None
        self.case_data: Dict = {}
        self.firm_config: Dict = {}
        self.demand_calculation: Dict = {}

    def load_case_summary(self) -> None:
        """Load case summary JSON data."""
        if not self.case_summary_path.exists():
            raise FileNotFoundError(f"Case summary not found: {self.case_summary_path}")

        with open(self.case_summary_path, 'r') as f:
            self.case_data = json.load(f)

    def load_firm_config(self) -> None:
        """Load law firm configuration or use defaults."""
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.firm_config = json.load(f)
        else:
            self.firm_config = self.DEFAULT_CONFIG.copy()

    def classify_injury_severity(self) -> InjurySeverity:
        """
        Classify injury severity based on case data.

        Returns highest applicable severity level.
        """
        injuries = self.case_data.get('injuries', {})
        imaging = injuries.get('imaging_findings', [])
        diagnoses = injuries.get('diagnoses', [])
        prognosis = injuries.get('prognosis', '')
        ny_serious = self.case_data.get('ny_serious_injury_analysis', {})
        threshold_categories = ny_serious.get('threshold_categories', [])

        # Combine all text for keyword searching
        imaging_text = ' '.join(imaging).lower() if isinstance(imaging, list) else str(imaging).lower()
        diagnoses_text = ' '.join(diagnoses).lower() if isinstance(diagnoses, list) else str(diagnoses).lower()
        prognosis_lower = prognosis.lower()
        all_text = f"{imaging_text} {diagnoses_text} {prognosis_lower}"

        # Check for permanency indicators
        permanent_keywords = ['permanent', 'chronic', 'irreversible', 'uncertain recovery']
        if any(kw in all_text for kw in permanent_keywords):
            # Confirm with NY serious injury threshold
            if 'Permanent consequential limitation' in threshold_categories:
                return InjurySeverity.PERMANENT

        # Check imaging for herniation
        if 'herniation' in imaging_text or 'herniated' in imaging_text:
            return InjurySeverity.DISC_HERNIATION

        # Check for radiculopathy
        if 'radiculopathy' in all_text:
            return InjurySeverity.RADICULOPATHY

        # Check for disc bulging
        if 'bulging' in imaging_text or 'bulge' in imaging_text or 'protrusion' in imaging_text:
            return InjurySeverity.DISC_BULGING

        # Default to soft tissue
        return InjurySeverity.SOFT_TISSUE

    def calculate_liability_strength(self) -> float:
        """
        Calculate liability strength from 0.0 to 1.0.

        Returns:
            Float between 0.0 (weak) and 1.0 (very strong)
        """
        liability = self.case_data.get('liability_analysis', {})

        score = 0.5  # Start neutral

        # Fault determination
        fault = liability.get('fault_determination', '').lower()
        if '100%' in fault or 'at fault' in fault or 'driver 2' in fault:
            score += 0.2

        # Traffic violations
        violations = liability.get('violations', [])
        if not violations:
            # Check defendant info for violations
            defendant = self.case_data.get('defendant', {})
            violations = defendant.get('violations', [])

        if violations:
            score += 0.1 * min(len(violations), 2)  # Up to 0.2 for violations

        # Evidence strength
        evidence = liability.get('evidence', [])
        evidence_text = ' '.join(evidence).lower() if evidence else ''

        if 'camera' in evidence_text or 'video' in evidence_text:
            score += 0.15
        if 'witness' in evidence_text:
            score += 0.1

        # Contributing factors against defendant
        factors = liability.get('contributing_factors', [])
        if factors:
            score += 0.05 * min(len(factors), 2)

        return min(1.0, max(0.0, score))

    def calculate_demand_amount(self) -> Dict[str, Any]:
        """
        Calculate demand amount with detailed breakdown.

        Returns:
            Dictionary with demand calculation details
        """
        # Get medical specials
        bills = self.case_data.get('medical_bills', {})
        total_specials = bills.get('total_charges', 0)

        if total_specials == 0:
            # Try special_damages
            special_damages = self.case_data.get('special_damages', {})
            medical_expenses = special_damages.get('medical_expenses', {})
            total_specials = medical_expenses.get('total_billed', 0)

        # Classify injury severity
        severity = self.classify_injury_severity()
        low_mult, high_mult = SEVERITY_MULTIPLIERS[severity]

        # Get liability strength
        liability_strength = self.calculate_liability_strength()

        # Select multiplier based on liability
        if liability_strength >= 0.9:
            selected_mult = high_mult
        elif liability_strength >= 0.75:
            selected_mult = (low_mult + high_mult) / 2 + (high_mult - low_mult) * 0.25
        elif liability_strength >= 0.5:
            selected_mult = (low_mult + high_mult) / 2
        else:
            selected_mult = low_mult

        # Calculate amounts
        pain_suffering = total_specials * selected_mult
        total_demand = total_specials + pain_suffering

        # Round to nearest $500
        total_demand = round(total_demand / 500) * 500

        # Get available coverage
        coverage = self.case_data.get('insurance_coverage', {})
        defendant_policy = coverage.get('defendant_policy', {})

        # Parse BI limits
        bi_limits_str = defendant_policy.get('bi_limits', '')
        defendant_bi = self._parse_bi_limits(bi_limits_str)

        if not defendant_bi:
            # Try numeric fields
            defendant_bi = defendant_policy.get('bi_per_person', 0)

        self.demand_calculation = {
            'total_specials': total_specials,
            'severity_classification': severity.value,
            'multiplier_range': (low_mult, high_mult),
            'multiplier_used': round(selected_mult, 2),
            'liability_strength': round(liability_strength, 2),
            'pain_and_suffering': round(pain_suffering, 2),
            'total_demand': total_demand,
            'defendant_bi_limit': defendant_bi,
            'exceeds_coverage': total_demand > defendant_bi if defendant_bi else None
        }

        return self.demand_calculation

    def _parse_bi_limits(self, limits_str: str) -> Optional[int]:
        """Parse BI limits string like '$100,000/300,000' to get per-person limit."""
        if not limits_str:
            return None

        # Remove $ and commas, get first number
        match = re.search(r'[\$]?([\d,]+)', limits_str)
        if match:
            return int(match.group(1).replace(',', ''))
        return None

    # === Content Generation Methods ===

    def generate_letterhead(self) -> str:
        """Generate law firm letterhead."""
        firm = self.firm_config
        addr = firm.get('firm_address', {})
        attorney = firm.get('attorney', {})

        lines = [
            f"**{firm.get('firm_name', '[LAW FIRM NAME]')}**",
            f"{addr.get('street', '')}",
            f"{addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}",
            f"Tel: {firm.get('firm_phone', '')} | Fax: {firm.get('firm_fax', '')}",
            f"{firm.get('firm_email', '')}",
            "",
            "---",
            ""
        ]
        return '\n'.join(lines)

    def generate_date_and_addressee(self) -> str:
        """Generate date and insurance carrier address block."""
        today = datetime.now().strftime("%B %d, %Y")

        # Get defendant insurance info
        coverage = self.case_data.get('insurance_coverage', {})
        defendant_policy = coverage.get('defendant_policy', {})

        # Also check defendant info
        defendant = self.case_data.get('defendant', {})

        carrier = defendant_policy.get('carrier', '')
        if not carrier:
            carrier = defendant.get('insurance', '').split(' Policy')[0] if defendant.get('insurance') else '[INSURANCE CARRIER]'

        lines = [
            today,
            "",
            "**VIA CERTIFIED MAIL AND REGULAR MAIL**",
            "",
            "Claims Department",
            carrier,
            "[Claims Address]",
            ""
        ]
        return '\n'.join(lines)

    def generate_re_line(self) -> str:
        """Generate Re: line with claim details."""
        plaintiff = self.case_data.get('plaintiff', {})
        accident = self.case_data.get('accident', {})
        defendant = self.case_data.get('defendant', {})
        coverage = self.case_data.get('insurance_coverage', {})
        defendant_policy = coverage.get('defendant_policy', {})

        plaintiff_name = plaintiff.get('name', '[CLAIMANT NAME]')
        accident_date = accident.get('date', '[DATE OF LOSS]')

        # Get claim/policy numbers
        claim_number = defendant_policy.get('claim_number', '[CLAIM NUMBER]')
        policy_number = defendant_policy.get('policy_number', '')
        if not policy_number:
            # Try to extract from defendant insurance string
            ins = defendant.get('insurance', '')
            match = re.search(r'#([A-Z0-9\-]+)', ins)
            policy_number = match.group(1) if match else '[POLICY NUMBER]'

        defendant_name = defendant.get('name', '[INSURED NAME]')

        lines = [
            f"**Re:** Claimant: {plaintiff_name}",
            f"       Date of Loss: {accident_date}",
            f"       Claim Number: {claim_number}",
            f"       Insured: {defendant_name}",
            f"       Policy Number: {policy_number}",
            "",
            "Dear Claims Representative:",
            ""
        ]
        return '\n'.join(lines)

    def generate_introduction(self) -> str:
        """Generate introduction paragraph."""
        plaintiff = self.case_data.get('plaintiff', {})
        accident = self.case_data.get('accident', {})

        plaintiff_name = plaintiff.get('name', '[CLIENT NAME]')
        accident_date = accident.get('date', '[DATE]')
        location = accident.get('location', '[LOCATION]')

        return f"""## Introduction

This firm represents **{plaintiff_name}** for injuries sustained in a motor vehicle collision that occurred on **{accident_date}** at **{location}**. This letter serves as a formal demand for settlement of our client's bodily injury claim.

"""

    def generate_facts_section(self) -> str:
        """Generate facts of accident section."""
        accident = self.case_data.get('accident', {})

        narrative = accident.get('description', '')
        if not narrative:
            narrative = accident.get('narrative', '[Accident narrative to be inserted]')

        date = accident.get('date', '')
        time = accident.get('time', '')
        location = accident.get('location', '')
        report_num = accident.get('report_number', '')

        lines = [
            "## Facts of the Accident",
            "",
            f"On **{date}** at approximately **{time}**, a motor vehicle collision occurred at **{location}**.",
            ""
        ]

        if report_num:
            lines.append(f"*Police Report No. {report_num}*")
            lines.append("")

        lines.append(narrative)
        lines.append("")

        return '\n'.join(lines)

    def generate_liability_section(self) -> str:
        """Generate liability discussion section."""
        liability = self.case_data.get('liability_analysis', {})
        defendant = self.case_data.get('defendant', {})

        fault = liability.get('fault_determination', '')
        violations = defendant.get('violations', [])
        if not violations:
            violations = liability.get('violations', [])
        evidence = liability.get('evidence', [])
        factors = liability.get('contributing_factors', [])

        lines = [
            "## Liability",
            "",
            "Liability in this matter is clear and uncontested.",
            ""
        ]

        if fault:
            lines.append(f"**Fault Determination:** {fault}")
            lines.append("")

        if violations:
            lines.append("**Traffic Violations Cited:**")
            for v in violations:
                lines.append(f"- {v}")
            lines.append("")

        if factors:
            lines.append("**Contributing Factors:**")
            for f in factors:
                lines.append(f"- {f}")
            lines.append("")

        if evidence:
            lines.append("**Evidence Supporting Liability:**")
            for e in evidence:
                lines.append(f"- {e}")
            lines.append("")

        lines.append("Based on the foregoing, your insured bears 100% liability for this collision.")
        lines.append("")

        return '\n'.join(lines)

    def generate_injuries_section(self) -> str:
        """Generate injuries and treatment section."""
        injuries = self.case_data.get('injuries', {})

        diagnoses = injuries.get('diagnoses', [])
        body_parts = injuries.get('body_parts', [])
        icd_codes = injuries.get('icd_codes', [])
        imaging = injuries.get('imaging_findings', [])
        treatment_plan = injuries.get('treatment_plan', [])
        prognosis = injuries.get('prognosis', '')

        lines = [
            "## Injuries and Medical Treatment",
            "",
            "As a direct and proximate result of this collision, our client sustained the following injuries:",
            ""
        ]

        if body_parts:
            lines.append("**Body Parts Affected:**")
            for bp in body_parts:
                lines.append(f"- {bp}")
            lines.append("")

        if diagnoses:
            lines.append("**Diagnoses:**")
            for i, diag in enumerate(diagnoses):
                icd = icd_codes[i] if i < len(icd_codes) else ""
                if icd:
                    lines.append(f"- {diag} (ICD-10: `{icd}`)")
                else:
                    lines.append(f"- {diag}")
            lines.append("")

        if imaging:
            lines.append("**Diagnostic Imaging Findings:**")
            for finding in imaging:
                lines.append(f"- {finding}")
            lines.append("")

        if treatment_plan:
            lines.append("**Treatment:**")
            for treatment in treatment_plan[:5]:  # Limit to first 5
                lines.append(f"- {treatment}")
            lines.append("")

        if prognosis:
            lines.append("**Prognosis:**")
            lines.append(prognosis)
            lines.append("")

        return '\n'.join(lines)

    def generate_specials_table(self) -> str:
        """Generate medical specials itemization table."""
        bills = self.case_data.get('medical_bills', {})

        total_charges = bills.get('total_charges', 0)
        total_paid = bills.get('total_paid', 0)
        total_owed = bills.get('total_owed', 0)
        providers = bills.get('providers', [])
        liens = bills.get('liens', [])
        cpt_codes = bills.get('cpt_codes', [])

        lines = [
            "## Medical Specials Itemization",
            "",
            "| Provider | Total Charges | Paid | Balance |",
            "|----------|-------------:|-----:|--------:|"
        ]

        # If we have provider breakdown
        if providers:
            # Create a simple breakdown (in real implementation, would use line items)
            charge_per_provider = total_charges / len(providers) if providers else 0
            paid_per_provider = total_paid / len(providers) if providers else 0
            balance_per_provider = total_owed / len(providers) if providers else 0

            for provider in providers:
                lines.append(
                    f"| {provider} | ${charge_per_provider:,.2f} | "
                    f"${paid_per_provider:,.2f} | ${balance_per_provider:,.2f} |"
                )

        # Totals row
        lines.append(
            f"| **TOTAL** | **${total_charges:,.2f}** | "
            f"**${total_paid:,.2f}** | **${total_owed:,.2f}** |"
        )
        lines.append("")

        # Liens
        if liens:
            lines.append("### Outstanding Medical Liens")
            lines.append("")
            for lien in liens:
                provider = lien.get('provider', 'Unknown')
                amount = lien.get('amount', 0)
                lines.append(f"- {provider}: ${amount:,.2f}")
            lines.append("")

        # CPT codes summary
        if cpt_codes:
            lines.append(f"*CPT Codes: {', '.join(cpt_codes[:8])}*")
            lines.append("")

        return '\n'.join(lines)

    def generate_serious_injury_section(self) -> str:
        """Generate NY Serious Injury threshold section."""
        ny_serious = self.case_data.get('ny_serious_injury_analysis', {})

        meets_threshold = ny_serious.get('meets_threshold', False)
        categories = ny_serious.get('threshold_categories', [])
        evidence = ny_serious.get('supporting_evidence', [])
        notes = ny_serious.get('notes', '')

        if not meets_threshold and not categories:
            return ""  # Skip section if not applicable

        lines = [
            "## NY Serious Injury Threshold (Insurance Law 5102(d))",
            "",
            f"Our client's injuries meet the serious injury threshold under New York Insurance Law 5102(d).",
            ""
        ]

        if categories:
            lines.append("**Threshold Categories Met:**")
            for cat in categories:
                lines.append(f"- {cat}")
            lines.append("")

        if evidence:
            lines.append("**Supporting Evidence:**")
            for ev in evidence:
                lines.append(f"- {ev}")
            lines.append("")

        return '\n'.join(lines)

    def generate_damages_discussion(self) -> str:
        """Generate damages discussion section."""
        injuries = self.case_data.get('injuries', {})
        prognosis = injuries.get('prognosis', '')
        work_restrictions = injuries.get('work_restrictions', '')

        severity = self.classify_injury_severity()

        lines = [
            "## Damages",
            "",
            "As a result of this collision, our client has endured significant pain and suffering, "
            "including but not limited to:",
            "",
            "- Physical pain from injuries sustained",
            "- Emotional distress and anxiety",
            "- Interference with daily activities and quality of life",
            "- Medical treatment and rehabilitation",
        ]

        if work_restrictions:
            lines.append(f"- Lost time from work: {work_restrictions}")

        lines.append("")

        if severity in [InjurySeverity.PERMANENT, InjurySeverity.DISC_HERNIATION]:
            lines.append(
                "Given the permanent nature of our client's injuries and the documented "
                "structural damage, the impact on our client's quality of life will continue indefinitely."
            )
            lines.append("")

        if prognosis:
            lines.append(f"*Prognosis: {prognosis}*")
            lines.append("")

        return '\n'.join(lines)

    def generate_demand_section(self) -> str:
        """Generate demand amount section."""
        if not self.demand_calculation:
            self.calculate_demand_amount()

        calc = self.demand_calculation
        total_specials = calc.get('total_specials', 0)
        pain_suffering = calc.get('pain_and_suffering', 0)
        total_demand = calc.get('total_demand', 0)
        multiplier = calc.get('multiplier_used', 0)
        severity = calc.get('severity_classification', '')
        defendant_bi = calc.get('defendant_bi_limit', 0)

        deadline_days = self.firm_config.get('defaults', {}).get('response_deadline_days', 30)
        deadline_date = (datetime.now() + timedelta(days=deadline_days)).strftime("%B %d, %Y")

        lines = [
            "## Demand",
            "",
            "Based on the foregoing facts, injuries, and damages, we hereby demand the sum of "
            f"**${total_demand:,.2f}** to settle all claims arising from this incident.",
            "",
            "| Category | Amount |",
            "|----------|-------:|",
            f"| Medical Specials | ${total_specials:,.2f} |",
            f"| Pain and Suffering | ${pain_suffering:,.2f} |",
            f"| **TOTAL DEMAND** | **${total_demand:,.2f}** |",
            "",
        ]

        if defendant_bi and total_demand > defendant_bi:
            lines.append(
                f"*Note: This demand exceeds your insured's policy limits of ${defendant_bi:,}. "
                "We reserve the right to pursue the excess from your insured personally.*"
            )
            lines.append("")

        lines.extend([
            f"This demand will remain open for **{deadline_days} days** from the date of this letter "
            f"(until {deadline_date}). Please respond with your settlement position within this timeframe. "
            "Failure to respond may result in the commencement of litigation without further notice.",
            ""
        ])

        return '\n'.join(lines)

    def generate_enclosures(self) -> str:
        """Generate enclosures list."""
        lines = [
            "## Enclosures",
            "",
            "- Police Report",
            "- Medical Records",
            "- Medical Bills",
            "- Photographs (if available)",
            ""
        ]
        return '\n'.join(lines)

    def generate_closing(self) -> str:
        """Generate closing and signature block."""
        attorney = self.firm_config.get('attorney', {})
        firm_name = self.firm_config.get('firm_name', '')
        cc_client = self.firm_config.get('defaults', {}).get('cc_client', True)

        plaintiff = self.case_data.get('plaintiff', {})
        plaintiff_name = plaintiff.get('name', '')

        lines = [
            "Please do not hesitate to contact the undersigned with any questions.",
            "",
            "Very truly yours,",
            "",
            f"**{attorney.get('name', '[Attorney Name]')}**",
            firm_name,
            f"Tel: {attorney.get('direct_phone', '')}",
            f"Email: {attorney.get('email', '')}",
            ""
        ]

        if cc_client and plaintiff_name:
            lines.extend([
                f"cc: {plaintiff_name} (Client)",
                ""
            ])

        return '\n'.join(lines)

    # === Output Methods ===

    def generate_markdown(self) -> str:
        """Generate complete demand letter in Markdown format."""
        # Ensure data is loaded
        if not self.case_data:
            self.load_case_summary()
        if not self.firm_config:
            self.load_firm_config()

        # Calculate demand if not already done
        if not self.demand_calculation:
            self.calculate_demand_amount()

        sections = [
            self.generate_letterhead(),
            self.generate_date_and_addressee(),
            self.generate_re_line(),
            self.generate_introduction(),
            self.generate_facts_section(),
            self.generate_liability_section(),
            self.generate_injuries_section(),
            self.generate_specials_table(),
            self.generate_serious_injury_section(),
            self.generate_damages_discussion(),
            self.generate_demand_section(),
            self.generate_enclosures(),
            self.generate_closing(),
        ]

        return '\n'.join(sections)

    def generate_html(self) -> str:
        """Generate complete demand letter in HTML format with styling."""
        markdown_content = self.generate_markdown()

        # Convert markdown to simple HTML
        html_content = self._markdown_to_html(markdown_content)

        plaintiff = self.case_data.get('plaintiff', {})
        case_id = self.case_data.get('case_id', 'demand_letter')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demand Letter - {plaintiff.get('name', case_id)}</title>
    <style>
        @page {{
            margin: 1in;
            size: letter;
        }}
        @media print {{
            .no-print {{ display: none; }}
            body {{ font-size: 11pt; }}
        }}
        body {{
            font-family: 'Times New Roman', Times, serif;
            font-size: 12pt;
            line-height: 1.6;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 0.5in;
            color: #000;
        }}
        h2 {{
            font-size: 14pt;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            border-bottom: 1px solid #ccc;
            padding-bottom: 0.25em;
        }}
        h3 {{
            font-size: 12pt;
            margin-top: 1em;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #000;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        td:nth-child(n+2) {{
            text-align: right;
        }}
        .letterhead {{
            text-align: center;
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 2px solid #000;
        }}
        .letterhead strong {{
            font-size: 16pt;
        }}
        hr {{
            border: none;
            border-top: 2px solid #000;
            margin: 1em 0;
        }}
        ul {{
            margin: 0.5em 0;
            padding-left: 2em;
        }}
        li {{
            margin: 0.25em 0;
        }}
        em {{
            font-style: italic;
        }}
        strong {{
            font-weight: bold;
        }}
        code {{
            font-family: monospace;
            background: #f5f5f5;
            padding: 0.1em 0.3em;
        }}
        .signature-block {{
            margin-top: 2em;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        return html

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (simple conversion)."""
        html = markdown

        # Headers
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Code
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

        # Horizontal rule
        html = html.replace('---', '<hr>')

        # Tables
        lines = html.split('\n')
        in_table = False
        new_lines = []

        for line in lines:
            if line.strip().startswith('|') and '|' in line[1:]:
                if not in_table:
                    new_lines.append('<table>')
                    in_table = True

                # Skip separator line
                if re.match(r'\|[\s\-:|]+\|', line):
                    continue

                cells = [c.strip() for c in line.split('|')[1:-1]]
                if new_lines[-1] == '<table>':
                    # Header row
                    row = '<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>'
                else:
                    row = '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
                new_lines.append(row)
            else:
                if in_table:
                    new_lines.append('</table>')
                    in_table = False
                new_lines.append(line)

        if in_table:
            new_lines.append('</table>')

        html = '\n'.join(new_lines)

        # Lists
        lines = html.split('\n')
        new_lines = []
        in_list = False

        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    new_lines.append('<ul>')
                    in_list = True
                new_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    new_lines.append('</ul>')
                    in_list = False
                new_lines.append(line)

        if in_list:
            new_lines.append('</ul>')

        html = '\n'.join(new_lines)

        # Paragraphs (lines with content not already wrapped)
        lines = html.split('\n')
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('<') and not stripped.startswith('|'):
                new_lines.append(f'<p>{line}</p>')
            else:
                new_lines.append(line)

        return '\n'.join(new_lines)

    def save_outputs(self, output_dir: str) -> Dict[str, str]:
        """
        Save demand letter to files.

        Args:
            output_dir: Directory to save output files

        Returns:
            Dictionary with paths to saved files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate content
        markdown = self.generate_markdown()
        html = self.generate_html()

        # Save files
        md_path = output_path / "demand_letter.md"
        html_path = output_path / "demand_letter.html"

        md_path.write_text(markdown)
        html_path.write_text(html)

        return {
            'markdown': str(md_path),
            'html': str(html_path),
            'demand_amount': self.demand_calculation.get('total_demand', 0)
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate demand letter from PI case summary'
    )
    parser.add_argument(
        'case_summary',
        help='Path to case_summary.json file'
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to law_firm_config.json file',
        default=None
    )
    parser.add_argument(
        '--output', '-o',
        help='Output directory',
        default='.'
    )

    args = parser.parse_args()

    # Generate demand letter
    generator = DemandLetterGenerator(args.case_summary, args.config)
    generator.load_case_summary()
    generator.load_firm_config()

    results = generator.save_outputs(args.output)

    # Print summary
    calc = generator.demand_calculation
    print(f"Demand Letter Generated")
    print(f"=======================")
    print(f"Injury Severity: {calc.get('severity_classification', 'N/A')}")
    print(f"Liability Strength: {calc.get('liability_strength', 0):.0%}")
    print(f"Multiplier Used: {calc.get('multiplier_used', 0):.1f}x")
    print(f"Medical Specials: ${calc.get('total_specials', 0):,.2f}")
    print(f"Pain & Suffering: ${calc.get('pain_and_suffering', 0):,.2f}")
    print(f"TOTAL DEMAND: ${calc.get('total_demand', 0):,.2f}")
    print(f"")
    print(f"Markdown: {results['markdown']}")
    print(f"HTML: {results['html']}")


if __name__ == "__main__":
    main()
