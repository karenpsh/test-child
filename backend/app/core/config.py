"""Application configuration and the default, versioned methodology constants.

Weights and thresholds here mirror the SAGE PRD (v0.2). Per FRA-006 and
acceptance criterion 11, methodology values are *versioned*: changing a weight
must produce a new methodology version rather than mutating historical
decisions. These defaults are the seed for methodology version ``v0.2``.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, overridable via environment variables (prefix ``SAGE_``)."""

    model_config = SettingsConfigDict(env_prefix="SAGE_", env_file=".env", extra="ignore")

    app_name: str = "SAGE"
    app_description: str = "Sarawak Allocation and Grant Evaluation"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # Default methodology version applied when a programme does not pin one.
    default_methodology_version: str = "v0.2"

    # Individual assessor outlier threshold on a 0-10 scale (PRD 10.1).
    individual_outlier_threshold: float = Field(default=3.0, ge=0, le=10)


settings = Settings()


# --- Seed methodology: SAGE PRD v0.2 --------------------------------------
# These dictionaries are the *default* content of methodology version v0.2.
# The Rules Engine consumes a MethodologyVersion object (see domain.methodology),
# not these constants directly, so a programme can pin an alternative version.

# SAI. Sarawak Allocation Index (PRD 6.1)
SAI_WEIGHTS_V0_2: dict[str, float] = {
    "technical_delivery_credibility": 0.25,
    "commercial_adoption_readiness": 0.20,
    "strategic_programme_fit": 0.15,
    "financial_stewardship": 0.15,
    "execution_capacity": 0.15,
    "public_value_outcomes": 0.10,
}

# SSAI. Sarawak Strategic Alignment Index (PRD 6.2)
SSAI_WEIGHTS_V0_2: dict[str, float] = {
    "blueprint_sector_pillar_alignment": 0.20,
    "digital_economy_contribution": 0.20,
    "sarawak_economic_additionality": 0.15,
    "local_talent_capability_creation": 0.15,
    "rural_inclusive_access": 0.10,
    "research_innovation_commercialisation": 0.10,
    "scalability_within_sarawak": 0.10,
}

# SSEI. Sarawak Sustainability and ESG Index (PRD 6.4). The PRD lists three
# components without fixed weights; equal weighting is the configurable seed.
SSEI_WEIGHTS_V0_2: dict[str, float] = {
    "enterprise_esg": 1 / 3,
    "solution_impact": 1 / 3,
    "impact_integrity": 1 / 3,
}
