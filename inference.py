# =============================================================================
# INSTRUCTIONS FOR RUNNING LOCALLY:
# 1. Ensure you have installed requirements and initialized the env.
# 2. Start the environment server in a separate terminal:
#      uv run server
# 3. Export your Hugging Face token in the terminal running this script:
#      export HF_TOKEN="hf_your_token_here"
# 4. Run your inference logic:
#      python inference.py
# =============================================================================

import asyncio
import os
import json
import textwrap
from typing import List, Optional

from dotenv import load_dotenv

# Load secret keys from .env into environment
load_dotenv()

from openai import OpenAI

import sys
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from plant_soil_env import PlantAction, PlantEnv
except ImportError:
    from client import PlantEnv
    from models import PlantAction

# ====================================================================
# USER INPUT REQUIRED: Environment Variables Configuration
# ====================================================================
# You can set these in your terminal using e.g. `export HF_TOKEN="your_token"`
# For submissions, DO NOT hardcode your API_KEY. Always read from os.getenv.

# 1. Docker image tag (leave blank to test locally)
IMAGE_NAME = os.getenv("IMAGE_NAME") 
# 2. Your HuggingFace Token (required to hit the Inference Endpoints)
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or "dummy_key"
# 3. Default inference router or specific endpoint URL
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
# 4. Model you want to use for generating controls
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

TASK_NAME = os.getenv("MY_ENV_V4_TASK", "plant-soil-regulation")
BENCHMARK = os.getenv("MY_ENV_V4_BENCHMARK", "plant_soil_env")
MAX_STEPS = 10
TEMPERATURE = 0.7
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.1

_MAX_REWARD_PER_STEP = 1.0
MAX_TOTAL_REWARD = MAX_STEPS * _MAX_REWARD_PER_STEP

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI agricultural agent controlling a plant-soil simulation environment.
    Your goal is to manage plant growth by precisely adjusting 4 continuous controls:
    1. theta_boundary_norm (soil moisture, 0.0 to 1.0)
    2. fertilizer_n_norm (nitrogen, 0.0 to 1.0)
    3. fertilizer_p_norm (phosphorus, 0.0 to 1.0)
    4. fertilizer_k_norm (potassium, 0.0 to 1.0)

    You must output your action as a valid JSON object exactly matching this format:
    {"theta_boundary_norm": 0.5, "fertilizer_n_norm": 0.1, "fertilizer_p_norm": 0.1, "fertilizer_k_norm": 0.1}

    Reply with strictly the JSON object and no other text or explanation. 
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def build_user_prompt(step: int, obs: dict, last_reward: float, history: List[str]) -> str:
    history_block = "\n".join(history[-4:]) if history else "None"
    obs_str = json.dumps(obs)
    return textwrap.dedent(
        f"""
        Step: {step}
        Observation: {obs_str}
        Last reward: {last_reward:.2f}
        Previous steps:
        {history_block}
        Send your next action JSON.
        """
    ).strip()


def get_model_message(client: OpenAI, step: int, obs: dict, last_reward: float, history: List[str]) -> str:
    user_prompt = build_user_prompt(step, obs, last_reward, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text if text else "{}"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return '{"theta_boundary_norm": 0.5, "fertilizer_n_norm": 0.0, "fertilizer_p_norm": 0.0, "fertilizer_k_norm": 0.0}'


def parse_action(text: str) -> PlantAction:
    try:
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[-1].split("```")[0].strip()
        data = json.loads(clean_text)
        return PlantAction(
            theta_boundary_norm=float(data.get("theta_boundary_norm", 0.5)),
            fertilizer_n_norm=float(data.get("fertilizer_n_norm", 0.0)),
            fertilizer_p_norm=float(data.get("fertilizer_p_norm", 0.0)),
            fertilizer_k_norm=float(data.get("fertilizer_k_norm", 0.0))
        )
    except Exception as e:
        print(f"[DEBUG] Failed to parse action JSON: {e} from text: {text}", flush=True)
        return PlantAction()


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    if IMAGE_NAME:
        env = await PlantEnv.from_docker_image(IMAGE_NAME)
    else:
        # USER INPUT: Local environment endpoint. If you run your server on a
        # different port, update the 'http://localhost:8000' URL here.
        env = PlantEnv(base_url="http://localhost:8000")

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset()
        obs_dict = result.observation.model_dump() if hasattr(result.observation, 'model_dump') else dict(result.observation)
        last_reward = 0.0

        for step in range(1, MAX_STEPS + 1):
            if hasattr(result, 'done') and result.done:
                break

            message = get_model_message(client, step, obs_dict, last_reward, history)
            action = parse_action(message)
            error = None

            try:
                result = await env.step(action)
                obs_dict = result.observation.model_dump() if hasattr(result.observation, 'model_dump') else dict(result.observation)
                reward = result.reward or 0.0
                done = result.done
            except Exception as e:
                error = str(e)
                reward = 0.0
                done = True

            rewards.append(reward)
            steps_taken = step
            last_reward = reward

            # Standardize action string to single line for log
            action_str = json.dumps({"theta_boundary_norm": action.theta_boundary_norm, "fertilizer_n_norm": action.fertilizer_n_norm, "fertilizer_p_norm": action.fertilizer_p_norm, "fertilizer_k_norm": action.fertilizer_k_norm})
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(f"Step {step}: {action_str} -> reward {reward:+.2f}")

            if done:
                break

        total_reward = sum(rewards)
        # Normalize score into [0, 1]. This assumes max reward around max steps (e.g. 1.0 per step is typical or we just map linearly)
        # Without exact knowledge of plant_soil_env reward scale, we clamp or pass it directly.
        # But instructions state: "score in [0, 1]".
        score_val = (total_reward - min(rewards)*MAX_STEPS) / (MAX_STEPS * 2) if MAX_STEPS > 0 else 0
        score = min(max(abs(score_val), 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())
