# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Plant Growth Environment Client."""

from typing import Dict, Optional

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import PlantAction, PlantObservation


class PlantEnv(EnvClient[PlantAction, PlantObservation, State]):
    """
    Client for the Plant Growth RL Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency for plant growth simulations.
    Each client instance has its own dedicated environment session on the server.

    The environment simulates realistic plant development under agent control over a 90-day
    episode. The agent makes daily management decisions (irrigation, fertilizer, pruning,
    temperature control) and receives observations about plant state (biomass, LAI, stress levels)
    and environmental conditions (rainfall, soil water/nitrogen).

    Example:
        >>> # Connect to a running server
        >>> with PlantEnv(base_url="http://localhost:8000") as client:
        ...     # Reset for a specific task (easy, medium, or hard)
        ...     result = client.reset(task="medium")
        ...     print(f"Initial biomass: {result.observation.biomass}")
        ...
        ...     # Simulate 5 days of management
        ...     for day in range(5):
        ...         action = PlantAction(irrigation=0.5, nitrogen_fertilizer=0.3)
        ...         result = client.step(action)
        ...         print(f"Day {day}: biomass={result.observation.biomass}, reward={result.reward}")

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = PlantEnv.from_docker_image("plant-growth-env:latest")
        >>> try:
        ...     result = client.reset(task="hard")
        ...     # Run episode...
        ...     final_score = client.get_task_success_score()
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: PlantAction) -> Dict:
        """
        Convert PlantAction to JSON payload for step message.

        Serializes all four management decision variables into a dictionary
        suitable for JSON encoding and WebSocket transmission.

        Args:
            action: PlantAction instance with irrigation, fertilizer, pruning, temperature_control

        Returns:
            Dictionary representation with all action fields
        """
        return {
            "irrigation": action.irrigation,
            "nitrogen_fertilizer": action.nitrogen_fertilizer,
            "pruning": action.pruning,
            "temperature_control": action.temperature_control,
        }

    def _parse_result(self, payload: Dict) -> StepResult[PlantObservation]:
        """
        Parse server response into StepResult[PlantObservation].

        Deserializes the JSON response from the server into strongly-typed Python objects.
        Extracts all 13 plant observation fields, done flag, and reward signal.

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with PlantObservation, reward, and done flag
        """
        obs_data = payload.get("observation", {})
        observation = PlantObservation(
            # Plant growth metrics
            biomass=obs_data.get("biomass", 0.0),
            leaf_area_index=obs_data.get("leaf_area_index", 0.0),
            plant_height=obs_data.get("plant_height", 0.0),
            # Soil conditions
            soil_water=obs_data.get("soil_water", 0.0),
            soil_nitrogen=obs_data.get("soil_nitrogen", 0.0),
            # Plant development
            phenological_stage=obs_data.get("phenological_stage", 0),
            # Stress indices
            water_stress=obs_data.get("water_stress", 0.0),
            nitrogen_stress=obs_data.get("nitrogen_stress", 0.0),
            # Health and time
            health_index=obs_data.get("health_index", 1.0),
            day_of_simulation=obs_data.get("day_of_simulation", 0),
            # Environment
            daily_rainfall=obs_data.get("daily_rainfall", 0.0),
            # Reward tracking
            cumulative_reward=obs_data.get("cumulative_reward", 0.0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=payload.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )

    def get_task_success_score(self) -> Optional[float]:
        """
        Compute the grader score (0.0-1.0) based on current episode performance.

        This extracts the grader score from environment metadata if available.
        Typically called after done=True to get the final task evaluation.

        Returns:
            Task success score (0.0-1.0) or None if not available
        """
        # Score is typically stored in the last observation's metadata
        # This is a placeholder; actual implementation depends on server response
        if hasattr(self, "_last_observation"):
            return self._last_observation.metadata.get("task_score")
        return None

    def get_resource_efficiency(self) -> Optional[Dict[str, float]]:
        """
        Calculate resource usage efficiency from episode performance.

        Returns a breakdown of how efficiently the agent used water and nitrogen
        relative to plant growth achieved.

        Returns:
            Dictionary with 'water_efficiency' and 'nitrogen_efficiency' (0.0-1.0)
            or None if data unavailable
        """
        if hasattr(self, "_last_observation"):
            metadata = self._last_observation.metadata
            return {
                "water_efficiency": metadata.get("water_efficiency", 0.0),
                "nitrogen_efficiency": metadata.get("nitrogen_efficiency", 0.0),
                "total_irrigation_used": metadata.get("total_irrigation_used", 0.0),
                "total_fertilizer_used": metadata.get("total_fertilizer_used", 0.0),
            }
        return None

    def is_task_passed(self, threshold: float = 0.7) -> Optional[bool]:
        """
        Check if agent passed the task based on grader score.

        Args:
            threshold: Success threshold (default 0.7, range 0.0-1.0)

        Returns:
            True if score >= threshold, False otherwise, None if score unavailable
        """
        score = self.get_task_success_score()
        if score is not None:
            return score >= threshold
        return None

    def get_reward_components(self) -> Optional[Dict[str, float]]:
        """
        Extract the breakdown of reward into constituent components.

        Useful for analysis and debugging to understand what drove the reward signal
        (growth vs. health vs. efficiency).

        Returns:
            Dictionary with 'growth', 'health', 'efficiency', 'survival' components
            or None if data unavailable
        """
        if hasattr(self, "_last_observation"):
            metadata = self._last_observation.metadata
            return {
                "growth_reward": metadata.get("growth_reward", 0.0),
                "health_reward": metadata.get("health_reward", 0.0),
                "efficiency_reward": metadata.get("efficiency_reward", 0.0),
                "survival_reward": metadata.get("survival_reward", 0.0),
            }
        return None
