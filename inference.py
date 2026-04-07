import asyncio
import os
import json
import textwrap
from typing import List, Optional

from openai import OpenAI

# Assuming you use GenericEnvClient to connect to the environment
from openenv.core.generic_client import GenericEnvClient

# --- MANDATORY ENVIRONMENT VARIABLES ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://api-inference.huggingface.co/v1/")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME") # Optional, for docker setups

# --- ENVIRONMENT SETTINGS ---
# The hackathon runner will evaluate this environment
ENV_URL = os.getenv("ENV_URL", "https://rahulselvakumar-enterprise-incident-commander.hf.space")
TASK_NAME = os.getenv("TASK_NAME", "triage-hard")
BENCHMARK = os.getenv("BENCHMARK", "enterprise-incident-commander")

MAX_STEPS = 10
TEMPERATURE = 0.3
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.1  # normalized score in [0, 1]


# --- EXACT STDOUT LOGGING FUNCTIONS (DO NOT MODIFY) ---
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


# --- AGENT LOGIC ---
def get_model_decision(client: OpenAI, obs_dict: dict) -> dict:
    """
    Takes the environment observation, prompts the LLM, and returns an action dictionary.
    Uses dicts safely to avoid Pydantic V2 deprecation warnings.
    """
    
    # 1. Extract lists to help the LLM make good choices
    unassigned = obs_dict.get('unassigned_tickets', [])
    depts = obs_dict.get('departments', [])
    
    available_tickets = [t.get('id', t.get('ticket_id', 'N/A')) for t in unassigned]
    available_depts = [d.get('name', d.get('dept_name', 'N/A')) for d in depts]
    
    state_summary = {
        "available_ticket_ids": available_tickets[:5], # Show top 5 to save tokens
        "available_departments": available_depts,
        "full_state": obs_dict
    }

    prompt = textwrap.dedent(f"""
        You are a Senior Incident Commander. 
        DATA: {json.dumps(state_summary)}
        
        GOAL: Pick a TICKET_ID from 'available_ticket_ids' and assign to a DEPARTMENT.
        
        RULES:
        - Prioritize 'Critical' severity tickets first.
        - Only assign to a department where current_load < max_capacity.
        - Reply ONLY with a valid raw JSON object.
        - Example: {{"ticket_id": "TKT-101", "assign_to": "DevOps"}}
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a JSON-only API. No conversational text."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        content = (completion.choices[0].message.content or "").strip()
        
        # Clean up Markdown JSON blocks if the LLM adds them
        if "```" in content:
            content = content.split("```")[-2].replace("json", "").strip()
            
        return json.loads(content)
        
    except Exception as exc:
        # SAFE FALLBACK: If LLM fails, pick the first ticket carefully
        t_id = available_tickets[0] if available_tickets else "none"
        dept = available_depts[0] if available_depts else "DevOps"
        return {"ticket_id": t_id, "assign_to": dept}


# --- MAIN LIFECYCLE ---
async def main() -> None:
    # Initialize the mandatory OpenAI client
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Use GenericEnvClient to connect to the space
        async with GenericEnvClient(base_url=ENV_URL) as env:
            result = await env.reset(task_name=TASK_NAME)
            
            for step in range(1, MAX_STEPS + 1):
                if result.done:
                    break

                # Get observation as a dictionary
                obs_dict = result.observation
                if not obs_dict:
                    break

                # Get LLM decision
                action_dict = get_model_decision(client, obs_dict)
                action_str = f"{action_dict.get('ticket_id')}_to_{action_dict.get('assign_to')}"

                # Step the environment
                result = await env.step(action_dict)

                # Extract rewards and logs
                reward = result.reward if result.reward is not None else 0.0
                done = result.done
                error = result.error if hasattr(result, 'error') else None

                rewards.append(reward)
                steps_taken = step

                log_step(step=step, action=action_str, reward=reward, done=done, error=error)

                if done:
                    break

            # --- SCORE NORMALIZATION ---
            # Using your previous successful math to ensure score is between [0, 1]
            total_r = sum(rewards)
            score = max(0.0, min(1.0, (total_r + 300) / 400))
            success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        # If the environment connection completely fails, ensure [END] still prints
        pass
    finally:
        # Always emit the [END] log exactly as requested
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())