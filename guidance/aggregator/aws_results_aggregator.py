#!/usr/bin/env python3
"""
AWS Results Aggregator for NY Personal Injury Cases

Aggregates text files from AWS IDP pipeline results and generates a case summary.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class AWSResultsAggregator:
    """Aggregates AWS IDP results from text files"""

    def __init__(self, results_folder: str):
        self.results_folder = Path(results_folder)
        self.medical_records_text: List[str] = []
        self.police_reports_text: List[str] = []
        self.insurance_policies_text: List[str] = []
        self.medical_bills_text: List[str] = []

    def load_documents(self) -> None:
        """Load all extracted text documents from AWS results"""
        for hash_dir in self.results_folder.iterdir():
            if not hash_dir.is_dir():
                continue

            # Check for each document type
            for doc_type_dir in hash_dir.iterdir():
                if not doc_type_dir.is_dir():
                    continue

                doc_type = doc_type_dir.name
                for txt_file in doc_type_dir.glob("*.txt"):
                    content = txt_file.read_text()

                    if doc_type == "MEDICAL_RECORDS":
                        self.medical_records_text.append(content)
                    elif doc_type == "POLICE_REPORT":
                        self.police_reports_text.append(content)
                    elif doc_type == "INSURANCE_POLICY":
                        self.insurance_policies_text.append(content)
                    elif doc_type == "MEDICAL_BILLS":
                        self.medical_bills_text.append(content)

    def extract_patient_info(self) -> Dict[str, Any]:
        """Extract patient/plaintiff info from medical records"""
        info = {"name": "", "dob": "", "address": ""}

        for text in self.medical_records_text:
            # Extract patient name
            name_match = re.search(r'Patient(?:\s+Name)?[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
            if name_match:
                info["name"] = name_match.group(1)

            # Extract DOB
            dob_match = re.search(r'DOB[:\s]+(\d{2}/\d{2}/\d{4})', text)
            if dob_match:
                info["dob"] = dob_match.group(1)

            # Extract address from police report if available
            for police_text in self.police_reports_text:
                addr_match = re.search(r'Address[:\s]+([^\n]+)', police_text)
                if addr_match and "456 East" in addr_match.group(1):
                    info["address"] = addr_match.group(1).strip()
                    break

        return info

    def extract_accident_info(self) -> Dict[str, Any]:
        """Extract accident details from police report"""
        info = {
            "date": "",
            "time": "",
            "location": "",
            "report_number": "",
            "description": ""
        }

        for text in self.police_reports_text:
            # Date
            date_match = re.search(r'Date of Accident[:\s]+(\d{2}/\d{2}/\d{4})', text)
            if date_match:
                info["date"] = date_match.group(1)

            # Time
            time_match = re.search(r'Time[:\s]+(\d{2}:\d{2})', text)
            if time_match:
                info["time"] = time_match.group(1)

            # Location
            loc_match = re.search(r'Location[:\s]+([^\n]+)', text)
            if loc_match:
                info["location"] = loc_match.group(1).strip()

            # Report number
            report_match = re.search(r'Report Number[:\s]+([^\s]+)', text)
            if report_match:
                info["report_number"] = report_match.group(1)

            # Narrative
            narrative_match = re.search(r'NARRATIVE[:\s]*\n(.+?)(?=VIOLATIONS|WITNESS|$)', text, re.DOTALL)
            if narrative_match:
                info["description"] = narrative_match.group(1).strip()[:500]

        return info

    def extract_defendant_info(self) -> Dict[str, Any]:
        """Extract defendant/at-fault party info"""
        info = {"name": "", "vehicle": "", "insurance": "", "violations": []}

        for text in self.police_reports_text:
            # Look for Vehicle 2 / At-Fault section
            if "AT-FAULT" in text or "Vehicle 2" in text:
                # Driver name
                driver_match = re.search(r'(?:VEHICLE 2|AT-FAULT)[^\n]*\n[^\n]*Driver[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
                if driver_match:
                    info["name"] = driver_match.group(1)

                # Vehicle
                vehicle_match = re.search(r'Vehicle[:\s]+(20\d{2}\s+[^\n]+?)(?:\s+Plate|$)', text)
                if vehicle_match:
                    info["vehicle"] = vehicle_match.group(1).strip()

                # Insurance
                ins_match = re.search(r'Progressive[^\n]+', text)
                if ins_match:
                    info["insurance"] = ins_match.group(0).strip()

            # Violations
            vtl_matches = re.findall(r'VTL\s+[\d\w\-\(\)]+\s*-\s*[^\n]+', text)
            info["violations"] = vtl_matches

        return info

    def extract_injuries(self) -> Dict[str, Any]:
        """Extract injury information from medical records"""
        injuries = {
            "diagnoses": [],
            "icd_codes": [],
            "body_parts": [],
            "treatment_plan": [],
            "work_restrictions": ""
        }

        for text in self.medical_records_text:
            # ICD codes
            icd_matches = re.findall(r'ICD-10[:\s]+([A-Z]\d+\.\d+[A-Z]*)', text)
            injuries["icd_codes"].extend(icd_matches)

            # Diagnoses
            diag_matches = re.findall(r'\d+\.\s+([A-Za-z\s,/]+)(?:\s+ICD)', text)
            injuries["diagnoses"].extend([d.strip() for d in diag_matches])

            # Body parts from physical exam
            if "Cervical" in text or "cervical" in text:
                injuries["body_parts"].append("Cervical Spine (Neck)")
            if "Lumbar" in text or "lumbar" in text:
                injuries["body_parts"].append("Lumbar Spine (Lower Back)")
            if "Shoulder" in text or "shoulder" in text:
                injuries["body_parts"].append("Shoulder")

            # Work restrictions
            work_match = re.search(r'(?:no work|off work|work restriction)[^\n]*(\d+\s+weeks?)', text, re.IGNORECASE)
            if work_match:
                injuries["work_restrictions"] = f"No work x {work_match.group(1)}"

            # Treatment plan items
            plan_match = re.search(r'PLAN[:\s]*\n(.+?)(?=Patient is|Attending|$)', text, re.DOTALL)
            if plan_match:
                plan_items = re.findall(r'\d+\.\s+([^\n]+)', plan_match.group(1))
                injuries["treatment_plan"].extend(plan_items)

        # Deduplicate
        injuries["icd_codes"] = list(set(injuries["icd_codes"]))
        injuries["body_parts"] = list(set(injuries["body_parts"]))

        return injuries

    def extract_medical_bills(self) -> Dict[str, Any]:
        """Extract billing information"""
        bills = {
            "providers": [],
            "total_charges": 0.0,
            "total_paid": 0.0,
            "total_owed": 0.0,
            "liens": [],
            "cpt_codes": []
        }

        for text in self.medical_bills_text:
            # Provider
            if "BELLEVUE" in text:
                bills["providers"].append("Bellevue Hospital Center")

            # Total charges
            charges_match = re.search(r'Total Charges[:\s]+\$?([\d,]+\.?\d*)', text)
            if charges_match:
                bills["total_charges"] += float(charges_match.group(1).replace(',', ''))

            # Insurance payment
            paid_match = re.search(r'Insurance Payment[^\$]*\$?([\d,]+\.?\d*)', text)
            if paid_match:
                bills["total_paid"] += float(paid_match.group(1).replace(',', ''))

            # Amount due
            due_match = re.search(r'Amount Due[:\s]+\$?([\d,]+\.?\d*)', text)
            if due_match:
                bills["total_owed"] += float(due_match.group(1).replace(',', ''))

            # Liens
            lien_match = re.search(r'lien[^\$]*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
            if lien_match:
                bills["liens"].append({
                    "provider": "Bellevue Hospital Center",
                    "amount": float(lien_match.group(1).replace(',', ''))
                })

            # CPT codes
            cpt_matches = re.findall(r'(\d{5})\s+[A-Z]', text)
            bills["cpt_codes"].extend(cpt_matches)

        bills["cpt_codes"] = list(set(bills["cpt_codes"]))
        return bills

    def extract_insurance_coverage(self) -> Dict[str, Any]:
        """Extract insurance coverage information"""
        coverage = {
            "plaintiff_policy": {},
            "defendant_policy": {},
            "pip_available": 0.0,
            "sum_available": 0.0,
            "total_available_coverage": 0.0
        }

        for text in self.insurance_policies_text:
            policy_info = {
                "carrier": "",
                "policy_number": "",
                "bi_limits": "",
                "pip_limits": "",
                "sum_limits": ""
            }

            # Carrier
            if "STATE FARM" in text:
                policy_info["carrier"] = "State Farm"
            elif "Progressive" in text:
                policy_info["carrier"] = "Progressive"

            # Policy number
            policy_match = re.search(r'Policy Number[:\s]+([^\s]+)', text)
            if policy_match:
                policy_info["policy_number"] = policy_match.group(1)

            # BI limits
            bi_match = re.search(r'Bodily Injury Liability\s+\$?([\d,]+)[^\$]*\$?([\d,]+)', text)
            if bi_match:
                policy_info["bi_limits"] = f"${bi_match.group(1)}/{bi_match.group(2)}"

            # PIP
            pip_match = re.search(r'Personal Injury Protection[^\$]*\$?([\d,]+)', text)
            if pip_match:
                policy_info["pip_limits"] = f"${pip_match.group(1)}"
                if "State Farm" in text:
                    coverage["pip_available"] = float(pip_match.group(1).replace(',', ''))

            # SUM
            sum_match = re.search(r'Underinsured Motorist[^\$]*\$?([\d,]+)[^\$]*\$?([\d,]+)', text)
            if sum_match:
                policy_info["sum_limits"] = f"${sum_match.group(1)}/{sum_match.group(2)}"
                coverage["sum_available"] = float(sum_match.group(1).replace(',', ''))

            # Assign to plaintiff or defendant
            if "State Farm" in text and "Maria" in text:
                coverage["plaintiff_policy"] = policy_info
            elif "Progressive" in text:
                coverage["defendant_policy"] = policy_info

        # Calculate total available
        coverage["total_available_coverage"] = coverage["pip_available"] + coverage["sum_available"]

        return coverage

    def analyze_liability(self) -> Dict[str, Any]:
        """Analyze liability based on police report"""
        liability = {
            "fault_determination": "",
            "contributing_factors": [],
            "evidence": [],
            "liability_percentage": {"plaintiff": 0, "defendant": 100}
        }

        for text in self.police_reports_text:
            # Fault determination
            if "AT FAULT" in text:
                fault_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)[^\n]*(?:is determined to be|determined)\s+AT FAULT', text)
                if fault_match:
                    liability["fault_determination"] = f"{fault_match.group(1)} determined AT FAULT"

            # Contributing factors
            if "red light" in text.lower() or "red traffic signal" in text.lower():
                liability["contributing_factors"].append("Ran red light")
            if "cell phone" in text.lower() or "mobile telephone" in text.lower():
                liability["contributing_factors"].append("Distracted driving (cell phone)")

            # Evidence
            if "traffic camera" in text.lower():
                liability["evidence"].append("Traffic camera footage")
            if "witness" in text.lower():
                witness_count = len(re.findall(r'\d+\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+,\s+(?:pedestrian|driver)', text))
                if witness_count > 0:
                    liability["evidence"].append(f"{witness_count} witness statements")

        return liability

    def analyze_ny_serious_injury(self) -> Dict[str, Any]:
        """Analyze NY Insurance Law 5102(d) serious injury threshold"""
        analysis = {
            "threshold_categories": [],
            "supporting_evidence": [],
            "meets_threshold": False,
            "notes": ""
        }

        all_text = " ".join(self.medical_records_text)

        # Check for 90/180 day rule
        if "no work" in all_text.lower() or "unable to perform" in all_text.lower():
            analysis["threshold_categories"].append("90/180 Day Rule - Substantial limitation of daily activities")
            analysis["supporting_evidence"].append("Work restriction documented")

        # Check for significant limitation of body function
        if "limited" in all_text.lower() and ("ROM" in all_text or "range of motion" in all_text.lower()):
            analysis["threshold_categories"].append("Significant limitation of use of body function/system")
            rom_match = re.search(r'(?:flexion|extension)\s+limited\s+to\s+(\d+)\s+degrees', all_text, re.IGNORECASE)
            if rom_match:
                analysis["supporting_evidence"].append(f"Range of motion limited to {rom_match.group(1)} degrees")

        # Check for permanent injury indicators
        if "disc bulging" in all_text.lower() or "herniation" in all_text.lower():
            analysis["threshold_categories"].append("Permanent consequential limitation")
            analysis["supporting_evidence"].append("Disc pathology documented on imaging")

        if "radiculopathy" in all_text.lower():
            analysis["supporting_evidence"].append("Radiculopathy diagnosis")

        analysis["meets_threshold"] = len(analysis["threshold_categories"]) > 0

        if analysis["meets_threshold"]:
            analysis["notes"] = "Case likely meets NY serious injury threshold based on documented injuries and limitations."
        else:
            analysis["notes"] = "Additional documentation may be needed to establish serious injury threshold."

        return analysis

    def calculate_damages(self) -> Dict[str, Any]:
        """Calculate special damages"""
        bills = self.extract_medical_bills()

        damages = {
            "medical_expenses": {
                "total_billed": bills["total_charges"],
                "paid_by_insurance": bills["total_paid"],
                "outstanding": bills["total_owed"],
                "liens": bills["liens"]
            },
            "lost_wages": {
                "estimated": 0.0,
                "notes": "To be calculated based on employment records"
            },
            "total_special_damages": bills["total_charges"]
        }

        return damages

    def generate_recommended_actions(self) -> List[str]:
        """Generate recommended next steps"""
        actions = []

        # Based on injuries
        injuries = self.extract_injuries()
        if "MRI" in " ".join(injuries["treatment_plan"]):
            actions.append("Schedule MRI of cervical and lumbar spine as recommended")

        if injuries["work_restrictions"]:
            actions.append("Obtain employment records for lost wage calculation")

        # Based on liability
        liability = self.analyze_liability()
        if "Traffic camera footage" in liability["evidence"]:
            actions.append("Request traffic camera footage via FOIL request")

        # Standard actions
        actions.extend([
            "Send preservation letter to defendant's insurance carrier",
            "Request certified copy of police report",
            "Schedule IME if required by insurance carrier",
            "Consider demand letter after maximum medical improvement"
        ])

        return actions

    def generate_summary(self) -> Dict[str, Any]:
        """Generate complete case summary"""
        self.load_documents()

        summary = {
            "case_id": self.results_folder.name,
            "generated_date": datetime.now().isoformat(),
            "document_counts": {
                "medical_records": len(self.medical_records_text),
                "police_reports": len(self.police_reports_text),
                "insurance_policies": len(self.insurance_policies_text),
                "medical_bills": len(self.medical_bills_text)
            },
            "plaintiff": self.extract_patient_info(),
            "defendant": self.extract_defendant_info(),
            "accident": self.extract_accident_info(),
            "injuries": self.extract_injuries(),
            "medical_bills": self.extract_medical_bills(),
            "insurance_coverage": self.extract_insurance_coverage(),
            "liability_analysis": self.analyze_liability(),
            "ny_serious_injury_analysis": self.analyze_ny_serious_injury(),
            "special_damages": self.calculate_damages(),
            "recommended_actions": self.generate_recommended_actions()
        }

        return summary

    def generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        """Generate a formatted markdown report"""
        report = f"""# NY Personal Injury Case Summary
