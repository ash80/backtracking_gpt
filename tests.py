from file_viewer import all_tags, tag_attrs
from prompt import global_tags, global_tag_attrs
from text_util import extract_commands, parse_command_and_params


def test_util():
    text = '''
<n note="Moffatt sued Air Canada for the fare difference due to misleading advice from the chatbot. Air Canada argued the chatbot was a separate legal entity."/>

<next_page reason="To find the information about how much money Air Canada must pay to Moffatt."/>
'''
    commands = extract_commands(text, global_tags)
    for command in commands:
        a = parse_command_and_params(command, global_tags, global_tag_attrs)
        print(a)
    
    commands = extract_commands(text, all_tags)
    for command in commands:
        b = parse_command_and_params(command, all_tags, tag_attrs)
        print(b)

if __name__ == '__main__':
    test_util()
