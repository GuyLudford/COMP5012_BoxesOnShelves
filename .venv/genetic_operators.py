import random
import copy
from typing import List, Tuple, Any, Type
from validation import validate_solution


## Reorganize products on a shelf to avoid overlap.
def reorganize_shelf_products(placements: List[Any], bay_index: int, shelf_y: float) -> None:
    # Get products on this shelf
    shelf_placements = [
        (i, p) for i, p in enumerate(placements)
        if p.bay_index == bay_index and p.y_position == shelf_y
    ]

    # If no products or only one product, no reorganization needed
    if len(shelf_placements) <= 1:
        return

    # Sort by x position
    shelf_placements.sort(key=lambda item: item[1].x_position)

    # Assume first product stays at its position
    current_x = shelf_placements[0][1].x_position

    # Reorganize from left to right
    for i, (idx, placement) in enumerate(shelf_placements):
        # Skip first product (it stays at its position)
        if i == 0:
            current_x += placement.product.length + 2.0  # Add standard gap
            continue

        # Position current product after previous one with a gap
        placement.x_position = current_x

        # Update for next product
        current_x += placement.product.length + 2.0  # Add standard gap


#Get the maximum product height on a specific shelf.
def get_max_product_height(placements: List[Any], bay_index: int, shelf_y: float) -> float:
    # Find all products on this shelf
    shelf_products = [
        p.product.width for p in placements
        if p.bay_index == bay_index and p.y_position == shelf_y
    ]

    if not shelf_products:
        return 0.0

    return max(shelf_products)

#Adjust all shelf positions based on product heights.
#This ensures shelves don't overlap with products below them.
#If shelves go beyond bay height, they are moved to the next bay.
def adjust_shelf_positions(placements: List[Any], bays: List[Any], shelves: List[Any]) -> List[Any]:
    # Create a deep copy to avoid modifying the original
    adjusted_placements = copy.deepcopy(placements)

    # Group placements by bay
    bay_placements = {}
    for i, placement in enumerate(adjusted_placements):
        if placement.bay_index not in bay_placements:
            bay_placements[placement.bay_index] = []
        bay_placements[placement.bay_index].append((i, placement))

    # Process each bay
    for bay_idx in sorted(bay_placements.keys()):
        bay = bays[bay_idx] if bay_idx < len(bays) else None
        if not bay:
            continue

        # Group placements by shelf
        shelf_placements = {}
        for idx, placement in bay_placements[bay_idx]:
            shelf_y = placement.y_position
            if shelf_y not in shelf_placements:
                shelf_placements[shelf_y] = []
            shelf_placements[shelf_y].append((idx, placement))

        # Sort shelves from bottom to top
        shelf_positions = sorted(shelf_placements.keys())

        # Adjust shelf positions from bottom to top
        current_y = 0  # Start at bottom of bay
        for shelf_y in shelf_positions:
            # Find minimum shelf thickness (assuming all products on same shelf have same thickness)
            shelf_thickness = 1.0  # Default thickness
            if shelf_placements[shelf_y]:
                # Get first product's shelf index and use it to get thickness
                _, first_placement = shelf_placements[shelf_y][0]
                if 0 <= first_placement.shelf_index < len(shelves):
                    shelf_thickness = shelves[first_placement.shelf_index].thickness

            # Position the shelf at current_y
            new_shelf_y = current_y + shelf_thickness

            # Get max product height on this shelf
            shelf_products = [p.product for _, p in shelf_placements[shelf_y]]
            max_product_height = max(p.width for p in shelf_products) if shelf_products else 0

            # Move products on this shelf to the new y position
            for idx, placement in shelf_placements[shelf_y]:
                # Calculate the y-difference
                y_diff = new_shelf_y - shelf_y

                # Update y position
                adjusted_placements[idx].y_position = new_shelf_y

            # Move current_y to after this shelf and its products
            current_y = new_shelf_y + max_product_height

        # Check if the final position exceeds bay height
        if current_y > bay.height:
            # Need to move top shelves to next bay
            handle_bay_overflow(adjusted_placements, bay_idx, current_y, bay.height, bays, shelves)

    return adjusted_placements

