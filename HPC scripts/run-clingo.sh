#!/bin/bash
#SBATCH --account=compsci
#SBATCH --partition=ada
#SBATCH --nodes=1 --ntasks=40
#SBATCH --time=10:00:00
#SBATCH --job-name="ClingoTestInstances"
#SBATCH --mail-user=mdxroa001@myuct.ac.za
#SBATCH --mail-type=BEGIN,END,FAIL

# Use module to gain easy access to software
module load python/miniconda3-py3.12
source activate clingoConda

# For shared memory (default for standard Clingo):
export OMP_NUM_THREADS=$SLURM_NTASKS

echo "Starting ASP solving on all test instances..."

# Loop through all test XML files
for xml_file in ITC2021_Test*.xml; do
    if [ -f "$xml_file" ]; then
        # Extract test number for output naming
        test_num=$(echo "$xml_file" | sed 's/ITC2021_Test\([0-9]*\)\.xml/\1/')

        echo "Processing Test $test_num..."

        # Generate facts from XML
        python3 itc2021_fact_parser.py "$xml_file" "facts_test${test_num}.lp"

        # Run Clingo and save to JSON
        clingo encodingV4.lp "facts_test${test_num}.lp" \
            --parallel-mode=$OMP_NUM_THREADS,split \
            --time-limit=3600 \
            --outf=2 > "/home/mdxroa001/testInstanceOutput/split_test${test_num}.json"
    fi
done

echo "All test instances completed."