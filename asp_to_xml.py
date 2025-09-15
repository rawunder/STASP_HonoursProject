#!/usr/bin/env python3
"""
Convert ASP solver results to ITC 2021 XML format
Parses JSON files with schedule(home, away, slot) atoms and generates XML solutions
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

def parse_schedule_atom(atom_str):
    """Parse a schedule atom string like 'schedule(1,4,0)' to extract home, away, slot"""
    match = re.match(r'schedule\((\d+),(\d+),(\d+)\)', atom_str.strip())
    if match:
        home = int(match.group(1))
        away = int(match.group(2))
        slot = int(match.group(3))
        return (home, away, slot)
    return None

def extract_instance_info(filename):
    """Extract instance information from JSON filename
    e.g., early12_BB2.json -> ('early', 12, 'BB2')
    """
    base = filename.replace('.json', '')
    
    # Match pattern like early12_BB2 or middle5_USC15-CR
    match = re.match(r'([a-z]+)(\d+)_(.+)', base)
    if match:
        category = match.group(1)
        number = int(match.group(2))
        config = match.group(3)
        return (category, number, config)
    
    return None

def create_xml_solution(instance_info, schedule_data, cost=None, is_optimal=False):
    """Create XML solution document"""
    category, number, config = instance_info
    
    # Create root element
    root = ET.Element("Solution")
    
    # Create MetaData section - minimal format like working examples
    metadata = ET.SubElement(root, "MetaData")
    
    # Instance name: Use format from working examples
    instance_name = ET.SubElement(metadata, "InstanceName")
    if category == "early":
        instance_name.text = f"inst{number}_e.xml"
    elif category == "late":
        instance_name.text = f"inst{number}_l.xml"  
    elif category == "middle":
        instance_name.text = f"inst{number}_m.xml"
    else:
        instance_name.text = f"ITC2021_{category.title()}_{number}.xml"
    
    # Contributor
    contributor = ET.SubElement(metadata, "Contributor")
    contributor.text = f"ASP_{config}"
    
    # Skip ObjectiveValue - let RobinX calculate it
    # if cost is not None:
    #     obj_value = ET.SubElement(metadata, "ObjectiveValue")
    #     obj_value.set("infeasibility", "0")
    #     obj_value.set("objective", str(int(cost)))
    
    # Date
    date = ET.SubElement(metadata, "Date")
    now = datetime.now()
    date.set("day", str(now.day))
    date.set("month", str(now.month))
    date.set("year", str(now.year))
    
    # Create Games section
    games = ET.SubElement(root, "Games")
    
    # Add scheduled matches
    if schedule_data:
        # Sort by slot for consistent output
        sorted_schedule = sorted(schedule_data, key=lambda x: x[2])
        
        for home, away, slot in sorted_schedule:
            match = ET.SubElement(games, "ScheduledMatch")
            match.set("home", str(home))
            match.set("away", str(away))
            match.set("slot", str(slot))
    
    return root

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ").replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')

def process_json_file(filepath):
    """Process a single JSON file and extract solution data"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Extract instance info from filename
        filename = os.path.basename(filepath)
        instance_info = extract_instance_info(filename)
        if not instance_info:
            print(f"Could not parse filename: {filename}")
            return None
        
        # Extract solution data
        result = data.get("Result", "UNKNOWN")
        cost = None
        is_optimal = False
        schedule_data = []
        
        # Check for solution
        if result == "SATISFIABLE" or result == "OPTIMUM FOUND":
            is_optimal = (result == "OPTIMUM FOUND")
            
            # Get witnesses (solutions)
            calls = data.get("Call", [])
            if calls:
                witnesses = calls[0].get("Witnesses", [])
                if witnesses:
                    # Find the witness with the minimum cost (best solution)
                    best_witness = None
                    best_cost = float('inf')
                    
                    for witness in witnesses:
                        witness_costs = witness.get("Costs", [])
                        if witness_costs:
                            witness_cost = witness_costs[0]
                            if witness_cost < best_cost:
                                best_cost = witness_cost
                                best_witness = witness
                    
                    if best_witness:
                        cost = best_cost
                        # Extract schedule from the best witness
                        values = best_witness.get("Value", [])
                        for atom in values:
                            if atom.startswith("schedule("):
                                parsed = parse_schedule_atom(atom)
                                if parsed:
                                    schedule_data.append(parsed)
        
        return {
            'instance_info': instance_info,
            'result': result,
            'cost': cost,
            'is_optimal': is_optimal,
            'schedule_data': schedule_data,
            'filename': filename
        }
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def convert_json_to_xml(json_file, output_dir):
    """Convert a single JSON file to XML format"""
    solution_data = process_json_file(json_file)
    if not solution_data:
        return False
    
    # Skip instances where no solution was found (empty schedule)
    if not solution_data['schedule_data']:
        print(f"Skipping {solution_data['filename']} - no solution found")
        return False
    
    # Create XML
    xml_root = create_xml_solution(
        solution_data['instance_info'],
        solution_data['schedule_data'],
        solution_data['cost'],
        solution_data['is_optimal']
    )
    
    # Generate output filename
    category, number, config = solution_data['instance_info']
    xml_filename = f"{category.title()}_{number}_{config}.xml"
    output_path = os.path.join(output_dir, xml_filename)
    
    # Write XML file
    xml_string = prettify_xml(xml_root)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_string)
    
    return True

def convert_all_results(input_dir="Results/main_exp", 
                       output_dir="xml_solutions"):
    """Convert all JSON results to XML format"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all JSON files
    json_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Process each file
    successful = 0
    failed = 0
    
    for json_file in json_files:
        print(f"Processing: {os.path.basename(json_file)}")
        try:
            if convert_json_to_xml(json_file, output_dir):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Failed to process {json_file}: {e}")
            failed += 1
    
    print(f"\nConversion complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}")
    
    # List generated files
    xml_files = [f for f in os.listdir(output_dir) if f.endswith('.xml')]
    print(f"Generated {len(xml_files)} XML files")
    
    return successful, failed

def main():
    """Main function"""
    print("Converting ASP results to XML format...")
    successful, failed = convert_all_results()
    
    if successful > 0:
        print(f"\nSample XML files created:")
        xml_dir = "xml_solutions"
        xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')][:5]
        for xml_file in xml_files:
            print(f"  {xml_file}")

if __name__ == "__main__":
    main()