#Handle case where shelves exceed bay height by moving top shelves to next bay.
def handle_bay_overflow(placements: List[Any], bay_idx: int, current_height: float, bay_height: float, bays: List[Any],
                        shelves: List[Any]) -> None:
    # Find next available bay
    next_bay_idx = bay_idx + 1

    # Check if next bay exists
    if next_bay_idx >= len(bays):
        #print(f"Warning: No more bays available for overflow from bay {bay_idx}")
        return

    # Find all shelves that exceed bay height
    overflow_placements = []
    for i, placement in enumerate(placements):
        if placement.bay_index == bay_idx and placement.y_position + placement.product.width > bay_height:
            overflow_placements.append((i, placement))

    # If no overflow, nothing to do
    if not overflow_placements:
        return

    # Group by shelf (y position)
    shelf_groups = {}
    for idx, placement in overflow_placements:
        shelf_y = placement.y_position
        if shelf_y not in shelf_groups:
            shelf_groups[shelf_y] = []
        shelf_groups[shelf_y].append((idx, placement))

    # Move each overflowing shelf to the next bay
    # Start at the bottom of the next bay
    current_y = 0

    for shelf_y in sorted(shelf_groups.keys()):
        # Calculate shelf thickness
        shelf_thickness = 1.0  # Default
        if shelf_groups[shelf_y]:
            _, first_placement = shelf_groups[shelf_y][0]
            if 0 <= first_placement.shelf_index < len(shelves):
                shelf_thickness = shelves[first_placement.shelf_index].thickness

        # Position at current_y (top of shelf)
        new_shelf_y = current_y + shelf_thickness

        # Move all products on this shelf
        for idx, placement in shelf_groups[shelf_y]:
            # Update bay and y position
            placements[idx].bay_index = next_bay_idx
            placements[idx].y_position = new_shelf_y

            # Keep same x position, or reorganize if needed
            # This is a simplification - you might need more logic here

        # Get max product height on this shelf
        max_product_height = max(p.product.width for _, p in shelf_groups[shelf_y])

        # Update current_y for next shelf
        current_y = new_shelf_y + max_product_height

    # Check if we now have overflow in the next bay
    if current_y > bays[next_bay_idx].height:
        # Recursive call to handle overflow in next bay
        handle_bay_overflow(placements, next_bay_idx, current_y, bays[next_bay_idx].height, bays, shelves)

#######MUTATTIONS###########

#Completely reorder products on shelves to optimize family grouping
def mutate_reorder_shelf_products(placements: List[Any], mutation_rate: float = 0.7) -> List[Any]:
    # Create a deep copy to avoid modifying the original
    mutated_placements = copy.deepcopy(placements)

    # Always attempt at least one shelf reordering
    # Try to reorder multiple shelves based on mutation rate
    mutation_attempts = max(1, int(len(set((p.bay_index, p.y_position) for p in mutated_placements)) * mutation_rate))

    # Track if any successful mutations occurred
    successful_mutations = 0

    # Group placements by bay and shelf
    shelf_placements = {}
    for i, placement in enumerate(mutated_placements):
        # Create a key that identifies the specific shelf
        shelf_key = (placement.bay_index, placement.y_position)

        if shelf_key not in shelf_placements:
            shelf_placements[shelf_key] = []
        shelf_placements[shelf_key].append((i, placement))

    # Only consider shelves with multiple products
    shelves_with_multiple_products = [
        shelf_key for shelf_key, placements_list in shelf_placements.items()
        if len(placements_list) >= 2
    ]

    # If no shelves have multiple products, return the original
    if not shelves_with_multiple_products:
        #print("Warning: No shelves with multiple products found for reordering.")
        return mutated_placements

    # Randomly select shelves to reorder
    shelves_to_reorder = random.sample(
        shelves_with_multiple_products,
        min(mutation_attempts, len(shelves_with_multiple_products))
    )

    # Process each selected shelf
    for shelf_key in shelves_to_reorder:
        bay_index, shelf_y_position = shelf_key
        placements_on_shelf = shelf_placements[shelf_key]

        # Skip if not enough products to reorder
        if len(placements_on_shelf) < 2:
            continue

        # Get all placement indices and products on this shelf
        product_indices = [idx for idx, _ in placements_on_shelf]
        products_on_shelf = [(idx, placement.product, placement.x_position)
                             for idx, placement in placements_on_shelf]

        # Group products by family
        family_groups = {}
        for idx, product, x_pos in products_on_shelf:
            if product.family not in family_groups:
                family_groups[product.family] = []
            family_groups[product.family].append((idx, product, x_pos))

        # Determine shelf properties - find the leftmost position and shelf width from the current placement
        # Also determine any inter-product gap to maintain (assuming it's consistent)
        min_x = min(x_pos for _, _, x_pos in products_on_shelf)
        max_x_end = max(x_pos + product.length for _, product, x_pos in products_on_shelf)
        shelf_width = max_x_end - min_x

        # If we have multiple products, estimate the inter-product gap
        if len(products_on_shelf) > 1:
            # Sort products by x position
            sorted_products = sorted(products_on_shelf, key=lambda x: x[2])
            gaps = []
            for i in range(len(sorted_products) - 1):
                _, prod1, x1 = sorted_products[i]
                _, prod2, x2 = sorted_products[i + 1]
                gap = x2 - (x1 + prod1.length)
                if gap > 0:  # Only consider positive gaps
                    gaps.append(gap)
            # Use average gap if we found any, otherwise default to a small value
            inter_product_gap = sum(gaps) / len(gaps) if gaps else 2.0
        else:
            inter_product_gap = 2.0  # Default gap if only one product

        # Create a new ordering that keeps families together
        # Randomize the order of families to promote diversity
        family_keys = list(family_groups.keys())
        random.shuffle(family_keys)

        # Flatten the grouped products back into a list, keeping families together
        new_product_order = []
        for family in family_keys:
            # Also randomize product order within a family for more diversity
            family_products = family_groups[family]
            random.shuffle(family_products)
            new_product_order.extend(family_products)

        # Now place products left to right, respecting their dimensions
        current_x = min_x  # Start at the leftmost position
        for i, (idx, product, _) in enumerate(new_product_order):
            # Update the x position for this product
            mutated_placements[idx].x_position = current_x

            # Move to the next position, accounting for product length and gap
            current_x += product.length + inter_product_gap

        successful_mutations += 1

    # Debug information if no mutations were successful
    if successful_mutations == 0:
        print("Warning: No successful shelf reorderings occurred in this iteration.")

    print('Successful reorder shelf products mutations', successful_mutations)
    return mutated_placements

