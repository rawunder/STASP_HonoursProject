#!/usr/bin/env python3
import os
import subprocess
import csv
from pathlib import Path

def validate_sa_xml_files():
    xml_dir = "sa_xml_solutions"
    validator_path = "Validation/RobinX/RobinX"
    results = []
    
    xml_files = list(Path(xml_dir).glob("*.xml"))
    print(f"Validating {len(xml_files)} SA XML files...")
    
    for xml_file in xml_files:
        try:
            # Run RobinX validator
            cmd = f"{validator_path} {xml_file}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            instance_name = xml_file.stem.replace("_SA", "")
            
            # Parse validation output
            validation_status = "UNKNOWN"
            objective_value = None
            
            if result.returncode == 0:
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'objective' in line.lower() and 'value' in line.lower():
                        try:
                            # Extract objective value
                            import re
                            match = re.search(r'(\d+)', line)
                            if match:
                                objective_value = int(match.group(1))
                        except:
                            pass
                    if 'valid' in line.lower():
                        validation_status = "VALID"
                    elif 'invalid' in line.lower():
                        validation_status = "INVALID"
            
            results.append({
                'Instance': instance_name,
                'XMLFile': xml_file.name,
                'ValidationStatus': validation_status,
                'ValidatedObjective': objective_value,
                'ValidatorOutput': result.stdout.strip(),
                'ValidatorError': result.stderr.strip()
            })
            
        except Exception as e:
            print(f"Error validating {xml_file}: {e}")
            results.append({
                'Instance': instance_name,
                'XMLFile': xml_file.name,
                'ValidationStatus': "ERROR",
                'ValidatedObjective': None,
                'ValidatorOutput': "",
                'ValidatorError': str(e)
            })
    
    # Save validation results
    output_file = "sa_validation_results.csv"
    with open(output_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"Validation results saved to: {output_file}")
    
    # Print summary
    valid_count = len([r for r in results if r['ValidationStatus'] == 'VALID'])
    print(f"Validation summary: {valid_count}/{len(results)} files validated successfully")

if __name__ == "__main__":
    validate_sa_xml_files()
