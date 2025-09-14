"""
Command line interface for WeddingTableMatch.

This module provides a command-line interface for running the wedding
table seating optimization solver.
"""

import argparse
import sys
from pathlib import Path
from .solver import WeddingTableSolver


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='WeddingTableMatch: Optimize wedding table seating arrangements'
    )
    
    parser.add_argument(
        '--guests',
        type=str,
        required=True,
        help='Path to guests CSV file'
    )
    
    parser.add_argument(
        '--tables',
        type=str,
        required=True,
        help='Path to tables CSV file'
    )
    
    parser.add_argument(
        '--relationships',
        type=str,
        required=True,
        help='Path to relationships CSV file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='seating_arrangement.txt',
        help='Output file for the seating arrangement (default: seating_arrangement.txt)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate input files exist
    for file_arg, file_path in [
        ('guests', args.guests),
        ('tables', args.tables),
        ('relationships', args.relationships)
    ]:
        if not Path(file_path).exists():
            print(f"Error: {file_arg} file '{file_path}' does not exist", file=sys.stderr)
            return 1
    
    try:
        # Initialize solver
        solver = WeddingTableSolver()
        
        if args.verbose:
            print("Loading data files...")
        
        # Load data
        solver.load_guests_from_csv(args.guests)
        solver.load_tables_from_csv(args.tables)
        solver.load_relationships_from_csv(args.relationships)
        
        if args.verbose:
            stats = solver.get_stats()
            print(f"Loaded {stats['guests']} guests, {stats['tables']} tables, "
                  f"{stats['relationships']} relationships")
            print(f"Total table capacity: {stats['total_capacity']}")
        
        # Solve the problem
        if args.verbose:
            print("Solving seating arrangement...")
            
        arrangement = solver.solve()
        
        if arrangement is None:
            print("Error: No solution found", file=sys.stderr)
            return 1
            
        # Validate solution
        if not solver.validate_solution(arrangement):
            print("Error: Generated solution is invalid", file=sys.stderr)
            return 1
            
        if args.verbose:
            print(f"Solution found with score: {arrangement.score:.2f}")
        
        # Write output
        write_seating_arrangement(arrangement, solver, args.output)
        
        if args.verbose:
            print(f"Seating arrangement written to: {args.output}")
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def write_seating_arrangement(arrangement, solver, filename):
    """Write the seating arrangement to a file."""
    with open(filename, 'w') as f:
        f.write("Wedding Table Seating Arrangement\n")
        f.write("=" * 35 + "\n\n")
        
        # Get guest and table lookup dictionaries
        guests_by_id = {guest.id: guest for guest in solver.guests}
        tables_by_id = {table.id: table for table in solver.tables}
        
        # Write arrangement by table
        for table in solver.tables:
            guests_at_table = arrangement.get_guests_at_table(table.id)
            
            f.write(f"Table {table.id}: {table.name}\n")
            f.write(f"Capacity: {table.capacity}, Seated: {len(guests_at_table)}\n")
            
            if table.location:
                f.write(f"Location: {table.location}\n")
                
            if guests_at_table:
                f.write("Guests:\n")
                for guest_id in guests_at_table:
                    guest = guests_by_id[guest_id]
                    f.write(f"  - {guest.name}")
                    if guest.age:
                        f.write(f" (age {guest.age})")
                    if guest.dietary_restrictions:
                        f.write(f" [dietary: {guest.dietary_restrictions}]")
                    f.write("\n")
            else:
                f.write("No guests assigned\n")
                
            f.write("\n")
            
        f.write(f"Overall Score: {arrangement.score:.2f}\n")


if __name__ == '__main__':
    sys.exit(main())