#Reorder shelves within a bay to optimize family grouping
def mutate_reorder_bay_shelves(placements: List[Any], bays: List[Any], shelves: List[Any],
                               mutation_rate: float = 0.5) -> List[Any]:
    # Create a deep copy to avoid modifying the original
    mutated_placements = copy.deepcopy(placements)

    # Determine how many bays to mutate
    num_bays_to_mutate = max(1, int(len(bays) * mutation_rate))

    # Group placements by bay
    bay_placements = {}
    for i, placement in enumerate(mutated_placements):
        if placement.bay_index not in bay_placements:
            bay_placements[placement.bay_index] = []
        bay_placements[placement.bay_index].append((i, placement))

    # Find bays with multiple shelves
    bays_with_multiple_shelves = []
    for bay_idx in bay_placements:
        # Group placements by shelf (y_position)
        shelves_in_bay = set(p.y_position for _, p in bay_placements[bay_idx])
        if len(shelves_in_bay) >= 2:
            bays_with_multiple_shelves.append(bay_idx)

    # If no bays have multiple shelves, return the original
    if not bays_with_multiple_shelves:
        #print("Warning: No bays with multiple shelves found for reordering.")
        return mutated_placements

    # Randomly select bays to reorder shelves in
    bays_to_reorder = random.sample(
        bays_with_multiple_shelves,
        min(num_bays_to_mutate, len(bays_with_multiple_shelves))
    )

    # Process each selected bay
    for bay_idx in bays_to_reorder:
        # Group by shelf
        shelf_groups = {}
        for idx, placement in bay_placements[bay_idx]:
            shelf_y = placement.y_position
            if shelf_y not in shelf_groups:
                shelf_groups[shelf_y] = []
            shelf_groups[shelf_y].append((idx, placement))

        shelf_positions = sorted(shelf_groups.keys())

        # Need at least 2 shelves to reorder
        if len(shelf_positions) < 2:
            continue

        # Calculate shelf properties
        shelf_info = []
        for shelf_y in shelf_positions:
            products_on_shelf = [p.product for _, p in shelf_groups[shelf_y]]

            # Determine shelf thickness from the original shelf configuration
            # This is a simplification - you might need a more sophisticated approach
            shelf_thickness = shelves[0].thickness  # Default

            # Calculate max product height on this shelf
            max_product_height = max(p.width for p in products_on_shelf) if products_on_shelf else 0

            shelf_info.append({
                'y_position': shelf_y,
                'thickness': shelf_thickness,
                'products': shelf_groups[shelf_y],
                'max_product_height': max_product_height
            })

        # Reordering strategy:
        # 1. We'll randomize shelf order (to explore new configurations)
        # 2. Then place them with proper vertical spacing

        # Create a new shelf order (randomized)
        new_shelf_order = shelf_info.copy()
        random.shuffle(new_shelf_order)

        # Arrange shelves from bottom to top
        current_y = 0  # Start at the bottom of the bay

        for shelf in new_shelf_order:
            # Set new y position for this shelf
            new_y = current_y + shelf['thickness']  # Position after shelf thickness

            # Get old y position to calculate the difference
            old_y = shelf['y_position']
            y_diff = new_y - old_y

            # Update all placements on this shelf
            for idx, placement in shelf['products']:
                mutated_placements[idx].y_position = new_y

            # Move to position for next shelf
            current_y = new_y + shelf['max_product_height']

    return mutated_placements

