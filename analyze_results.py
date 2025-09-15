#!/usr/bin/env python3
"""
Comprehensive results analyzer with bounds comparison
Analyzes ASP results, compares with reference bounds, and generates detailed CSV report
"""

import pandas as pd
import numpy as np
import json
import os
import re
from pathlib import Path

def load_reference_bounds(bounds_file="reference_bounds.csv"):
    """Load reference bounds data"""
    try:
        bounds_df = pd.read_csv(bounds_file)
        # Create a lookup dictionary for quick access
        bounds_lookup = {}
        for _, row in bounds_df.iterrows():
            instance_key = row['instance_key']
            bounds_lookup[instance_key] = {
                'lower_bound': row['lower_bound'] if pd.notna(row['lower_bound']) else None,
                'upper_bound': row['upper_bound'] if pd.notna(row['upper_bound']) else None,
                'instance_name': row['instance_name']
            }
        return bounds_lookup
    except Exception as e:
        print(f"Error loading bounds file: {e}")
        return {}

def extract_instance_key(filename):
    """Extract standardized instance key from JSON filename
    e.g., early12_BB2.json -> early12
    """
    base = filename.replace('.json', '')
    match = re.match(r'([a-z]+\d+)_(.+)', base)
    if match:
        return match.group(1), match.group(2)  # instance_key, config
    return None, None

