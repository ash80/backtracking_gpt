import re
import math

from text_util import REASON_ATTR, extract_commands, parse_command_and_params

SEARCH_TAG = '<search'
NEXT_TAG = '<next_page'
PREVIOUS_TAG = '<previous_page'
CLOSE_TAG = '<back_to_file_list'
EXIT_SEARCH_TAG = '<exit_search'

all_tags = [SEARCH_TAG, NEXT_TAG, PREVIOUS_TAG, CLOSE_TAG, EXIT_SEARCH_TAG]

tag_attrs = {
    SEARCH_TAG: ['one_word_query', REASON_ATTR],
    NEXT_TAG: [REASON_ATTR],
    PREVIOUS_TAG: [REASON_ATTR],
    CLOSE_TAG: [REASON_ATTR],
    EXIT_SEARCH_TAG: [REASON_ATTR],
}

class TerminalFileViewer:
    def __init__(self, filepath, close_browser):
        self.filepath = filepath
        self.main_contents = self.read_file()
        self.close_browser = close_browser
        self.content_page = 1
        self.search_page = 1
        self.search_mode = False
        self.query = None
        self.search_results = []
        self.search_range = (-2, 2)
        self.contents_per_page = 5
        self.searches_per_page = 2


    def read_file(self):
        with open(self.filepath, 'r') as file:
            lines = file.readlines()
        return lines


    def display_content(self):
        display_str = "\n'''Resource - File Browser\n"
        if self.search_mode:
            top_bar = f'Search Mode: {tag_attrs[SEARCH_TAG][0]}="{self.query}"'
            top_bar += f' {SEARCH_TAG} {tag_attrs[SEARCH_TAG][0]}="?" {REASON_ATTR}="?"/>'
            top_bar += f' {CLOSE_TAG} {REASON_ATTR}="?"/>'
            contents = self.search_results
            page = self.search_page
            lines_per_page = self.searches_per_page
        else:
            top_bar = f'File: {self.filepath}'
            top_bar += f' {SEARCH_TAG} {tag_attrs[SEARCH_TAG][0]}="?" {REASON_ATTR}="?"/>'
            top_bar += f' {CLOSE_TAG} {REASON_ATTR}="?"/>'
            contents = self.main_contents
            page = self.content_page
            lines_per_page = self.contents_per_page
        # print(top_bar)
        display_str += f"{top_bar}\n"

        start = (page - 1) * lines_per_page
        end = start + (lines_per_page if lines_per_page < len(contents) else len(contents))
        for line in contents[start:end]:
            # print(line.strip())
            display_str += f"{line.strip()}\n"

        bottom_bar = ''
        if page > 1:
            bottom_bar += f'{PREVIOUS_TAG} {REASON_ATTR}="?"/> '
        max_pages = math.ceil(len(contents) / lines_per_page)
        bottom_bar += f'Page {page} of {max_pages}'

        if page < max_pages:
            bottom_bar += f' {NEXT_TAG} {REASON_ATTR}="?"/>'

        # print(bottom_bar)
        display_str += f"{bottom_bar}\n"
        display_str += "'''\n"
        return display_str


    def search(self, query, reason):
        self.search_mode = True
        self.search_results = []
        self.search_page = 1
        self.query = query
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        for i, line in enumerate(self.main_contents):
            if not pattern.search(line):
                continue
            range = self.search_range
            lower_bound = i + range[0] if i + range[0] > 0 else 0
            upper_bound = i + range[1] if i + range[1] < len(self.main_contents) else len(self.main_contents)

            self.search_results.append('\n'.join(self.main_contents[lower_bound:upper_bound]))
        if not self.search_results:
            self.search_results.append("No exact match! please search for some other word\n")
        return self.display_content(), f'({SEARCH_TAG[1:]}: {query}): {reason}'


    def next_page(self, reason):
        if self.search_mode and self.search_page < len(self.search_results):
            self.search_page += 1
        elif self.content_page < len(self.main_contents):
            self.content_page += 1
        return self.display_content(), f'({NEXT_TAG[1:]}): {reason}'


    def previous_page(self, reason):
        if self.search_mode and self.search_page > 1:
            self.search_page -= 1
        elif self.content_page > 1:
            self.content_page -= 1
        return self.display_content(), f'({PREVIOUS_TAG[1:]}): {reason}'


    def exit_search(self, reason):
        self.search_mode = False
        return self.display_content(), f'({EXIT_SEARCH_TAG[1:]}): {reason}'


    # def close_browser(self, reason):
    #     self.end_viewer = True
    #     return None, f'({CLOSE_TAG[1:]}): {reason}'


    def run(self, text=None):
        if not text:
            return self.display_content(), None

        commands = extract_commands(text, all_tags)
        for command in commands:
            command_tag, params = parse_command_and_params(command, all_tags, tag_attrs)
            if command_tag == SEARCH_TAG:
                return self.search(*params)
            elif command_tag == NEXT_TAG:
                return self.next_page(*params)
            elif command_tag == PREVIOUS_TAG:
                return self.previous_page(*params)
            elif command_tag == EXIT_SEARCH_TAG:
                return self.exit_search(*params)
            elif command_tag == CLOSE_TAG:
                formatted_reason = f'({CLOSE_TAG[1:]}): {params[0]}'
                return self.close_browser(formatted_reason)
        else:
            return self.display_content(), None


if __name__ == '__main__':
    # Example usage:
    viewer = TerminalFileViewer('src_text.txt')
    text = None
    while True:
        disp, reason = viewer.run(text)
        print(disp)
        if viewer.end_viewer:
            break
        else:
            text = input('Enter command: ')
