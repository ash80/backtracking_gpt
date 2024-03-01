from typing import List, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage

from file_list_viewer import TerminalFileListViewer
from global_actions import DELETE_TAG, FINISH_TAG, GLOBAL_ACTIONS, GLOBAL_TAG_ATTRS, GLOBAL_TAGS, NOTE_TAG, add_note, add_reason, delete_note
from prettify_util import color_tags
from prompts import NOTES_START_STRING, REASONS_START_STRING, get_base_system_message, get_human_message
from text_util import extract_commands, parse_command_and_params


def list_to_str(a_list):
    final_str = ''
    for item in a_list:
        final_str += f"- {item}\n"
    return final_str


def main():
    notes = []
    reasons = []
    model_name : Literal['gpt-4-turbo-preview', 'gpt-3.5-turbo', 'gpt-4'] = 'gpt-4-turbo-preview'
    context_lengths = {'gpt-3.5-turbo': 4097, 'gpt-4-turbo-preview': 4096, 'gpt-4': 32000}
    max_tokens = context_lengths[model_name]
    llm = ChatOpenAI(model=model_name, temperature=0.1, max_tokens=max_tokens)
    def context_window_func(x) -> str: 
        return f"Available tokens {max_tokens - x} | {(x * 100/max_tokens):.2f}% Used\n"
    # goal = input("Enter goal: ")
    goal = "How much money air canada must pay to Moffatt?"
    text = None

    app = TerminalFileListViewer()
    continue_yes = 'y'
    end_program = False
    while not end_program and continue_yes == 'y':
        all_messages: List[BaseMessage] = [
            get_base_system_message(),
            get_human_message(goal),
        ]
        disps, reason = app.run(text)
        if reason:    
            add_reason(reasons, reason)
        reasons_str = list_to_str(reasons) if reasons else 'No actions and reasons\n\n'
        notes_str = list_to_str(notes) if notes else 'No notes added\n\n'
        system_message_contents = f'{REASONS_START_STRING}\n{reasons_str}'
        system_message_contents += f'\n{NOTES_START_STRING}\n{notes_str}'

        num_tokens = llm.get_num_tokens_from_messages(all_messages)
        num_tokens += llm.get_num_tokens(system_message_contents)
        num_tokens += llm.get_num_tokens(context_window_func(3 * max_tokens // 4))
        token_usage_str = context_window_func(num_tokens)
        system_message_contents = token_usage_str + system_message_contents
        
        system_message_contents += disps[0]
        all_messages.append(SystemMessage(content=system_message_contents))

        print('\n=========================')
        print(f"Goal: {goal}")
        print(token_usage_str)
        print(f"\nGlobal Actions:")
        for global_act in GLOBAL_ACTIONS:
            print(f'- {color_tags(global_act)}')
        print('')
        print(disps[1])
        # break

        # for message in all_messages[2:]:
        #     print(f"{message.type}:\n{message.content}")
        # # https://stackoverflow.com/questions/76639580/
        # prompt = ChatPromptTemplate.from_messages(all_messages)
        # print(prompt.format())

        text = ''
        print("Agent:")
        for chunk in llm.stream(all_messages):
            chunk_content = chunk.content
            text += chunk_content
            print(chunk_content, end='' if chunk_content else '\n', flush=True)

        commands = extract_commands(text, GLOBAL_TAGS)
        for command in commands:
            command_tag, params = parse_command_and_params(command, GLOBAL_TAGS, GLOBAL_TAG_ATTRS)
            if command_tag == DELETE_TAG:
                delete_note(notes, reasons, *params)
            elif command_tag == NOTE_TAG:
                add_note(notes, *params)
            elif command_tag == FINISH_TAG:
                end_program = True
                add_reason(reasons, f'({FINISH_TAG[1:]}): {params[0]}')
                # print(f"Final Reasons:\n{reasons}")
                print(f"\nFinal Notes:\n{notes[-2:]}")
                break
        continue_yes = input("Continue? (y/n): ")


if __name__ == '__main__':
    main()
