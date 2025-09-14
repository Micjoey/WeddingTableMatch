# WeddingTableMatch

Constraint-based wedding seating optimizer using operations research and constraint programming to find optimal seating arrangements for wedding guests.

## Features

- Load guest data, table configurations, and relationship constraints from CSV files
- Use constraint programming to optimize seating arrangements
- Consider guest relationships, dietary restrictions, and table capacity constraints
- Command-line interface for easy execution
- Extensible design for adding custom constraints and objectives

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Micjoey/WeddingTableMatch.git
cd WeddingTableMatch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Run the seating optimizer with your data files:

```bash
python -m src.wedding_table_match.cli \
    --guests data/guests.csv \
    --tables data/tables.csv \
    --relationships data/relationships.csv \
    --output seating_arrangement.txt \
    --verbose
```

### Data Format

#### Guests CSV (`guests.csv`)
```csv
id,name,age,dietary_restrictions
1,Alice Johnson,28,vegetarian
2,Bob Smith,32,
```

#### Tables CSV (`tables.csv`)
```csv
id,name,capacity,location
1,Head Table,8,Front Center
2,Family Table A,10,Left Side
```

#### Relationships CSV (`relationships.csv`)
```csv
guest1_id,guest2_id,relationship_type,strength
1,2,family,1.0
3,4,friend,0.8
5,6,avoid,1.0
```

Relationship types: `family`, `friend`, `colleague`, `plus_one`, `avoid`

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
WeddingTableMatch/
├── src/wedding_table_match/
│   ├── __init__.py
│   ├── models.py          # Data models (Guest, Table, Relationship)
│   ├── solver.py          # Main optimization solver
│   └── cli.py             # Command-line interface
├── tests/
│   └── test_solver.py     # Unit tests
├── data/                  # Sample data files
│   ├── guests.csv
│   ├── tables.csv
│   └── relationships.csv
├── requirements.txt
└── README.md
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request
