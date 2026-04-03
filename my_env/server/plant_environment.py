# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Plant Growth Environment Implementation.

A mechanistic plant growth model integrating carbon allocation,
nutrient uptake, and abiotic factors.
"""

import math
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import PlantAction, PlantObservation
except ImportError:
    import sys
    import os
    # Add the my_env directory to path for direct execution
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from models import PlantAction, PlantObservation


class PlantEnvironment(Environment):
    """
    Plant Growth Environment simulating daily development.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the plant environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        # Model parameters
        self.A_max = 15.0       # g C m-2 d-1 (Maximum photosynthetic capacity)
        self.k_ext = 0.6        # dimensionless (Light extinction coefficient)
        self.K_U = 300.0        # umol m-2 s-1 (Half-saturation irradiance)
        self.C_ell = 1.5e-6     # specific leaf area coeff for LAI
        self.f_g = 0.5          # growth vs storage allocation fraction
        self.k_g = 0.05         # d-1 (First-order growth mobilization rate)
        self.r_m = 0.015        # d-1 (Maintenance respiration coefficient)
        self.alpha = 0.75       # dimensionless (Growth efficiency)
        self.delta = 0.005      # d-1 (Senescence/turnover rate)
        
        # Nitrogen uptake parameters (Michaelis-Menten)
        self.I_max = 0.1        # Max uptake rate
        self.K_m = 0.2          # Half-saturation constant
        
        # Define simulation length
        self.max_days = 90
        
        self._reset_environment()

    def _reset_environment(self):
        """Reset internal plant and soil state."""
        # Plant state - start larger to avoid death by vanishing initial LAI (C_p^3 dependency)
        self.C_s = 20.0         # Initial storage carbon (g C m-2)
        self.C_p = 80.0         # Initial structural carbon (g C m-2)
        self.phenological_stage = 0
        self.health_index = 1.0
        
        # Soil state
        self.W_soil = 0.5       # Soil water fraction [0, 1]
        self.N_soil = 0.5       # Soil nitrogen availability [0, 1]
        
        # Tracking
        self.cumulative_reward = 0.0
        
    def reset(self) -> PlantObservation:
        """
        Reset the environment for a new episode.
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_environment()
        
        return self._get_observation(reward=0.0, done=False)

    def _get_weather(self, day: int):
        """Sine-based seasonal/daily weather generator."""
        # Sunlight (U) in umol photons m-2 s-1
        # Following a gentle seasonal sine-curve peaking at day 45
        season_phase = math.pi * (day / max(1, self.max_days - 1))
        # Base sunlight 500, max 2000
        U = 500.0 + 1500.0 * max(0.0, math.sin(season_phase))
        
        # Temperature (C). Impacts respiration and health.
        T_base = 15.0
        T_amp = 15.0
        T_day = T_base + T_amp * math.sin(season_phase)
        
        # Rainfall (mm/day)
        # Random bursty rainfall or sine generated base. Using simple abstract setup
        rainfall = 5.0 * max(0.0, math.sin(season_phase * 3.0)) # waves of rain
        
        return U, T_day, rainfall

    def step(self, action: PlantAction) -> PlantObservation:
        """
        Execute one day of plant growth.
        """
        day = self._state.step_count
        done = day >= (self.max_days - 1)
        
        # 1. Weather and Environmental conditions
        U, T_day, rainfall = self._get_weather(day)
        
        # Apply actions
        # Irrigation adds to soil water
        self.W_soil = min(1.0, self.W_soil + action.irrigation * 0.5 + rainfall * 0.01)
        # Fertilizer adds to soil N
        self.N_soil = min(1.0, self.N_soil + action.nitrogen_fertilizer * 0.5)
        # Pruning removes structural carbon
        if action.pruning > 0:
            self.C_p *= (1.0 - action.pruning)
        # Temp control
        T_effective = T_day + (action.temperature_control - 0.5) * 10.0
        
        # Natural soil depletion (evaporation, leaching)
        self.W_soil = max(0.0, self.W_soil - 0.05)
        self.N_soil = max(0.0, self.N_soil - 0.02)
        
        # 2. Plant Status
        LAI = min(8.0, self.C_ell * (self.C_p ** 3))
        plant_height = min(300.0, self.C_p * 0.5) # approximate correlation
        
        # Nitrogen Uptake (Michaelis-Menten)
        # We model this as a stress multiplier [0, 1]
        U_N = (self.I_max * self.N_soil) / (self.K_m + self.N_soil)
        nitrogen_factor = min(1.0, U_N / (self.I_max / (self.K_m + 1.0)))
        nitrogen_stress = 1.0 - nitrogen_factor
        
        # Water Stress
        water_factor = min(1.0, self.W_soil / 0.3) if self.W_soil < 0.3 else 1.0 # Stress below 0.3
        water_stress = 1.0 - water_factor
        
        # Temperature Stress
        # Ideal temp around 25C
        temp_stress = min(1.0, max(0.0, abs(T_effective - 25.0) / 15.0))
        
        # 3. Carbon Assimilation (A)
        # A(t) = A_max * (1 - e^(-k LAI)) * (U / (K_U + U))
        assimilation_potential = self.A_max * (1.0 - math.exp(-self.k_ext * LAI)) * (U / (self.K_U + U))
        # Stresses reduce assimilation
        A = assimilation_potential * water_factor * nitrogen_factor * (1.0 - temp_stress * 0.5)
        
        # 4. Carbon Allocation
        G = self.f_g * A
        S = (1.0 - self.f_g) * A
        
        # 5. Storage Carbon Dynamics
        # Respiration increases with high temperature
        rm_effective = self.r_m * (1.0 + max(0.0, (T_effective - 25.0) * 0.05))
        R_m = rm_effective * self.C_p
        
        dC_s = S - self.k_g * self.C_s - R_m
        
        # 6. Structural Carbon Dynamics
        dC_p = self.alpha * self.k_g * self.C_s - self.delta * self.C_p
        
        # Integration step (dt = 1 day)
        self.C_s = max(0.0, self.C_s + dC_s)
        self.C_p = max(0.1, self.C_p + dC_p)
        
        # Plant takes up water and N -> reduce pools based on growth
        self.W_soil = max(0.0, self.W_soil - water_factor * 0.02 * LAI)
        self.N_soil = max(0.0, self.N_soil - nitrogen_factor * 0.01 * dC_p)
        
        # Health index updates based on extreme stresses
        total_stress = water_stress + nitrogen_stress + temp_stress
        if total_stress > 1.5:
            self.health_index = max(0.0, self.health_index - 0.05)
        else:
            self.health_index = min(1.0, self.health_index + 0.02)
            
        # Phenological stage progression
        self.phenological_stage = min(10, int(10 * (day / self.max_days)))
        
        # Reward calculation: Net structural growth minus resource costs
        growth_reward = dC_p * 0.1
        resource_cost = (action.irrigation * 0.02 + action.nitrogen_fertilizer * 0.05 + abs(action.temperature_control - 0.5) * 0.02)
        health_penalty = (1.0 - self.health_index) * 0.5
        
        reward = growth_reward - resource_cost - health_penalty
        self.cumulative_reward += reward
        
        self._state.step_count += 1
        
        obs_reward = reward if not done else reward + (self.C_p * 0.01) # Final bonus
        
        obs = self._get_observation(reward=obs_reward, done=done)
        obs.daily_rainfall = rainfall
        obs.metadata = {
            "temperature": T_effective,
            "sunlight": U,
            "assimilation": A,
            "dC_p": dC_p,
            "dC_s": dC_s,
            "growth_reward": growth_reward,
            "health_reward": -health_penalty,
            "efficiency_reward": -resource_cost,
        }
        
        return obs

    def _get_observation(self, reward: float, done: bool) -> PlantObservation:
        # Re-calc derived properties for the Observation schema
        LAI = min(8.0, max(0.0, self.C_ell * (self.C_p ** 3)))
        plant_height = self.C_p * 0.5
        
        # Stresses
        U_N = (self.I_max * self.N_soil) / (self.K_m + self.N_soil)
        nitrogen_factor = min(1.0, U_N / (self.I_max / (self.K_m + 1.0)))
        nitrogen_stress = max(0.0, min(1.0, 1.0 - nitrogen_factor))
        
        water_factor = min(1.0, self.W_soil / 0.3) if self.W_soil < 0.3 else 1.0
        water_stress = max(0.0, min(1.0, 1.0 - water_factor))
        
        return PlantObservation(
            biomass=float(self.C_p + self.C_s),
            leaf_area_index=float(LAI),
            plant_height=float(plant_height),
            soil_water=float(max(0.0, min(1.0, self.W_soil))),
            soil_nitrogen=float(max(0.0, min(1.0, self.N_soil))),
            phenological_stage=int(self.phenological_stage),
            water_stress=float(water_stress),
            nitrogen_stress=float(nitrogen_stress),
            health_index=float(max(0.0, min(1.0, self.health_index))),
            day_of_simulation=int(self._state.step_count),
            daily_rainfall=0.0, # Filled in caller
            cumulative_reward=float(self.cumulative_reward),
            done=done,
            reward=float(reward),
            metadata={} # Filled in caller
        )

    @property
    def state(self) -> State:
        """Get the current environment state."""
        return self._state

if __name__ == "__main__":
    env = PlantEnvironment()
    obs = env.reset()
    for _ in range(90):
        # Apply standard optimal action
        action = PlantAction(irrigation=0.5, nitrogen_fertilizer=0.5, pruning=0.0, temperature_control=0.5)
        obs = env.step(action)
        print(f"Day {obs.day_of_simulation}: Bio={obs.biomass:.2f}, LAI={obs.leaf_area_index:.2f}, W_soil={obs.soil_water:.2f}, reward={obs.reward:.2f}")
