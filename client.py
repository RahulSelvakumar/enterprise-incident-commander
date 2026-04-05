from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from models import TriageAction, TriageObservation, TriageState, Ticket, Department

class TicketTriageClient(EnvClient[TriageAction, TriageObservation, TriageState]):
    def _step_payload(self, action: TriageAction) -> dict:
        return {
            "ticket_id": action.ticket_id,
            "assign_to": action.assign_to
        }

    def _parse_result(self, payload: dict) -> StepResult:
        obs_data = payload.get("observation", {})
        tickets = [Ticket(**t) for t in obs_data.get("unassigned_tickets", [])]
        departments = [Department(**d) for d in obs_data.get("departments", [])]

        return StepResult(
            observation=TriageObservation(
                done=payload.get("done", False),
                reward=payload.get("reward", 0.0),
                unassigned_tickets=tickets,
                departments=departments,
                current_step=obs_data.get("current_step", 0),
                message=obs_data.get("message", "")
            ),
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> TriageState:
        return TriageState(**payload)