#Swap products between shelves across all bays
def mutate_swap_shelf_products(
        placements: List[Any],
        bays: List[Any],
        shelves: List[Any],
        mutation_rate: float = 0.5,
        Placement: Type[Any] = None,
        Placement_Product: Type[Any] = None
) -> List[Any]:
    # Create a deep copy to avoid modifying the original
    mutated_placements = copy.deepcopy(placements)

    # Determine how many swap attempts to make
    num_swap_attempts = max(1, int(len(mutated_placements) * mutation_rate))

    # Group placements by bay and shelf
    bay_shelf_placements = {}
    for i, placement in enumerate(mutated_placements):
        if placement.bay_index not in bay_shelf_placements:
            bay_shelf_placements[placement.bay_index] = {}

        if placement.y_position not in bay_shelf_placements[placement.bay_index]:
            bay_shelf_placements[placement.bay_index][placement.y_position] = []

        bay_shelf_placements[placement.bay_index][placement.y_position].append(i)

    # Track successful mutations
    successful_mutations = 0

    # Attempt mutations
    for _ in range(num_swap_attempts):
        # Get all bays with products
        bays_with_products = list(bay_shelf_placements.keys())

        if not bays_with_products:
            break

        # Choose two random bays (might be the same bay)
        if len(bays_with_products) >= 2 and random.random() < 0.5:
            # 50% chance to select different bays for cross-bay swaps
            bay_idx1, bay_idx2 = random.sample(bays_with_products, 2)
        else:
            # 50% chance to select the same bay for within-bay swaps
            bay_idx1 = random.choice(bays_with_products)
            bay_idx2 = bay_idx1

        # Skip if either bay has no shelves with products
        if not bay_shelf_placements[bay_idx1] or not bay_shelf_placements[bay_idx2]:
            continue

        # Choose a random shelf from each bay
        shelf1_y = random.choice(list(bay_shelf_placements[bay_idx1].keys()))
        shelf2_y = random.choice(list(bay_shelf_placements[bay_idx2].keys()))

        # Get placements on these shelves
        shelf1_placement_indices = bay_shelf_placements[bay_idx1][shelf1_y]
        shelf2_placement_indices = bay_shelf_placements[bay_idx2][shelf2_y]

        # Skip if either shelf is empty
        if not shelf1_placement_indices or not shelf2_placement_indices:
            continue

        # Try to find best swap candidates
        best_swap_candidates = None
        best_swap_score = float('inf')  # Lower is better

        # Try all possible product swaps between shelves
        for idx1 in shelf1_placement_indices:
            for idx2 in shelf2_placement_indices:
                # Get current placements
                placement1 = mutated_placements[idx1]
                placement2 = mutated_placements[idx2]

                # Calculate swap score based on multiple factors
                # 1. Height difference (lower is better)
                height_diff = abs(placement1.product.width - placement2.product.width)

                # 2. Family similarity (same family is better)
                family_factor = 0 if placement1.product.family == placement2.product.family else 10

                # 3. Length compatibility with target shelves
                # Check if product 1 would fit on shelf 2's available space and vice versa
                length_compatibility = min(
                    placement1.product.length - placement2.product.length,
                    placement2.product.length - placement1.product.length
                )
                length_factor = abs(length_compatibility)

                # Combined score (lower is better)
                swap_score = height_diff + family_factor + length_factor

                # Update best candidates if better score found
                if swap_score < best_swap_score:
                    best_swap_candidates = (idx1, idx2)
                    best_swap_score = swap_score

        # If no good swap candidates found, continue to next attempt
        if not best_swap_candidates:
            continue

        # Perform the swap
        idx1, idx2 = best_swap_candidates
        placement1 = mutated_placements[idx1]
        placement2 = mutated_placements[idx2]

        # Save original product assignments
        original_product1 = placement1.product
        original_product2 = placement2.product

        # Swap the products
        placement1.product = original_product2
        placement2.product = original_product1

        # Adjust horizontal position if necessary (on both shelves)
        # First reorganize shelf 1
        reorganize_shelf_products(
            mutated_placements,
            placement1.bay_index,
            placement1.y_position
        )

        # Then reorganize shelf 2 (if different from shelf 1)
        if placement1.bay_index != placement2.bay_index or placement1.y_position != placement2.y_position:
            reorganize_shelf_products(
                mutated_placements,
                placement2.bay_index,
                placement2.y_position
            )

        # After swap, check if shelves need vertical repositioning due to product height changes
        # This happens when the max product height on a shelf changes
        adjusted_placements = adjust_shelf_positions(
            mutated_placements,
            bays,
            shelves
        )

        # Check if the adjusted solution is valid
        if validate_solution(adjusted_placements, bays):
            # Update placements with the adjusted ones
            mutated_placements = adjusted_placements
            successful_mutations += 1
        else:
            # Revert the swap if solution is invalid
            placement1.product = original_product1
            placement2.product = original_product2
            # Revert any shelf reorganization
            reorganize_shelf_products(
                mutated_placements,
                placement1.bay_index,
                placement1.y_position
            )
            if placement1.bay_index != placement2.bay_index or placement1.y_position != placement2.y_position:
                reorganize_shelf_products(
                    mutated_placements,
                    placement2.bay_index,
                    placement2.y_position
                )

    # If no successful mutations, print a warning
    #if successful_mutations == 0:
        #print("Warning: No successful product swaps occurred.")

    return mutated_placements

