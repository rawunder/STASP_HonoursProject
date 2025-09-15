
import pandas as pd
from parse_results import parse_results

if __name__ == "__main__":
    results_df = parse_results("Results/main_exp")
    
    # Convert numeric columns
    results_df['Cost'] = pd.to_numeric(results_df['Cost'], errors='coerce')
    results_df['LowerBound'] = pd.to_numeric(results_df['LowerBound'], errors='coerce')
    results_df['UpperBound'] = pd.to_numeric(results_df['UpperBound'], errors='coerce')
    
    # Write all results to a CSV file
    results_df.to_csv("main_exp_results.csv", index=False)
    print("All results saved to main_exp_results.csv")
    
    # Find the best configuration for each instance and write to a CSV file
    if not results_df.empty and 'Cost' in results_df.columns:
        best_configs = pd.DataFrame()
        for instance, group in results_df.groupby('Instance'):
            if group['Cost'].notna().any():
                best_config = group.loc[group['Cost'].idxmin()]
                best_configs = pd.concat([best_configs, best_config.to_frame().T])

        if not best_configs.empty:
            best_configs.to_csv("best_main_exp_configurations.csv", index=False)
            print("Best configurations saved to best_main_exp_configurations.csv")
            
            # Summary statistics
            print(f"\nSummary statistics:")
            print(f"Total instances processed: {len(results_df['Instance'].unique())}")
            print(f"Instances with solutions: {len(best_configs)}")
            print(f"Instances with bounds: {results_df['LowerBound'].notna().sum()}")
            print(f"Best cost found: {best_configs['Cost'].min():.0f}")
            print(f"Average best cost: {best_configs['Cost'].mean():.2f}")
            
        else:
            print("No instances with valid cost information found.")
