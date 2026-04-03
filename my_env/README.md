---
title: Plant Growth RL Environment
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - reinforcement-learning
  - agriculture
---

# Plant Growth RL Environment

A mechanistic Reinforcement Learning (RL) environment that simulates plant growth, carbon allocation, and resource dynamics (water, nitrogen) over a 90-day season. It is designed to expose modern precision agriculture control challenges to an RL agent.

The simulation uses core biological mathematical equations including Michaelis-Menten kinetics for nitrogen uptake, Beer-Lambert light extinction, and active tracking of structural ($C_p$) and storage ($C_s$) carbon pools.

## Quick Start (Client)

The simplest way to interact with the Plant Growth environment is through the `PlantEnv` client:

```python
from my_env import PlantEnv
from my_env.models import PlantAction

try:
    # Create environment from Docker image
    plant_env = PlantEnv.from_docker_image("plant_growth_env:latest")

    # Reset
    result = plant_env.reset()
    print(f"Initial Biomass: {result.observation.biomass}")

    # Step through the 90 day season
    for day in range(5):
        # 0.0 - 1.0 bounded actions
        action = PlantAction(
            irrigation=0.5, 
            nitrogen_fertilizer=0.5, 
            pruning=0.0, 
            temperature_control=0.5
        )
        result = plant_env.step(action)
        
        print(f"Day {result.observation.day_of_simulation}:")
        print(f"  → Biomass: {result.observation.biomass:.2f} g/m²")
        print(f"  → Reward: {result.reward:.2f}")

finally:
    # Always clean up
    plant_env.close()
```

## Running the Server (Docker)

To run the environment server locally for development or manual HTTP/WebSocket interaction:

1. **Build the Docker Image**:
```bash
# From the my_env directory
docker build -t plant_growth_env -f Dockerfile .
```

2. **Run the Docker Container**:
```bash
docker run -d -p 8000:8000 --name plant_growth_container plant_growth_env
```

3. **Check the Server Status**:
```bash
curl http://localhost:8000/health
# Returns: {"status":"healthy"}
```

You can now hit the `/reset` and `/step` endpoints exposed on `localhost:8000`. Step actions require the `action` wrapper in the API:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"action": {"irrigation": 0.5, "nitrogen_fertilizer": 0.5, "pruning": 0.0, "temperature_control": 0.5}}' http://localhost:8000/step
```

## Environment Details

### Action Space (`PlantAction`)
Control variables normalized between `[0.0, 1.0]`:
- `irrigation`: Fraction of max daily water applied.
- `nitrogen_fertilizer`: Fraction of max daily Nitrogen application.
- `pruning`: Fraction of structural leaf biomass removed.
- `temperature_control`: Adjusts the baseline seasonal temperature (0.5 = no change, >0.5 warms, <0.5 cools).

### Observation Space (`PlantObservation`)
A full list of internal biological states:
- **Biomass metrics**: `biomass`, `leaf_area_index`, `plant_height`
- **Soil conditions**: `soil_water`, `soil_nitrogen`
- **Stress & Health**: `water_stress`, `nitrogen_stress`, `health_index`, `phenological_stage`
- **Simulation progress**: `day_of_simulation`, `daily_rainfall`, `cumulative_reward`

### Reward
The reward balances the raw structural carbon accumulated ($dC_p$) against the resource efficiency penalties evaluated from the agent's actions (e.g., deducting points for excessive watering, fertilizing, or poor plant health).

## Deploying to Hugging Face Spaces

You can easily deploy your OpenEnv environment to Hugging Face Spaces using the OpenEnv CLI:

```bash
# Install the CLI first if you haven't!
pip install openenv-core

# Push the directory to HuggingFace
openenv push
```

## Local Python Testing

If you have `uv` installed, you can test the simulation pure logic locally without Docker or networking overhead using:
```bash
uv run --project . python server/plant_environment.py
```
*(This initiates a quick 90-day simulation loop directly through the python interpreter)*
