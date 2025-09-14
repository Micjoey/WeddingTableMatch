"""
WeddingTableMatch: Constraint-based wedding seating optimizer.

A Python package for solving wedding table seating arrangements using 
constraint programming and optimization techniques.
"""

__version__ = "0.1.0"
__author__ = "WeddingTableMatch Contributors"

from .models import Guest, Table, Relationship
from .solver import WeddingTableSolver

__all__ = ["Guest", "Table", "Relationship", "WeddingTableSolver"]