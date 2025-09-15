#!/bin/bash
#SBATCH --account=compsci
#SBATCH --partition=ada
#SBATCH --nodes=1 --ntasks=40
#SBATCH --time=96:00:00
#SBATCH --job-name="ClingoEarlyInstances"
#SBATCH --mail-user=mdxroa001@myuct.ac.za
#SBATCH --mail-type=BEGIN,END,FAIL

# Use module to gain easy access to software
module load python/miniconda3-py3.12
source activate clingoConda

# For shared memory (default for standard Clingo):
export OMP_NUM_THREADS=$SLURM_NTASKS

echo "Starting ASP solving on ITC2021 Early instances with top configurations..."

# Define all 15 configurations
declare -A configs=(
    ["BB2"]="--opt-strategy=bb,hier"
    ["Dom5"]="--dom-mod=5,16"
    ["USC15-CR"]="--opt-strategy=usc,oll,7 --configuration=crafty"
)

# Loop through all ITC2021 Early XML files (1-15)
for i in {1..15}; do
    xml_file="ITC2021_Early_${i}.xml"

    if [ -f "$xml_file" ]; then
        echo "Processing ITC2021_Early_${i}..."

        # Generate facts from XML
        python3 itc2021_fact_parser.py "$xml_file" "facts_early${i}.lp"

        # Test each configuration
        for config_name in "${!configs[@]}"; do
            echo "  Running configuration: $config_name"

            # Run Clingo with 10-minute timeout and save to JSON
            clingo encodingV4.lp "facts_early${i}.lp" \
                ${configs[$config_name]} \
                --parallel-mode=$OMP_NUM_THREADS \
                --time-limit=7200 \
                --outf=2 > "/home/mdxroa001/results/main_exp/early/early${i}_${config_name}.json"

            # Check if timeout occurred
            if [ $? -eq 124 ]; then
                echo "  Timeout occurred for Early_${i} with $config_name"
            fi
        done

        # Clean up facts file
        rm "facts_early${i}.lp"
    else
        echo "Warning: $xml_file not found"
    fi
done

echo "All ITC2021 Early instances completed."