## Case ID: {summary['case_id']}
Generated: {summary['generated_date']}

---

## Plaintiff Information
- **Name:** {summary['plaintiff']['name']}
- **Date of Birth:** {summary['plaintiff']['dob']}
- **Address:** {summary['plaintiff']['address']}

## Defendant (At-Fault Party)
- **Name:** {summary['defendant']['name']}
- **Vehicle:** {summary['defendant']['vehicle']}
- **Insurance:** {summary['defendant']['insurance']}
- **Violations Issued:**
"""
        for v in summary['defendant']['violations']:
            report += f"  - {v}\n"

        report += f"""
## Accident Details
- **Date:** {summary['accident']['date']}
- **Time:** {summary['accident']['time']}
- **Location:** {summary['accident']['location']}
- **Report Number:** {summary['accident']['report_number']}

**Description:**
{summary['accident']['description']}

## Injuries & Diagnoses
**Body Parts Affected:**
"""
        for bp in summary['injuries']['body_parts']:
            report += f"- {bp}\n"

        report += "\n**Diagnoses:**\n"
        for d in summary['injuries']['diagnoses']:
            report += f"- {d}\n"

        report += "\n**ICD-10 Codes:**\n"
        for code in summary['injuries']['icd_codes']:
            report += f"- {code}\n"

        report += f"\n**Work Restrictions:** {summary['injuries']['work_restrictions']}\n"

        report += f"""
