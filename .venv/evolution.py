import random
import copy
from typing import List, Tuple, Any

from archive import identify_pareto_front
from selection import tournament_selection
from genetic_operators import (
    mutate_reorder_shelf_products,
    mutate_reorder_bay_shelves,
    mutate_swap_shelf_products,
    mutate_consolidate_bays,
    crossover_bay_based,
    crossover_family_based,
    crossover_shelf_based
)
from validation import validate_solution


#Evolve the population using selection, crossover, and mutation strategies
def evolve_population(
        evaluated_populations: List[Tuple[List[Any], float, float]],
        bays: List[Any],
        shelves: List[Any],
        mutation_rate: float = 0.7,
        crossover_rate: float = 0.3
) -> List[List[Any]]:
    # Selection
    selected_populations = tournament_selection(evaluated_populations)

    # Create a new population through crossover and mutation
    new_population = []

    # Elitism: Keep the best solutions (Pareto front)
    pareto_front = identify_pareto_front(evaluated_populations)

    # Debug info
    print(f"Pareto front has {len(pareto_front)} solutions")
    for i, (solution, obj1, obj2) in enumerate(pareto_front):
        print(f"  Solution {i + 1}: Bays={obj1}, Distance={obj2}")
        # Check solution validity
        is_valid = validate_solution(solution, bays)
        if not is_valid:
            print(f"  Warning: Solution {i + 1} has validity issues!")

    # Only add pareto solutions if they exist
    if pareto_front:
        for solution, _, _ in pareto_front:
            # Only add if solution is valid
            if validate_solution(solution, bays):
                new_population.append(copy.deepcopy(solution))
            else:
                print("Skipping invalid pareto solution")

    # Apply crossover and mutations to create diversity
    # Make multiple attempts to get valid solutions
    max_attempts = 100  # Limit attempts to avoid infinite loop
    attempts = 0
    crossover_attempts = 0
    crossover_successes = 0

    while len(new_population) < len(evaluated_populations) and attempts < max_attempts:
        attempts += 1

        # Create a new solution using either crossover or mutation
        parent = random.choice(selected_populations)

        # Skip invalid parents
        if not validate_solution(parent, bays):
            continue

        # Track what type of mutation was applied
        last_mutation_type = None

        # Apply mutation first to create diversity
        offspring = copy.deepcopy(parent)

        # Choose a mutation strategy randomly
        mutation_strategy = random.choice([
            # 30% chance of shelf product reordering
            "reorder_products",
            "reorder_products",
            "reorder_products",
            # 20% chance of shelf reordering
            "reorder_shelves",
            "reorder_shelves",
            # 20% chance of product swap
            "swap_shelf_products",
            "swap_shelf_products",
            # 30% chance of bay consolidation (new mutation operator)
            "consolidate_bays",
            "consolidate_bays",
            "consolidate_bays"
        ])

        # Apply selected mutation
        if mutation_strategy == "reorder_products":
            offspring = mutate_reorder_shelf_products(offspring, mutation_rate)
            last_mutation_type = "reorder_products"
        elif mutation_strategy == "reorder_shelves":
            offspring = mutate_reorder_bay_shelves(offspring, bays, shelves, mutation_rate)
            last_mutation_type = "reorder_shelves"
        elif mutation_strategy == "swap_shelf_products":
            offspring = mutate_swap_shelf_products(offspring, bays, shelves, mutation_rate)
            last_mutation_type = "swap_shelf_products"
        else:  # consolidate_bays
            offspring = mutate_consolidate_bays(offspring, bays, shelves, mutation_rate)
            last_mutation_type = "consolidate_bays"

        # Check if offspring is valid after mutation
        if not validate_solution(offspring, bays):
            continue

        # Now decide whether to perform crossover - only do this if:
        # 1. We haven't done cross-bay product swapping
        # 2. We meet the crossover probability
        if last_mutation_type not in ["swap_shelf_products", "consolidate_bays"] and random.random() < crossover_rate and len(selected_populations) >= 2:
            crossover_attempts += 1

            # Try to find a suitable second parent for crossover
            second_parent = None

            # Try a few times to find a compatible parent
            for _ in range(5):  # Limit search attempts
                candidate = random.choice(selected_populations)
                if candidate != offspring and validate_solution(candidate, bays):
                    second_parent = candidate
                    break

            if second_parent:
                # Apply bay-based crossover
                crossover_result = crossover_bay_based(offspring, second_parent, bays, shelves)

                # If crossover succeeded, use the result
                if crossover_result is not None:
                    offspring = crossover_result
                    crossover_successes += 1
                    #print(f"Bay-based crossover successful")

        # Check if offspring is valid and different from parent
        if validate_solution(offspring, bays):
            # Check if offspring is different from parent
            different = False
            for i in range(len(offspring)):
                if i < len(parent) and (
                        offspring[i].x_position != parent[i].x_position or
                        offspring[i].y_position != parent[i].y_position or
                        offspring[i].product != parent[i].product or
                        offspring[i].bay_index != parent[i].bay_index
                ):
                    different = True
                    break

            if different or not new_population:  # Always accept if population is empty
                new_population.append(offspring)

    # Print crossover statistics
    if crossover_attempts > 0:
        print(f"Crossover success rate: {crossover_successes}/{crossover_attempts} ({crossover_successes/crossover_attempts:.1%})")

    # If we couldn't generate enough valid solutions, clone from existing ones
    if len(new_population) < len(evaluated_populations):
        #print(f"Warning: Could only generate {len(new_population)} valid solutions. Cloning to fill population.")
        while len(new_population) < len(evaluated_populations):
            # Clone a random valid solution
            if new_population:
                clone = copy.deepcopy(random.choice(new_population))
                new_population.append(clone)
            else:
                # If no valid solutions, exit with error
                print("Error: No valid solutions could be generated!")
                break

    # Check if the population has diversity
    if len(new_population) > 1:
        # Check if all solutions are identical
        # Compare first solution with all others
        all_identical = True
        reference = new_population[0]
        for i in range(1, len(new_population)):
            solution = new_population[i]
            # Check if any x or y position differs
            for j in range(min(len(reference), len(solution))):
                if (reference[j].bay_index != solution[j].bay_index or
                        reference[j].y_position != solution[j].y_position or
                        reference[j].x_position != solution[j].x_position or
                        reference[j].product != solution[j].product):
                    all_identical = False
                    break
            if not all_identical:
                break

        if all_identical:
            print("WARNING: All solutions in population are identical!")

    return new_population
