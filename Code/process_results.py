#!/usr/bin/env python3
"""
Process Clingo JSON output files to extract schedules and optimization values.
"""

import json
import glob
import sys
import os

def process_clingo_json(json_file):
    """Process a single Clingo JSON output file."""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading {json_file}: {e}")
        return None
    
    result = {
        'file': json_file,
        'status': 'UNKNOWN',
        'optimization_value': None,
        'schedule': None,
        'solve_time': None
    }
    
    # Extract solver result
    if 'Result' in data:
        result['status'] = data['Result']
    
    # Extract solving time
    if 'Time' in data and 'Total' in data['Time']:
        result['solve_time'] = data['Time']['Total']
    
    # Process models if any
    if 'Models' in data and len(data['Models']) > 0:
        last_model = data['Models'][-1]
        
        # Extract optimization value
        if 'Costs' in last_model and len(last_model['Costs']) > 0:
            result['optimization_value'] = last_model['Costs'][0]
        
        # Extract schedule facts
        if 'Value' in last_model:
            schedule_facts = []
            for atom in last_model['Value']:
                if atom.startswith('schedule('):
                    schedule_facts.append(atom)
            result['schedule'] = schedule_facts
    
    return result

def print_summary_table(results):
    """Print a summary table of all results."""
    print("\nSUMMARY TABLE")
    print("=" * 80)
    print(f"{'Test':<6} {'Status':<15} {'Opt Value':<12} {'Schedule Size':<15} {'Time (s)':<10}")
    print("-" * 80)
    
    for result in results:
        if result is None:
            continue
            
        # Extract test number from filename
        test_num = result['file'].replace('test', '').replace('.json', '')
        
        status = result['status']
        opt_val = result['optimization_value'] if result['optimization_value'] is not None else "N/A"
        schedule_size = len(result['schedule']) if result['schedule'] else "N/A"
        time_val = f"{result['solve_time']:.2f}" if result['solve_time'] is not None else "N/A"
        
        print(f"{test_num:<6} {status:<15} {opt_val:<12} {schedule_size:<15} {time_val:<10}")

def save_detailed_results(results, output_file='detailed_results.txt'):
    """Save detailed results to a text file."""
    with open(output_file, 'w') as f:
        f.write("DETAILED CLINGO RESULTS\n")
        f.write("=" * 50 + "\n\n")
        
        for result in results:
            if result is None:
                continue
                
            test_num = result['file'].replace('test', '').replace('.json', '')
            f.write(f"TEST {test_num}\n")
            f.write(f"Status: {result['status']}\n")
            f.write(f"Optimization Value: {result['optimization_value']}\n")
            f.write(f"Solve Time: {result['solve_time']} seconds\n")
            
            if result['schedule']:
                f.write(f"Schedule ({len(result['schedule'])} games):\n")
                for fact in sorted(result['schedule']):
                    f.write(f"  {fact}\n")
            else:
                f.write("No schedule found\n")
            
            f.write("\n" + "-" * 50 + "\n\n")

def main():
    # Find all test JSON files
    json_files = sorted(glob.glob('test*.json'))
    
    if not json_files:
        print("No test*.json files found in current directory")
        return
    
    print(f"Processing {len(json_files)} JSON files...")
    
    results = []
    for json_file in json_files:
        print(f"Processing {json_file}...")
        result = process_clingo_json(json_file)
        results.append(result)
    
    # Print summary
    print_summary_table(results)
    
    # Save detailed results
    save_detailed_results(results)
    print(f"\nDetailed results saved to 'detailed_results.txt'")
    
    # Print quick stats
    successful = sum(1 for r in results if r and r['status'] == 'SATISFIABLE')
    optimal = sum(1 for r in results if r and r['status'] == 'OPTIMUM FOUND')
    
    print(f"\nQUICK STATS:")
    print(f"Total instances: {len(json_files)}")
    print(f"Satisfiable: {successful}")
    print(f"Optimal found: {optimal}")

if __name__ == "__main__":
    main()