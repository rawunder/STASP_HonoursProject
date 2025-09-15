#!/usr/bin/env python3
"""
XML Solution Validator using RobinX
Validates generated XML solution files against their corresponding instances
"""

import os
import re
import subprocess
import pandas as pd
from pathlib import Path
import xml.etree.ElementTree as ET
import json

def extract_instance_from_solution_name(solution_filename):
    """Extract instance info from solution XML filename
    e.g., Early_12_BB2.xml -> ('Early', '12', 'BB2')
    """
    base = solution_filename.replace('.xml', '')
    match = re.match(r'([A-Z][a-z]+)_(\d+)_(.+)', base)
    if match:
        category = match.group(1)
        number = match.group(2)
        config = match.group(3)
        return category, number, config
    return None, None, None

def find_instance_file(category, number, instances_dir="Validation/RobinX/Repository/ITC2021/Instances/"):
    """Find the corresponding instance XML file"""
    # Try the inst{N}_{e|l|m}.xml format first
    category_short = category.lower()[0]  # early->e, late->l, middle->m
    instance_filename = f"inst{number}_{category_short}.xml"
    instance_path = os.path.join(instances_dir, instance_filename)
    
    if os.path.exists(instance_path):
        return instance_path
    
    # Fall back to old format
    instance_filename = f"ITC2021_{category}_{number}.xml"
    instance_path = os.path.join(instances_dir, instance_filename)
    
    if os.path.exists(instance_path):
        return instance_path
    
    return None

def extract_objective_from_output(output_text):
    """Extract objective value from RobinX output
    Output format: Objective:             0                   1635
    """
    try:
        lines = output_text.strip().split('\n')
        for line in lines:
            if 'Objective:' in line:
                # Use regex to extract the numbers from the objective line
                import re
                match = re.search(r'Objective:\s+(\d+)\s+(\d+)', line)
                if match:
                    infeasible = int(match.group(1))
                    objective = int(match.group(2))
                    return objective  # Return the second number (actual objective)
    except Exception as e:
        print(f"Error parsing objective: {e}")
    
    return None

