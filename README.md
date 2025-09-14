# WeddingTableMatch

A small demo project showing a constraint-based approach to wedding seating.
The solver uses a lightweight heuristic that keeps friends together and
avoids known conflicts when possible.

## Setting up a Python Virtual Environment (venv)

It is recommended to use a virtual environment to manage dependencies for this project. Follow these steps to create and activate a `venv` environment:

1. **Create a virtual environment:**

    ```bash
    python3 -m venv venv
    ```

2. **Activate the virtual environment:**

    - On macOS/Linux:

      ```bash
      source venv/bin/activate
      ```

    - On Windows:

      ```cmd
      venv\Scripts\activate
      ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Deactivate the environment when done:**

    ```bash
    deactivate
    ```


## Quickstart

Install dependencies:

```bash
pip install -r requirements.txt
```

### Command line interface

Run the solver on the sample data:

```bash
python -m wedding_table_match.cli \
    --guests tests/data/guests.csv \
    --relationships tests/data/relationships.csv \
    --tables tests/data/tables.csv
```

### Streamlit app

Launch the web UI:

```bash
streamlit run app.py
```

Upload the three CSV files, review the data and click **Run solver** to see
assignments. A download button is provided to export the results as CSV.
