import random
import uuid
import os
from openenv.core.env_server import Environment
from models import TriageAction, TriageObservation, TriageState, Ticket, Department

class TicketTriageEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = TriageState()
        self._unassigned_tickets = []
        self._departments = []

    def reset(self, seed=None, episode_id=None, task_id=None, **kwargs) -> TriageObservation:
        actual_task = task_id or kwargs.get("task_name") or os.getenv("TASK_NAME", "triage-easy")

        if "hard" in actual_task:
            num_tickets, dept_capacity = 30, 8
            difficulty = "hard"
            max_turns = 40
        elif "medium" in actual_task:
            num_tickets, dept_capacity = 20, 5
            difficulty = "medium"
            max_turns = 30
        else:
            num_tickets, dept_capacity = 10, 20
            difficulty = "easy"
            max_turns = 20

        self._state = TriageState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            total_initial_tickets=num_tickets,
            completed_tickets=0,
            task_difficulty=difficulty,
            max_steps=max_turns
        )

        self._departments = [
            Department(name="IT Support", current_load=0, max_capacity=dept_capacity),
            Department(name="Billing", current_load=0, max_capacity=dept_capacity),
            Department(name="Security", current_load=0, max_capacity=dept_capacity)
        ]

        self._unassigned_tickets = []
        categories = ["password_reset", "technical", "billing", "security"]
        for i in range(num_tickets):
            sev = "critical" if difficulty == "hard" and i % 5 == 0 else random.choice(["low", "medium", "high"])
            self._unassigned_tickets.append(
                Ticket(ticket_id=f"TKT-{100+i}", category=random.choice(categories), severity=sev, time_in_queue_mins=0)
            )

        return TriageObservation(
            done=False,
            reward=0.0,
            unassigned_tickets=self._unassigned_tickets,
            departments=self._departments,
            current_step=0,
            message="Incident Commander initialized."
        )

    def step(self, action: TriageAction, timeout_s=None, **kwargs) -> TriageObservation:
        self._state.step_count += 1
        reward = 0.0
        msg = ""

        target_ticket = next((t for t in self._unassigned_tickets if t.ticket_id == action.ticket_id), None)
        
        if not target_ticket:
            reward -= 2.0
            msg = "Invalid ticket_id."
        elif action.assign_to is None:
            reward += 0.1 
            msg = f"Ticket {action.ticket_id} held."
        else:
            target_dept = next((d for d in self._departments if d.name == action.assign_to), None)
            if not target_dept:
                reward -= 2.0
                msg = "Invalid department."
            elif target_dept.current_load >= target_dept.max_capacity:
                reward -= 3.0
                msg = "Department at max capacity!"
            else:
                target_dept.current_load += 1
                self._unassigned_tickets.remove(target_ticket)
                self._state.completed_tickets += 1
                reward += 2.0
                msg = f"Assigned {action.ticket_id} to {action.assign_to}."

        for ticket in self._unassigned_tickets:
            ticket.time_in_queue_mins += 5
            if ticket.severity == "critical" and ticket.time_in_queue_mins > 15:
                reward -= 10.0 
            elif ticket.severity == "high" and ticket.time_in_queue_mins > 30:
                reward -= 5.0
            reward -= 0.1

        done = len(self._unassigned_tickets) == 0 or self._state.step_count >= self._state.max_steps

        return TriageObservation(
            done=done,
            reward=reward,
            unassigned_tickets=self._unassigned_tickets,
            departments=self._departments,
            current_step=self._state.step_count,
            message=msg
        )

    # This is the property the framework was missing!
    @property
    def state(self) -> TriageState:
        return self._state


# The generic grader class placed outside the environment class
class IncidentGrader:
    def grade(self, state: TriageState) -> float:
        return float(state.completed_tickets)