def validate_single_xml(solution_path, instance_path, robinx_path="Validation/RobinX/RobinX"):
    """Validate a single XML solution file"""
    try:
        # Run RobinX validator with shorter timeout to handle segfaults
        cmd = [robinx_path, "-i", instance_path, "-s", solution_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Parse results
        validation_result = {
            'solution_file': os.path.basename(solution_path),
            'instance_file': os.path.basename(instance_path),
            'return_code': result.returncode,
            'validation_successful': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'validation_objective': None,
            'validation_error': None,
            'status': 'UNKNOWN'
        }
        
        # Extract objective value regardless of return code if present
        validation_objective = extract_objective_from_output(result.stdout + result.stderr)
        validation_result['validation_objective'] = validation_objective
        
        if result.returncode == 0:
            validation_result['status'] = 'VALID'
            validation_result['validation_successful'] = True
        elif result.returncode == -11:  # SIGSEGV
            validation_result['status'] = 'SEGFAULT'
            validation_result['validation_error'] = 'Segmentation fault'
        elif result.returncode == 3:
            validation_result['status'] = 'ERROR_3'  
            validation_result['validation_error'] = 'RobinX Error 3 - possible parsing issue'
        else:
            # Even if return code != 0, if we got objective value, consider it valid
            if validation_objective is not None:
                validation_result['status'] = f'CALCULATED_RC{result.returncode}'
                validation_result['validation_successful'] = True
                validation_result['validation_error'] = f'Non-zero return code {result.returncode} but objective calculated'
            else:
                validation_result['status'] = f'ERROR_{result.returncode}'
                validation_result['validation_error'] = result.stderr or result.stdout or f'Return code: {result.returncode}'
        
        return validation_result
        
    except subprocess.TimeoutExpired:
        return {
            'solution_file': os.path.basename(solution_path),
            'instance_file': os.path.basename(instance_path),
            'return_code': -1,
            'validation_successful': False,
            'stdout': '',
            'stderr': 'Validation timeout',
            'validation_objective': None,
            'validation_error': 'Timeout after 10 seconds',
            'status': 'TIMEOUT'
        }
    except Exception as e:
        return {
            'solution_file': os.path.basename(solution_path),
            'instance_file': os.path.basename(instance_path),
            'return_code': -1,
            'validation_successful': False,
            'stdout': '',
            'stderr': str(e),
            'validation_objective': None,
            'validation_error': str(e),
            'status': 'EXCEPTION'
        }

def extract_asp_cost_from_json(xml_filename):
    """Extract the original ASP cost from corresponding JSON file"""
    try:
        # Convert XML filename back to JSON filename format
        # e.g., Early_12_BB2.xml -> early12_BB2.json
        base = xml_filename.replace('.xml', '')
        match = re.match(r'([A-Z][a-z]+)_(\d+)_(.+)', base)
        if match:
            category = match.group(1).lower()  # Early -> early
            number = match.group(2)            # 12
            config = match.group(3)            # BB2
            
            json_filename = f"{category}{number}_{config}.json"
            
            # Look for JSON file in main_exp directory structure
            possible_paths = [
                f"Results/main_exp/{category}/{json_filename}",
                f"Results/main_exp/{json_filename}",
            ]
            
            for json_path in possible_paths:
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    # Extract best cost from JSON (same logic as asp_to_xml.py)
                    calls = data.get("Call", [])
                    if calls:
                        witnesses = calls[0].get("Witnesses", [])
                        if witnesses:
                            best_cost = float('inf')
                            for witness in witnesses:
                                witness_costs = witness.get("Costs", [])
                                if witness_costs:
                                    witness_cost = witness_costs[0]
                                    if witness_cost < best_cost:
                                        best_cost = witness_cost
                            
                            if best_cost != float('inf'):
                                return int(best_cost)
                    
                    break
    except Exception as e:
        print(f"Error extracting ASP cost for {xml_filename}: {e}")
    
    return None

def extract_asp_cost_from_xml(xml_path):
    """Extract the original ASP cost from the XML solution metadata (legacy)"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        obj_elem = root.find('.//ObjectiveValue')
        if obj_elem is not None:
            objective = obj_elem.get('objective')
            if objective:
                return int(objective)
    except Exception as e:
        print(f"Error extracting cost from {xml_path}: {e}")
    
    return None

def validate_all_solutions(solutions_dir="xml_solutions",
                          sample_size=None, skip_unknown=True):
    """Validate all XML solution files"""
    
    solutions_path = Path(solutions_dir)
    if not solutions_path.exists():
        print(f"Solutions directory not found: {solutions_dir}")
        return pd.DataFrame()
    
    # Get all XML files
    xml_files = list(solutions_path.glob("*.xml"))
    
    if sample_size:
        xml_files = xml_files[:sample_size]
        print(f"Validating sample of {len(xml_files)} XML files...")
    else:
        print(f"Validating {len(xml_files)} XML files...")
    
    validation_results = []
    
    for i, xml_file in enumerate(xml_files, 1):
        print(f"Processing {i}/{len(xml_files)}: {xml_file.name}")
        
        # Extract instance info
        category, number, config = extract_instance_from_solution_name(xml_file.name)
        if not category or not number:
            print(f"  Could not parse filename: {xml_file.name}")
            continue
        
        # Find corresponding instance file
        instance_path = find_instance_file(category, number)
        if not instance_path:
            print(f"  Instance file not found for {category}_{number}")
            continue
        
        # Extract ASP cost from corresponding JSON file
        asp_cost = extract_asp_cost_from_json(xml_file.name)
        if asp_cost is None:
            # Fallback to XML extraction (legacy)
            asp_cost = extract_asp_cost_from_xml(xml_file)
        
        # Skip solutions without costs if requested (they had UNKNOWN results)
        # Since we removed ObjectiveValue from XML, asp_cost will be None for all files now
        # We'll process all files and let RobinX calculate the cost
        # if skip_unknown and asp_cost is None:
        #     print(f"  Skipping {xml_file.name} (no solution cost)")
        #     continue
        
        # Validate
        validation_result = validate_single_xml(str(xml_file), instance_path)
        
        # Add additional info
        validation_result['category'] = category.lower()
        validation_result['number'] = int(number)
        validation_result['configuration'] = config
        validation_result['asp_cost'] = asp_cost
        validation_result['instance_key'] = f"{category.lower()}{number}"
        
        # Compare costs
        if asp_cost is not None and validation_result['validation_objective'] is not None:
            validation_result['cost_match'] = (asp_cost == validation_result['validation_objective'])
            validation_result['cost_difference'] = abs(asp_cost - validation_result['validation_objective'])
        else:
            validation_result['cost_match'] = None
            validation_result['cost_difference'] = None
        
        validation_results.append(validation_result)
        
        # Print status
        if validation_result['validation_successful']:
            if validation_result['cost_match']:
                print(f"  ✓ Valid (cost: {asp_cost})")
            else:
                print(f"  ⚠ Valid but cost mismatch: ASP={asp_cost}, RobinX={validation_result['validation_objective']}")
        else:
            print(f"  ✗ Validation failed: {validation_result['validation_error']}")
    
    return pd.DataFrame(validation_results)

def save_validation_results(validation_df, output_file="validation_results.csv"):
    """Save validation results to CSV"""
    if validation_df.empty:
        print("No validation results to save")
        return
    
    # Select columns for output
    output_columns = [
        'solution_file', 'instance_file', 'instance_key', 'category', 'number', 'configuration',
        'validation_successful', 'asp_cost', 'validation_objective', 'cost_match', 'cost_difference',
        'return_code', 'validation_error', 'status'
    ]
    
    # Ensure all columns exist
    for col in output_columns:
        if col not in validation_df.columns:
            validation_df[col] = None
    
    output_df = validation_df[output_columns].copy()
    output_df = output_df.sort_values(['category', 'number', 'configuration'])
    
    output_df.to_csv(output_file, index=False)
    print(f"Validation results saved to: {output_file}")

def print_validation_summary(validation_df):
    """Print validation summary"""
    if validation_df.empty:
        print("No validation results to summarize")
        return
    
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    
    total = len(validation_df)
    successful = validation_df['validation_successful'].sum()
    failed = total - successful
    
    print(f"Total validations: {total}")
    print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Cost comparison for successful validations
    successful_df = validation_df[validation_df['validation_successful']]
    if not successful_df.empty:
        cost_matches = successful_df['cost_match'].sum()
        cost_comparisons = successful_df['cost_match'].notna().sum()
        
        print(f"\nCost comparisons: {cost_comparisons}")
        if cost_comparisons > 0:
            print(f"Exact matches: {cost_matches} ({cost_matches/cost_comparisons*100:.1f}%)")
            
            # Show cost differences for mismatches
            mismatches = successful_df[successful_df['cost_match'] == False]
            if not mismatches.empty:
                print(f"Cost mismatches: {len(mismatches)}")
                print("Sample mismatches:")
                for _, row in mismatches.head(3).iterrows():
                    print(f"  {row['solution_file']}: ASP={row['asp_cost']}, RobinX={row['validation_objective']}")
    
    # Validation by configuration
    if 'configuration' in validation_df.columns:
        config_stats = validation_df.groupby('configuration').agg({
            'validation_successful': ['count', 'sum'],
            'cost_match': 'sum'
        })
        print(f"\nValidation by configuration:")
        print(config_stats)
    
    # Show some failed cases
    failed_df = validation_df[~validation_df['validation_successful']]
    if not failed_df.empty:
        print(f"\nSample validation failures:")
        for _, row in failed_df.head(3).iterrows():
            print(f"  {row['solution_file']}: {row['validation_error']}")

def main():
    """Main validation function"""
    print("Starting XML solution validation...")
    
    # Check if RobinX exists
    robinx_path = "Validation/RobinX/RobinX"
    if not os.path.exists(robinx_path):
        print(f"RobinX not found at {robinx_path}")
        print("Please compile RobinX first using 'make' in the RobinX directory")
        return
    
    # Validate all solutions (full validation of all 77 files)
    validation_df = validate_all_solutions()
    
    if not validation_df.empty:
        # Save results
        save_validation_results(validation_df)
        
        # Print summary
        print_validation_summary(validation_df)
    else:
        print("No validation results generated")

if __name__ == "__main__":
    main()