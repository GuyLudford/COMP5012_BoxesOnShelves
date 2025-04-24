from typing import List, Any

#Check if a solution is valid (no overlapping products)
def check_solution_validity(placements: List[Any]) -> bool:
    # Group by bay and shelf
    shelf_placements = {}
    for placement in placements:
        shelf_key = (placement.bay_index, placement.y_position)
        if shelf_key not in shelf_placements:
            shelf_placements[shelf_key] = []
        shelf_placements[shelf_key].append(placement)

    # Check each shelf for overlaps
    for shelf_key, placements_on_shelf in shelf_placements.items():
        # Sort by x position
        sorted_placements = sorted(placements_on_shelf, key=lambda p: p.x_position)

        # Check for overlaps
        for i in range(len(sorted_placements) - 1):
            p1 = sorted_placements[i]
            p2 = sorted_placements[i + 1]

            # Calculate end position of first product
            p1_end = p1.x_position + p1.product.length

            # Check if it overlaps with start of next product
            if p1_end > p2.x_position:
                return False  # Overlap detected

    return True  # No overlaps found

#  Check if shelves are properly spaced (no overlapping shelves or products)
def check_shelf_spacing_validity(placements: List[Any]) -> bool:
    # Group placements by bay
    bay_placements = {}
    for placement in placements:
        if placement.bay_index not in bay_placements:
            bay_placements[placement.bay_index] = []
        bay_placements[placement.bay_index].append(placement)

    # For each bay, group placements by shelf
    for bay_idx, bay_group in bay_placements.items():
        # Group by shelf (y_position)
        shelf_groups = {}
        for placement in bay_group:
            if placement.y_position not in shelf_groups:
                shelf_groups[placement.y_position] = []
            shelf_groups[placement.y_position].append(placement)

        # Sort shelves by y position
        sorted_shelves = sorted(shelf_groups.keys())

        # Check for overlaps between shelves and products
        for i in range(len(sorted_shelves) - 1):
            lower_shelf_y = sorted_shelves[i]
            upper_shelf_y = sorted_shelves[i + 1]

            # Products on lower shelf
            lower_shelf_products = shelf_groups[lower_shelf_y]

            # Find max height of any product on lower shelf
            # Assuming product width is the vertical dimension
            max_product_height = max(p.product.width for p in lower_shelf_products) if lower_shelf_products else 0

            # Calculate the top edge of the lower shelf's products
            # (shelf position + product height)
            lower_shelf_top = lower_shelf_y + max_product_height

            # If upper shelf position is less than lower shelf's top edge
            if upper_shelf_y <= lower_shelf_top:
                return False  # Overlap detected - shelves too close

    return True  # No shelf spacing issues found

#Check if all products fit within their bay width.
def check_bay_width_validity(placements: List[Any], bays: List[Any]) -> bool:
    
    # Group by bay and shelf
    shelf_placements = {}
    for placement in placements:
        shelf_key = (placement.bay_index, placement.y_position)
        if shelf_key not in shelf_placements:
            shelf_placements[shelf_key] = []
        shelf_placements[shelf_key].append(placement)

    # Check each shelf's products against bay width
    for (bay_idx, _), placements_on_shelf in shelf_placements.items():
        # Skip if bay index is invalid
        if bay_idx >= len(bays):
            return False

        bay = bays[bay_idx]

        for placement in placements_on_shelf:
            # Check if product extends beyond bay width
            if placement.x_position + placement.product.length > bay.width:
                return False

    return True

# Comprehensive solution validation checking both product and shelf validity
#     across all bays.
def validate_solution(placements: List[Any], bays: List[Any] = None) -> bool:
    # Check for product overlaps on shelves
    product_valid = check_solution_validity(placements)

    # Check for proper shelf spacing
    shelf_valid = check_shelf_spacing_validity(placements)

    # Check that products fit within bay width if bays are provided
    bay_width_valid = True
    if bays is not None:
        bay_width_valid = check_bay_width_validity(placements, bays)

    return product_valid and shelf_valid and bay_width_valid