#Attempt to consolidate products into fewer bays
# by moving products from less utilized bays to more utilized ones.
def mutate_consolidate_bays(placements: List[Any], bays: List[Any], shelves: List[Any],
                            mutation_rate: float = 0.7) -> List[Any]:
    # Create a deep copy to avoid modifying the original
    mutated_placements = copy.deepcopy(placements)

    # Group placements by bay and calculate utilization
    bay_placements = {}
    bay_utilization = {}

    for placement in mutated_placements:
        if placement.bay_index not in bay_placements:
            bay_placements[placement.bay_index] = []
        bay_placements[placement.bay_index].append(placement)

    # Calculate utilization for each bay
    for bay_idx, bay_products in bay_placements.items():
        if bay_idx >= len(bays):
            continue

        bay_height = bays[bay_idx].height
        total_vertical_space = sum(p.product.width for p in bay_products)
        bay_utilization[bay_idx] = total_vertical_space / bay_height

    # If we have only one bay, nothing to consolidate
    if len(bay_placements) <= 1:
        return mutated_placements

    # Sort bays by utilization (least utilized first)
    sorted_bays = sorted(bay_utilization.keys(), key=lambda idx: bay_utilization[idx])

    # Determine how many bays to try to consolidate based on mutation rate
    num_bays_to_attempt = max(1, int(len(sorted_bays) * mutation_rate))

    # Start with least utilized bays and try to move their products to other bays
    bays_to_consolidate = sorted_bays[:num_bays_to_attempt]
    destination_bays = sorted_bays[num_bays_to_attempt:]

    # If no destination bays, try a different bay to consolidate
    if not destination_bays and len(sorted_bays) > 1:
        bays_to_consolidate = [sorted_bays[0]]  # Just try to consolidate the least utilized bay
        destination_bays = sorted_bays[1:]

    # Track products that were successfully moved
    moved_products = []

    # Try to move products from bays_to_consolidate to destination_bays
    for source_bay_idx in bays_to_consolidate:
        # Skip if there are no products in this bay
        if not bay_placements.get(source_bay_idx):
            continue

        # Get all products from this bay
        source_products = bay_placements[source_bay_idx]

        # Try to move each product to a destination bay
        for product in source_products:
            # Skip if we've already moved this product
            if product in moved_products:
                continue

            # Try each destination bay
            for dest_bay_idx in destination_bays:
                # Skip if source and destination are the same
                if dest_bay_idx == source_bay_idx:
                    continue

                # Try to place the product in this bay
                original_bay_idx = product.bay_index
                original_x = product.x_position
                original_y = product.y_position

                # Attempt to place at the bottom of the destination bay
                # This is a simple approach - in a real scenario, you'd want a more
                # sophisticated placement strategy
                dest_bay = bays[dest_bay_idx]

                # Find existing shelves in destination bay
                dest_shelves = []
                for p in mutated_placements:
                    if p.bay_index == dest_bay_idx and p.y_position not in dest_shelves:
                        dest_shelves.append(p.y_position)

                # If no shelves exist, create one at the bottom
                if not dest_shelves:
                    new_shelf_y = shelves[0].thickness  # Position after shelf thickness
                    product.bay_index = dest_bay_idx
                    product.y_position = new_shelf_y
                    product.x_position = 0  # Start at leftmost position
                    moved_products.append(product)
                    break

                # Try to place on an existing shelf with sufficient space
                placed = False
                for shelf_y in sorted(dest_shelves):
                    # Find products on this shelf
                    shelf_products = [p for p in mutated_placements
                                      if p.bay_index == dest_bay_idx and p.y_position == shelf_y]

                    # Calculate the rightmost position
                    if shelf_products:
                        rightmost_x = max(p.x_position + p.product.length for p in shelf_products)
                        # Check if there's enough room for our product
                        if rightmost_x + product.product.length <= dest_bay.width:
                            # Place it after the rightmost product
                            product.bay_index = dest_bay_idx
                            product.y_position = shelf_y
                            product.x_position = rightmost_x + 2.0  # Add a small gap
                            placed = True
                            moved_products.append(product)
                            break

                if placed:
                    break

                # If we couldn't place on existing shelves, try to create a new shelf above existing ones
                if not placed:
                    # Find topmost shelf and its product height
                    top_shelf_y = max(dest_shelves)
                    top_shelf_products = [p for p in mutated_placements
                                          if p.bay_index == dest_bay_idx and p.y_position == top_shelf_y]

                    top_product_height = max(p.product.width for p in top_shelf_products) if top_shelf_products else 0

                    # Calculate position for new shelf
                    new_shelf_y = top_shelf_y + top_product_height + shelves[0].thickness

                    # Check if this would fit in the bay height
                    if new_shelf_y + product.product.width <= dest_bay.height:
                        product.bay_index = dest_bay_idx
                        product.y_position = new_shelf_y
                        product.x_position = 0  # Start at leftmost position
                        moved_products.append(product)
                        break

                # If we couldn't place it, revert to original position
                product.bay_index = original_bay_idx
                product.x_position = original_x
                product.y_position = original_y

    # Check if we've successfully emptied any bays
    emptied_bays = []
    for bay_idx in bays_to_consolidate:
        if bay_idx in bay_placements:
            # Count how many products remain in this bay after moves
            remaining_products = [p for p in mutated_placements
                                  if p.bay_index == bay_idx and p not in moved_products]

            if not remaining_products:
                emptied_bays.append(bay_idx)

    # Debug info about consolidation results
    # print(f"Moved {len(moved_products)} products, emptied {len(emptied_bays)} bays")

    # Adjust layout after consolidation
    # This ensures products are properly arranged on shelves
    for bay_idx in destination_bays:
        # Group by shelf
        shelf_groups = {}
        for p in mutated_placements:
            if p.bay_index == bay_idx:
                if p.y_position not in shelf_groups:
                    shelf_groups[p.y_position] = []
                shelf_groups[p.y_position].append(p)

        # Reorganize each shelf
        for shelf_y, shelf_products in shelf_groups.items():
            if len(shelf_products) <= 1:
                continue

            # Sort products by x position
            shelf_products.sort(key=lambda p: p.x_position)

            # Reposition from left to right with proper spacing
            current_x = shelf_products[0].x_position
            for i, product in enumerate(shelf_products):
                if i == 0:
                    current_x += product.product.length + 2.0  # Standard gap
                    continue

                # Position product
                product.x_position = current_x

                # Update for next product
                current_x += product.product.length + 2.0  # Standard gap

    # Verify solution validity after consolidation
    if not validate_solution(mutated_placements, bays):
        # If consolidation led to an invalid solution, return the original
        # print("Consolidation resulted in invalid solution - reverting to original")
        return placements

    return mutated_placements

