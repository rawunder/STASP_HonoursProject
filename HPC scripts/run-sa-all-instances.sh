#!/bin/bash
#SBATCH --account=compsci
#SBATCH --partition=ada
#SBATCH --nodes=1 --ntasks=40
#SBATCH --time=10:00:00
#SBATCH --job-name="SA-AllInstances"
#SBATCH --mail-user=mdxroa001@myuct.ac.za
#SBATCH --mail-type=BEGIN,END,FAIL

# Load required modules
module load tools/boost-1.86.0

# Set working directory to simulated annealing folder

echo "Starting Simulated Annealing on all 45 ITC2021 instances..."

# Create results directory
mkdir -p /home/mdxroa001/results/sa_exp/

# Define all 45 instances across Early, Middle, and Late categories
declare -a instances=(
    "instances/itc2021/ITC2021_Early_1.xml"
    "instances/itc2021/ITC2021_Early_2.xml"
    "instances/itc2021/ITC2021_Early_3.xml"
    "instances/itc2021/ITC2021_Early_4.xml"
    "instances/itc2021/ITC2021_Early_5.xml"
    "instances/itc2021/ITC2021_Early_6.xml"
    "instances/itc2021/ITC2021_Early_7.xml"
    "instances/itc2021/ITC2021_Early_8.xml"
    "instances/itc2021/ITC2021_Early_9.xml"
    "instances/itc2021/ITC2021_Early_10.xml"
    "instances/itc2021/ITC2021_Early_11.xml"
    "instances/itc2021/ITC2021_Early_12.xml"
    "instances/itc2021/ITC2021_Early_13.xml"
    "instances/itc2021/ITC2021_Early_14.xml"
    "instances/itc2021/ITC2021_Early_15.xml"
    "instances/itc2021/ITC2021_Middle_1.xml"
    "instances/itc2021/ITC2021_Middle_2.xml"
    "instances/itc2021/ITC2021_Middle_3.xml"
    "instances/itc2021/ITC2021_Middle_4.xml"
    "instances/itc2021/ITC2021_Middle_5.xml"
    "instances/itc2021/ITC2021_Middle_6.xml"
    "instances/itc2021/ITC2021_Middle_7.xml"
    "instances/itc2021/ITC2021_Middle_8.xml"
    "instances/itc2021/ITC2021_Middle_9.xml"
    "instances/itc2021/ITC2021_Middle_10.xml"
    "instances/itc2021/ITC2021_Middle_11.xml"
    "instances/itc2021/ITC2021_Middle_12.xml"
    "instances/itc2021/ITC2021_Middle_13.xml"
    "instances/itc2021/ITC2021_Middle_14.xml"
    "instances/itc2021/ITC2021_Middle_15.xml"
    "instances/itc2021/ITC2021_Late_1.xml"
    "instances/itc2021/ITC2021_Late_2.xml"
    "instances/itc2021/ITC2021_Late_3.xml"
    "instances/itc2021/ITC2021_Late_4.xml"
    "instances/itc2021/ITC2021_Late_5.xml"
    "instances/itc2021/ITC2021_Late_6.xml"
    "instances/itc2021/ITC2021_Late_7.xml"
    "instances/itc2021/ITC2021_Late_8.xml"
    "instances/itc2021/ITC2021_Late_9.xml"
    "instances/itc2021/ITC2021_Late_10.xml"
    "instances/itc2021/ITC2021_Late_11.xml"
    "instances/itc2021/ITC2021_Late_12.xml"
    "instances/itc2021/ITC2021_Late_13.xml"
    "instances/itc2021/ITC2021_Late_14.xml"
    "instances/itc2021/ITC2021_Late_15.xml"
)

# Function to run SA on a single instance
run_sa_instance() {
    local instance_path=$1
    local instance_name=$(basename "$instance_path" .xml)
    
    echo "Processing $instance_name..."
    
    # Run SA with best tuned parameters (default config) and JSON output
    timeout 7200 ./bin/stt \
        --main::instance "$instance_path" \
        --main::method ESA-3S \
        --main::use_hcp-enable > "/home/mdxroa001/results/sa_exp/${instance_name}.json"
    
    local exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "  Timeout occurred for $instance_name (7200s)"
    elif [ $exit_code -ne 0 ]; then
        echo "  Error occurred for $instance_name (exit code: $exit_code)"
    else
        echo "  Completed $instance_name successfully"
    fi
}

# Export function for parallel execution
export -f run_sa_instance

# Run instances in parallel using GNU parallel or xargs
# Since we have 45 instances and 40 cores, run 40 in parallel and queue the remaining 5
printf '%s\n' "${instances[@]}" | xargs -n 1 -P 40 -I {} bash -c 'run_sa_instance "$@"' _ {}

echo "All 45 ITC2021 instances completed."
echo "Results saved to /home/mdxroa001/results/sa_exp/"