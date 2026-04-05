from typing import List, Optional
from pydantic import BaseModel
from openenv.core.env_server import Action, Observation, State

class Ticket(BaseModel):
    ticket_id: str
    category: str
    severity: str
    time_in_queue_mins: int

class Department(BaseModel):
    name: str
    current_load: int
    max_capacity: int

class TriageAction(Action):
    ticket_id: str
    assign_to: Optional[str] = None

class TriageObservation(Observation):
    unassigned_tickets: List[Ticket]
    departments: List[Department]
    current_step: int
    message: str

class TriageState(State):
    total_initial_tickets: int = 0
    completed_tickets: int = 0
    task_difficulty: str = "easy"
    max_steps: int = 20