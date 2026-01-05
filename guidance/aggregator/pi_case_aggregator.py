#!/usr/bin/env python3
"""
NY Personal Injury Case Summary Aggregator

This script aggregates extracted document data from the IDP pipeline
and generates a comprehensive case summary report for PI litigation.

Usage:
    python pi_case_aggregator.py <case_folder_path> [--output <output_path>]

Example:
    python pi_case_aggregator.py ./sample_files/pi_case_001/output --output case_summary.json
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class CaseSummary:
    """Main case summary structure"""
    case_id: str
    generated_date: str
    plaintiff: Dict[str, Any]
    defendant: Dict[str, Any]
    accident: Dict[str, Any]
    injuries: Dict[str, Any]
    treatment_timeline: List[Dict[str, Any]]
    medical_providers: List[Dict[str, Any]]
    special_damages: Dict[str, Any]
    insurance_coverage: Dict[str, Any]
    liability_analysis: Dict[str, Any]
    ny_serious_injury_analysis: Dict[str, Any]
    case_value_factors: Dict[str, Any]
    recommended_actions: List[str]


class PICaseAggregator:
    """Aggregates PI case data from IDP extracted documents"""

    def __init__(self, case_folder: str):
        self.case_folder = Path(case_folder)
        self.medical_records: List[Dict] = []
        self.police_reports: List[Dict] = []
        self.insurance_policies: List[Dict] = []
        self.medical_bills: List[Dict] = []

    def load_documents(self) -> None:
        """Load all extracted JSON documents from case folder"""

        # Load medical records
        med_records_path = self.case_folder / "MEDICAL_RECORDS"
        if med_records_path.exists():
            for file in med_records_path.glob("*.json"):
                with open(file) as f:
                    self.medical_records.append(json.load(f))

        # Load police reports
        police_path = self.case_folder / "POLICE_REPORT"
        if police_path.exists():
            for file in police_path.glob("*.json"):
                with open(file) as f:
                    self.police_reports.append(json.load(f))

        # Load insurance policies
        insurance_path = self.case_folder / "INSURANCE_POLICY"
        if insurance_path.exists():
            for file in insurance_path.glob("*.json"):
                with open(file) as f:
                    self.insurance_policies.append(json.load(f))

        # Load medical bills
        bills_path = self.case_folder / "MEDICAL_BILLS"
        if bills_path.exists():
            for file in bills_path.glob("*.json"):
                with open(file) as f:
                    self.medical_bills.append(json.load(f))

    def extract_plaintiff_info(self) -> Dict[str, Any]:
        """Extract plaintiff information from documents"""
        plaintiff = {
            "name": "",
            "date_of_birth": "",
            "age_at_accident": 0,
            "address": "",
            "phone": ""
        }

        # Get from medical records
        if self.medical_records:
            patient = self.medical_records[0].get("patient_info", {})
            plaintiff["name"] = patient.get("name", "")
            plaintiff["date_of_birth"] = patient.get("date_of_birth", "")
            plaintiff["age_at_accident"] = patient.get("age_at_visit", 0)

        # Get address from police report
        if self.police_reports:
            for driver in self.police_reports[0].get("drivers", []):
                if driver.get("vehicle_number") == 1:
                    plaintiff["address"] = driver.get("address", "")
                    plaintiff["phone"] = driver.get("phone", "")

        return plaintiff

    def extract_defendant_info(self) -> Dict[str, Any]:
        """Extract defendant information from documents"""
        defendant = {
            "driver_name": "",
            "driver_address": "",
            "driver_phone": "",
            "employer": "",
            "employer_address": "",
            "vehicle": {},
            "insurance": {}
        }

        if self.police_reports:
            report = self.police_reports[0]

            # Get defendant driver info
            for driver in report.get("drivers", []):
                if driver.get("vehicle_number") == 2:
                    defendant["driver_name"] = driver.get("name", "")
                    defendant["driver_address"] = driver.get("address", "")
                    defendant["driver_phone"] = driver.get("phone", "")

            # Get defendant vehicle info
            for vehicle in report.get("vehicles", []):
                if vehicle.get("vehicle_number") == 2:
                    defendant["vehicle"] = {
                        "year": vehicle.get("year", ""),
                        "make": vehicle.get("make", ""),
                        "model": vehicle.get("model", ""),
                        "plate": vehicle.get("license_plate", "")
                    }
                    owner = vehicle.get("registered_owner", {})
                    defendant["employer"] = owner.get("name", "")
                    defendant["employer_address"] = owner.get("address", "")

        # Get defendant insurance from policies
        for policy in self.insurance_policies:
            if "Commercial" in policy.get("policy_info", {}).get("policy_type", ""):
                defendant["insurance"] = {
                    "company": policy["policy_info"].get("insurance_company", ""),
                    "policy_number": policy["policy_info"].get("policy_number", ""),
                    "claim_number": policy.get("claims_info", {}).get("claim_number", ""),
                    "bi_limits": {
                        "per_person": policy.get("coverages", {}).get("bodily_injury_liability", {}).get("per_person", 0),
                        "per_accident": policy.get("coverages", {}).get("bodily_injury_liability", {}).get("per_accident", 0)
                    }
                }

        return defendant

    def extract_accident_info(self) -> Dict[str, Any]:
        """Extract accident information from police report"""
        accident = {
            "date": "",
            "time": "",
            "location": "",
            "borough": "",
            "weather": "",
            "road_conditions": "",
            "description": "",
            "police_report_number": "",
            "precinct": ""
        }

        if self.police_reports:
            report = self.police_reports[0]
            accident_details = report.get("accident_details", {})
            location = accident_details.get("location", {})

            accident["date"] = accident_details.get("date", "")
            accident["time"] = accident_details.get("time", "")
            accident["location"] = f"{location.get('street_address', '')} at {location.get('cross_street', '')}"
            accident["borough"] = location.get("borough", "")
            accident["weather"] = accident_details.get("weather_conditions", "")
            accident["road_conditions"] = accident_details.get("road_conditions", "")
            accident["description"] = report.get("narrative", "")
            accident["police_report_number"] = report.get("report_info", {}).get("report_number", "")
            accident["precinct"] = report.get("report_info", {}).get("precinct", "")

        return accident

    def extract_injuries(self) -> Dict[str, Any]:
        """Consolidate all injuries from medical records"""
        injuries = {
            "primary_diagnoses": [],
            "all_diagnoses": [],
            "icd_codes": [],
            "body_parts_affected": [],
            "injury_summary": ""
        }

        all_diagnoses = []
        icd_codes = set()
        body_parts = set()

        for record in self.medical_records:
            for diagnosis in record.get("diagnoses", []):
                diag_entry = {
                    "description": diagnosis.get("description", ""),
                    "icd_code": diagnosis.get("icd_code", ""),
                    "body_part": diagnosis.get("body_part", ""),
                    "is_primary": diagnosis.get("is_primary", False)
                }
                all_diagnoses.append(diag_entry)

                if diagnosis.get("icd_code"):
                    icd_codes.add(diagnosis["icd_code"])
                if diagnosis.get("body_part"):
                    body_parts.add(diagnosis["body_part"])

                if diagnosis.get("is_primary"):
                    injuries["primary_diagnoses"].append(diag_entry)

        injuries["all_diagnoses"] = all_diagnoses
        injuries["icd_codes"] = list(icd_codes)
        injuries["body_parts_affected"] = list(body_parts)

        # Generate injury summary
        if injuries["primary_diagnoses"]:
            primary_list = [d["description"] for d in injuries["primary_diagnoses"]]
            injuries["injury_summary"] = f"Primary injuries: {'; '.join(primary_list)}"

        return injuries

    def build_treatment_timeline(self) -> List[Dict[str, Any]]:
        """Build chronological treatment timeline"""
        timeline = []

        # From medical records
        for record in self.medical_records:
            entry = {
                "date": record.get("document_info", {}).get("date_of_service", ""),
                "provider": record.get("document_info", {}).get("facility_name", ""),
                "type": record.get("document_info", {}).get("record_type", ""),
                "chief_complaint": record.get("chief_complaint", ""),
                "treatments": [t.get("description", "") for t in record.get("treatment_provided", [])],
                "referrals": [r.get("specialty", "") for r in record.get("referrals", [])]
            }
            timeline.append(entry)

        # Sort by date
        timeline.sort(key=lambda x: x.get("date", ""))

        return timeline

    def extract_medical_providers(self) -> List[Dict[str, Any]]:
        """Extract all medical provider information"""
        providers = []
        seen_providers = set()

        for record in self.medical_records:
            doc_info = record.get("document_info", {})
            provider_name = doc_info.get("facility_name", "")

            if provider_name and provider_name not in seen_providers:
                seen_providers.add(provider_name)
                providers.append({
                    "name": provider_name,
                    "address": doc_info.get("facility_address", ""),
                    "phone": doc_info.get("facility_phone", ""),
                    "type": doc_info.get("record_type", ""),
                    "treating_physician": record.get("provider_info", {}).get("name", "")
                })

        for bill in self.medical_bills:
            provider_name = bill.get("billing_provider", {}).get("name", "")
            if provider_name and provider_name not in seen_providers:
                seen_providers.add(provider_name)
                bp = bill.get("billing_provider", {})
                providers.append({
                    "name": provider_name,
                    "address": bp.get("address", ""),
                    "phone": bp.get("phone", ""),
                    "type": bp.get("provider_type", ""),
                    "npi": bp.get("npi", "")
                })

        return providers

    def calculate_special_damages(self) -> Dict[str, Any]:
        """Calculate total special damages from medical bills"""
        specials = {
            "total_medical_charges": 0,
            "total_paid_by_no_fault": 0,
            "total_paid_by_health_insurance": 0,
            "total_adjustments": 0,
            "total_outstanding_balance": 0,
            "total_liens": 0,
            "no_fault_exhausted": False,
            "no_fault_remaining": 50000,  # NY Basic PIP
            "breakdown_by_provider": [],
            "breakdown_by_category": defaultdict(float)
        }

        for bill in self.medical_bills:
            summary = bill.get("billing_summary", {})
            lien = bill.get("lien_info", {})
            treatment = bill.get("treatment_summary", {})

            provider_total = summary.get("total_charges", 0)
            specials["total_medical_charges"] += provider_total
            specials["total_adjustments"] += summary.get("total_adjustments", 0)
            specials["total_outstanding_balance"] += summary.get("balance_due", 0)

            # Track payments
            for payment in bill.get("payments_received", []):
                if "No-Fault" in payment.get("payment_type", ""):
                    specials["total_paid_by_no_fault"] += payment.get("amount", 0)
                elif "Health" in payment.get("payer", ""):
                    specials["total_paid_by_health_insurance"] += payment.get("amount", 0)

            # Track liens
            if lien.get("lien_filed"):
                specials["total_liens"] += lien.get("lien_amount", 0)

            # Provider breakdown
            specials["breakdown_by_provider"].append({
                "provider": bill.get("billing_provider", {}).get("name", ""),
                "total_charges": provider_total,
                "balance_due": summary.get("balance_due", 0),
                "lien_amount": lien.get("lien_amount", 0) if lien.get("lien_filed") else 0
            })

            # Category breakdown
            for category, amount in treatment.items():
                if amount and isinstance(amount, (int, float)) and amount > 0:
                    clean_category = category.replace("_charges", "").replace("_", " ").title()
                    specials["breakdown_by_category"][clean_category] += amount

        # Calculate No-Fault remaining
        specials["no_fault_remaining"] = max(0, 50000 - specials["total_paid_by_no_fault"])
        specials["no_fault_exhausted"] = specials["no_fault_remaining"] == 0

        # Convert defaultdict to regular dict
        specials["breakdown_by_category"] = dict(specials["breakdown_by_category"])

        return specials

    def analyze_insurance_coverage(self) -> Dict[str, Any]:
        """Analyze available insurance coverage"""
        coverage = {
            "plaintiff_coverage": {},
            "defendant_coverage": {},
            "total_available_coverage": 0,
            "coverage_analysis": ""
        }

        for policy in self.insurance_policies:
            policy_type = policy.get("policy_info", {}).get("policy_type", "")
            insured = policy.get("named_insured", {}).get("name", "")
            coverages = policy.get("coverages", {})

            if "Personal" in policy_type:
                # Plaintiff's policy
                coverage["plaintiff_coverage"] = {
                    "company": policy["policy_info"].get("insurance_company", ""),
                    "policy_number": policy["policy_info"].get("policy_number", ""),
                    "no_fault_pip": coverages.get("personal_injury_protection_no_fault", {}).get("basic_pip", 0),
                    "obel": coverages.get("personal_injury_protection_no_fault", {}).get("obel", 0),
                    "sum_per_person": coverages.get("underinsured_motorist_sum", {}).get("per_person", 0),
                    "sum_per_accident": coverages.get("underinsured_motorist_sum", {}).get("per_accident", 0)
                }
            elif "Commercial" in policy_type:
                # Defendant's policy
                coverage["defendant_coverage"] = {
                    "company": policy["policy_info"].get("insurance_company", ""),
                    "policy_number": policy["policy_info"].get("policy_number", ""),
                    "bi_per_person": coverages.get("bodily_injury_liability", {}).get("per_person", 0),
                    "bi_per_accident": coverages.get("bodily_injury_liability", {}).get("per_accident", 0)
                }

        # Calculate total available
        def_bi = coverage.get("defendant_coverage", {}).get("bi_per_person", 0)
        plt_sum = coverage.get("plaintiff_coverage", {}).get("sum_per_person", 0)

        coverage["total_available_coverage"] = def_bi + plt_sum

        # Generate analysis
        if def_bi >= plt_sum:
            coverage["coverage_analysis"] = f"Defendant's BI limits (${def_bi:,}) exceed plaintiff's SUM. No SUM claim available."
        else:
            sum_available = plt_sum - def_bi
            coverage["coverage_analysis"] = f"Potential SUM claim of ${sum_available:,} if defendant's policy is exhausted."

        return coverage

    def analyze_liability(self) -> Dict[str, Any]:
        """Analyze liability based on police report"""
        liability = {
            "fault_determination": "",
            "contributing_factors": [],
            "violations_cited": [],
            "witness_statements": [],
            "liability_assessment": "",
            "comparative_fault_risk": "Low"
        }

        if self.police_reports:
            report = self.police_reports[0]
            fault = report.get("fault_indicators", {})

            liability["fault_determination"] = fault.get("fault_determination", "")
            liability["contributing_factors"] = fault.get("contributing_factors", [])
            liability["violations_cited"] = fault.get("violations_cited", [])

            # Witness statements
            for witness in report.get("witnesses", []):
                liability["witness_statements"].append({
                    "name": witness.get("name", ""),
                    "summary": witness.get("statement_summary", "")
                })

            # Generate liability assessment
            if liability["violations_cited"]:
                violations = [v.get("description", "") for v in liability["violations_cited"]]
                liability["liability_assessment"] = f"Strong liability case. Defendant cited for: {', '.join(violations)}. "

            if liability["witness_statements"]:
                liability["liability_assessment"] += f"{len(liability['witness_statements'])} independent witness(es) support plaintiff's version."

            # Assess comparative fault risk
            if fault.get("fault_determination") == "Driver 2":
                liability["comparative_fault_risk"] = "Low"
            elif "Shared" in str(fault.get("fault_determination", "")):
                liability["comparative_fault_risk"] = "High"

        return liability

    def analyze_ny_serious_injury(self) -> Dict[str, Any]:
        """Analyze NY serious injury threshold under Insurance Law 5102(d)"""
        analysis = {
            "meets_threshold": False,
            "categories_met": [],
            "supporting_evidence": [],
            "strength_assessment": "",
            "risk_factors": []
        }

        categories_found = set()
        evidence = []

        for record in self.medical_records:
            indicators = record.get("ny_serious_injury_indicators", {})

            if indicators.get("permanent_consequential_limitation"):
                categories_found.add("Permanent Consequential Limitation")
            if indicators.get("significant_limitation_of_use"):
                categories_found.add("Significant Limitation of Use")
            if indicators.get("permanent_loss_of_use"):
                categories_found.add("Permanent Loss of Use")
            if indicators.get("fracture"):
                categories_found.add("Fracture")
            if indicators.get("significant_disfigurement"):
                categories_found.add("Significant Disfigurement")
            if indicators.get("ninety_one_eighty_disability"):
                categories_found.add("90/180 Day Disability")

            for lang in indicators.get("supporting_language", []):
                evidence.append(lang)

        analysis["categories_met"] = list(categories_found)
        analysis["supporting_evidence"] = evidence
        analysis["meets_threshold"] = len(categories_found) > 0

        # Strength assessment
        if "Permanent Consequential Limitation" in categories_found or "Permanent Loss of Use" in categories_found:
            analysis["strength_assessment"] = "Strong - Permanent limitation documented"
        elif "Significant Limitation of Use" in categories_found:
            analysis["strength_assessment"] = "Moderate-Strong - Significant limitation with objective findings"
        elif "90/180 Day Disability" in categories_found:
            analysis["strength_assessment"] = "Moderate - Must document 90 days disability in first 180 days"
        else:
            analysis["strength_assessment"] = "Weak - May not meet serious injury threshold"
            analysis["risk_factors"].append("Limited objective findings documented")

        return analysis

    def assess_case_value_factors(self) -> Dict[str, Any]:
        """Assess factors affecting case value"""
        factors = {
            "positive_factors": [],
            "negative_factors": [],
            "value_multipliers": [],
            "special_damages_total": 0,
            "estimated_value_range": {}
        }

        specials = self.calculate_special_damages()
        factors["special_damages_total"] = specials["total_medical_charges"]

        # Positive factors
        liability = self.analyze_liability()
        if liability.get("comparative_fault_risk") == "Low":
            factors["positive_factors"].append("Clear liability - defendant 100% at fault")
        if liability.get("violations_cited"):
            factors["positive_factors"].append("Traffic violations cited against defendant")
        if len(liability.get("witness_statements", [])) >= 2:
            factors["positive_factors"].append("Multiple independent witnesses")

        serious_injury = self.analyze_ny_serious_injury()
        if "Permanent" in str(serious_injury.get("categories_met", [])):
            factors["positive_factors"].append("Permanent injury documented")
            factors["value_multipliers"].append("Permanent injury multiplier: 3-5x specials")

        # Check for objective findings
        for record in self.medical_records:
            if record.get("imaging_findings"):
                for finding in record["imaging_findings"]:
                    if "herniation" in finding.get("findings", "").lower():
                        factors["positive_factors"].append("MRI-confirmed disc herniation")
                        factors["value_multipliers"].append("Disc herniation multiplier: 2-4x specials")
                        break

        # Negative factors
        if specials.get("no_fault_exhausted"):
            factors["negative_factors"].append("No-fault benefits exhausted")
        if serious_injury.get("strength_assessment", "").startswith("Weak"):
            factors["negative_factors"].append("Serious injury threshold may be challenged")

        # Estimate value range
        base = factors["special_damages_total"]
        if "Permanent" in str(serious_injury.get("categories_met", [])):
            factors["estimated_value_range"] = {
                "low": base * 2,
                "mid": base * 3.5,
                "high": base * 5
            }
        else:
            factors["estimated_value_range"] = {
                "low": base * 1.5,
                "mid": base * 2.5,
                "high": base * 3.5
            }

        return factors

    def generate_recommended_actions(self) -> List[str]:
        """Generate recommended next actions for the case"""
        actions = []

        # Check No-Fault status
        specials = self.calculate_special_damages()
        if specials["no_fault_remaining"] < 10000:
            actions.append("URGENT: No-Fault benefits nearly exhausted. Consider filing NF-10 denial appeal or transition to health insurance.")

        # Check statute of limitations
        if self.police_reports:
            accident_date_str = self.police_reports[0].get("accident_details", {}).get("date", "")
            if accident_date_str:
                try:
                    accident_date = datetime.strptime(accident_date_str, "%m/%d/%Y")
                    sol_date = accident_date + timedelta(days=365*3)
                    days_remaining = (sol_date - datetime.now()).days
                    if days_remaining < 180:
                        actions.append(f"URGENT: Statute of limitations expires in {days_remaining} days ({sol_date.strftime('%m/%d/%Y')})")
                    elif days_remaining < 365:
                        actions.append(f"NOTE: Statute of limitations expires in {days_remaining} days ({sol_date.strftime('%m/%d/%Y')})")
                except ValueError:
                    pass

        # Treatment recommendations
        serious_injury = self.analyze_ny_serious_injury()
        if "90/180 Day Disability" in serious_injury.get("categories_met", []) and \
           "Permanent" not in str(serious_injury.get("categories_met", [])):
            actions.append("Obtain narrative report documenting 90/180 day disability with specific activity limitations")

        if serious_injury.get("strength_assessment", "").startswith("Moderate"):
            actions.append("Request updated narrative report with permanency opinion from treating physician")

        # Insurance actions
        coverage = self.analyze_insurance_coverage()
        def_limits = coverage.get("defendant_coverage", {}).get("bi_per_person", 0)
        if def_limits > 0:
            actions.append(f"Send policy limits demand to defendant's carrier (${def_limits:,} available)")

        # Medical records
        actions.append("Request updated records from all treating providers")
        actions.append("Obtain final bills with No-Fault payments and balances due")

        # Liens
        if specials["total_liens"] > 0:
            actions.append(f"Negotiate medical liens totaling ${specials['total_liens']:,.2f}")

        return actions

    def generate_summary(self) -> CaseSummary:
        """Generate complete case summary"""
        self.load_documents()

        case_id = self.case_folder.name

        summary = CaseSummary(
            case_id=case_id,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            plaintiff=self.extract_plaintiff_info(),
            defendant=self.extract_defendant_info(),
            accident=self.extract_accident_info(),
            injuries=self.extract_injuries(),
            treatment_timeline=self.build_treatment_timeline(),
            medical_providers=self.extract_medical_providers(),
            special_damages=self.calculate_special_damages(),
            insurance_coverage=self.analyze_insurance_coverage(),
            liability_analysis=self.analyze_liability(),
            ny_serious_injury_analysis=self.analyze_ny_serious_injury(),
            case_value_factors=self.assess_case_value_factors(),
            recommended_actions=self.generate_recommended_actions()
        )

        return summary

    def generate_report(self, output_format: str = "json") -> str:
        """Generate formatted report"""
        summary = self.generate_summary()

        if output_format == "json":
            return json.dumps(asdict(summary), indent=2, default=str)
        elif output_format == "markdown":
            return self._format_markdown(summary)
        elif output_format == "html":
            return self._format_html(summary)
        else:
            return json.dumps(asdict(summary), indent=2, default=str)

    def _format_markdown(self, summary: CaseSummary) -> str:
        """Format summary as Markdown"""
        md = []
        md.append(f"# Case Summary: {summary.case_id}")
        md.append(f"*Generated: {summary.generated_date}*\n")

        md.append("## Plaintiff Information")
        md.append(f"- **Name:** {summary.plaintiff['name']}")
        md.append(f"- **DOB:** {summary.plaintiff['date_of_birth']}")
        md.append(f"- **Age at Accident:** {summary.plaintiff['age_at_accident']}")
        md.append(f"- **Address:** {summary.plaintiff['address']}\n")

        md.append("## Defendant Information")
        md.append(f"- **Driver:** {summary.defendant['driver_name']}")
        md.append(f"- **Employer:** {summary.defendant['employer']}")
        md.append(f"- **Vehicle:** {summary.defendant['vehicle'].get('year', '')} {summary.defendant['vehicle'].get('make', '')} {summary.defendant['vehicle'].get('model', '')}")
        ins = summary.defendant.get('insurance', {})
        md.append(f"- **Insurance:** {ins.get('company', '')} - Limits: ${ins.get('bi_limits', {}).get('per_person', 0):,}/{ins.get('bi_limits', {}).get('per_accident', 0):,}\n")

        md.append("## Accident Details")
        md.append(f"- **Date:** {summary.accident['date']} at {summary.accident['time']}")
        md.append(f"- **Location:** {summary.accident['location']}, {summary.accident['borough']}")
        md.append(f"- **Report #:** {summary.accident['police_report_number']}")
        md.append(f"- **Description:** {summary.accident['description'][:500]}...\n")

        md.append("## Injuries")
        md.append("### Primary Diagnoses")
        for diag in summary.injuries['primary_diagnoses']:
            md.append(f"- {diag['description']} ({diag['icd_code']})")
        md.append(f"\n**Body Parts Affected:** {', '.join(summary.injuries['body_parts_affected'])}\n")

        md.append("## Special Damages")
        sd = summary.special_damages
        md.append(f"| Category | Amount |")
        md.append(f"|----------|--------|")
        md.append(f"| Total Medical Charges | ${sd['total_medical_charges']:,.2f} |")
        md.append(f"| Paid by No-Fault | ${sd['total_paid_by_no_fault']:,.2f} |")
        md.append(f"| Adjustments | ${sd['total_adjustments']:,.2f} |")
        md.append(f"| Outstanding Balance | ${sd['total_outstanding_balance']:,.2f} |")
        md.append(f"| Total Liens | ${sd['total_liens']:,.2f} |")
        md.append(f"| No-Fault Remaining | ${sd['no_fault_remaining']:,.2f} |")
        md.append("")

        md.append("## NY Serious Injury Analysis")
        si = summary.ny_serious_injury_analysis
        md.append(f"**Meets Threshold:** {'Yes' if si['meets_threshold'] else 'No'}")
        md.append(f"**Categories Met:** {', '.join(si['categories_met']) if si['categories_met'] else 'None'}")
        md.append(f"**Strength:** {si['strength_assessment']}\n")

        md.append("### Supporting Evidence")
        for evidence in si['supporting_evidence'][:5]:
            md.append(f"- {evidence}")
        md.append("")

        md.append("## Liability Analysis")
        la = summary.liability_analysis
        md.append(f"**Fault Determination:** {la['fault_determination']}")
        md.append(f"**Comparative Fault Risk:** {la['comparative_fault_risk']}")
        md.append(f"**Assessment:** {la['liability_assessment']}\n")

        md.append("## Case Value Assessment")
        cvf = summary.case_value_factors
        md.append(f"**Special Damages:** ${cvf['special_damages_total']:,.2f}")
        md.append(f"\n**Estimated Value Range:**")
        evr = cvf['estimated_value_range']
        md.append(f"- Low: ${evr.get('low', 0):,.2f}")
        md.append(f"- Mid: ${evr.get('mid', 0):,.2f}")
        md.append(f"- High: ${evr.get('high', 0):,.2f}")
        md.append(f"\n**Positive Factors:**")
        for factor in cvf['positive_factors']:
            md.append(f"- {factor}")
        if cvf['negative_factors']:
            md.append(f"\n**Negative Factors:**")
            for factor in cvf['negative_factors']:
                md.append(f"- {factor}")
        md.append("")

        md.append("## Recommended Actions")
        for i, action in enumerate(summary.recommended_actions, 1):
            md.append(f"{i}. {action}")

        return "\n".join(md)

    def _format_html(self, summary: CaseSummary) -> str:
        """Format summary as HTML"""
        md_content = self._format_markdown(summary)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Case Summary - {summary.case_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        .urgent {{ color: #e74c3c; font-weight: bold; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        pre {{ background: #f4f4f4; padding: 15px; overflow-x: auto; }}
    </style>
</head>
<body>
<pre>{md_content}</pre>
</body>
</html>"""
        return html


def main():
    parser = argparse.ArgumentParser(description="NY Personal Injury Case Aggregator")
    parser.add_argument("case_folder", help="Path to case output folder")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", "-f", choices=["json", "markdown", "html"],
                       default="json", help="Output format")

    args = parser.parse_args()

    if not os.path.exists(args.case_folder):
        print(f"Error: Case folder not found: {args.case_folder}")
        sys.exit(1)

    aggregator = PICaseAggregator(args.case_folder)
    report = aggregator.generate_report(args.format)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
