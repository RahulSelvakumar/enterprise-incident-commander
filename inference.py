import os
import sys
from openai import OpenAI

# Import your local environment and action models
from server.environment import TicketTriageEnvironment
from models import TriageAction
from grader import IncidentGrader

# ==========================================
# 1. MANDATORY ENVIRONMENT VARIABLES
# ==========================================
# Defaults are set strictly for the API endpoint and Model Name.
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# ==========================================
# 2. SETUP OPENAI CLIENT
# ==========================================
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)
def run_inference():
    # Dynamically fetch the task from the Scaler pipeline
    task_name = os.getenv("TASK_NAME", "triage-easy")
    env_name = "enterprise-incident-commander"
    
    # Initialize variables for strict STDOUT tracking
    steps = 0
    rewards = []
    success = False
    score = 0.0
    
    # [START] Rule: One start line at episode begin. flush=True required.
    print(f"[START] task={task_name} env={env_name} model={MODEL_NAME}", flush=True)

    try:
        # Initialize your local environment
        env = TicketTriageEnvironment()
        obs = env.reset(task_id=task_name)
        done = obs.done

        while not done:
            steps += 1
            error_msg = "null"
            action_str = "unknown_action"
            
            try:
                # ==========================================
                # 3. AI AGENT LLM CALL & PARSING
                # ==========================================
                # TODO: Replace this prompt with your actual agent instructions
                system_prompt = "You are an Incident Commander. Return only the ticket ID and Department."
                user_prompt = f"Tickets waiting: {len(obs.unassigned_tickets)}. Assign one."
                
                # Must use the OpenAI client object
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=50
                )
                
                # Extract the raw text from the LLM
                action_str = response.choices[0].message.content.strip().replace('\n', ' ').replace('\r', ' ')
                
                # TODO: Parse action_str into your TriageAction object here
                # Example: If LLM says "TKT-100 IT Support" -> parse it
                # Hardcoded example for structure:
                action = TriageAction(ticket_id="TKT-100", assign_to="IT Support") 
                
                # Step the environment
                obs = env.step(action)
                done = obs.done
                
            except Exception as step_error:
                error_msg = str(step_error).replace("\n", " ")
                done = True  # Forcefully end the loop on error

            # Format reward to exactly 2 decimal places
            step_reward = float(obs.reward)
            rewards.append(step_reward)
            
            # [STEP] Rule: Emit immediately after env.step(). Booleans MUST be lowercase.
            print(f"[STEP] step={steps} action={action_str} reward={step_reward:.2f} done={str(done).lower()} error={error_msg}", flush=True)

        # Loop finished without fatal application crashes
        success = True
        
        # Calculate final score [0.0 - 1.0] using your standalone grader
        grader = IncidentGrader()
        score = grader.grade(env.state)

    except Exception as e:
        success = False
        print(f"Exception during inference: {str(e)}", file=sys.stderr)
    
    finally:
        # [END] Rule: Always emitted even on exception.
        # Format array of rewards to 2 decimal places with no spaces
        formatted_rewards = ",".join([f"{r:.2f}" for r in rewards])
        
        print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={formatted_rewards}", flush=True)

if __name__ == "__main__":
    run_inference()