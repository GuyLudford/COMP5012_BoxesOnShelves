import copy
import random
from typing import List, Any, Callable
from data_models import Product, Bay, Shelf, Placement
from data_loader import load_problem_data
#from visualisation import visualisation

#Generate multiple random initial populations
def initialize_population(
        num_populations: int,
        products: List[Any],
        bays: List[Any],
        shelves: List[Any],
        place_products_randomly_func: callable
) -> List[List[Any]]:
    populations = []

    for _ in range(num_populations):
        # Deep copy to ensure each population starts from original product list
        current_products = copy.deepcopy(products)
        current_bays = copy.deepcopy(bays)
        current_shelves = copy.deepcopy(shelves)

        # Reset bays and shelves
        for bay in current_bays:
            bay.shelves.clear()

        # Generate a random placement
        placement = place_products_randomly_func(
            current_products,
            current_bays,
            current_shelves
        )

        populations.append(placement)

    return populations

#Generate a varied initial population using only the random placement function,
#but with different configurations to create diversity in bay usage.
def initialize_varied_population(
        num_populations: int,
        products: List[Any],
        bays: List[Any],
        shelves: List[Any],
        place_products_randomly_func: callable
) -> List[List[Any]]:
    populations = []

    print(f"Generating {num_populations} populations with varied configurations")

    # Generate populations with varying degrees of efficiency
    for i in range(num_populations):
        # Deep copy to ensure each population starts from original product list
        current_products = copy.deepcopy(products)
        current_bays = copy.deepcopy(bays)
        current_shelves = copy.deepcopy(shelves)

        # Reset bays and shelves
        for bay in current_bays:
            bay.shelves.clear()

        # For creating diversity
        # 1. Use different subsets of bays (forces inefficiency for some placements)
        # 2. Shuffle product order differently to affect placement

        # Create diversity with varied bay usage
        if random.random() < 0.4:  # 40% chance to restrict bay usage
            # Use only a subset of bays to force inefficiency
            max_bays_to_use = random.randint(1, len(current_bays))
            available_bays = current_bays[:max_bays_to_use]
        else:
            available_bays = current_bays

        # Create diversity with product ordering
        sorted_products = copy.deepcopy(current_products)

        # Choose a sorting strategy for products
        sort_strategy = random.randint(0, 4)
        if sort_strategy == 0:
            # Default random order
            random.shuffle(sorted_products)
        elif sort_strategy == 1:
            # Sort by family
            sorted_products.sort(key=lambda p: p.family)
        elif sort_strategy == 2:
            # Sort by size (length * width), largest first
            sorted_products.sort(key=lambda p: p.length * p.width, reverse=True)
        elif sort_strategy == 3:
            # Sort by width (height), tallest first
            sorted_products.sort(key=lambda p: p.width, reverse=True)
        elif sort_strategy == 4:
            # Group by family then shuffle groups
            by_family = {}
            for p in sorted_products:
                if p.family not in by_family:
                    by_family[p.family] = []
                by_family[p.family].append(p)

            # Rebuild product list with grouped families
            sorted_products = []
            family_keys = list(by_family.keys())
            random.shuffle(family_keys)
            for family in family_keys:
                sorted_products.extend(by_family[family])

        # Generate a random placement using chosen configuration
        placement = place_products_randomly_func(
            sorted_products,
            available_bays,
            current_shelves
        )

        populations.append(placement)

    # Validate and report on initial population
    valid_count = 0
    bay_usage_stats = []
    fractional_bays_stats = []

    for population in populations:
        if validate_solution(population, bays):
            valid_count += 1

            # Calculate bay usage for statistics
            bay_placements = {}
            for placement in population:
                if placement.bay_index not in bay_placements:
                    bay_placements[placement.bay_index] = []
                bay_placements[placement.bay_index].append(placement)

            num_bays_used = len(bay_placements)
            bay_usage_stats.append(num_bays_used)

            # Calculate fractional bays for diversity check
            fractional_bays = 0
            for bay_idx, placements_list in bay_placements.items():
                # Skip invalid bay indices
                if bay_idx >= len(bays):
                    continue

                # Get bay height
                bay_height = bays[bay_idx].height

                # Group by shelf
                shelf_groups = {}
                for p in placements_list:
                    if p.y_position not in shelf_groups:
                        shelf_groups[p.y_position] = []
                    shelf_groups[p.y_position].append(p)

                # Calculate total vertical space
                if shelf_groups:
                    total_vertical = 0
                    for shelf_y, items in shelf_groups.items():
                        max_height = max(p.product.width for p in items)
                        shelf_thickness = 1.0  # Default
                        total_vertical += shelf_thickness + max_height

                    # Calculate fraction
                    bay_usage_fraction = min(1.0, total_vertical / bay_height)
                    fractional_bays += 1.0 if bay_usage_fraction > 0.95 else bay_usage_fraction

            fractional_bays_stats.append(fractional_bays)

    # Report statistics on initial population
    if bay_usage_stats:
        min_bays = min(bay_usage_stats)
        max_bays = max(bay_usage_stats)
        avg_bays = sum(bay_usage_stats) / len(bay_usage_stats)

        min_frac = min(fractional_bays_stats)
        max_frac = max(fractional_bays_stats)
        avg_frac = sum(fractional_bays_stats) / len(fractional_bays_stats)

        print(f"Initial population statistics:")
        print(f"  Valid solutions: {valid_count}/{len(populations)}")
        print(f"  Bay usage range: {min_bays} to {max_bays} bays (avg: {avg_bays:.2f})")
        print(f"  Fractional bays range: {min_frac:.2f} to {max_frac:.2f} (avg: {avg_frac:.2f})")

        # Check diversity of bay usage
        unique_bay_counts = len(set(f"{x:.2f}" for x in fractional_bays_stats))
        print(f"  Unique fractional bay values: {unique_bay_counts}")
        print(f"  Diversity ratio: {unique_bay_counts / len(fractional_bays_stats):.2%}")

    return populations

