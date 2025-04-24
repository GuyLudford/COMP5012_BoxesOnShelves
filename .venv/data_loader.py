from typing import List, Tuple
from data_models import Product, Bay, Shelf

def load_products(products_file: str) -> List[Product]:
    products = []
    with open(products_file, 'r') as file:
        for line in file:
            family, quantity, length, width, height = map(int, line.split())
            products.append(Product(family, quantity, length, width, height))
    return products


def load_bays(bay_file: str) -> List[Bay]:
    bays = []
    with open(bay_file, 'r') as file:
        for line in file:
            width, height, depth, available_height = map(float, line.split())
            bays.append(Bay(width, height, depth, available_height))
    return bays


def load_shelves(shelves_file: str) -> List[Shelf]:
    shelves = []
    with open(shelves_file, 'r') as file:
        for line in file:
            number, thickness, position, top_gap, left_gap, inter_gap, right_gap = map(float, line.split())
            shelves.append(Shelf(int(number), thickness, position, top_gap, left_gap, inter_gap, right_gap))
    return shelves


def load_problem_data(products_file, bay_file, shelves_file):
    products = load_products(products_file)
    bays = load_bays(bay_file)
    shelves = load_shelves(shelves_file)
    return products, bays, shelves