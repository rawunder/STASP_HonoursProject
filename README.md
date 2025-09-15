# Sports Timetabling with ASP and Simulated Annealing

This project provides a comprehensive framework for solving the International Timetabling Competition (ITC) 2021 problem using two primary methods: Answer Set Programming (ASP) and Simulated Annealing (SA).

It includes:
- ASP encodings for the ITC2021 problem.
- A winning Simulated Annealing solver adapted for the ITC2021 problem.
- A suite of Python scripts for parsing, analyzing, validating, and processing results from both solvers.

## Project Structure

- **`/Code`**: Contains the core ASP encoding, fact parser and instances
- **`/simulated_annealing`**: Contains the C++ source code for the SA solver.
- **`/Results`**: Contains the JSON output from the ASP and SA solver experiments.
- **`/Validation`**: Contains the RobinX validator for verifying solution correctness.
- **`/` (root)**: Contains a  Python scripts for processing.

## Dependencies

- **Python 3**: For running the analysis and processing scripts.
- **pandas**: `pip install pandas`
- **Clingo**: For the ASP solver. (See [Potassco installation guide](https://potassco.org/doc/INSTALL.html))
- **C++ Compiler & Make**: For building the SA solver (e.g., `g++`, `make`).
- **Boost Libraries**: The SA solver requires `libboost` (>= 1.71). On Debian/Ubuntu, you can install it with `sudo apt-get install libboost-all-dev`.

## How to Run

### Answer Set Programming (ASP) Solver

**a. Generate ASP Facts:**

First, convert an ITC2021 XML instance file into ASP facts using the provided parser:

```bash
python3 Code/itc2021_fact_parser.py <path_to_instance.xml> facts.lp
```

**b. Run Clingo:**

Next, run Clingo with the main encoding (`encoding_final.lp`) and the generated facts file. 
```bash
clingo Code/encoding_final.lp facts.lp
```

The output should be redirected to a JSON file for processing.
```bash
clingo Code/encoding_final.lp facts.lp --outf=2 > solution.json
```

**To run the full ASP analysis pipeline:**

```bash
python3 process_all.py
```

This will:
1.  Extract reference bounds from the validator.
2.  Convert all JSON results in `Results/main_exp` to XML.
3.  Perform a comprehensive analysis and generate `complete_analysis.csv`.

## Tutorial: Running the ASP Solver

This tutorial guides you through solving an ITC2021 instance with the ASP solver.

**Prerequisites:**
- You have installed all dependencies.
- The ITC2021 XML instances are in `instances/early/`, `instances/middle/`, and `instances/late/`.

**Step 1: Convert XML to ASP Facts**

Use the `itc2021_fact_parser.py` script to convert the XML instance into ASP facts. For example, to convert the `ITC2021_Early_1.xml` instance:

```bash
python3 Code/itc2021_fact_parser.py instances/early/ITC2021_Early_1.xml early_1_facts.lp
```

This will create a `early_1_facts.lp` file in your project root.

**Step 2: Run the ASP Solver with a Portfolio Configuration**

This project uses different Clingo configurations (portfolios) for each instance type. Here are the recommended portfolios:

*   **Top 3 Portfolios:**

    ```bash
    # Portfolio 1: BB2
    clingo Code/encoding_final.lp early_1_facts.lp --opt-strategy=bb,hier --outf=2 > early_1_bb2.json

    # Portfolio 2: Dom5
    clingo Code/encoding_final.lp early_1_facts.lp --dom-mod=5,16  --outf=2 > early_1_dom5.json

    # Portfolio 3: USC15-CR
    clingo Code/encoding_final.lp early_1_facts.lp --opt-strategy=usc,oll,7 --configuration=crafty  --outf=2 > early_1_usc15_cr.json
    ```


**Step 3: Interpreting the Output**

The output of Clingo will be a JSON file (e.g., `early_1_bb2.json`). This file contains detailed information about the solving process, including:
- **`Result`**: The solver result (e.g., `SATISFIABLE`, `OPTIMUM FOUND`, `UNKNOWN`).
- **`Models`**: Information about the solutions found, including the optimization cost.
- **`Time`**: Detailed timing information.

This JSON file can then be used with the analysis scripts in this project.

## Script Descriptions

Here is a description of the main Python scripts in this project:

-   `parse_results.py`: Parses Clingo JSON results from configuration experiments into a pandas DataFrame.
-   `analyze_results.py`: Performs a comprehensive analysis of ASP results, compares with reference bounds, and generates a detailed CSV report.
-   `asp_to_xml.py`: Converts ASP solver results (in JSON format) into the ITC2021 XML solution format.
-   `Code/itc2021_fact_parser.py`: Converts ITC2021 XML instance files into ASP facts.
-   `Code/process_results.py`: A simple script to process Clingo JSON output and extract schedules and optimization values.
-   `compare_sa_validation.py`: Compares the costs from the SA solver with the objectives from the RobinX validator.
-   `create_sa_summary.py`: Creates a summary report for the simulated annealing results.
-   `extract_bounds.py`: Extracts reference bounds from the RobinX repository XML files and creates a `reference_bounds.csv` file.
-   `process_all.py`: The main pipeline script that orchestrates the entire ASP results processing workflow.
-   `sa_analyze_results.py`: Analyzes the results from the simulated annealing solver.
-   `sa_process_all.py`: The main pipeline script for the simulated annealing results processing.
-   `sa_to_xml.py`: Converts simulated annealing results into ITC2021 XML solution format.
-   `simulated_annealing/sa4stt/solver/pugixml/scripts/archive.py`: A third-party script for creating archives (zip, tar.gz).
-   `validate_sa_xml.py`: Validates SA XML solution files using the RobinX validator.
-   `validate_xml.py`: Validates ASP XML solution files using the RobinX validator.