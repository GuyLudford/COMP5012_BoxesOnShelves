import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Tuple, Any

from data_models import Product, Bay, Shelf, Placement

#Visualize the product placements using matplotlib with enhanced tracking.
def visualize_placements(placements: List[Placement], bays: List[Bay], shelves: List[Shelf]):

    # Debugging print out placement details to verify data
    print("Total Placements:", len(placements))
    for placement in placements:
        print(f"Product Family: {placement.product.family}, "
              f"Bay: {placement.bay_index}, "
              f"Shelf: {placement.shelf_index}, "
              f"X: {placement.x_position}, "
              f"Y: {placement.y_position}")

    # Create figure and axis with more explicit sizing
    fig, ax = plt.subplots(figsize=(20, 15))

    # Color mapping for product families
    color_map = {}

    # Plot bays
    for bay_index, bay in enumerate(bays):
        # Plot bay outline
        bay_rect = patches.Rectangle(
            (bay_index * bay.width, 0),
            bay.width, bay.height,
            fill=False,
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(bay_rect)

        # Verify shelf placement
        print(f"\nBay {bay_index} Shelves:")
        for shelf in bay.shelves:
            print(f"  Shelf {shelf.number}: Position {shelf.position}, "
                  f"Thickness {shelf.thickness}")

            # Draw shelf as a thin rectangle
            shelf_rect = patches.Rectangle(
                (bay_index * bay.width, shelf.position),
                bay.width,
                shelf.thickness,
                fill=True,
                facecolor='lightgray',
                edgecolor='darkgray',
                alpha=0.5
            )
            ax.add_patch(shelf_rect)

            # Annotate shelf
            ax.text(
                bay_index * bay.width + bay.width / 2,
                shelf.position,
                f'Bay {bay_index}, Shelf {shelf.number}',
                ha='center',
                va='bottom',
                fontsize=8
            )

        # Plot products
        for placement in placements:
            if placement.bay_index == bay_index:
                # Assign unique color to each product family
                if placement.product.family not in color_map:
                    color_map[placement.product.family] = plt.cm.Set3(
                        len(color_map) % plt.cm.Set3.N
                    )

                # Calculate absolute x position
                x = bay_index * bay.width + placement.x_position

                # Create rectangle for product
                product_rect = patches.Rectangle(
                    (x, placement.y_position),
                    placement.product.length,
                    placement.product.width,
                    fill=True,
                    edgecolor='black',
                    facecolor=color_map[placement.product.family],
                    alpha=0.7
                )
                ax.add_patch(product_rect)

    # Adjust plot limits dynamically
    max_width = len(bays) * bays[0].width
    max_height = max(bay.height for bay in bays)
    ax.set_xlim(0, max_width)
    ax.set_ylim(0, 3000)

    ax.set_xlabel('Bay Width')
    ax.set_ylabel('Height')
    ax.set_title('Product Placement Planogram')

    # Create legend for product families
    legend_elements = [
        patches.Patch(facecolor=color, alpha=0.7, label=f'Family {family}')
        for family, color in color_map.items()
    ]
    ax.legend(handles=legend_elements, title='Product Families', loc='best')

    plt.tight_layout()
    plt.show()

#Plot objectives and highlight Pareto front
def plot_objectives(
        evaluated_populations: List[Tuple[List[Any], float, float]],
        pareto_front: List[Tuple[List[Any], float, float]]
):
    plt.figure(figsize=(10, 6))

    # Plot all populations
    fractional_bays_used = [obj1 for _, obj1, _ in evaluated_populations]
    family_distances = [obj2 for _, _, obj2 in evaluated_populations]
    plt.scatter(fractional_bays_used, family_distances,
                label='Population Solutions',
                alpha=0.6, color='blue')

    # Highlight Pareto front
    pareto_bays_used = [obj1 for _, obj1, _ in pareto_front]
    pareto_family_distances = [obj2 for _, _, obj2 in pareto_front]
    plt.scatter(pareto_bays_used, pareto_family_distances,
                label='Pareto Front',
                color='red', marker='x', s=100)

    plt.xlabel('Fractional Bays Used')
    plt.ylabel('Product Family Distance')
    plt.title('Multi-Objective Evaluation of Product Placements')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

#Plot objectives and highlight Pareto front with a history of all solutions
def plot_objectives_with_history(
        evaluated_populations: List[Tuple[List[Any], float, float]],
        pareto_front: List[Tuple[List[Any], float, float]],
        all_solutions_history: List[Tuple[float, float]] = None
):
    plt.figure(figsize=(12, 9))

    # Plot all historical solutions first (if provided)
    if all_solutions_history and len(all_solutions_history) > 0:
        historical_bays = [obj1 for obj1, obj2 in all_solutions_history]
        historical_distances = [obj2 for obj1, obj2 in all_solutions_history]
        plt.scatter(historical_bays, historical_distances,
                    label='Historical Solutions',
                    alpha=0.15, color='gray', s=20)

    # Plot current population
    fractional_bays_used = [obj1 for _, obj1, _ in evaluated_populations]
    family_distances = [obj2 for _, _, obj2 in evaluated_populations]
    plt.scatter(fractional_bays_used, family_distances,
                label='Current Population',
                alpha=0.6, color='blue', s=60)

    # Highlight Pareto front
    pareto_bays_used = [obj1 for _, obj1, _ in pareto_front]
    pareto_family_distances = [obj2 for _, _, obj2 in pareto_front]
    plt.scatter(pareto_bays_used, pareto_family_distances,
                label='Pareto Front',
                color='red', marker='*', s=160)

    # Label points on Pareto front
    for i, (_, bays, distance) in enumerate(pareto_front):
        plt.annotate(f'({bays:.2f}, {distance})',
                     (bays, distance),
                     xytext=(5, 5),
                     textcoords='offset points',
                     fontsize=8)

    plt.xlabel('Fractional Bays Used (minimize)')
    plt.ylabel('Product Family Distance (minimize)')
    plt.title('Multi-Objective Evaluation of Product Placements')

    # Add detailed counts to legend
    legend_title = (f"Solutions: {len(evaluated_populations)} current, "
                    f"{len(all_solutions_history) if all_solutions_history else 0} historical, "
                    f"{len(pareto_front)} Pareto")
    plt.legend(title=legend_title)

    plt.grid(True, linestyle='--', alpha=0.7)

    # Set axis limits with some padding
    if all_solutions_history and len(all_solutions_history) > 0:
        all_bays = historical_bays + fractional_bays_used
        all_distances = historical_distances + family_distances

        x_min, x_max = min(all_bays), max(all_bays)
        y_min, y_max = min(all_distances), max(all_distances)

        # Add 5% padding
        x_padding = (x_max - x_min) * 0.05
        y_padding = (y_max - y_min) * 0.05

        plt.xlim(max(0, x_min - x_padding), x_max + x_padding)
        plt.ylim(max(0, y_min - y_padding), y_max + y_padding)

    plt.show()