def process_json_results(results_dir="Results/main_exp"):
    """Process all JSON results and extract data"""
    results = []
    
    # Find all JSON files
    json_files = []
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    print(f"Processing {len(json_files)} JSON result files...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            filename = os.path.basename(json_file)
            instance_key, config = extract_instance_key(filename)
            
            if not instance_key or not config:
                print(f"Could not parse filename: {filename}")
                continue
            
            # Extract basic information
            result = data.get("Result", "UNKNOWN")
            total_time = data.get("Time", {}).get("Total")
            solve_time = data.get("Time", {}).get("Solve")
            cpu_time = data.get("Time", {}).get("CPU")
            threads = data.get("Threads")
            
            # Initialize solution-specific fields
            cost = None
            lower_bound_solver = None
            upper_bound_solver = None
            models_found = data.get("Models", {}).get("Number", 0)
            is_optimal = data.get("Models", {}).get("Optimum") == "yes"
            
            # Extract solution data if available
            if result in ["SATISFIABLE", "OPTIMUM FOUND"]:
                calls = data.get("Call", [])
                if calls and "Witnesses" in calls[0]:
                    witnesses = calls[0]["Witnesses"]
                    if witnesses:
                        # Get best witness (first one, as they're usually sorted by cost)
                        best_witness = witnesses[0]
                        
                        # Extract cost
                        costs = best_witness.get("Costs", [])
                        if costs:
                            cost = costs[0]
                
                # Check for bounds in the JSON (some results have bounds)
                bounds = data.get("Bounds", {})
                if bounds:
                    if bounds.get("Lower") and len(bounds.get("Lower", [])) > 0:
                        lower_bound_solver = bounds["Lower"][0]
                    if bounds.get("Upper") and len(bounds.get("Upper", [])) > 0:
                        upper_bound_solver = bounds["Upper"][0]
            
            results.append({
                'filename': filename,
                'instance_key': instance_key,
                'configuration': config,
                'result': result,
                'cost': cost,
                'lower_bound_solver': lower_bound_solver,
                'upper_bound_solver': upper_bound_solver,
                'total_time': total_time,
                'solve_time': solve_time,
                'cpu_time': cpu_time,
                'threads': threads,
                'models_found': models_found,
                'is_optimal': is_optimal
            })
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    return pd.DataFrame(results)

def calculate_analysis_metrics(results_df, bounds_lookup):
    """Calculate analysis metrics including gaps and rankings"""
    
    # Add reference bounds
    results_df['ref_lower_bound'] = results_df['instance_key'].map(
        lambda x: bounds_lookup.get(x, {}).get('lower_bound')
    )
    results_df['ref_upper_bound'] = results_df['instance_key'].map(
        lambda x: bounds_lookup.get(x, {}).get('upper_bound')
    )
    results_df['ref_instance_name'] = results_df['instance_key'].map(
        lambda x: bounds_lookup.get(x, {}).get('instance_name', 'Unknown')
    )
    
    # Calculate gaps
    def calculate_gap(row):
        if pd.isna(row['cost']) or pd.isna(row['ref_lower_bound']):
            return None
        if row['ref_lower_bound'] == 0:
            return row['cost']  # When lower bound is 0, gap is just the cost
        return ((row['cost'] - row['ref_lower_bound']) / row['ref_lower_bound']) * 100
    
    results_df['gap_percent'] = results_df.apply(calculate_gap, axis=1)
    
    # Add instance category (early, late, middle)
    results_df['instance_category'] = results_df['instance_key'].str.extract(r'([a-z]+)')[0]
    results_df['instance_number'] = results_df['instance_key'].str.extract(r'([a-z]+)(\d+)')[1].astype(int)
    
    # Calculate rankings per instance
    results_df['rank_by_instance'] = results_df.groupby('instance_key')['cost'].rank(method='min', na_option='bottom')
    
    # Find best configuration per instance
    def get_best_config(group):
        valid_costs = group.dropna(subset=['cost'])
        if valid_costs.empty:
            return None
        return valid_costs.loc[valid_costs['cost'].idxmin(), 'configuration']
    
    best_configs = results_df.groupby('instance_key').apply(get_best_config)
    results_df['best_config_for_instance'] = results_df['instance_key'].map(best_configs)
    results_df['is_best_config'] = results_df['configuration'] == results_df['best_config_for_instance']
    
    return results_df

def generate_summary_stats(results_df):
    """Generate summary statistics"""
    summary = {}
    
    # Overall statistics
    summary['total_instances'] = len(results_df['instance_key'].unique())
    summary['total_configurations'] = len(results_df['configuration'].unique())
    summary['total_runs'] = len(results_df)
    
    # Results by status
    status_counts = results_df['result'].value_counts().to_dict()
    summary['results_by_status'] = status_counts
    
    # Solutions found
    solutions_found = results_df[results_df['cost'].notna()]
    summary['solutions_found'] = len(solutions_found)
    summary['solution_rate'] = len(solutions_found) / len(results_df) * 100
    
    # Optimal solutions
    optimal_solutions = results_df[results_df['is_optimal'] == True]
    summary['optimal_solutions'] = len(optimal_solutions)
    
    # Performance by configuration
    config_performance = results_df.groupby('configuration').agg({
        'cost': ['count', 'mean', 'std', 'min'],
        'solve_time': 'mean',
        'is_best_config': 'sum'
    }).round(2)
    summary['config_performance'] = config_performance
    
    # Performance by instance category
    category_performance = results_df.groupby('instance_category').agg({
        'cost': ['count', 'mean', 'std', 'min'],
        'gap_percent': 'mean',
        'solve_time': 'mean'
    }).round(2)
    summary['category_performance'] = category_performance
    
    return summary

def save_results(results_df, output_file="complete_analysis.csv"):
    """Save results to CSV with proper column ordering"""
    
    # Select and order columns for output
    output_columns = [
        'instance_key', 'instance_category', 'instance_number', 'configuration',
        'result', 'cost', 'ref_lower_bound', 'ref_upper_bound', 'gap_percent',
        'rank_by_instance', 'is_best_config', 'best_config_for_instance',
        'total_time', 'solve_time', 'cpu_time', 'models_found', 'is_optimal',
        'lower_bound_solver', 'upper_bound_solver', 'threads',
        'ref_instance_name', 'filename'
    ]
    
    # Ensure all columns exist (in case some are missing)
    for col in output_columns:
        if col not in results_df.columns:
            results_df[col] = None
    
    output_df = results_df[output_columns].copy()
    
    # Sort by instance and cost
    output_df = output_df.sort_values(['instance_category', 'instance_number', 'cost'], na_position='last')
    
    # Save to CSV
    output_df.to_csv(output_file, index=False)
    print(f"Complete analysis saved to: {output_file}")
    
    return output_df

def print_summary_report(summary, results_df):
    """Print a summary report"""
    print("\n" + "="*60)
    print("ASP RESULTS ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"Total instances: {summary['total_instances']}")
    print(f"Total configurations: {summary['total_configurations']}")
    print(f"Total runs: {summary['total_runs']}")
    print(f"Solutions found: {summary['solutions_found']} ({summary['solution_rate']:.1f}%)")
    print(f"Optimal solutions: {summary['optimal_solutions']}")
    
    print("\nResults by status:")
    for status, count in summary['results_by_status'].items():
        print(f"  {status}: {count}")
    
    print("\nPerformance by configuration:")
    print(summary['config_performance'])
    
    print("\nPerformance by instance category:")
    print(summary['category_performance'])
    
    # Best instances (with solutions and good gaps)
    valid_solutions = results_df.dropna(subset=['cost', 'gap_percent'])
    if not valid_solutions.empty:
        best_gaps = valid_solutions.nsmallest(5, 'gap_percent')
        print("\nBest results (smallest gaps):")
        for _, row in best_gaps.iterrows():
            print(f"  {row['instance_key']} {row['configuration']}: cost={row['cost']}, gap={row['gap_percent']:.1f}%")

def main():
    """Main analysis function"""
    print("Starting comprehensive results analysis...")
    
    # Load reference bounds
    print("Loading reference bounds...")
    bounds_lookup = load_reference_bounds()
    print(f"Loaded bounds for {len(bounds_lookup)} instances")
    
    # Process JSON results
    print("Processing JSON results...")
    results_df = process_json_results()
    print(f"Processed {len(results_df)} result entries")
    
    # Calculate analysis metrics
    print("Calculating analysis metrics...")
    results_df = calculate_analysis_metrics(results_df, bounds_lookup)
    
    # Generate summary statistics
    summary = generate_summary_stats(results_df)
    
    # Save results
    output_df = save_results(results_df)
    
    # Print summary report
    print_summary_report(summary, results_df)
    
    print(f"\nAnalysis complete! Check complete_analysis.csv for detailed results.")

if __name__ == "__main__":
    main()