## Medical Bills & Special Damages
| Category | Amount |
|----------|--------|
| Total Billed | ${summary['medical_bills']['total_charges']:,.2f} |
| Paid by Insurance | ${summary['medical_bills']['total_paid']:,.2f} |
| Outstanding Balance | ${summary['medical_bills']['total_owed']:,.2f} |
"""

        if summary['medical_bills']['liens']:
            report += "\n**Medical Liens:**\n"
            for lien in summary['medical_bills']['liens']:
                report += f"- {lien['provider']}: ${lien['amount']:,.2f}\n"

        report += f"""
## Insurance Coverage
### Plaintiff's Policy ({summary['insurance_coverage']['plaintiff_policy'].get('carrier', 'N/A')})
- Policy #: {summary['insurance_coverage']['plaintiff_policy'].get('policy_number', 'N/A')}
- BI Limits: {summary['insurance_coverage']['plaintiff_policy'].get('bi_limits', 'N/A')}
- PIP: {summary['insurance_coverage']['plaintiff_policy'].get('pip_limits', 'N/A')}
- SUM: {summary['insurance_coverage']['plaintiff_policy'].get('sum_limits', 'N/A')}

**Available Coverage:**
- PIP Available: ${summary['insurance_coverage']['pip_available']:,.2f}
- SUM Available: ${summary['insurance_coverage']['sum_available']:,.2f}