##########################################################################################

Randomly place products onto shelves within bays, with enhanced tracking.
def place_products_randomly(products: List[Product], bays: List[Bay], shelves: List[Shelf]) -> List[Placement]:
    
    # Create a copy of products to work with (to track remaining quantities)
    remaining_products = [
        Product(p.family, p.quantity, p.length, p.width, p.height)
        for p in products
    ]

    # List to store final placements
    placements = []

    # Iterate through bays
    for bay_index, bay in enumerate(bays):
        # Reset bay height to 0 for each new bay
        current_bay_height = 0

        # Track current shelf configuration
        current_shelf_index = 0

        # Clear any existing shelves in this bay
        bay.shelves.clear()

        # Continue placing shelves until bay height is exhausted
        while current_bay_height < bay.height and remaining_products:
            # Ensure the current shelf exists and update its position
            if current_shelf_index < len(shelves):
                # Create a new Shelf instance with the same properties
                current_shelf = Shelf(
                    number=shelves[current_shelf_index].number,
                    thickness=shelves[current_shelf_index].thickness,
                    position=current_bay_height,
                    top_gap=shelves[current_shelf_index].top_gap,
                    left_gap=shelves[current_shelf_index].left_gap,
                    inter_gap=shelves[current_shelf_index].inter_gap,
                    right_gap=shelves[current_shelf_index].right_gap,
                    bay_index=bay_index
                )
            else:
                # If used all base shelves, clone the last shelf
                last_shelf = shelves[-1]
                current_shelf = Shelf(
                    number=last_shelf.number + 1,
                    thickness=last_shelf.thickness,
                    position=current_bay_height,
                    top_gap=last_shelf.top_gap,
                    left_gap=last_shelf.left_gap,
                    inter_gap=last_shelf.inter_gap,
                    right_gap=last_shelf.right_gap,
                    bay_index=bay_index
                )

            # Calculate available shelf width
            current_shelf_width = bay.width - (
                    current_shelf.left_gap +
                    current_shelf.right_gap
            )

            # Track current x position on the shelf
            current_x = current_shelf.left_gap

            # Shuffle products to ensure randomness
            random.shuffle(remaining_products)

            # Track the tallest product on this shelf for precise next shelf placement
            max_product_height = 0

            # Iterate through products
            for product in remaining_products[:]:
                # Skip if no quantity left
                if product.quantity <= 0:
                    remaining_products.remove(product)
                    continue

                # Check if product fits on current shelf width
                if current_x + product.length <= current_shelf_width:
                    # Place product ON TOP of the shelf (adding shelf thickness)
                    placement = Placement(
                        product=product,
                        bay_index=bay_index,
                        shelf_index=current_shelf_index,
                        x_position=current_x,
                        y_position=current_shelf.position + current_shelf.thickness
                    )
                    placements.append(placement)

                    # Add product to shelf's product list with its x position
                    current_shelf.products.append((product, current_x))

                    # Update max product height
                    max_product_height = max(max_product_height, product.width)

                    # Update product quantity
                    product.quantity -= 1

                    # Move x position
                    current_x += product.length + current_shelf.inter_gap

                    # If no more quantity, remove product
                    if product.quantity <= 0:
                        remaining_products.remove(product)

                # If shelf width is full, stop placing on this shelf
                if current_x >= current_shelf_width:
                    break

            # Add current shelf to bay's shelf list
            bay.shelves.append(current_shelf)

            # Update bay height to start next shelf above the tallest product
            current_bay_height = current_shelf.position + current_shelf.thickness + max_product_height

            # Move to next shelf
            current_shelf_index += 1

        # Break if no more products to place
        if not remaining_products:
            break
    #recalculate_shelf_positions(placements, bays, shelves)
    return placements

