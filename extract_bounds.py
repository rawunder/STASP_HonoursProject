#!/usr/bin/env python3
"""
Extract reference bounds from RobinX ITC2021 repository
Parses XML bound files and creates CSV lookup table for analysis
"""

import xml.etree.ElementTree as ET
import pandas as pd
import os
from pathlib import Path
import re

def parse_bound_file(filepath):
    """Parse a single bound XML file and extract bounds data"""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Extract instance name from metadata
        instance_name = root.find('.//InstanceName').text
        
        # Extract bounds
        lower_bound = None
        upper_bound = None
        
        lower_elem = root.find('.//LowerBound/Objective')
        if lower_elem is not None:
            lower_bound = float(lower_elem.text)
            
        upper_elem = root.find('.//UpperBound/Objective')
        if upper_elem is not None:
            upper_bound = float(upper_elem.text)
        
        return {
            'instance_name': instance_name,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'source_file': os.path.basename(filepath)
        }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def extract_instance_key(filename):
    """Extract standardized instance key from filename
    e.g., ITC2021_Early_1_Bound.xml -> early1
    """
    # Remove .xml and _Bound suffix
    base = filename.replace('.xml', '').replace('_Bound', '')
    
    # Extract parts using regex
    match = re.match(r'ITC2021_(\w+)_(\d+)', base)
    if match:
        category = match.group(1).lower()
        number = int(match.group(2))
        return f"{category}{number}"
    
    return None

def extract_all_bounds(bounds_dir="Validation/RobinX/Repository/ITC2021/Bounds/"):
    """Extract bounds from all XML files in the bounds directory"""
    bounds_data = []
    
    bounds_path = Path(bounds_dir)
    if not bounds_path.exists():
        print(f"Bounds directory not found: {bounds_dir}")
        return pd.DataFrame()
    
    print(f"Processing bounds files from: {bounds_dir}")
    
    # Process all XML files in bounds directory
    xml_files = list(bounds_path.glob("*.xml"))
    print(f"Found {len(xml_files)} XML files")
    
    for filepath in xml_files:
        bound_data = parse_bound_file(filepath)
        if bound_data:
            # Extract standardized instance key
            instance_key = extract_instance_key(filepath.name)
            if instance_key:
                bound_data['instance_key'] = instance_key
                bounds_data.append(bound_data)
    
    if not bounds_data:
        print("No bounds data extracted")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(bounds_data)
    
    # Group by instance and get best (minimum) bounds
    print(f"Extracted {len(df)} bound entries")
    print(f"Unique instances: {len(df['instance_key'].unique())}")
    
    # For each instance, take the minimum lower bound and upper bound
    best_bounds = []
    for instance in df['instance_key'].unique():
        instance_data = df[df['instance_key'] == instance]
        
        # Get best lower bound (minimum non-null)
        lower_bounds = instance_data['lower_bound'].dropna()
        best_lower = lower_bounds.min() if len(lower_bounds) > 0 else None
        
        # Get best upper bound (minimum non-null)
        upper_bounds = instance_data['upper_bound'].dropna()
        best_upper = upper_bounds.min() if len(upper_bounds) > 0 else None
        
        # Get the original instance name
        original_name = instance_data['instance_name'].iloc[0]
        
        best_bounds.append({
            'instance_key': instance,
            'instance_name': original_name,
            'lower_bound': best_lower,
            'upper_bound': best_upper,
            'has_lower': best_lower is not None,
            'has_upper': best_upper is not None,
            'num_bound_files': len(instance_data)
        })
    
    best_df = pd.DataFrame(best_bounds)
    return best_df

def main():
    """Main function to extract bounds and save to CSV"""
    print("Extracting reference bounds from RobinX repository...")
    
    bounds_df = extract_all_bounds()
    
    if bounds_df.empty:
        print("No bounds data found!")
        return
    
    # Save to CSV
    output_file = "reference_bounds.csv"
    bounds_df.to_csv(output_file, index=False)
    
    print(f"\nBounds data saved to: {output_file}")
    print(f"Total instances with bounds: {len(bounds_df)}")
    print(f"Instances with lower bounds: {bounds_df['has_lower'].sum()}")
    print(f"Instances with upper bounds: {bounds_df['has_upper'].sum()}")
    
    # Show sample data
    print("\nSample bounds data:")
    print(bounds_df.head(10).to_string(index=False))
    
    # Show statistics by instance type
    bounds_df['instance_type'] = bounds_df['instance_key'].str.extract(r'([a-z]+)')[0]
    print("\nBounds by instance type:")
    type_stats = bounds_df.groupby('instance_type').agg({
        'has_lower': 'sum',
        'has_upper': 'sum',
        'instance_key': 'count'
    }).rename(columns={'instance_key': 'total'})
    print(type_stats)

if __name__ == "__main__":
    main()