
from langchain_core.messages import HumanMessage, SystemMessage

from global_actions import DELETE_ACT, DELETE_TAG, FINISH_ACT, GLOBAL_TAG_ATTRS, MAX_NUM_PAST_ACTIONS, NOTE_ACT, NOTE_TAG, REASON_ATTR

RESOURCE = 'Resource'

NOTES_START_STRING = "Notes (old to new):"
REASONS_START_STRING = f"Last {MAX_NUM_PAST_ACTIONS} actions and reasons (old to new):"


def get_base_system_message() -> SystemMessage:
    return SystemMessage(content=f'''You are a helpful LLM agent. You objective is to find the info that perfectly achieves the "goal". Rest assured that available {RESOURCE} is sufficient to achieve the goal.
You have a finite token length so you need keep your notes under that length.
You can take some actions by typing out that action. Each action can be identified by an html like tag. Most actions have a {REASON_ATTR}="?" attribute. Replace ? with why you're taking that action.
Below are some global actions that are always available:

1. {NOTE_ACT}: To take a variety of notes.
2. {DELETE_ACT}: To delete a previously added note. Replace ? for {GLOBAL_TAG_ATTRS[DELETE_TAG][0]} with the few starting words of the summary.
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
