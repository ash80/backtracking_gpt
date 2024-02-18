from typing import List, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from file_viewer import TerminalFileViewer
from text_util import REASON_ATTR, extract_commands, parse_command_and_params
# from langchain.prompts import HumanMessagePromptTemplate

DELETE_TAG = '<d'
NOTE_TAG = '<n'
FINISH_TAG = '<f'

global_tags = [DELETE_TAG, NOTE_TAG, FINISH_TAG]

global_tag_attrs = {
    DELETE_TAG: ["starts_with", REASON_ATTR],
    NOTE_TAG: ["note"],
    FINISH_TAG: [REASON_ATTR]
}

NOTES_START_STRING = "Notes (old to new)):\n"
REASONS_START_STRING = "Last few actions and reasons (old to new):\n"

def delete_note(notes: List[str], reasons: List[str], starts_with: str, reason: str):
    if (starts_with.startswith('- ')):
        starts_with = starts_with[2:]
    for note in notes:
        if note.startswith(starts_with):
            notes.remove(note)
            add_reason(reasons, f'({DELETE_TAG[1:]}): {reason}')


def add_note(notes: List[str], note: str):
    notes.append(note)


def add_reason(reasons: List[str], reason: str):
    if len(reasons) == 3:
        del reasons[0]
    reasons.append(reason)


def list_to_str(a_list):
    final_str = ''
    for item in a_list:
        final_str = f"- {item}\n"
    return final_str

def get_base_system_message() -> SystemMessage:
    return SystemMessage(content=f'''You are a helpful LLM agent. You objective is to find the info that perfectly achieves the "goal".
You have a finite token length so you need keep your notes under that length.
You can take some actions by typing out that action. Each action can be identified by an html like tag. Most tags have a {REASON_ATTR}="?" attribute. Replace ? with why you're taking that action.
Below are some actions that are always available:

1. note: To take note of important stuff that might be relevant for achieving the goal. Format: {NOTE_TAG} note="?"/>
2. delete: To delete a previously added note. Format: {DELETE_TAG} {global_tag_attrs[DELETE_TAG][0]}="?" {REASON_ATTR}="?"/>. Replace ? for {global_tag_attrs[DELETE_TAG][0]} with the few starting words of the summary.
3. finish: Once you've achieved your goal type this action. Format {FINISH_TAG} {REASON_ATTR}="?"/>

To fit everything in the limited token length, it's essential to keep on deleting the notes that become irrelevant in light of new info.
Other actions are available along with the resource. You must only respond with one or more actions and ensure that tags you generate match the displayed format.
Don't take the same action as in the {REASONS_START_STRING} list.
''')


def get_human_message(goal) -> HumanMessage:
    return HumanMessage(content=f'Goal: {goal}')


def main():
    notes = []
    reasons = []
    model_name : Literal['gpt-4-turbo-preview', 'gpt-3.5-turbo', 'gpt-4'] = 'gpt-4-turbo-preview'
    llm = ChatOpenAI(model=model_name, temperature=0.1)
    context_lengths = {'gpt-3.5-turbo': 4097, 'gpt-4-turbo-preview': 128000, 'gpt-4': 32000}
    max_tokens = context_lengths[model_name]
    def context_window_func(x) -> SystemMessage: 
        return SystemMessage(content=f"Available tokens {max_tokens - x} | {x * 100//max_tokens}% Used")
    # goal = input("Enter goal: ")
    goal = "How much money air canada must pay to Moffatt?"
    text = None
    all_messages: List[BaseMessage] = [
        get_base_system_message(),
        get_human_message(goal),
    ]

    viewer = TerminalFileViewer('src_text.txt')
    continue_yes = 'y'
    end_program = False
    while not end_program and continue_yes == 'y':
        disp, reason = viewer.run(text)
        if reason:    
            add_reason(reasons, reason)
        reasons_str = list_to_str(reasons) if reasons else 'No actions and reasons\n\n'
        notes_str = list_to_str(notes) if notes else 'No notes added\n\n'
        all_messages.append(SystemMessage(content=f'{REASONS_START_STRING}\n{reasons_str}'))
        all_messages.append(SystemMessage(content=f'{NOTES_START_STRING}\n{notes_str}'))
        if disp:
            all_messages.append(SystemMessage(content=disp))

        num_tokens = llm.get_num_tokens_from_messages(all_messages)
        llm.get_num_tokens(str(context_window_func(3 * max_tokens // 4)))
        num_tokens += llm.get_num_tokens(str(context_window_func(3 * max_tokens // 4)))
        all_messages.insert(2, context_window_func(num_tokens))

        for message in all_messages:
            print(f"{message.type}:\n{message.content}")
        # break

        text = ''
        print("--------------\nAgent:")
        for chunk in llm.stream(all_messages):
            chunk_content = chunk.content
            text += chunk_content
            print(chunk_content, end='' if chunk_content else '\n', flush=True)

        commands = extract_commands(text, global_tags)
        for command in commands:
            command_tag, params = parse_command_and_params(command, global_tags, global_tag_attrs)
            if command_tag == DELETE_TAG:
                delete_note(notes, reasons, *params)
            elif command_tag == NOTE_TAG:
                add_note(notes, *params)
            elif command_tag == FINISH_TAG:
                end_program = True
                add_reason(reasons, f'({FINISH_TAG[1:]}): {params[0]}')
                print(f"Final Reasons:\n{reasons}")
                print(f"Final Notes:\n{notes}")
                break
        continue_yes = input("Continue? (y/n): ")


if __name__ == '__main__':
    main()
