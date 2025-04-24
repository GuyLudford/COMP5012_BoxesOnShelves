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
from genetic_algorithm import run_genetic_algorithm, run_genetic_algorithm_with_solution_history

def main():
    #Run the genetic algorithm
    # run_genetic_algorithm(
    #     load_problem_data,       # Function to load problem data
    #     place_products_inefficiently, # Function to place products randomly
    #     visualize_placements,    # Function to visualize placements
    #     'ProductsTrim',          # Products file
    #     'Baytp1Trim',            # Bays file
    #     'ShelvesTrim',           # Shelves file
    #     Placement,               # Placement class
    #     Product,                 # Product class
    #     num_populations=10,       # Optional: number of initial populations
    #     num_generations=20,
    #     mutation_rate=0.7,
    #     visualize_generations=False
    # )

    run_genetic_algorithm_with_solution_history(
        load_problem_data,  # Function to load problem data
        place_products_randomly,  # Original random placement function
        visualize_placements,  # Function to visualize placements
        'Products',  # Products file
        'Baytp1',  # Bays file
        'Shelves',  # Shelves file
        Placement,  # Placement class
        Product,  # Product class
        num_populations=50,  # Number of initial populations
        num_generations=20,  # More generations to see evolution
        mutation_rate=0.8,
        visualize_generations=False
    )

if __name__ == '__main__':
    main()
    #SingleInitialise()