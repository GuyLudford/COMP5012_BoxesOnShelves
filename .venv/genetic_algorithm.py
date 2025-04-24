import random
import copy
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Any, Type, Callable

from data_loader import load_problem_data
from data_models import Product, Bay, Shelf, Placement
from initialization import initialize_population, initialize_varied_population, place_products_randomly
from objectives import evaluate_population
from archive import identify_pareto_front
from evolution import evolve_population
from validation import validate_solution
from visualization import visualize_placements, plot_objectives,  plot_objectives_with_history

def run_genetic_algorithm(
        load_problem_data_func: callable,
        place_products_randomly_func: callable,
        visualize_placements_func: callable,
        products_file: str,
        bays_file: str,
        shelves_file: str,
        Placement: Type[Any],
        Placement_Product: Type[Any],
        num_populations: int = 50,
        num_generations: int = 20,
        mutation_rate: float = 0.7,
        visualize_generations: bool = False,
        debug_mode: bool = False
):
    # Load problem data
    products, bays, shelves = load_problem_data_func(
        products_file,
        bays_file,
        shelves_file
    )

    # Initialize populations
    print("Generating initial population...")
    populations = initialize_population(
        num_populations,
        products,
        bays,
        shelves,
        place_products_randomly_func
    )

    # Verify initial population validity
    print("Checking initial population validity...")
    valid_populations = []
    for i, population in enumerate(populations):
        is_valid = check_solution_validity(population)
        if is_valid:
            valid_populations.append(population)
        else:
            print(f"Initial solution {i + 1} is invalid - discarding")

    # Replace populations with only valid ones
    if len(valid_populations) < len(populations):
        #print(f"Warning: {len(populations) - len(valid_populations)} invalid solutions in initial population")
        if valid_populations:
            # If we have at least some valid solutions, use them
            populations = valid_populations
            # And duplicate them to maintain population size
            while len(populations) < num_populations:
                populations.append(copy.deepcopy(random.choice(valid_populations)))
        else:
            print("Error: No valid solutions in initial population. Check product placement logic.")
            return

    # Track objectives across generations for analysis
    best_bays_history = []
    best_distance_history = []
    pareto_size_history = []

    # Evolution loop
    for generation in range(num_generations):
        print(f"\nGeneration {generation + 1}/{num_generations}")

        # Evaluate populations
        evaluated_populations = evaluate_population(
            populations,
            bays,
            Placement,
            Placement_Product
        )

        # Identify Pareto front for this generation
        pareto_front = identify_pareto_front(evaluated_populations)

        # Print statistics
        print(f"Population size: {len(populations)}")
        print(f"Pareto front size: {len(pareto_front)}")

        # Check for potential issues with objectives
        all_bays = [obj1 for _, obj1, _ in evaluated_populations]
        all_distances = [obj2 for _, obj2, _ in evaluated_populations]

        #if len(set(f"{x:.2f}" for x in all_bays)) == 1:
            #print("Warning: All solutions have the same fractional bays used!")

        #if len(set(all_distances)) == 1:
            #print("Warning: All solutions have the same family distance!")

        # Print the best solutions in this generation
        if pareto_front:
            # Find best solutions
            best_bays_solution = min(pareto_front, key=lambda x: x[1])
            best_distance_solution = min(pareto_front, key=lambda x: x[2])

            print(f"Best solution for bays used: {best_bays_solution[1]:.2f} fractional bays, {best_bays_solution[2]} distance")
            print(f"Best solution for family distance: {best_distance_solution[1]:.2f} fractional bays, {best_distance_solution[2]} distance")

            # Track history
            best_bays_history.append(best_bays_solution[1])
            best_distance_history.append(best_distance_solution[2])
            pareto_size_history.append(len(pareto_front))

        # Stop if we've reached the last generation
        if generation == num_generations - 1:
            break

        # Evolve population
        populations = evolve_population(
            evaluated_populations,
            bays,
            shelves,
            mutation_rate
        )

    # Final evaluation
    final_evaluated_populations = evaluate_population(
        populations,
        bays,
        Placement,
        Placement_Product
    )

    # Identify final Pareto front
    final_pareto_front = identify_pareto_front(final_evaluated_populations)

    # Print out final Pareto front details
    print("\nFinal Pareto Front Solutions:")
    for i, (placement, fractional_bays_used, family_distance) in enumerate(final_pareto_front, 1):
        print(f"Solution {i}:")
        print(f"  Fractional Bays Used: {fractional_bays_used:.2f}")
        print(f"  Total Occupied Bays: {int(np.ceil(fractional_bays_used))} bays")
        print(f"  Family Distance: {family_distance}")

    # Plot objectives
    plot_objectives(final_evaluated_populations, final_pareto_front)

    # Plot history of objectives over generations
    if len(best_bays_history) > 1:  # Only plot if we have history
        plt.figure(figsize=(12, 8))

        plt.subplot(2, 1, 1)
        plt.plot(range(1, len(best_bays_history) + 1), best_bays_history, 'b-', marker='o', label='Fractional Bays Used')
        plt.xlabel('Generation')
        plt.ylabel('Fractional Bays Used')
        plt.title('Evolution of Fractional Bays Used')
        plt.grid(True, linestyle='--', alpha=0.7)

        plt.subplot(2, 1, 2)
        plt.plot(range(1, len(best_distance_history) + 1), best_distance_history, 'r-', marker='o',
                 label='Best Distance')
        plt.xlabel('Generation')
        plt.ylabel('Family Distance')
        plt.title('Evolution of Best Family Distance')
        plt.grid(True, linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.show()

        # Plot Pareto front size evolution
        plt.figure(figsize=(10, 5))
        plt.plot(range(1, len(pareto_size_history) + 1), pareto_size_history, 'g-', marker='o')
        plt.xlabel('Generation')
        plt.ylabel('Number of Solutions')
        plt.title('Evolution of Pareto Front Size')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.show()

    # Visualize solutions from the Pareto front
    if final_pareto_front:
        num_solutions_to_visualize = min(3, len(final_pareto_front))

        # Choose solutions: best bays, best distance, and a compromise
        best_solutions = []

        # Best bays solution
        best_bays_solution = min(final_pareto_front, key=lambda x: x[1])
        best_solutions.append(best_bays_solution)

        # Best distance solution
        best_distance_solution = min(final_pareto_front, key=lambda x: x[2])
        if best_distance_solution != best_bays_solution:
            best_solutions.append(best_distance_solution)

        # Compromise solution (if there are more than 2 solutions)
        if len(final_pareto_front) > 2 and len(best_solutions) < num_solutions_to_visualize:
            # Find solution that balances both objectives
            compromise_solution = None
            min_sum = float('inf')

            for solution in final_pareto_front:
                if solution in best_solutions:
                    continue

                # Normalize objectives
                max_bays = max(sol[1] for sol in final_pareto_front)
                max_distance = max(sol[2] for sol in final_pareto_front)

                norm_bays = solution[1] / max_bays if max_bays > 0 else 0
                norm_distance = solution[2] / max_distance if max_distance > 0 else 0

                solution_sum = norm_bays + norm_distance

                if solution_sum < min_sum:
                    min_sum = solution_sum
                    compromise_solution = solution

            if compromise_solution:
                best_solutions.append(compromise_solution)

        # Visualize each selected solution
        for i, solution in enumerate(best_solutions):
            print(f"\nVisualizing Solution {i + 1}: Fractional Bays={solution[1]:.2f}, Distance={solution[2]}")

            # Deep copy bays to preserve shelf information
            best_bays = copy.deepcopy(bays)

            # Reconstruct bay and shelf information
            for placement in solution[0]:
                # Find the corresponding bay
                target_bay = best_bays[placement.bay_index]

                # Find or create appropriate shelf
                matching_shelf = None
                for shelf in target_bay.shelves:
                    # Check if this placement fits on an existing shelf
                    # Adjust the comparison to account for shelf thickness
                    if (shelf.position + shelf.thickness <= placement.y_position <
                            shelf.position + 2 * shelf.thickness):
                        matching_shelf = shelf
                        break

                # If no matching shelf found, create a new one
                if not matching_shelf:
                    matching_shelf = copy.deepcopy(shelves[0])  # Use base shelf config
                    # Position the shelf just below the product
                    matching_shelf.position = placement.y_position - matching_shelf.thickness
                    target_bay.shelves.append(matching_shelf)

                # Add product to the shelf's product list
                matching_shelf.products.append((placement.product, placement.x_position))

            # Visualize with reconstructed bay and shelf information
            visualize_placements_func(solution[0], best_bays, shelves)


#Tracks the history of all solutions across all generations.
def run_genetic_algorithm_with_solution_history(
        load_problem_data_func: callable,
        place_products_randomly_func: callable,
        visualize_placements_func: callable,
        products_file: str,
        bays_file: str,
        shelves_file: str,
        Placement: Type[Any],
        Placement_Product: Type[Any],
        num_populations: int = 50,
        num_generations: int = 30,
        mutation_rate: float = 0.7,
        visualize_generations: bool = False,
        debug_mode: bool = False
):
    
    # Load problem data
    products, bays, shelves = load_problem_data_func(
        products_file,
        bays_file,
        shelves_file
    )

    # Initialize varied population
    print("Generating initial varied population...")
    populations = initialize_population(
        num_populations,
        products,
        bays,
        shelves,
        place_products_randomly_func
    )

    # Verify initial population validity
    print("Checking initial population validity...")
    valid_populations = []
    for i, population in enumerate(populations):
        is_valid = validate_solution(population, bays)
        if is_valid:
            valid_populations.append(population)
        else:
            print(f"Initial solution {i + 1} is invalid - discarding")

    # Replace populations with only valid ones
    if len(valid_populations) < len(populations):
        print(f"Warning: {len(populations) - len(valid_populations)} invalid solutions in initial population")
        if valid_populations:
            # If we have at least some valid solutions, use them
            populations = valid_populations
            # And duplicate them to maintain population size
            while len(populations) < num_populations:
                populations.append(copy.deepcopy(random.choice(valid_populations)))
        else:
            print("Error: No valid solutions in initial population. Check product placement logic.")
            return

    # Track objectives across generations for analysis
    best_bays_history = []
    best_distance_history = []
    pareto_size_history = []
    avg_bays_history = []  # Track average bay usage too

    # Track ALL solutions across ALL generations
    all_solutions_history = []

    # Evolution loop
    for generation in range(num_generations):
        print(f"\nGeneration {generation + 1}/{num_generations}")

        # Evaluate populations
        evaluated_populations = evaluate_population(
            populations,
            bays,
            Placement,
            Placement_Product
        )

        # Add current generation's solutions to history
        for _, bays_used, family_distance in evaluated_populations:
            all_solutions_history.append((bays_used, family_distance))

        # Identify Pareto front for this generation
        pareto_front = identify_pareto_front(evaluated_populations)

        # Print statistics
        print(f"Population size: {len(populations)}")
        print(f"Pareto front size: {len(pareto_front)}")

        # Check for potential issues with objectives
        all_bays = [obj1 for _, obj1, _ in evaluated_populations]
        all_distances = [obj2 for _, obj2, _ in evaluated_populations]

        # Calculate average bay usage
        avg_bays = sum(all_bays) / len(all_bays)
        avg_bays_history.append(avg_bays)

        # Print distribution of bay usage
        unique_bays = sorted(set(f"{x:.2f}" for x in all_bays))
        print(f"Unique bay usage values: {len(unique_bays)}")
        print(f"Average bay usage: {avg_bays:.2f}")
        print(f"Min bay usage: {min(all_bays):.2f}, Max bay usage: {max(all_bays):.2f}")

        if len(unique_bays) == 1:
            print("Warning: All solutions have the same fractional bays used!")

        if len(set(all_distances)) == 1:
            print("Warning: All solutions have the same family distance!")

        # Print the best solutions in this generation
        if pareto_front:
            # Find best solutions
            best_bays_solution = min(pareto_front, key=lambda x: x[1])
            best_distance_solution = min(pareto_front, key=lambda x: x[2])

            print(
                f"Best solution for bays used: {best_bays_solution[1]:.2f} fractional bays, {best_bays_solution[2]} distance")
            print(
                f"Best solution for family distance: {best_distance_solution[1]:.2f} fractional bays, {best_distance_solution[2]} distance")

            # Track history
            best_bays_history.append(best_bays_solution[1])
            best_distance_history.append(best_distance_solution[2])
            pareto_size_history.append(len(pareto_front))

        # Visualize current generation if requested
        if visualize_generations and pareto_front:
            print(f"\nVisualizing Generation {generation + 1} Best Solution:")
            best_solution = min(pareto_front, key=lambda x: x[1])  # Best bay usage solution
            visualize_placements_func(best_solution[0], bays, shelves)

        # Stop if we've reached the last generation
        if generation == num_generations - 1:
            break

        # Evolve population
        populations = evolve_population(
            evaluated_populations,
            bays,
            shelves,
            mutation_rate
        )

    # Final evaluation
    final_evaluated_populations = evaluate_population(
        populations,
        bays,
        Placement,
        Placement_Product
    )

    # Identify final Pareto front
    final_pareto_front = identify_pareto_front(final_evaluated_populations)

    # Print out final Pareto front details
    print("\nFinal Pareto Front Solutions:")
    for i, (placement, fractional_bays_used, family_distance) in enumerate(final_pareto_front, 1):
        print(f"Solution {i}:")
        print(f"  Fractional Bays Used: {fractional_bays_used:.2f}")
        print(f"  Total Occupied Bays: {int(np.ceil(fractional_bays_used))} bays")
        print(f"  Family Distance: {family_distance}")

    # Plot objectives with history
    plot_objectives_with_history(final_evaluated_populations, final_pareto_front, all_solutions_history)

    # Plot history of objectives over generations
    if len(best_bays_history) > 1:  # Only plot if we have history
        plt.figure(figsize=(12, 12))

        plt.subplot(3, 1, 1)
        plt.plot(range(1, len(best_bays_history) + 1), best_bays_history, 'b-', marker='o',
                 label='Best Fractional Bays')
        plt.plot(range(1, len(avg_bays_history) + 1), avg_bays_history, 'g--', marker='x',
                 label='Average Fractional Bays')
        plt.xlabel('Generation')
        plt.ylabel('Fractional Bays Used')
        plt.title('Evolution of Bays Used (Best and Average)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)

        plt.subplot(3, 1, 2)
        plt.plot(range(1, len(best_distance_history) + 1), best_distance_history, 'r-', marker='o',
                 label='Best Distance')
        plt.xlabel('Generation')
        plt.ylabel('Family Distance')
        plt.title('Evolution of Best Family Distance')
        plt.grid(True, linestyle='--', alpha=0.7)

        plt.subplot(3, 1, 3)
        plt.plot(range(1, len(pareto_size_history) + 1), pareto_size_history, 'g-', marker='o')
        plt.xlabel('Generation')
        plt.ylabel('Number of Solutions')
        plt.title('Evolution of Pareto Front Size')
        plt.grid(True, linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.show()

        # Plot a 3D scatter of all solutions over generations
        if len(all_solutions_history) > 0:
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(111, projection='3d')

            # Extract data
            solution_x = []  # bays
            solution_y = []  # distance
            solution_z = []  # generation

            for gen in range(len(best_bays_history)):
                # Calculate start and end indices for this generation
                start_idx = gen * num_populations
                end_idx = min((gen + 1) * num_populations, len(all_solutions_history))

                # Check if indices are valid
                if start_idx < len(all_solutions_history):
                    # Get solutions for this generation
                    solutions_in_gen = all_solutions_history[start_idx:end_idx]
                    for bays_used, distance in solutions_in_gen:
                        solution_x.append(bays_used)
                        solution_y.append(distance)
                        solution_z.append(gen + 1)  # Generation number (1-based)

            # Create scatter plot with color gradient based on generation
            sc = ax.scatter(solution_x, solution_y, solution_z,
                            c=solution_z, cmap='viridis',
                            alpha=0.6, s=30)

            # Add color bar
            cbar = plt.colorbar(sc)
            cbar.set_label('Generation')

            # Final pareto front as highlighted points
            pareto_x = [obj1 for _, obj1, _ in final_pareto_front]
            pareto_y = [obj2 for _, _, obj2 in final_pareto_front]
            pareto_z = [num_generations] * len(final_pareto_front)

            ax.scatter(pareto_x, pareto_y, pareto_z,
                       color='red', marker='*', s=200,
                       label='Final Pareto Front')

            ax.set_xlabel('Fractional Bays Used')
            ax.set_ylabel('Family Distance')
            ax.set_zlabel('Generation')
            ax.set_title('Evolution of Solutions Across Generations')

            plt.legend()
            plt.tight_layout()
            plt.show()

        # Visualize solutions from the Pareto front
        if final_pareto_front:
            num_solutions_to_visualize = min(3, len(final_pareto_front))

            # Choose solutions: best bays, best distance, and a compromise
            best_solutions = []

            # Best bays solution
            best_bays_solution = min(final_pareto_front, key=lambda x: x[1])
            best_solutions.append(best_bays_solution)

            # Best distance solution
            best_distance_solution = min(final_pareto_front, key=lambda x: x[2])
            if best_distance_solution != best_bays_solution:
                best_solutions.append(best_distance_solution)

            # Compromise solution (if there are more than 2 solutions)
            if len(final_pareto_front) > 2 and len(best_solutions) < num_solutions_to_visualize:
                # Find solution that balances both objectives
                compromise_solution = None
                min_sum = float('inf')

                for solution in final_pareto_front:
                    if solution in best_solutions:
                        continue

                    # Normalize objectives
                    max_bays = max(sol[1] for sol in final_pareto_front)
                    max_distance = max(sol[2] for sol in final_pareto_front)

                    norm_bays = solution[1] / max_bays if max_bays > 0 else 0
                    norm_distance = solution[2] / max_distance if max_distance > 0 else 0

                    solution_sum = norm_bays + norm_distance

                    if solution_sum < min_sum:
                        min_sum = solution_sum
                        compromise_solution = solution

                if compromise_solution:
                    best_solutions.append(compromise_solution)

            # Visualize each selected solution
            for i, solution in enumerate(best_solutions):
                print(f"\nVisualizing Solution {i + 1}: Fractional Bays={solution[1]:.2f}, Distance={solution[2]}")

                # Deep copy bays to preserve shelf information
                best_bays = copy.deepcopy(bays)

                # Reconstruct bay and shelf information
                for placement in solution[0]:
                    # Find the corresponding bay
                    target_bay = best_bays[placement.bay_index]

                    # Find or create appropriate shelf
                    matching_shelf = None
                    for shelf in target_bay.shelves:
                        # Check if this placement fits on an existing shelf
                        # Adjust the comparison to account for shelf thickness
                        if (shelf.position + shelf.thickness <= placement.y_position <
                                shelf.position + 2 * shelf.thickness):
                            matching_shelf = shelf
                            break

                    # If no matching shelf found, create a new one
                    if not matching_shelf:
                        matching_shelf = copy.deepcopy(shelves[0])  # Use base shelf config
                        # Position the shelf just below the product
                        matching_shelf.position = placement.y_position - matching_shelf.thickness
                        target_bay.shelves.append(matching_shelf)

                    # Add product to the shelf's product list
                    matching_shelf.products.append((placement.product, placement.x_position))

                # Visualize with reconstructed bay and shelf information
                visualize_placements_func(solution[0], best_bays, shelves)
