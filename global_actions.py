from typing import List


MAX_NUM_PAST_ACTIONS = 10

REASON_ATTR = 'reason'

DELETE_TAG = '<delete'
NOTE_TAG = '<note'
FINISH_TAG = '<finish'

GLOBAL_TAGS = [DELETE_TAG, NOTE_TAG, FINISH_TAG]

GLOBAL_TAG_ATTRS = {
    DELETE_TAG: ["starts_with", REASON_ATTR],
    NOTE_TAG: ["note"],
    FINISH_TAG: [REASON_ATTR]
}


NOTE_ACT = f'{NOTE_TAG} {GLOBAL_TAG_ATTRS[NOTE_TAG][0]}="?"/>'
DELETE_ACT = f'{DELETE_TAG} {GLOBAL_TAG_ATTRS[DELETE_TAG][0]}="?" {REASON_ATTR}="?"/>'
FINISH_ACT = f'{FINISH_TAG} {REASON_ATTR}="?"/>'

GLOBAL_ACTIONS = [NOTE_ACT, DELETE_ACT, FINISH_ACT]

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
