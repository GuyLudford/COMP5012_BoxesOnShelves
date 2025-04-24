from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class Product:
    family: int
    quantity: int
    length: float
    width: float
    height: float


@dataclass
class Bay:
    width: float
    height: float
    depth: float
    available_height: float
    shelves: List['Shelf'] = field(default_factory=list)


@dataclass
class Shelf:
    number: int
    thickness: float
    position: float  # height of top surface
    top_gap: float
    left_gap: float
    inter_gap: float
    right_gap: float
    products: List[Tuple[Product, float]] = field(default_factory=list)  # (product, x_position)
    bay_index: int = -1  # Track which bay this shelf is in


@dataclass
class Placement:
    product: Product
    bay_index: int
    shelf_index: int
    x_position: float
    y_position: float