#Check if both parents have the same products in each bay (ignoring positions).
def has_same_bay_contents(parent1: List[Any], parent2: List[Any]) -> bool:
    # Group products by bay for both parents
    bays_parent1 = {}
    for p in parent1:
        bay_idx = p.bay_index
        if bay_idx not in bays_parent1:
            bays_parent1[bay_idx] = []
        # Store product key (family, length, width) to identify products
        bays_parent1[bay_idx].append((p.product.family, p.product.length, p.product.width))

    bays_parent2 = {}
    for p in parent2:
        bay_idx = p.bay_index
        if bay_idx not in bays_parent2:
            bays_parent2[bay_idx] = []
        bays_parent2[bay_idx].append((p.product.family, p.product.length, p.product.width))

    # Check if all bays contain the same products
    for bay_idx in set(bays_parent1.keys()) | set(bays_parent2.keys()):
        # If bay exists in only one parent
        if bay_idx not in bays_parent1 or bay_idx not in bays_parent2:
            return False

        # Sort products for comparison
        products1 = sorted(bays_parent1[bay_idx])
        products2 = sorted(bays_parent2[bay_idx])

        # Check if products match
        if products1 != products2:
            return False

    return True


#####CROSSOVERS#############

#Perform a bay-based crossover between two parent solutions.
#This crossover preserves bay validity by taking complete bays from either parent.
## Only works correctly when both parents have the same products in each bay.
def crossover_bay_based(
        parent1: List[Any],
        parent2: List[Any],
        bays: List[Any],
        shelves: List[Any]
) -> List[Any]:
    # Verify if parents have the same products in each bay
    if not has_same_bay_contents(parent1, parent2):
        #print("Parents have different bay contents, bay-based crossover not applicable")
        return None
    # Create a deep copy of the first parent as the base for our offspring
    offspring = copy.deepcopy(parent1)

    # Determine how many bays we're working with
    used_bays = set()
    for p in parent1:
        used_bays.add(p.bay_index)

    max_bay_index = max(used_bays) if used_bays else 0

    # Randomly decide which bays to take from parent2
    bays_from_parent2 = []
    for bay_idx in range(max_bay_index + 1):
        # Randomly choose which parent to take this bay from
        if random.random() < 0.5:  # 50% chance
            bays_from_parent2.append(bay_idx)

    if not bays_from_parent2:
        # If no bays selected from parent2, pick at least one randomly
        if max_bay_index >= 0:
            bays_from_parent2 = [random.randint(0, max_bay_index)]

    # Group parent2 placements by bay
    parent2_by_bay = {}
    for i, p in enumerate(parent2):
        bay_idx = p.bay_index
        if bay_idx not in parent2_by_bay:
            parent2_by_bay[bay_idx] = []
        parent2_by_bay[bay_idx].append((i, p))

    # Replace selected bays in offspring with those from parent2
    for bay_idx in bays_from_parent2:
        # First, remove placements for this bay from offspring
        offspring = [p for p in offspring if p.bay_index != bay_idx]

        # Then add the placements from parent2 for this bay
        if bay_idx in parent2_by_bay:
            for _, p in parent2_by_bay[bay_idx]:
                # Deep copy to avoid reference issues
                offspring.append(copy.deepcopy(p))

    # Check if the offspring is valid
    if not validate_solution(offspring, bays):
        #print("Warning: Crossover produced invalid solution")
        return None

    return offspring

