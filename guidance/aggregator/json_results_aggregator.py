#!/usr/bin/env python3
"""
JSON Results Aggregator for NY Personal Injury Cases

Aggregates structured JSON output from AWS IDP pipeline and generates a case summary.
This version works with the structured JSON extraction (report.txt files).
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class JSONResultsAggregator:
    """Aggregates structured JSON results from AWS IDP pipeline"""

    def __init__(self, results_folder: str):
        self.results_folder = Path(results_folder)
        self.medical_records: List[Dict] = []
        self.police_reports: List[Dict] = []
        self.insurance_policies: List[Dict] = []
        self.medical_bills: List[Dict] = []

    def load_documents(self) -> None:
        """Load all extracted JSON documents from AWS results"""
        for hash_dir in self.results_folder.iterdir():
            if not hash_dir.is_dir():
                continue

            for doc_type_dir in hash_dir.iterdir():
                if not doc_type_dir.is_dir():
                    continue

                doc_type = doc_type_dir.name
                report_file = doc_type_dir / "report.txt"

                if report_file.exists():
                    try:
                        content = report_file.read_text()
                        data = json.loads(content)

                        if doc_type == "MEDICAL_RECORDS":
                            self.medical_records.append(data)
                        elif doc_type == "POLICE_REPORT":
                            self.police_reports.append(data)
                        elif doc_type == "INSURANCE_POLICY":
                            self.insurance_policies.append(data)
                        elif doc_type == "MEDICAL_BILLS":
                            self.medical_bills.append(data)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Could not parse JSON in {report_file}: {e}")

    def extract_patient_info(self) -> Dict[str, Any]:
        """Extract patient/plaintiff info from medical records"""
        info = {"name": "", "dob": "", "address": "", "mrn": ""}

        for record in self.medical_records:
            # Patient info from medical record
            if "patientName" in record:
                info["name"] = record.get("patientName", "")
                info["dob"] = record.get("dateOfBirth", "")
                info["mrn"] = record.get("medicalRecordNumber", "")
            elif "patient_info" in record:
                patient = record["patient_info"]
                info["name"] = patient.get("name", "")
                info["dob"] = patient.get("date_of_birth", "")
                info["mrn"] = patient.get("medical_record_number", "")

        # Get address from police report
        for report in self.police_reports:
            drivers = report.get("drivers", [])
            for driver in drivers:
                if driver.get("vehicle_number") == 1:
                    info["address"] = driver.get("address", "")
                    break

        return info

    def extract_accident_info(self) -> Dict[str, Any]:
        """Extract accident details from police report"""
        info = {
            "date": "",
            "time": "",
            "location": "",
            "report_number": "",
            "description": "",
            "weather": "",
            "road_conditions": ""
        }

        for report in self.police_reports:
            report_info = report.get("report_info", {})
            info["report_number"] = report_info.get("report_number", "")
            info["date"] = report_info.get("date_prepared", "")

            accident = report.get("accident_details", {})
            info["date"] = accident.get("date", info["date"])
            info["time"] = accident.get("time", "")
            info["weather"] = accident.get("weather_conditions", "")
            info["road_conditions"] = accident.get("road_conditions", "")

            location = accident.get("location", {})
            if isinstance(location, dict):
                cross = location.get("cross_street", "")
                borough = location.get("borough", "")
                county = location.get("county", "")
                info["location"] = f"{cross}, {borough}, {county}".strip(", ")
            else:
                info["location"] = str(location)

            info["description"] = report.get("narrative", "")

        return info

    def extract_defendant_info(self) -> Dict[str, Any]:
        """Extract defendant/at-fault party info"""
        info = {
            "name": "",
            "vehicle": "",
            "insurance": "",
            "violations": [],
            "contributing_factors": []
        }

        for report in self.police_reports:
            # Find at-fault driver (usually vehicle 2)
            drivers = report.get("drivers", [])
            for driver in drivers:
                if driver.get("vehicle_number") == 2:
                    info["name"] = driver.get("name", "")
                    break

            # Get vehicle info
            vehicles = report.get("vehicles", [])
            for vehicle in vehicles:
                if vehicle.get("vehicle_number") == 2:
                    year = vehicle.get("year", "")
                    make = vehicle.get("make", "")
                    model = vehicle.get("model", "")
                    info["vehicle"] = f"{year} {make} {model}".strip()

                    insurance = vehicle.get("insurance", {})
                    company = insurance.get("company", "")
                    policy = insurance.get("policy_number", "")
                    info["insurance"] = f"{company} Policy #{policy}".strip()
                    break

            # Get violations
            fault = report.get("fault_indicators", {})
            violations = fault.get("violations_cited", [])
            for v in violations:
                vtl = v.get("vtl_section", "")
                desc = v.get("description", "")
                if vtl or desc:
                    info["violations"].append(f"VTL {vtl} - {desc}".strip(" -"))

            info["contributing_factors"] = fault.get("contributing_factors", [])

        return info

    def extract_injuries(self) -> Dict[str, Any]:
        """Extract injury information from medical records"""
        injuries = {
            "diagnoses": [],
            "icd_codes": [],
            "body_parts": [],
            "treatment_plan": [],
            "work_restrictions": "",
            "prognosis": "",
            "imaging_findings": []
        }

        for record in self.medical_records:
            # Handle different JSON structures
            if "assessment" in record:
                # New structured format
                for diagnosis in record.get("assessment", []):
                    diag_text = diagnosis.get("diagnosis", "")
                    icd = diagnosis.get("icd10Code", "")
                    if diag_text:
                        injuries["diagnoses"].append(diag_text)
                    if icd:
                        injuries["icd_codes"].append(icd)

                injuries["treatment_plan"] = record.get("plan", [])
                injuries["prognosis"] = record.get("prognosis", "")

                # Extract body parts from diagnoses
                for diag in injuries["diagnoses"]:
                    diag_lower = diag.lower()
                    if "cervical" in diag_lower:
                        injuries["body_parts"].append("Cervical Spine (Neck)")
                    if "lumbar" in diag_lower:
                        injuries["body_parts"].append("Lumbar Spine (Lower Back)")
                    if "shoulder" in diag_lower or "ac joint" in diag_lower:
                        injuries["body_parts"].append("Shoulder")

                # Imaging findings
                imaging = record.get("diagnosticImaging", {})
                for study, finding in imaging.items():
                    if finding:
                        injuries["imaging_findings"].append(f"{study}: {finding}")

            elif "diagnoses" in record:
                # Alternative format
                for diag in record.get("diagnoses", []):
                    if isinstance(diag, dict):
                        injuries["diagnoses"].append(diag.get("description", ""))
                        if diag.get("icd_code"):
                            injuries["icd_codes"].append(diag["icd_code"])
                        if diag.get("body_part"):
                            injuries["body_parts"].append(diag["body_part"])

            # Work restrictions
            func = record.get("functional_limitations", {})
            if func:
                restrictions = func.get("work_restrictions", [])
                if restrictions:
                    injuries["work_restrictions"] = ", ".join(restrictions) if isinstance(restrictions, list) else restrictions

            # Check plan items for work restrictions
            for item in injuries["treatment_plan"]:
                if "no work" in item.lower():
                    injuries["work_restrictions"] = item

        # Deduplicate
        injuries["icd_codes"] = list(set(injuries["icd_codes"]))
        injuries["body_parts"] = list(set(injuries["body_parts"]))
        injuries["diagnoses"] = list(dict.fromkeys(injuries["diagnoses"]))

        return injuries

    def extract_medical_bills(self) -> Dict[str, Any]:
        """Extract billing information"""
        bills = {
            "providers": [],
            "total_charges": 0.0,
            "total_paid": 0.0,
            "total_owed": 0.0,
            "total_adjustments": 0.0,
            "liens": [],
            "cpt_codes": [],
            "line_items": []
        }

        for bill in self.medical_bills:
            # Provider info
            provider = bill.get("billing_provider", {})
            provider_name = provider.get("name", "")
            if provider_name and provider_name not in bills["providers"]:
                bills["providers"].append(provider_name)

            # Billing summary
            summary = bill.get("billing_summary", {})
            bills["total_charges"] += summary.get("total_charges", 0.0)
            bills["total_paid"] += summary.get("total_payments", 0.0)
            bills["total_owed"] += summary.get("balance_due", 0.0)
            bills["total_adjustments"] += summary.get("total_adjustments", 0.0)

            # Line items with CPT codes
            for item in bill.get("line_items", []):
                cpt = item.get("cpt_code", "")
                if cpt:
                    bills["cpt_codes"].append(cpt)
                bills["line_items"].append({
                    "date": item.get("date_of_service", ""),
                    "cpt": cpt,
                    "description": item.get("description", ""),
                    "charge": item.get("total_charge", 0.0)
                })

            # Liens
            lien_info = bill.get("lien_info", {})
            if lien_info.get("lien_filed"):
                bills["liens"].append({
                    "provider": lien_info.get("lien_holder", provider_name),
                    "amount": lien_info.get("lien_amount", bills["total_owed"])
                })
            elif bills["total_owed"] > 0:
                # If there's a balance due, track it as potential lien
                bills["liens"].append({
                    "provider": provider_name,
                    "amount": bills["total_owed"]
                })

        bills["cpt_codes"] = list(set(bills["cpt_codes"]))
        return bills

    def extract_insurance_coverage(self) -> Dict[str, Any]:
        """Extract insurance coverage information"""
        coverage = {
            "plaintiff_policy": {},
            "defendant_policy": {},
            "pip_available": 0.0,
            "sum_available": 0.0,
            "um_available": 0.0,
            "total_available_coverage": 0.0,
            "meets_ny_minimum": False
        }

        for policy in self.insurance_policies:
            policy_info = policy.get("policy_info", {})
            named_insured = policy.get("named_insured", {})
            coverages = policy.get("coverages", {})

            carrier = policy_info.get("insurance_company", "")
            policy_number = policy_info.get("policy_number", "")

            # BI Limits
            bi = coverages.get("bodily_injury_liability", {})
            bi_per_person = bi.get("per_person", 0)
            bi_per_accident = bi.get("per_accident", 0)
            bi_limits = f"${bi_per_person:,}/{bi_per_accident:,}" if bi_per_person else ""

            # PIP
            pip = coverages.get("personal_injury_protection_no_fault", {})
            pip_basic = pip.get("basic_pip", 0)
            pip_additional = pip.get("additional_pip", 0)
            pip_total = pip_basic + pip_additional
            pip_limits = f"${pip_total:,}" if pip_total else ""

            # UM/SUM
            um = coverages.get("uninsured_motorist", {})
            sum_coverage = coverages.get("underinsured_motorist_sum", {})
            um_per_person = um.get("bodily_injury_per_person", 0)
            sum_per_person = sum_coverage.get("per_person", 0)
            sum_per_accident = sum_coverage.get("per_accident", 0)
            sum_limits = f"${sum_per_person:,}/{sum_per_accident:,}" if sum_per_person else ""

            policy_data = {
                "carrier": carrier,
                "policy_number": policy_number,
                "bi_limits": bi_limits,
                "pip_limits": pip_limits,
                "sum_limits": sum_limits,
                "pip_amount": pip_total,
                "sum_amount": sum_per_person,
                "um_amount": um_per_person
            }

            # Determine if plaintiff or defendant policy
            insured_name = named_insured.get("name", "").lower()
            if "rodriguez" in insured_name or "maria" in insured_name:
                coverage["plaintiff_policy"] = policy_data
                coverage["pip_available"] = pip_total
                coverage["sum_available"] = sum_per_person
                coverage["um_available"] = um_per_person
            else:
                coverage["defendant_policy"] = policy_data

            # Check NY minimums
            liability_analysis = policy.get("liability_analysis", {})
            if liability_analysis.get("meets_ny_minimum"):
                coverage["meets_ny_minimum"] = True

        coverage["total_available_coverage"] = (
            coverage["pip_available"] +
            coverage["sum_available"]
        )

        return coverage

    def analyze_liability(self) -> Dict[str, Any]:
        """Analyze liability based on police report"""
        liability = {
            "fault_determination": "",
            "at_fault_party": "",
            "contributing_factors": [],
            "evidence": [],
            "liability_percentage": {"plaintiff": 0, "defendant": 100}
        }

        for report in self.police_reports:
            fault = report.get("fault_indicators", {})

            liability["fault_determination"] = fault.get("fault_determination", "")
            liability["at_fault_party"] = fault.get("apparent_fault", "")
            liability["contributing_factors"] = fault.get("contributing_factors", [])

            # Evidence
            if report.get("diagram_present"):
                liability["evidence"].append("Accident diagram")
            if report.get("photos_taken"):
                liability["evidence"].append("Photos taken at scene")

            # Witnesses
            witnesses = report.get("witnesses", [])
            if witnesses:
                liability["evidence"].append(f"{len(witnesses)} witness statement(s)")

            # Check narrative for evidence mentions
            narrative = report.get("narrative", "").lower()
            if "traffic camera" in narrative or "camera footage" in narrative:
                liability["evidence"].append("Traffic camera footage")

        return liability

    def analyze_ny_serious_injury(self) -> Dict[str, Any]:
        """Analyze NY Insurance Law 5102(d) serious injury threshold"""
        analysis = {
            "threshold_categories": [],
            "supporting_evidence": [],
            "meets_threshold": False,
            "notes": ""
        }

        injuries = self.extract_injuries()

        # Check for 90/180 day rule
        if injuries["work_restrictions"]:
            analysis["threshold_categories"].append("90/180 Day Rule - Substantial limitation of daily activities")
            analysis["supporting_evidence"].append(f"Work restriction: {injuries['work_restrictions']}")

        # Check diagnoses for serious injury indicators
        for diag in injuries["diagnoses"]:
            diag_lower = diag.lower()
            if "radiculopathy" in diag_lower:
                analysis["threshold_categories"].append("Significant limitation of use of body function/system")
                analysis["supporting_evidence"].append("Radiculopathy diagnosis")
            if "fracture" in diag_lower:
                analysis["threshold_categories"].append("Fracture")
                analysis["supporting_evidence"].append(f"Fracture: {diag}")

        # Check imaging for structural damage
        for finding in injuries["imaging_findings"]:
            finding_lower = finding.lower()
            if "bulging" in finding_lower or "herniation" in finding_lower:
                analysis["threshold_categories"].append("Permanent consequential limitation")
                analysis["supporting_evidence"].append(f"Disc pathology: {finding}")
            if "tear" in finding_lower:
                analysis["supporting_evidence"].append(f"Soft tissue damage: {finding}")

        # Check prognosis
        if injuries["prognosis"]:
            if "uncertain" in injuries["prognosis"].lower() or "permanent" in injuries["prognosis"].lower():
                analysis["supporting_evidence"].append(f"Prognosis: {injuries['prognosis']}")

        # Deduplicate
        analysis["threshold_categories"] = list(set(analysis["threshold_categories"]))
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
                "adjustments": bills["total_adjustments"],
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

        injuries = self.extract_injuries()
        bills = self.extract_medical_bills()
        coverage = self.extract_insurance_coverage()

        # Based on treatment plan
        for item in injuries["treatment_plan"]:
            item_lower = item.lower()
            if "mri" in item_lower and "mri" not in " ".join(actions).lower():
                actions.append("Schedule MRI as recommended in treatment plan")
            if "follow up" in item_lower and "orthopedic" in item_lower:
                actions.append("Schedule orthopedic follow-up appointment")

        # Work restrictions -> lost wages
        if injuries["work_restrictions"]:
            actions.append("Obtain employment records for lost wage calculation")

        # Medical bills
        if bills["total_owed"] > 0:
            actions.append(f"Verify medical liens totaling ${bills['total_owed']:,.2f}")

        # Standard PI case actions
        actions.extend([
            "Request traffic camera footage via FOIL request",
            "Send preservation letter to defendant's insurance carrier",
            "Request certified copy of police report",
            "Obtain complete medical records from all treating providers",
        ])

        # Coverage-based actions
        if coverage["pip_available"] > 0:
            actions.append(f"File No-Fault claim (PIP available: ${coverage['pip_available']:,.2f})")

        actions.append("Consider demand letter after maximum medical improvement")

        return actions

    def generate_summary(self) -> Dict[str, Any]:
        """Generate complete case summary"""
        self.load_documents()

        summary = {
            "case_id": self.results_folder.name,
            "generated_date": datetime.now().isoformat(),
            "extraction_type": "structured_json",
            "document_counts": {
                "medical_records": len(self.medical_records),
                "police_reports": len(self.police_reports),
                "insurance_policies": len(self.insurance_policies),
                "medical_bills": len(self.medical_bills)
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
Extraction Type: {summary.get('extraction_type', 'structured_json')}

---

## Document Summary
| Document Type | Count |
|--------------|-------|
| Medical Records | {summary['document_counts']['medical_records']} |
| Police Reports | {summary['document_counts']['police_reports']} |
| Insurance Policies | {summary['document_counts']['insurance_policies']} |
| Medical Bills | {summary['document_counts']['medical_bills']} |

---

## Plaintiff Information
- **Name:** {summary['plaintiff']['name']}
- **Date of Birth:** {summary['plaintiff']['dob']}
- **Address:** {summary['plaintiff']['address']}
- **Medical Record #:** {summary['plaintiff'].get('mrn', 'N/A')}

## Defendant (At-Fault Party)
- **Name:** {summary['defendant']['name']}
- **Vehicle:** {summary['defendant']['vehicle']}
- **Insurance:** {summary['defendant']['insurance']}
"""
        if summary['defendant']['violations']:
            report += "- **Violations Issued:**\n"
            for v in summary['defendant']['violations']:
                report += f"  - {v}\n"

        report += f"""
## Accident Details
- **Date:** {summary['accident']['date']}
- **Time:** {summary['accident']['time']}
- **Location:** {summary['accident']['location']}
- **Report Number:** {summary['accident']['report_number']}

**Narrative:**
{summary['accident']['description'][:500]}{'...' if len(summary['accident'].get('description', '')) > 500 else ''}

---

## Injuries & Diagnoses

### Body Parts Affected
"""
        for bp in summary['injuries']['body_parts']:
            report += f"- {bp}\n"

        report += "\n### Diagnoses\n"
        for d in summary['injuries']['diagnoses']:
            report += f"- {d}\n"

        report += "\n### ICD-10 Codes\n"
        for code in summary['injuries']['icd_codes']:
            report += f"- `{code}`\n"

        if summary['injuries']['imaging_findings']:
            report += "\n### Imaging Findings\n"
            for finding in summary['injuries']['imaging_findings']:
                report += f"- {finding}\n"

        report += f"""
### Work Restrictions
{summary['injuries']['work_restrictions'] or 'None documented'}

### Prognosis
{summary['injuries'].get('prognosis', 'Not documented')}

---

## Medical Bills & Special Damages

| Category | Amount |
|----------|--------|
| Total Billed | ${summary['medical_bills']['total_charges']:,.2f} |
| Paid by Insurance | ${summary['medical_bills']['total_paid']:,.2f} |
| Adjustments | ${summary['medical_bills'].get('total_adjustments', 0):,.2f} |
| Outstanding Balance | ${summary['medical_bills']['total_owed']:,.2f} |

### Providers
"""
        for provider in summary['medical_bills']['providers']:
            report += f"- {provider}\n"

        if summary['medical_bills']['liens']:
            report += "\n### Medical Liens\n"
            for lien in summary['medical_bills']['liens']:
                report += f"- {lien['provider']}: ${lien['amount']:,.2f}\n"

        if summary['medical_bills']['cpt_codes']:
            report += "\n### CPT Codes\n"
            report += ", ".join([f"`{code}`" for code in summary['medical_bills']['cpt_codes'][:10]])
            if len(summary['medical_bills']['cpt_codes']) > 10:
                report += f" (+{len(summary['medical_bills']['cpt_codes']) - 10} more)"
            report += "\n"

        pp = summary['insurance_coverage'].get('plaintiff_policy', {})
        report += f"""
---

## Insurance Coverage

### Plaintiff's Policy ({pp.get('carrier', 'N/A')})
- **Policy #:** {pp.get('policy_number', 'N/A')}
- **BI Limits:** {pp.get('bi_limits', 'N/A')}
- **PIP:** {pp.get('pip_limits', 'N/A')}
- **SUM:** {pp.get('sum_limits', 'N/A')}

### Available Coverage
| Coverage Type | Amount |
|--------------|--------|
| PIP Available | ${summary['insurance_coverage']['pip_available']:,.2f} |
| SUM Available | ${summary['insurance_coverage']['sum_available']:,.2f} |
| UM Available | ${summary['insurance_coverage'].get('um_available', 0):,.2f} |
| **Total Available** | **${summary['insurance_coverage']['total_available_coverage']:,.2f}** |

---

## Liability Analysis

**Fault Determination:** {summary['liability_analysis']['fault_determination']}

### Contributing Factors
"""
        for f in summary['liability_analysis']['contributing_factors']:
            report += f"- {f}\n"

        report += "\n### Evidence\n"
        for e in summary['liability_analysis']['evidence']:
            report += f"- {e}\n"

        ny = summary['ny_serious_injury_analysis']
        report += f"""
---

## NY Serious Injury Analysis (Insurance Law 5102(d))

**Meets Threshold:** {'✅ YES' if ny['meets_threshold'] else '⚠️ NEEDS REVIEW'}

### Threshold Categories Met
"""
        if ny['threshold_categories']:
            for cat in ny['threshold_categories']:
                report += f"- {cat}\n"
        else:
            report += "- None identified\n"

        report += "\n### Supporting Evidence\n"
        for ev in ny['supporting_evidence']:
            report += f"- {ev}\n"

        report += f"\n**Notes:** {ny['notes']}\n"

        report += """
---

## Recommended Actions
"""
        for i, action in enumerate(summary['recommended_actions'], 1):
            report += f"{i}. {action}\n"

        report += """
---

## Case Value Summary

| Category | Amount |
|----------|--------|
"""
        report += f"| Total Medical Specials | ${summary['special_damages']['medical_expenses']['total_billed']:,.2f} |\n"
        report += f"| Outstanding Medical Bills | ${summary['special_damages']['medical_expenses']['outstanding']:,.2f} |\n"
        report += f"| Available Coverage | ${summary['insurance_coverage']['total_available_coverage']:,.2f} |\n"

        report += """
---
*This summary was automatically generated from structured JSON extraction via AWS IDP pipeline.*
"""
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Aggregate structured JSON results for PI case')
    parser.add_argument('results_folder', help='Path to AWS results folder')
    parser.add_argument('--output', '-o', help='Output file path', default='case_summary_json')
    args = parser.parse_args()

    aggregator = JSONResultsAggregator(args.results_folder)
    summary = aggregator.generate_summary()

    # Save JSON
    json_path = f"{args.output}.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ JSON summary saved to: {json_path}")

    # Save Markdown
    md_path = f"{args.output}.md"
    md_report = aggregator.generate_markdown_report(summary)
    with open(md_path, 'w') as f:
        f.write(md_report)
    print(f"✓ Markdown report saved to: {md_path}")

    # Print summary stats
    print(f"\nCase Summary:")
    print(f"  Plaintiff: {summary['plaintiff']['name']}")
    print(f"  Accident: {summary['accident']['date']} at {summary['accident']['location']}")
    print(f"  Diagnoses: {len(summary['injuries']['diagnoses'])}")
    print(f"  Medical Specials: ${summary['medical_bills']['total_charges']:,.2f}")
    print(f"  Meets Serious Injury: {'Yes' if summary['ny_serious_injury_analysis']['meets_threshold'] else 'Needs Review'}")

    return summary


if __name__ == "__main__":
    main()
