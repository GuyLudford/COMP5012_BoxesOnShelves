import random
from typing import List, Tuple, Any

from archive import identify_pareto_front

#Tournament selection for multi-objective optimization
def tournament_selection(
        evaluated_populations: List[Tuple[List[Any], float, float]],
        tournament_size: int = 3
) -> List[List[Any]]:
    selected_populations = []

    for _ in range(len(evaluated_populations)):
        # Randomly select tournament_size candidates
        tournament_candidates = random.sample(evaluated_populations, min(tournament_size, len(evaluated_populations)))

        # Find non-dominated solutions in the tournament
        tournament_pareto = identify_pareto_front(tournament_candidates)

        # If multiple Pareto-optimal solutions exist, randomly select one
        if tournament_pareto:
            selected = random.choice(tournament_pareto)
            selected_populations.append(selected[0])  # Add just the placements
        else:
            # This shouldn't happen, but as a fallback select a random candidate
            selected = random.choice(tournament_candidates)
            selected_populations.append(selected[0])

    return selected_populations

