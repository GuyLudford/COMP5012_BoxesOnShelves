from typing import List, Tuple, Any, Type


#Calculate two objectives:
#    1. Number of Bays Used (minimize)
#    2. Product Family Distance (minimize)
def calculate_objectives(
        placements: List[Any],
        bays: List[Any],
        Placement: Type[Any],
        Placement_Product: Type[Any]
) -> Tuple[float, float]:
    # Group placements by bay
    bay_placements = {}
    for placement in placements:
        if placement.bay_index not in bay_placements:
            bay_placements[placement.bay_index] = []
        bay_placements[placement.bay_index].append(placement)

    # Calculate bay usage based on vertical space taken up by shelves and products
    bays_used = 0.0
    for bay_index, bay_placements_list in bay_placements.items():
        # Skip invalid bay indices
        if bay_index >= len(bays):
            continue

        # Get the bay height
        bay_height = bays[bay_index].height

        # Group products by shelf (y_position)
        shelf_groups = {}
        for placement in bay_placements_list:
            if placement.y_position not in shelf_groups:
                shelf_groups[placement.y_position] = []
            shelf_groups[placement.y_position].append(placement)

        # Calculate total vertical space used in this bay
        if shelf_groups:
            # Sort shelves by position (bottom to top)
            shelf_positions = sorted(shelf_groups.keys())

            # Calculate space used by each shelf and its products
            total_vertical_space_used = 0
            for shelf_y in shelf_positions:
                products_on_shelf = shelf_groups[shelf_y]

                # Find tallest product on this shelf
                max_product_height = max(p.product.width for p in products_on_shelf)

                # Add this shelf's contribution to vertical space
                # (include shelf thickness and product height)
                shelf_thickness = 1.0  # Default value or get from shelves[x].thickness
                vertical_space = shelf_thickness + max_product_height
                total_vertical_space_used += vertical_space

            # Calculate fraction of bay used
            bay_usage_fraction = min(1.0, total_vertical_space_used / bay_height)

            # If bay is more than 95% used, count it as a full bay (1.0)
            # Otherwise, use the actual fractional usage
            bays_used += 1.0 if bay_usage_fraction > 0.95 else bay_usage_fraction
        else:
            # Empty bay, not used
            bays_used += 0.0

    # Objective 2: Product Family Distance
    # Group placements by family
    family_placements = {}
    for placement in placements:
        if placement.product.family not in family_placements:
            family_placements[placement.product.family] = []
        family_placements[placement.product.family].append(placement)

    # Calculate total distance within each family
    total_family_distance = 0
    for family, family_group in family_placements.items():
        if len(family_group) > 1:
            # Calculate pairwise distances
            for i in range(len(family_group)):
                for j in range(i + 1, len(family_group)):
                    # Distance considers bay index and x,y positions
                    distance = abs(family_group[i].bay_index - family_group[j].bay_index) + \
                               abs(family_group[i].x_position - family_group[j].x_position) + \
                               abs(family_group[i].y_position - family_group[j].y_position)
                    total_family_distance += distance

    return bays_used, total_family_distance

#Evaluate populations based on objectives
def evaluate_population(
        populations: List[List[Any]],
        bays: List[Any],
        Placement: Type[Any],
        Placement_Product: Type[Any]
) -> List[Tuple[List[Any], float, float]]:
    evaluated_populations = []

    for population in populations:
        # Calculate objectives
        fractional_bays_used, family_distance = calculate_objectives(
            population, bays, Placement, Placement_Product
        )

        evaluated_populations.append(
            (population, fractional_bays_used, family_distance)
        )

    return evaluated_populations