#Place products with greater diversity in bay utilization.
def place_products_with_diversity(products: List[Product], bays: List[Bay], shelves: List[Shelf]) -> List[Placement]:
    # Create a copy of products to work with
    remaining_products = [
        Product(p.family, p.quantity, p.length, p.width, p.height)
        for p in products
    ]

    # List to store final placements
    placements = []

    # Choose a placement strategy randomly for this solution
    strategy = random.randint(1, 5)

    # Strategy 1: Group by family
    if strategy == 1:
        # Group products by family
        family_groups = {}
        for product in remaining_products:
            if product.family not in family_groups:
                family_groups[product.family] = []
            family_groups[product.family].append(product)

        # Sort families by total product size (descending)
        sorted_families = sorted(
            family_groups.keys(),
            key=lambda f: sum(p.length * p.width * p.quantity for p in family_groups[f]),
            reverse=True
        )

        # Create a new ordered list of products grouped by family
        ordered_products = []
        for family in sorted_families:
            ordered_products.extend(family_groups[family])

        # Replace our working list with the family-grouped list
        remaining_products = ordered_products

    # Strategy 2: Distribute across bays
    elif strategy == 2:
        # Calculate target products per bay
        total_products_count = sum(p.quantity for p in remaining_products)
        target_per_bay = max(1, total_products_count // len(bays))

        # Shuffle products for randomness
        random.shuffle(remaining_products)

        # Process each bay
        for bay_index, bay in enumerate(bays):
            # Clear any existing shelves
            bay.shelves.clear()

            # Calculate available shelf width
            shelf_index = 0
            current_shelf = None

            # Set up first shelf
            if shelf_index < len(shelves):
                current_shelf = Shelf(
                    number=shelves[shelf_index].number,
                    thickness=shelves[shelf_index].thickness,
                    position=0,  # Start at bottom
                    top_gap=shelves[shelf_index].top_gap,
                    left_gap=shelves[shelf_index].left_gap,
                    inter_gap=shelves[shelf_index].inter_gap,
                    right_gap=shelves[shelf_index].right_gap,
                    bay_index=bay_index
                )
                bay.shelves.append(current_shelf)
            else:
                continue  # Skip if no shelf template available

            # Calculate available shelf width
            current_shelf_width = bay.width - (
                    current_shelf.left_gap + current_shelf.right_gap
            )

            # Track current x position on the shelf
            current_x = current_shelf.left_gap

            # Track products placed in this bay
            products_in_bay = 0

            # Place products until we reach target per bay or run out
            while remaining_products and products_in_bay < target_per_bay:
                product = remaining_products[0]

                # If product doesn't fit on current shelf, try to create a new shelf
                if current_x + product.length > current_shelf_width:
                    # Calculate position for next shelf based on previous shelf
                    next_shelf_position = current_shelf.position + current_shelf.thickness

                    # Only proceed if we have vertical space
                    if next_shelf_position + product.width < bay.height:
                        shelf_index += 1

                        # Create new shelf
                        if shelf_index < len(shelves):
                            next_shelf = Shelf(
                                number=shelves[shelf_index].number,
                                thickness=shelves[shelf_index].thickness,
                                position=next_shelf_position,
                                top_gap=shelves[shelf_index].top_gap,
                                left_gap=shelves[shelf_index].left_gap,
                                inter_gap=shelves[shelf_index].inter_gap,
                                right_gap=shelves[shelf_index].right_gap,
                                bay_index=bay_index
                            )
                        else:
                            # Clone the last shelf
                            next_shelf = Shelf(
                                number=shelf_index,
                                thickness=current_shelf.thickness,
                                position=next_shelf_position,
                                top_gap=current_shelf.top_gap,
                                left_gap=current_shelf.left_gap,
                                inter_gap=current_shelf.inter_gap,
                                right_gap=current_shelf.right_gap,
                                bay_index=bay_index
                            )

                        bay.shelves.append(next_shelf)
                        current_shelf = next_shelf
                        current_x = current_shelf.left_gap
                        current_shelf_width = bay.width - (
                                current_shelf.left_gap + current_shelf.right_gap
                        )
                    else:
                        # No more vertical space, move to next bay
                        break

                # Place the product
                if current_x + product.length <= current_shelf_width:
                    # Create placement
                    placement = Placement(
                        product=product,
                        bay_index=bay_index,
                        shelf_index=shelf_index,
                        x_position=current_x,
                        y_position=current_shelf.position + current_shelf.thickness
                    )
                    placements.append(placement)

                    # Add product to shelf
                    current_shelf.products.append((product, current_x))

                    # Update position
                    current_x += product.length + current_shelf.inter_gap

                    # Update product quantity
                    product.quantity -= 1
                    products_in_bay += 1

                    # Remove product if no more quantity
                    if product.quantity <= 0:
                        remaining_products.remove(product)
                else:
                    # Strange case - should not happen if we've created a new shelf
                    break

    # Strategy 3: Height prioritisation 
    elif strategy == 3:
        # Sort by height (descending)
        remaining_products.sort(key=lambda p: p.width, reverse=True)

    # Strategy 4: Width prioritization (place widest products first)
    elif strategy == 4:
        # Sort by length (descending)
        remaining_products.sort(key=lambda p: p.length, reverse=True)

    # Strategy 5: Random selection with scattered placement
    elif strategy == 5:
        # Use random bay selection for each product
        pass

    # Now place remaining products using a modified version of the random placement function

    # Randomize bay order for placement
    bay_order = list(range(len(bays)))
    random.shuffle(bay_order)

    # If strategy 5, we'll use scattered placement
    scattered_placement = (strategy == 5)

    # Process each bay in our randomized order
    for bay_idx in bay_order:
        bay = bays[bay_idx]

        # Reset bay height to 0 for each new bay
        current_bay_height = 0

        # Track current shelf configuration
        current_shelf_index = 0

        # Clear any existing shelves in this bay
        bay.shelves.clear()

        # Continue placing shelves until bay height is exhausted
        while current_bay_height < bay.height and remaining_products:
            # Ensure the current shelf exists and update its position
            if current_shelf_index < len(shelves):
                # Create a new Shelf instance with the same properties
                current_shelf = Shelf(
                    number=shelves[current_shelf_index].number,
                    thickness=shelves[current_shelf_index].thickness,
                    position=current_bay_height,
                    top_gap=shelves[current_shelf_index].top_gap,
                    left_gap=shelves[current_shelf_index].left_gap,
                    inter_gap=shelves[current_shelf_index].inter_gap,
                    right_gap=shelves[current_shelf_index].right_gap,
                    bay_index=bay_idx
                )
            else:
                # If we've used all base shelves, clone the last shelf
                last_shelf = shelves[-1]
                current_shelf = Shelf(
                    number=last_shelf.number + 1,
                    thickness=last_shelf.thickness,
                    position=current_bay_height,
                    top_gap=last_shelf.top_gap,
                    left_gap=last_shelf.left_gap,
                    inter_gap=last_shelf.inter_gap,
                    right_gap=last_shelf.right_gap,
                    bay_index=bay_idx
                )

            # Calculate available shelf width
            current_shelf_width = bay.width - (
                    current_shelf.left_gap + current_shelf.right_gap
            )

            # Track current x position on the shelf
            current_x = current_shelf.left_gap

            # If using scattered placement, introduce some randomness in how full we make each shelf
            max_fill_percentage = 1.0
            if scattered_placement:
                # Sometimes leave shelves partially empty (60-100%)
                max_fill_percentage = random.uniform(0.6, 1.0)

            # Calculate max width to use on this shelf
            max_width_to_use = current_shelf_width * max_fill_percentage

            # Iterate through products
            products_to_consider = remaining_products.copy()
            if scattered_placement:
                # In scattered mode, randomly shuffle before each shelf
                random.shuffle(products_to_consider)

            # Track the tallest product on this shelf for precise next shelf placement
            max_product_height = 0

            # Try to place products on this shelf
            for product in products_to_consider:
                # Skip if no quantity left
                if product.quantity <= 0:
                    continue

                # Check if product fits on current shelf width
                if current_x + product.length <= max_width_to_use:
                    # Place product ON TOP of the shelf (adding shelf thickness)
                    placement = Placement(
                        product=product,
                        bay_index=bay_idx,
                        shelf_index=current_shelf_index,
                        x_position=current_x,
                        y_position=current_shelf.position + current_shelf.thickness
                    )
                    placements.append(placement)

                    # Add product to shelf's product list with its x position
                    current_shelf.products.append((product, current_x))

                    # Update max product height
                    max_product_height = max(max_product_height, product.width)

                    # Update product quantity
                    product.quantity -= 1

                    # Move x position
                    current_x += product.length + current_shelf.inter_gap

                    # Update our working list
                    if product.quantity <= 0:
                        remaining_products = [p for p in remaining_products if p != product]

                # If shelf width is full or we've reached our target fill percentage, stop placing on this shelf
                if current_x >= max_width_to_use:
                    break

            # Add current shelf to bay's shelf list
            bay.shelves.append(current_shelf)

            # Update bay height to start next shelf above the tallest product
            current_bay_height = current_shelf.position + current_shelf.thickness + max_product_height

            # Move to next shelf
            current_shelf_index += 1

            # In scattered placement, sometimes intentionally leave vertical gaps
            if scattered_placement and random.random() < 0.3:
                # Add 5-20% extra vertical space
                extra_space = bay.height * random.uniform(0.05, 0.2)
                current_bay_height += extra_space

    # Handle any remaining products
    if remaining_products:
        # Just place remaining products in the last bay
        for product in remaining_products:
            # Find last bay with a shelf
            last_bay_idx = bay_order[-1]
            last_bay = bays[last_bay_idx]

            # Find or create a shelf
            if not last_bay.shelves:
                # Create a new shelf
                new_shelf = Shelf(
                    number=0,
                    thickness=shelves[0].thickness if shelves else 1.0,
                    position=0,
                    top_gap=shelves[0].top_gap if shelves else 0,
                    left_gap=shelves[0].left_gap if shelves else 0,
                    inter_gap=shelves[0].inter_gap if shelves else 2.0,
                    right_gap=shelves[0].right_gap if shelves else 0,
                    bay_index=last_bay_idx
                )
                last_bay.shelves.append(new_shelf)

            # Get the last shelf
            last_shelf = last_bay.shelves[-1]

            # Place the product
            placement = Placement(
                product=product,
                bay_index=last_bay_idx,
                shelf_index=len(last_bay.shelves) - 1,
                x_position=last_shelf.left_gap,
                y_position=last_shelf.position + last_shelf.thickness
            )
            placements.append(placement)

            # Add to shelf's products
            last_shelf.products.append((product, last_shelf.left_gap))

    return placements

def SingleInitialise():
    # Load problem data using existing functions
    products, bays, shelves = load_problem_data(
        'Products',
        'Baytp1',
        'Shelves'
    )

    # Place products randomly
    placements = place_products_randomly(products, bays, shelves)

    # Print detailed placement information
    print("Detailed Placement Information:")
    for bay_index, bay in enumerate(bays):
        print(f"\nBay {bay_index}:")
        for shelf in bay.shelves:
            print(f"  Shelf {shelf.number} (Position: {shelf.position}):")
            for (product, x_pos) in shelf.products:
                print(f"    - Product Family {product.family} at x={x_pos}")

    # Visualize the placements
    visualize_placements(placements, bays, shelves)