import os
from typing import Optional
from file_viewer import TerminalFileViewer

from text_util import REASON_ATTR, extract_commands, parse_command_and_params

OPEN_TAG = '<open_file'

all_tags = [OPEN_TAG]

tag_attrs = {
    OPEN_TAG: ['file_name', REASON_ATTR]
}

class TerminalFileListViewer:
    def __init__(self, doc_dir='docs', format='.txt') -> None:
        self.files = list(
            filter(
                lambda f: f.endswith(format),
                map(
                    lambda f: os.path.join(doc_dir, f),
                    os.listdir(doc_dir)
                )
            )
        )
        self.browse_mode = False
        self.viewer: Optional[TerminalFileViewer] = None


    def display_files(self):
        display_str = "\n'''Resource - File Lists\n"
        for a_file in self.files:
            display_str += f'{OPEN_TAG} {tag_attrs[OPEN_TAG][0]}="{a_file}" {REASON_ATTR}="?"/>\n'
        display_str += "'''\n"
        return display_str


    def open_file(self, filename, reason):
        if filename in self.files:
            self.browse_mode = True
            self.viewer = TerminalFileViewer(filename, self.close_browser)
            return self.viewer.run()[0], f'({OPEN_TAG[1:]}: {filename}): {reason}'
        else:
            return None, None

    def close_browser(self, formatted_reason):
        self.viewer = None
        self.browse_mode = False
        return self.display_files(), formatted_reason


    def run(self, text=None):
        if not text:
            return self.display_files(), None
        if self.browse_mode:
            return self.viewer.run(text)

        commands = extract_commands(text, all_tags)
        for command in commands:
            command_tag, params = parse_command_and_params(command, all_tags, tag_attrs)
            if command_tag == OPEN_TAG:
                return self.open_file(*params)
        else:
            return self.display_files(), None


if __name__ == '__main__':
    filelist_viewer = TerminalFileListViewer()
    text = None
    while True:
        disp, reason = filelist_viewer.run(text)
        print(disp)
        text = input('Enter command:\n')