##Perform a family-based crossover between two parent solutions.
#This crossover takes product families from either parent, then repairs the solution.
def crossover_family_based(
        parent1: List[Any],
        parent2: List[Any],
        bays: List[Any],
        shelves: List[Any]
) -> List[Any]:
    # Start with a copy of parent1
    offspring = copy.deepcopy(parent1)

    # Group products by family in both parents
    families_parent1 = {}
    for i, p in enumerate(parent1):
        family = p.product.family
        if family not in families_parent1:
            families_parent1[family] = []
        families_parent1[family].append((i, p))

    families_parent2 = {}
    for i, p in enumerate(parent2):
        family = p.product.family
        if family not in families_parent2:
            families_parent2[family] = []
        families_parent2[family].append((i, p))

    # Find families present in both parents
    common_families = set(families_parent1.keys()) & set(families_parent2.keys())

    if not common_families:
        print("No common families between parents, returning parent1")
        return copy.deepcopy(parent1)

    # Randomly select families to take from parent2
    num_families_to_swap = random.randint(1, len(common_families))
    families_to_swap = random.sample(list(common_families), num_families_to_swap)

    # Replace these families in offspring
    for family in families_to_swap:
        # Remove this family from offspring
        offspring = [p for p in offspring if p.product.family != family]

        # Add placements for this family from parent2
        for _, p in families_parent2[family]:
            offspring.append(copy.deepcopy(p))

    # Reorganize shelves to avoid product overlaps
    used_shelves = set()
    for p in offspring:
        used_shelves.add((p.bay_index, p.y_position))

    for bay_idx, shelf_y in used_shelves:
        reorganize_shelf_products(offspring, bay_idx, shelf_y)

    # Adjust shelf positions after crossover
    try:
        adjusted_offspring = adjust_shelf_positions(offspring, bays, shelves)

        # Validate the solution
        if validate_solution(adjusted_offspring, bays):
            return adjusted_offspring
    except Exception as e:
        print(f"Error during shelf adjustment after crossover: {str(e)}")

    # If we get here, the solution was invalid - return parent1
    #print("Warning: Crossover produced invalid solution, returning parent1")
    return copy.deepcopy(parent1)

