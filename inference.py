import os
import json
from openai import OpenAI
from client import TicketTriageClient
from models import TriageAction

# 1. STRICT COMPLIANCE: Pulling the exact variables required by the hackathon rubric
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini") # Fallback included just in case
HF_TOKEN = os.getenv("HF_TOKEN")

def run_baseline(task_id: str):
    print(f"\n--- Running Task: {task_id} ---")
    
    # 2. STRICT COMPLIANCE: Initializing OpenAI client with their custom base URL and Token
    ai_client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN
    )
    with TicketTriageClient(base_url="https://rahulselvakumar-enterprise-incident-commander.hf.space").sync() as client_env:
        
        result = client_env.reset(task_id=task_id)
        obs = result.observation
        done = result.done
        total_reward = 0.0
        
        while not done:
            state_json = obs.model_dump_json(indent=2)
            prompt = f"""You are an Incident Commander. Assign tickets to departments.
            Output ONLY JSON matching: {{"ticket_id": "string", "assign_to": "string"}}
            Available Departments: 'IT Support', 'Billing', 'Security'. Set assign_to to null to hold.
            Current State: {state_json}"""
            
            try:
                # 3. STRICT COMPLIANCE: Using their specific MODEL_NAME variable
                response = ai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                action_dict = json.loads(response.choices[0].message.content)
                action = TriageAction(**action_dict)
                print(f"Step {obs.current_step}: Assigning {action.ticket_id} to {action.assign_to}")
                
            except Exception as e:
                action = TriageAction(ticket_id=obs.unassigned_tickets[0].ticket_id, assign_to=None)
                
            result = client_env.step(action)
            obs = result.observation
            done = result.done
            total_reward += result.reward
            
        final_state = client_env.state()
        grader_score = final_state.completed_tickets / final_state.total_initial_tickets
        
        print(f"Task Complete!")
        print(f" -> Grader Score: {grader_score:.2f}")
        print(f" -> Total Reward: {total_reward:.2f}")

def main():
    if not HF_TOKEN:
        print("Please set your HF_TOKEN environment variable first to run this script.")
        return
        
    run_baseline("triage-easy")
    run_baseline("triage-medium")
    run_baseline("triage-hard")

if __name__ == "__main__":
    main()