#!/usr/bin/env python3
"""
ITC2021 XML to ASP Facts Parser

This script converts ITC2021 Sports Timetabling XML instances to ASP facts
that can be used with the provided ASP encoding.

Usage: python parser.py input.xml output.lp
"""

import xml.etree.ElementTree as ET
import sys
import argparse
from typing import List, Dict, Set


class ITC2021Parser:
    def __init__(self):
        self.constraint_counters = {
            'ca1': 0, 'ca2': 0, 'ca3': 0, 'ca4': 0,
            'ga1': 0, 'br1': 0, 'br2': 0, 'fa2': 0, 'se1': 0
        }
        self.facts = []

    def parse_list(self, text: str) -> List[int]:
        """Parse semicolon-separated list of integers."""
        if not text or text.strip() == "":
            return []
        return [int(x.strip()) for x in text.split(';') if x.strip()]

    def parse_range(self, text: str) -> List[int]:
        """Parse range notation like '0..19' or regular list."""
        if not text or text.strip() == "":
            return []
        
        text = text.strip()
        if '..' in text:
            # Handle range notation
            parts = text.split('..')
            if len(parts) == 2:
                start, end = int(parts[0]), int(parts[1])
                return list(range(start, end + 1))
        
        # Handle regular semicolon-separated list
        return self.parse_list(text)

    def parse_meetings(self, text: str) -> List[tuple]:
        """Parse meetings like '0,1;1,2;' into list of tuples."""
        if not text or text.strip() == "":
            return []
        
        meetings = []
        for meeting in text.split(';'):
            meeting = meeting.strip()
            if meeting and ',' in meeting:
                parts = meeting.split(',')
                if len(parts) == 2:
                    meetings.append((int(parts[0].strip()), int(parts[1].strip())))
        return meetings

    def add_fact(self, fact: str):
        """Add a fact to the output."""
        self.facts.append(fact)

    def get_constraint_id(self, constraint_type: str) -> str:
        """Generate unique constraint ID."""
        self.constraint_counters[constraint_type] += 1
        return f"{constraint_type}_{self.constraint_counters[constraint_type]}"

    def parse_basic_structure(self, root):
        """Parse teams, slots, and basic format information."""
        # Parse teams
        teams = root.find('.//Teams')
        if teams is not None:
            team_ids = []
            for team in teams.findall('team'):
                team_id = int(team.get('id'))
                team_ids.append(team_id)
                self.add_fact(f"team({team_id}).")
            
            if team_ids:
                num_teams = len(team_ids)
                max_team = max(team_ids)
                min_team = min(team_ids)
                self.add_fact(f"num_teams({num_teams}).")
                if min_team == 0 and max_team == num_teams - 1:
                    self.add_fact(f"team(0..{max_team}).")
                else:
                    for tid in team_ids:
                        self.add_fact(f"team({tid}).")

        # Parse slots
        slots = root.find('.//Slots')
        if slots is not None:
            slot_ids = []
            for slot in slots.findall('slot'):
                slot_id = int(slot.get('id'))
                slot_ids.append(slot_id)
                self.add_fact(f"slot({slot_id}).")
            
            if slot_ids:
                num_slots = len(slot_ids)
                max_slot = max(slot_ids)
                min_slot = min(slot_ids)
                self.add_fact(f"num_slots({num_slots}).")
                if min_slot == 0 and max_slot == num_slots - 1:
                    self.add_fact(f"slot(0..{max_slot}).")
                else:
                    for sid in slot_ids:
                        self.add_fact(f"slot({sid}).")

        # Parse format (check for phased tournaments)
        format_elem = root.find('.//Format')
        if format_elem is not None:
            game_mode_elem = format_elem.find('gameMode')
            if game_mode_elem is not None and game_mode_elem.text == 'P':
                self.add_fact("phased.")

    def parse_ca1_constraints(self, root):
        """Parse CA1 (Capacity) constraints."""
        ca1_elements = root.findall('.//CA1')
        for ca1 in ca1_elements:
            constraint_id = self.get_constraint_id('ca1')
            
            # Basic parameters
            constraint_type = ca1.get('type', 'HARD').lower()
            max_val = ca1.get('max', '0')
            min_val = ca1.get('min', '0')
            mode = ca1.get('mode', 'H')
            penalty = ca1.get('penalty', '1')
            
            self.add_fact(f'ca1_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'ca1_param({constraint_id}, max, {max_val}).')
            self.add_fact(f'ca1_param({constraint_id}, min, {min_val}).')
            self.add_fact(f'ca1_param({constraint_id}, mode, "{mode}").')
            self.add_fact(f'ca1_param({constraint_id}, penalty, {penalty}).')
            
            # Teams
            teams = self.parse_range(ca1.get('teams', ''))
            for team in teams:
                self.add_fact(f'ca1_teams({constraint_id}, {team}).')
            
            # Slots
            slots = self.parse_list(ca1.get('slots', ''))
            for slot in slots:
                self.add_fact(f'ca1_slots({constraint_id}, {slot}).')

    def parse_ca2_constraints(self, root):
        """Parse CA2 (Capacity vs Opponent Set) constraints."""
        ca2_elements = root.findall('.//CA2')
        for ca2 in ca2_elements:
            constraint_id = self.get_constraint_id('ca2')
            
            # Basic parameters
            constraint_type = ca2.get('type', 'HARD').lower()
            max_val = ca2.get('max', '0')
            min_val = ca2.get('min', '0')
            mode1 = ca2.get('mode1', 'H')
            mode2 = ca2.get('mode2', 'GLOBAL')
            penalty = ca2.get('penalty', '1')
            
            self.add_fact(f'ca2_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'ca2_param({constraint_id}, max, {max_val}).')
            self.add_fact(f'ca2_param({constraint_id}, min, {min_val}).')
            self.add_fact(f'ca2_param({constraint_id}, mode1, "{mode1}").')
            self.add_fact(f'ca2_param({constraint_id}, mode2, "{mode2}").')
            self.add_fact(f'ca2_param({constraint_id}, penalty, {penalty}).')
            
            # Teams1
            teams1 = self.parse_range(ca2.get('teams1', ''))
            for team in teams1:
                self.add_fact(f'ca2_teams1({constraint_id}, {team}).')
            
            # Teams2
            teams2 = self.parse_range(ca2.get('teams2', ''))
            for team in teams2:
                self.add_fact(f'ca2_teams2({constraint_id}, {team}).')
            
            # Slots
            slots = self.parse_list(ca2.get('slots', ''))
            for slot in slots:
                self.add_fact(f'ca2_slots({constraint_id}, {slot}).')

    def parse_ca3_constraints(self, root):
        """Parse CA3 (Consecutive Games) constraints."""
        ca3_elements = root.findall('.//CA3')
        for ca3 in ca3_elements:
            constraint_id = self.get_constraint_id('ca3')
            
            # Basic parameters
            constraint_type = ca3.get('type', 'HARD').lower()
            max_val = ca3.get('max', '0')
            min_val = ca3.get('min', '0')
            mode1 = ca3.get('mode1', 'H')
            mode2 = ca3.get('mode2', 'SLOTS')
            intp = ca3.get('intp', '1')
            penalty = ca3.get('penalty', '1')
            
            self.add_fact(f'ca3_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'ca3_param({constraint_id}, max, {max_val}).')
            self.add_fact(f'ca3_param({constraint_id}, min, {min_val}).')
            self.add_fact(f'ca3_param({constraint_id}, mode1, "{mode1}").')
            self.add_fact(f'ca3_param({constraint_id}, mode2, "{mode2}").')
            self.add_fact(f'ca3_param({constraint_id}, intp, {intp}).')
            self.add_fact(f'ca3_param({constraint_id}, penalty, {penalty}).')
            
            # Teams1
            teams1 = self.parse_range(ca3.get('teams1', ''))
            for team in teams1:
                self.add_fact(f'ca3_teams1({constraint_id}, {team}).')
            
            # Teams2 (if present)
            teams2 = self.parse_range(ca3.get('teams2', ''))
            for team in teams2:
                self.add_fact(f'ca3_teams2({constraint_id}, {team}).')

    def parse_ca4_constraints(self, root):
        """Parse CA4 (Group Capacity) constraints."""
        ca4_elements = root.findall('.//CA4')
        for ca4 in ca4_elements:
            constraint_id = self.get_constraint_id('ca4')
            
            # Basic parameters
            constraint_type = ca4.get('type', 'HARD').lower()
            max_val = ca4.get('max', '0')
            min_val = ca4.get('min', '0')
            mode1 = ca4.get('mode1', 'H')
            mode2 = ca4.get('mode2', 'GLOBAL')
            penalty = ca4.get('penalty', '1')
            
            self.add_fact(f'ca4_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'ca4_param({constraint_id}, max, {max_val}).')
            self.add_fact(f'ca4_param({constraint_id}, min, {min_val}).')
            self.add_fact(f'ca4_param({constraint_id}, mode1, "{mode1}").')
            self.add_fact(f'ca4_param({constraint_id}, mode2, "{mode2}").')
            self.add_fact(f'ca4_param({constraint_id}, penalty, {penalty}).')
            
            # Teams1
            teams1 = self.parse_range(ca4.get('teams1', ''))
            for team in teams1:
                self.add_fact(f'ca4_teams1({constraint_id}, {team}).')
            
            # Teams2
            teams2 = self.parse_range(ca4.get('teams2', ''))
            for team in teams2:
                self.add_fact(f'ca4_teams2({constraint_id}, {team}).')
            
            # Slots
            slots = self.parse_list(ca4.get('slots', ''))
            for slot in slots:
                self.add_fact(f'ca4_slots({constraint_id}, {slot}).')

    def parse_ga1_constraints(self, root):
        """Parse GA1 (Game Assignment) constraints."""
        ga1_elements = root.findall('.//GA1')
        for ga1 in ga1_elements:
            constraint_id = self.get_constraint_id('ga1')
            
            # Basic parameters
            constraint_type = ga1.get('type', 'HARD').lower()
            max_val = ga1.get('max', '1')
            min_val = ga1.get('min', '0')
            penalty = ga1.get('penalty', '1')
            
            self.add_fact(f'ga1_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'ga1_param({constraint_id}, max, {max_val}).')
            self.add_fact(f'ga1_param({constraint_id}, min, {min_val}).')
            self.add_fact(f'ga1_param({constraint_id}, penalty, {penalty}).')
            
            # Meetings
            meetings = self.parse_meetings(ga1.get('meetings', ''))
            for t1, t2 in meetings:
                self.add_fact(f'ga1_meetings({constraint_id}, {t1}, {t2}).')
            
            # Slots
            slots = self.parse_list(ga1.get('slots', ''))
            for slot in slots:
                self.add_fact(f'ga1_slots({constraint_id}, {slot}).')

    def parse_br1_constraints(self, root):
        """Parse BR1 (Break per Team) constraints."""
        br1_elements = root.findall('.//BR1')
        for br1 in br1_elements:
            constraint_id = self.get_constraint_id('br1')
            
            # Basic parameters
            constraint_type = br1.get('type', 'HARD').lower()
            intp = br1.get('intp', '0')
            mode1 = br1.get('mode1', 'LEQ')
            mode2 = br1.get('mode2', 'HA')
            penalty = br1.get('penalty', '1')
            
            self.add_fact(f'br1_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'br1_param({constraint_id}, intp, {intp}).')
            self.add_fact(f'br1_param({constraint_id}, mode1, "{mode1}").')
            self.add_fact(f'br1_param({constraint_id}, mode2, "{mode2}").')
            self.add_fact(f'br1_param({constraint_id}, penalty, {penalty}).')
            
            # Teams
            teams = self.parse_range(br1.get('teams', ''))
            for team in teams:
                self.add_fact(f'br1_teams({constraint_id}, {team}).')
            
            # Slots
            slots = self.parse_list(br1.get('slots', ''))
            for slot in slots:
                self.add_fact(f'br1_slots({constraint_id}, {slot}).')

    def parse_br2_constraints(self, root):
        """Parse BR2 (Global Break) constraints."""
        br2_elements = root.findall('.//BR2')
        for br2 in br2_elements:
            constraint_id = self.get_constraint_id('br2')
            
            # Basic parameters
            constraint_type = br2.get('type', 'HARD').lower()
            intp = br2.get('intp', '0')
            home_mode = br2.get('homeMode', 'HA')
            mode2 = br2.get('mode2', 'LEQ')
            penalty = br2.get('penalty', '1')
            
            self.add_fact(f'br2_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'br2_param({constraint_id}, intp, {intp}).')
            self.add_fact(f'br2_param({constraint_id}, homeMode, "{home_mode}").')
            self.add_fact(f'br2_param({constraint_id}, mode2, "{mode2}").')
            self.add_fact(f'br2_param({constraint_id}, penalty, {penalty}).')
            
            # Teams
            teams = self.parse_range(br2.get('teams', ''))
            for team in teams:
                self.add_fact(f'br2_teams({constraint_id}, {team}).')
            
            # Slots
            slots = self.parse_range(br2.get('slots', ''))
            for slot in slots:
                self.add_fact(f'br2_slots({constraint_id}, {slot}).')

    def parse_fa2_constraints(self, root):
        """Parse FA2 (Fairness) constraints."""
        fa2_elements = root.findall('.//FA2')
        for fa2 in fa2_elements:
            constraint_id = self.get_constraint_id('fa2')
            
            # Basic parameters
            constraint_type = fa2.get('type', 'SOFT').lower()
            intp = fa2.get('intp', '1')
            penalty = fa2.get('penalty', '1')
            
            self.add_fact(f'fa2_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'fa2_param({constraint_id}, intp, {intp}).')
            self.add_fact(f'fa2_param({constraint_id}, penalty, {penalty}).')
            
            # Teams
            teams = self.parse_range(fa2.get('teams', ''))
            for team in teams:
                self.add_fact(f'fa2_teams({constraint_id}, {team}).')
            
            # Slots
            slots = self.parse_range(fa2.get('slots', ''))
            for slot in slots:
                self.add_fact(f'fa2_slots({constraint_id}, {slot}).')

    def parse_se1_constraints(self, root):
        """Parse SE1 (Separation) constraints."""
        se1_elements = root.findall('.//SE1')
        for se1 in se1_elements:
            constraint_id = self.get_constraint_id('se1')
            
            # Basic parameters
            constraint_type = se1.get('type', 'SOFT').lower()
            min_val = se1.get('min', '1')
            penalty = se1.get('penalty', '1')
            
            self.add_fact(f'se1_param({constraint_id}, type, {constraint_type}).')
            self.add_fact(f'se1_param({constraint_id}, min, {min_val}).')
            self.add_fact(f'se1_param({constraint_id}, penalty, {penalty}).')
            
            # Teams
            teams = self.parse_range(se1.get('teams', ''))
            for team in teams:
                self.add_fact(f'se1_teams({constraint_id}, {team}).')

    def parse_xml_file(self, filename: str):
        """Parse the XML file and generate ASP facts."""
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            
            # Add header comment
            self.add_fact(f"% ASP facts generated from {filename}")
            self.add_fact("")
            
            # Parse basic structure
            self.add_fact("% Basic structure")
            self.parse_basic_structure(root)
            self.add_fact("")
            
            # Parse constraints
            self.add_fact("% Constraints")
            self.parse_ca1_constraints(root)
            self.parse_ca2_constraints(root)
            self.parse_ca3_constraints(root)
            self.parse_ca4_constraints(root)
            self.parse_ga1_constraints(root)
            self.parse_br1_constraints(root)
            self.parse_br2_constraints(root)
            self.parse_fa2_constraints(root)
            self.parse_se1_constraints(root)
            
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError:
            print(f"File not found: {filename}", file=sys.stderr)
            sys.exit(1)

    def write_facts(self, filename: str):
        """Write the generated facts to a file."""
        try:
            with open(filename, 'w') as f:
                for fact in self.facts:
                    f.write(fact + '\n')
        except IOError as e:
            print(f"Error writing to file: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Convert ITC2021 XML to ASP facts')
    parser.add_argument('input', help='Input XML file')
    parser.add_argument('output', help='Output ASP facts file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create parser instance
    itc_parser = ITC2021Parser()
    
    if args.verbose:
        print(f"Parsing {args.input}...")
    
    # Parse XML file
    itc_parser.parse_xml_file(args.input)
    
    if args.verbose:
        print(f"Generated {len(itc_parser.facts)} facts")
    
    # Write output
    itc_parser.write_facts(args.output)
    
    if args.verbose:
        print(f"ASP facts written to {args.output}")


if __name__ == "__main__":
    main()
