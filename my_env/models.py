# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Plant Growth RL Environment.

The plant_growth environment simulates plant development under agent control
with realistic agricultural dynamics (biomass, water, nutrients, stress).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PlantAction:
    """Action for the Plant Growth environment - management decisions."""

    irrigation: float = 0.0
    """Irrigation amount (0.0-1.0, fraction of max available water = 50mm/day)"""

    nitrogen_fertilizer: float = 0.0
    """Nitrogen fertilizer application (0.0-1.0, fraction of max = 100 kg/ha)"""

    pruning: float = 0.0
    """Leaf pruning ratio (0.0-1.0, fraction of leaf biomass to remove)"""

    temperature_control: float = 0.0
    """Temperature control (0.0-1.0, fraction of max cooling/heating, 0.5=no change)"""

    def __post_init__(self):
        """Validate action values are in valid range [0.0, 1.0]."""
        for attr in ["irrigation", "nitrogen_fertilizer", "pruning", "temperature_control"]:
            value = getattr(self, attr)
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"{attr} must be in range [0.0, 1.0], got {value}"
                )


@dataclass
class PlantObservation:
    """Observation from the Plant Growth environment - plant state and environmental conditions."""

    # Plant growth metrics
    biomass: float = 0.0
    """Total plant dry matter (g/m²)"""

    leaf_area_index: float = 0.0
    """Leaf Area Index (LAI, dimensionless, typical range 0-8)"""

    plant_height: float = 0.0
    """Plant height (cm)"""

    # Soil conditions
    soil_water: float = 0.0
    """Soil water availability (0.0-1.0, relative to field capacity)"""

    soil_nitrogen: float = 0.0
    """Soil nitrogen availability (0.0-1.0, relative to luxury uptake level)"""

    # Plant development stage
    phenological_stage: int = 0
    """Phenological stage (0=germination, 5=flowering, 10=maturity)"""

    # Stress indices
    water_stress: float = 0.0
    """Water stress level (0.0=no stress, 1.0=severe drought)"""

    nitrogen_stress: float = 0.0
    """Nitrogen stress level (0.0=no stress, 1.0=severe deficiency)"""

    # Plant health and time
    health_index: float = 1.0
    """Plant health index (0.0=dead, 1.0=perfect, accounts for disease/pests)"""

    day_of_simulation: int = 0
    """Current day of simulation (0-89, 90-day episode)"""

    # Environmental conditions
    daily_rainfall: float = 0.0
    """Daily rainfall (mm/day, provided for reference)"""

    # Reward tracking (optional)
    cumulative_reward: float = 0.0
    """Cumulative reward up to current step"""

    # OpenEnv compatibility fields
    done: bool = False
    """Episode termination flag"""

    reward: Optional[float] = None
    """Reward for this step"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata from environment"""

    def __post_init__(self):
        """Validate observation values are in expected ranges."""
        # Validate 0-1 normalized fields
        normalized_fields = {
            "soil_water": self.soil_water,
            "soil_nitrogen": self.soil_nitrogen,
            "water_stress": self.water_stress,
            "nitrogen_stress": self.nitrogen_stress,
            "health_index": self.health_index,
        }
        for field_name, value in normalized_fields.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"{field_name} must be in range [0.0, 1.0], got {value}"
                )

        # Validate day range
        if not (0 <= self.day_of_simulation <= 89):
            raise ValueError(
                f"day_of_simulation must be in range [0, 89], got {self.day_of_simulation}"
            )

        # Validate phenological stage
        if not (0 <= self.phenological_stage <= 10):
            raise ValueError(
                f"phenological_stage must be in range [0, 10], got {self.phenological_stage}"
            )
