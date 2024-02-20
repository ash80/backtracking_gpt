from typing import List, Literal
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from file_list_viewer import TerminalFileListViewer
from text_util import REASON_ATTR, extract_commands, parse_command_and_params
# from langchain.prompts import HumanMessagePromptTemplate

RESOURCE = 'Resource'

DELETE_TAG = '<delete'
NOTE_TAG = '<note'
FINISH_TAG = '<finish'

global_tags = [DELETE_TAG, NOTE_TAG, FINISH_TAG]

global_tag_attrs = {
    DELETE_TAG: ["starts_with", REASON_ATTR],
    NOTE_TAG: ["note"],
    FINISH_TAG: [REASON_ATTR]
}

NOTES_START_STRING = "Notes (old to new):"
REASONS_START_STRING = "Last few actions and reasons (old to new):"

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
    reasons.append(reason)


def list_to_str(a_list):
    final_str = ''
    for item in a_list:
        final_str += f"- {item}\n"
    return final_str

def get_base_system_message() -> SystemMessage:
    return SystemMessage(content=f'''You are a helpful LLM agent. You objective is to find the info that perfectly achieves the "goal". Rest assured that available {RESOURCE} is sufficient to achieve the goal.
You have a finite token length so you need keep your notes under that length.
You can take some actions by typing out that action. Each action can be identified by an html like tag. Most tags have a {REASON_ATTR}="?" attribute. Replace ? with why you're taking that action.
Below are some actions that are always available:

1. {NOTE_TAG} note="?"/>: To take a variety of notes.
2. {DELETE_TAG} {global_tag_attrs[DELETE_TAG][0]}="?" {REASON_ATTR}="?"/>: To delete a previously added note. Replace ? for {global_tag_attrs[DELETE_TAG][0]} with the few starting words of the summary.
3. {FINISH_TAG} {REASON_ATTR}="?"/>: Only type this action when you have successfully achieved your goal.

To fit everything in the limited token length, it's essential to keep on deleting the notes that become irrelevant in light of new info.
Other actions are available with the {RESOURCE}.
Don't take the same action as in the "{REASONS_START_STRING}" list.
All the notes are added to "{NOTES_START_STRING}" list, which will be fed to you in the next iteration.
You must always select one action with the {RESOURCE} below and others from above 3 actions. Typically you would always need to take {NOTE_TAG} action to note down alternative actions you could take, and actions you want to avoid. So that you know how backtrack if you get stuck.
You must only respond with two or more actions and ensure that tags you generate match the displayed format.
Don't take any action that is not listed. An action that isn't wrapped with html-tag is not active.
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
    def context_window_func(x) -> str: 
        return f"Available tokens {max_tokens - x} | {x * 100//max_tokens}% Used\n"
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
        disp, reason = app.run(text)
        if reason:    
            add_reason(reasons, reason)
        reasons_str = list_to_str(reasons) if reasons else 'No actions and reasons\n\n'
        notes_str = list_to_str(notes) if notes else 'No notes added\n\n'
        system_message_contents = f'{REASONS_START_STRING}\n{reasons_str}'
        system_message_contents += f'\n{NOTES_START_STRING}\n{notes_str}'

        num_tokens = llm.get_num_tokens_from_messages(all_messages)
        num_tokens += llm.get_num_tokens(system_message_contents)
        num_tokens += llm.get_num_tokens(context_window_func(3 * max_tokens // 4))
        system_message_contents = context_window_func(num_tokens) + system_message_contents
        if disp:
            system_message_contents += disp
        all_messages.append(SystemMessage(content=system_message_contents))

        print('\n\n=========================\n')
        # # https://stackoverflow.com/questions/76639580/
        prompt = ChatPromptTemplate.from_messages(all_messages)
        print(prompt.format())
        break

        for message in all_messages[1:]:
            print(f"{message.type}:\n{message.content}")

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
                # print(f"Final Reasons:\n{reasons}")
                print(f"\nFinal Notes:\n{notes}")
                break
        continue_yes = input("Continue? (y/n): ")


if __name__ == '__main__':
    main()
