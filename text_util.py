import re
from typing import List

REASON_ATTR = 'reason'

def extract_commands(text: str, all_tags: str) -> list[str]:
    # Create a regex pattern to match any of the tags in all_tags followed by any characters and then the closing '/>'
    pattern = '|'.join([f"({tag}\s+[^/>]*?/>)" for tag in all_tags])

    # Use re.findall to find all occurrences that match the pattern
    matches = re.findall(pattern, text)

    if not matches:
        return []
    
    # Since re.findall might return a list of tuples if there are multiple capturing groups, flatten the list
    if type(matches[0]) == list or type(matches[0]) == tuple:
        matches = [match for sublist in matches for match in sublist if match]

    return matches


def parse_command_and_params(command: str, all_tags: List[str], tag_attrs: dict):

    i = 0
    while not command.startswith(all_tags[i]):
        i += 1

    command_tag = all_tags[i]
    attrs: List[str] = tag_attrs.get(command_tag, [])

    pattern = f'{command_tag}'
    for attr in attrs:
        pattern += f' {attr}="(.*?)"'

    match = re.match(pattern, command)
    if match:
        i = 1
        attr_vals = []
        for attr in attrs:
            attr_vals.append(match.group(i))
            i += 1
        return command_tag, attr_vals
    else:
        # Return None if no match is found
        return None, None
