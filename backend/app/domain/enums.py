"""Controlled vocabularies from the SAGE PRD (roles, states, categories).

Keeping these as enums makes the governed vocabulary explicit and prevents
free-text drift in decision-critical fields (decision states, veto categories,
evidence tiers).
"""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """User roles (PRD 5)."""

    PROGRAMME_ADMINISTRATOR = "programme_administrator"
    INVESTMENT_GRANT_OFFICER = "investment_grant_officer"
    TECHNICAL_ASSESSOR = "technical_assessor"
    COMMERCIAL_ASSESSOR = "commercial_assessor"
    FINANCIAL_ASSESSOR = "financial_assessor"
    COMMITTEE_MEMBER = "committee_member"
    COMMITTEE_CHAIR = "committee_chair"
    SENIOR_MANAGEMENT = "senior_management"
    APPLICANT_RECIPIENT = "applicant_recipient"
    AUDITOR = "auditor"


class LensType(str, Enum):
    """The four independent evaluation lenses (PRD 1.1, 6)."""

    SAI = "sai"  # Sarawak Allocation Index
    SSAI = "ssai"  # Sarawak Strategic Alignment Index
    SSEI = "ssei"  # Sarawak Sustainability and ESG Index
    EVI = "evi"  # Evidence Veracity Index


class EvidenceState(str, Enum):
    """Evidence veracity tiers (PRD 6.6). Confidence weights live in the
    methodology object; this enum is the label set."""

    INDEPENDENTLY_VERIFIED = "independently_verified"
    CONTRACTUAL_OR_SYSTEM_GENERATED = "contractual_or_system_generated"
    THIRD_PARTY_DOCUMENTED = "third_party_documented"
    APPLICANT_DATA_WITH_SUPPORT = "applicant_data_with_support"
    APPLICANT_DECLARATION_ONLY = "applicant_declaration_only"
    AI_INFERENCE = "ai_inference"
    CONTRADICTED = "contradicted"


class StrategicMaturity(int, Enum):
    """Strategic-alignment maturity levels (PRD 6.3)."""

    THEME_MATCH = 1
    INITIATIVE_MATCH = 2
    OUTCOME_MATCH = 3
    KPI_CONTRIBUTION = 4


class VetoCategory(str, Enum):
    """Non-negotiable veto categories (PRD 10.2)."""

    ELIGIBILITY = "eligibility"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    GOVERNANCE = "governance"
    DELIVERY = "delivery"


class DecisionState(str, Enum):
    """Decision taxonomy (PRD 10.3)."""

    FUND = "fund"
    FUND_WITH_CONDITIONS = "fund_with_conditions"
    DEVELOP = "develop"
    REFER = "refer"
    DEFER = "defer"
    DECLINE = "decline"
    DISQUALIFY = "disqualify"


class ResolutionState(str, Enum):
    """Divergence resolution states (PRD 8.4)."""

    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    OVERRIDDEN = "overridden"
    WITHDRAWN = "withdrawn"


class VerificationStatus(str, Enum):
    """Human verification state of an AI-proposed output (PRD 12.3).

    Every AI output is unverified until a human accepts, edits or rejects it.
    The original AI output is retained regardless (auditable corrections).
    """

    UNVERIFIED = "unverified"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class ApplicationStatus(str, Enum):
    """High-level lifecycle status surfaced to users (PRD 8, acceptance #3)."""

    INGESTED = "ingested"
    UNDER_ASSESSMENT = "under_assessment"
    DIVERGENCE_REVIEW = "divergence_review"
    COMMITTEE = "committee"
    DECIDED = "decided"
    AWARDED = "awarded"
    WITHDRAWN = "withdrawn"


class Band(str, Enum):
    """Qualitative band used by the decision matrix (PRD 6.7)."""

    HIGH = "high"
    LOW = "low"


class EvidenceStrength(str, Enum):
    """Evidence strength band used by the decision matrix (PRD 6.7)."""

    STRONG = "strong"
    WEAK = "weak"
