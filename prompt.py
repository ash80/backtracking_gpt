from typing import List, Literal
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from file_list_viewer import TerminalFileListViewer
from prettify_util import color_tags
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

MAX_NUM_PAST_ACTIONS = 10

NOTES_START_STRING = "Notes (old to new):"
REASONS_START_STRING = f"Last {MAX_NUM_PAST_ACTIONS} actions and reasons (old to new):"

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
    if len(reasons) >= MAX_NUM_PAST_ACTIONS:
        del reasons[0]
    reasons.append(reason)


def list_to_str(a_list):
    final_str = ''
    for item in a_list:
        final_str += f"- {item}\n"
    return final_str

NOTE_ACT = f'{NOTE_TAG} {global_tag_attrs[NOTE_TAG][0]}="?"/>'
DELETE_ACT = f'{DELETE_TAG} {global_tag_attrs[DELETE_TAG][0]}="?" {REASON_ATTR}="?"/>'
FINISH_ACT = f'{FINISH_TAG} {REASON_ATTR}="?"/>'

GLOBAL_ACTIONS = [NOTE_ACT, DELETE_ACT, FINISH_ACT]

def get_base_system_message() -> SystemMessage:
    return SystemMessage(content=f'''You are a helpful LLM agent. You objective is to find the info that perfectly achieves the "goal". Rest assured that available {RESOURCE} is sufficient to achieve the goal.
You have a finite token length so you need keep your notes under that length.
You can take some actions by typing out that action. Each action can be identified by an html like tag. Most actions have a {REASON_ATTR}="?" attribute. Replace ? with why you're taking that action.
Below are some global actions that are always available:

1. {NOTE_ACT}: To take a variety of notes.
2. {DELETE_ACT}: To delete a previously added note. Replace ? for {global_tag_attrs[DELETE_TAG][0]} with the few starting words of the summary.
3. {FINISH_ACT}: Only type this action when you have successfully achieved your goal.

To fit everything in the limited token length, it's essential to keep on deleting the notes that become irrelevant in light of new info.
Other actions are available with the {RESOURCE}.
Don't take the same action as in the "{REASONS_START_STRING}" list.
All the notes are added to "{NOTES_START_STRING}" list, which will be fed to you in the next iteration.
You can select at most one action from the {RESOURCE} below and one or more from above 3 global actions. You MUST always take {NOTE_TAG} action to note down alternative actions you could take, and actions you want to avoid. So that you know how to backtrack if you get stuck.
You must only respond with two or more actions and ensure that tags you generate match the displayed format.
{RESOURCE} operate in different views. Each view has different set of actions. Any action you took in the past may not work now because {RESOURCE} may be in a different view. Only take actions that are in the global actions or {RESOURCE} action list. An action that isn't wrapped with html-tag is not active.
''')


def get_human_message(goal) -> HumanMessage:
    return HumanMessage(content=f'Goal: {goal}')


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
                print(f"\nFinal Notes:\n{notes[-2:]}")
                break
        continue_yes = input("Continue? (y/n): ")


if __name__ == '__main__':
    main()