#Perform a shelf-based crossover between two parent solutions.
#This crossover takes complete shelves from either parent.
def crossover_shelf_based(
        parent1: List[Any],
        parent2: List[Any],
        bays: List[Any],
        shelves: List[Any]
) -> List[Any]:
    # Start with a copy of parent1
    offspring = copy.deepcopy(parent1)

    # Group placements by bay and shelf for both parents
    shelves_parent1 = {}
    for i, p in enumerate(parent1):
        shelf_key = (p.bay_index, p.y_position)
        if shelf_key not in shelves_parent1:
            shelves_parent1[shelf_key] = []
        shelves_parent1[shelf_key].append((i, p))

    shelves_parent2 = {}
    for i, p in enumerate(parent2):
        shelf_key = (p.bay_index, p.y_position)
        if shelf_key not in shelves_parent2:
            shelves_parent2[shelf_key] = []
        shelves_parent2[shelf_key].append((i, p))

    # Randomly select which shelves to take from parent2
    # We'll use the shelves from parent2 but keep their original bay positions
    shelves_to_swap = []
    all_shelves = list(shelves_parent1.keys())

    # Choose approximately half the shelves
    num_shelves_to_swap = random.randint(1, max(1, len(all_shelves) // 2))
    if all_shelves:
        shelves_to_swap = random.sample(all_shelves, num_shelves_to_swap)

    # Replace these shelves in offspring
    for shelf_key in shelves_to_swap:
        bay_idx, shelf_y = shelf_key

        # Remove products on this shelf from offspring
        offspring = [p for p in offspring if not (p.bay_index == bay_idx and p.y_position == shelf_y)]

        # If parent2 has this shelf, add its products to offspring
        if shelf_key in shelves_parent2:
            for _, p in shelves_parent2[shelf_key]:
                offspring.append(copy.deepcopy(p))

    # Adjust shelf positions after crossover
    try:
        adjusted_offspring = adjust_shelf_positions(offspring, bays, shelves)

        # Validate the solution
        if validate_solution(adjusted_offspring, bays):
            return adjusted_offspring
    except Exception as e:
        print(f"Error during shelf adjustment after crossover: {str(e)}")

    # If we get here, the solution was invalid - return parent1
    #print("Warning: Crossover produced invalid solution, returning parent1")
    return copy.deepcopy(parent1)

#Apply a mutation that allows for subsequent crossover.
#Only applies mutations that don't swap products between bays.
def select_mutation_for_crossover(
        parent: List[Any],
        bays: List[Any],
        shelves: List[Any],
        mutation_rate: float = 0.7
) -> Tuple[List[Any], str]:
    # Create a deep copy of the parent
    offspring = copy.deepcopy(parent)

    # Only use mutations that preserve bay contents
    mutation_strategy = random.choice([
        "reorder_products",
        "reorder_shelves"
    ])

    # Apply selected mutation
    if mutation_strategy == "reorder_products":
        offspring = mutate_reorder_shelf_products(offspring, mutation_rate)
    else:  # reorder_shelves
        offspring = mutate_reorder_bay_shelves(offspring, bays, shelves, mutation_rate)

    # Check if offspring is valid
    if not validate_solution(offspring, bays):
        # If invalid, return parent and mark no mutation
        return copy.deepcopy(parent), "none"

    return offspring, mutation_strategy