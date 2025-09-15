#!/bin/bash
#SBATCH --account=compsci
#SBATCH --partition=ada
#SBATCH --nodes=1 --ntasks=40
#SBATCH --time=50:00:00
#SBATCH --job-name="ClingoLateInstances"
#SBATCH --mail-user=mdxroa001@myuct.ac.za
#SBATCH --mail-type=BEGIN,END,FAIL

# Use module to gain easy access to software
module load python/miniconda3-py3.12
source activate clingoInstall

# For shared memory (default for standard Clingo):
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK  

echo "Starting ASP solving on ITC2021 Late instances with all configurations..."

# Define all 15 configurations
declare -A configs=(
    ["BB0"]="--opt-strategy=bb,lin"
    ["BB0-HEU3-RST"]="--opt-strategy=bb,lin --opt-heuristic=sign,model --restart-on-model"
    ["BB2"]="--opt-strategy=bb,hier"
    ["BB2-TR"]="--opt-strategy=bb,hier --configuration=trendy"
    ["Dom5"]="--dom-mod=5,16"
    ["USC1"]="--opt-strategy=usc,oll"
    ["USC11"]="--opt-strategy=usc,oll,1"
    ["USC11-CR"]="--opt-strategy=usc,oll,1 --configuration=crafty"
    ["USC11-JP"]="--opt-strategy=usc,oll,1 --configuration=jumpy"
    ["USC13"]="--opt-strategy=usc,oll,3"
    ["USC13-CR"]="--opt-strategy=usc,oll,3 --configuration=crafty"
    ["USC13-HEU3-RST-HD"]="--opt-strategy=usc,oll,3 --opt-heuristic=sign,model --restart-on-model --configuration=handy"
    ["USC3-JP"]="--opt-strategy=usc,oll,1 --configuration=jumpy"
    ["USC15"]="--opt-strategy=usc,oll,7"
    ["USC15-CR"]="--opt-strategy=usc,oll,7 --configuration=crafty"
)

# Instance directory
INSTANCE_DIR="/home/denga/Project/simulated_annealing/sa4stt/instances/itc2021"

# Loop through all ITC2021 Late XML files (1-15)
for i in {1..15}; do
    xml_file="${INSTANCE_DIR}/ITC2021_Late_${i}.xml"
    
    if [ -f "$xml_file" ]; then
        echo "Processing ITC2021_Late_${i}..."
        
        # Generate facts from XML
        python3 itc2021_fact_parser.py "$xml_file" "facts_late${i}.lp"
        
        # Test each configuration
        for config_name in "${!configs[@]}"; do
            echo "  Running configuration: $config_name"
            
            # Create output directory if it doesn't exist
            mkdir -p "results/late"
            
            # Run Clingo with 10-minute timeout and save to JSON
            timeout 600s clingo encodingV4.lp "facts_late${i}.lp" \
                ${configs[$config_name]} \
                --parallel-mode=$OMP_NUM_THREADS \
                --opt-mode=optN \
                --outf=2 > "results/late/late${i}_${config_name}.json"
            
            # Check if timeout occurred
            if [ $? -eq 124 ]; then
                echo "  Timeout occurred for Late_${i} with $config_name"
            fi
        done
        
        # Clean up facts file
        rm "facts_late${i}.lp"
    else
        echo "Warning: $xml_file not found"
    fi
done

echo "All ITC2021 Late instances completed."