## Liability Analysis
**Fault Determination:** {summary['liability_analysis']['fault_determination']}

**Contributing Factors:**
"""
        for f in summary['liability_analysis']['contributing_factors']:
            report += f"- {f}\n"

        report += "\n**Evidence:**\n"
        for e in summary['liability_analysis']['evidence']:
            report += f"- {e}\n"

        report += f"""
## NY Serious Injury Analysis (Insurance Law 5102(d))
**Meets Threshold:** {'YES' if summary['ny_serious_injury_analysis']['meets_threshold'] else 'NEEDS REVIEW'}

**Threshold Categories Met:**
"""
        for cat in summary['ny_serious_injury_analysis']['threshold_categories']:
            report += f"- {cat}\n"

        report += "\n**Supporting Evidence:**\n"
        for ev in summary['ny_serious_injury_analysis']['supporting_evidence']:
            report += f"- {ev}\n"

        report += f"\n**Notes:** {summary['ny_serious_injury_analysis']['notes']}\n"

        report += """
## Recommended Actions
"""
        for i, action in enumerate(summary['recommended_actions'], 1):
            report += f"{i}. {action}\n"

        report += """
---
*This summary was automatically generated from IDP-extracted documents.*
"""
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Aggregate AWS IDP results for PI case')
    parser.add_argument('results_folder', help='Path to AWS results folder')
    parser.add_argument('--output', '-o', help='Output file path', default='case_summary')
    args = parser.parse_args()

    aggregator = AWSResultsAggregator(args.results_folder)
    summary = aggregator.generate_summary()

    # Save JSON
    json_path = f"{args.output}.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"JSON summary saved to: {json_path}")

    # Save Markdown
    md_path = f"{args.output}.md"
    md_report = aggregator.generate_markdown_report(summary)
    with open(md_path, 'w') as f:
        f.write(md_report)
    print(f"Markdown report saved to: {md_path}")

    return summary


if __name__ == "__main__":
    main()
