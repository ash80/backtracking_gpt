import re
import math
from global_actions import REASON_ATTR
from prettify_util import color_tags, wrap_and_format_line
from text_util import extract_commands, parse_command_and_params

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
        title = "Resource - File Browser"
        display_str = f"\n'''{title}\n"
        pretty_display_str = '=' * (len(title) + 4) + f'= {title} =' + '=' * (len(title) + 4) + '\n'
        search_act = f'{SEARCH_TAG} {tag_attrs[SEARCH_TAG][0]}="?" {REASON_ATTR}="?"/>'
        close_act = f'{CLOSE_TAG} {REASON_ATTR}="?"/>'
        if self.search_mode:
            top_bar = f'Search Mode - {tag_attrs[SEARCH_TAG][0]}: "{self.query}"'
            pretty_display_str += top_bar.center((len(title) + 4) * 3) + '\n'
            top_bar += f' {search_act}'
            top_bar += f' {close_act}'
            pretty_display_str += color_tags(f'{search_act}')
            pretty_display_str += color_tags(f'{close_act}'.rjust((len(title) + 4) * 3 - len(search_act)) + '\n')
            contents = self.search_results
            page = self.search_page
            lines_per_page = self.searches_per_page
        else:
            top_bar = f'File: {self.filepath}'
            pretty_display_str += top_bar.center((len(title) + 4) * 3) + '\n'
            top_bar += f' {search_act}'
            top_bar += f' {close_act}'
            pretty_display_str += color_tags(f'{search_act}')
            pretty_display_str += color_tags(f'{close_act}'.rjust((len(title) + 4) * 3 - len(search_act)) + '\n')
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
            pretty_display_str += wrap_and_format_line(line.strip(), (len(title) + 4) * 3)

        bottom_bar = ''
        max_pages = math.ceil(len(contents) / lines_per_page)
        page_num = f'Page {page} of {max_pages}'
        pretty_display_str += page_num.center((len(title) + 4) * 3) + '\n'
        if page > 1:
            prev_act = f'{PREVIOUS_TAG} {REASON_ATTR}="?"/>'
            pretty_display_str += color_tags(prev_act)
            bottom_bar += f'{prev_act} '
        bottom_bar += page_num

        if page < max_pages:
            next_act = f'{NEXT_TAG} {REASON_ATTR}="?"/>'
            bottom_bar += f' {next_act}'
            pretty_display_str += color_tags(f'{next_act}'.rjust((len(title) + 4) * 3 - (len(prev_act) if page > 1 else 0))) + '\n'

        # print(bottom_bar)
        display_str += f"{bottom_bar}\n"
        display_str += "'''\n"
        pretty_display_str += '=' * (len(title) + 4) * 3 + '\n'
        return display_str, pretty_display_str


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
            self.search_results.append("No exact match!\n")
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
    viewer = TerminalFileViewer('docs/src_text_p.txt', lambda a: a)
    text = None
    while True:
        disps, reason = viewer.run(text)
        print(disps[1])
        text = input('Enter command: ')
