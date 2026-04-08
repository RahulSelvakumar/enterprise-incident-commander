from models import TriageState

class IncidentGrader:
    def grade(self, state: TriageState) -> float:
        if state.total_initial_tickets == 0:
            return 0.0
        # Normalizes the score to a standard 0.0 - 1.0 scale
        return float(state.completed_tickets) / float(state.total_initial_tickets)