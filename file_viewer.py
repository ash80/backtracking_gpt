import re
import math

SEARCH_TAG = '<search'
NEXT_TAG = '<next_page'
PREVIOUS_TAG = '<previous_page'
CLOSE_TAG = '<close'
EXIT_SEARCH_TAG = '<exit_search'

class TerminalFileViewer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.main_contents = self.read_file()
        self.content_page = 1
        self.end_viewer = False
        self.search_page = 1
        self.search_mode = False
        self.query = None
        self.search_results = []
        self.search_range = (-2, 2)
        self.contents_per_page = 5
        self.searches_per_page = 2
        self.all_tags = [SEARCH_TAG, NEXT_TAG, PREVIOUS_TAG, CLOSE_TAG, EXIT_SEARCH_TAG]
        self.reason_attr = 'reason'
        self.query_attr = 'query'


    def read_file(self):
        with open(self.filepath, 'r') as file:
            lines = file.readlines()
        return lines


    def display_content(self):
        display_str = "\n'''\n"
        if self.search_mode:
            top_bar = f'Search: {self.query_attr}="{self.query}"'
            top_bar += f' {EXIT_SEARCH_TAG} {self.reason_attr}="?"/>'
            contents = self.search_results
            page = self.search_page
            lines_per_page = self.searches_per_page
        else:
            top_bar = f'File: {self.filepath}'
            top_bar += f' {SEARCH_TAG} {self.query_attr}="?" {self.reason_attr}="?"/>'
            top_bar += f' {CLOSE_TAG} {self.reason_attr}="?"/>'
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
            bottom_bar += f'{PREVIOUS_TAG} {self.reason_attr}="?"/> '
        max_pages = math.ceil(len(contents) / lines_per_page)
        bottom_bar += f'Page {page} of {max_pages}'

        if page < max_pages:
            bottom_bar += f' {NEXT_TAG} {self.reason_attr}="?"/>'

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
        return self.display_content(), reason


    def next_page(self, reason):
        if self.search_mode and self.search_page < len(self.search_results):
            self.search_page += 1
        elif self.content_page < len(self.main_contents):
            self.content_page += 1
        return self.display_content(), reason


    def previous_page(self, reason):
        if self.search_mode and self.search_page > 1:
            self.search_page -= 1
        elif self.content_page > 1:
            self.content_page -= 1
        return self.display_content(), reason


    def exit_search(self, reason):
        self.search_mode = False
        return self.display_content(), reason


    def close_browser(self, reason):
        self.end_viewer = True
        return None, reason


    def extract_commands(self, text):
        # Create a regex pattern to match any of the tags in all_tags followed by any characters and then the closing '/>'
        pattern = '|'.join([f"({tag}[^/>]*?/>)" for tag in self.all_tags])
        
        # Use re.findall to find all occurrences that match the pattern
        matches = re.findall(pattern, text)
        
        # Since re.findall might return a list of tuples if there are multiple capturing groups, flatten the list
        matches = [match for sublist in matches for match in sublist if match]

        return matches
    

    def get_command_and_params(self, command: str):
        if command.startswith(SEARCH_TAG):
            command_tag = SEARCH_TAG
            pattern = f'{self.all_tags[0]} {self.query_attr}="(.*?)" {self.reason_attr}="(.*?)"/>'
        else:
            i = 1
            while not command.startswith(self.all_tags[i]):
                i += 1
            command_tag = self.all_tags[i]
            pattern = f'{self.all_tags[i]} {self.reason_attr}="(.*?)"/>'
        
        match = re.match(pattern, command)
        if match:
            if command_tag == SEARCH_TAG:
                # Extract the values of 'query' and 'reason'
                query_value = match.group(1)
                reason_value = match.group(2)
                return command_tag, (query_value, reason_value)
            else:
                reason_value = match.group(1)
                return command_tag, (reason_value,)
        else:
            # Return None if no match is found
            return None, None


    def run(self, text=None):
        if not text:
            return self.display_content(), None
        else:
            commands = self.extract_commands(text)
            for command in commands:
                command_tag, params = self.get_command_and_params(command)
                
                if command_tag == SEARCH_TAG:
                    return self.search(*params)
                elif command_tag == NEXT_TAG:
                    return self.next_page(*params)
                elif command_tag == PREVIOUS_TAG:
                    return self.previous_page(*params)
                elif command_tag == EXIT_SEARCH_TAG:
                    return self.exit_search(*params)
                elif command_tag == CLOSE_TAG:
                    return self.close_browser(*params)
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
