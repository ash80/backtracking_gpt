import textwrap

RED = '\033[91m'
RESET = '\033[0m'

# Function to color HTML-like tags in red
def color_tags(line):
    # Splitting by < and > to identify tags and non-tags
    parts = line.split('<')
    new_line = ''
    for part in parts:
        if '>' in part:
            tag, text = part.split('>', 1)
            # Apply red color to tag and reset afterwards
            new_line += RED + '<' + tag + '>' + RESET + text
        else:
            new_line += part
    return new_line

def wrap_and_format_line(line, width):
    wrapped_lines = textwrap.wrap(line, width - 3)
    justified_wrapped_lines = ''
    for wrapped_line in wrapped_lines:
        justified_wrapped_lines += f'|  {wrapped_line.ljust(width - 3)}|' + '\n'
    return justified_wrapped_lines
