
from collections import defaultdict

# org_id -> live meeting document
LIVE_DOCUMENT_STATE = defaultdict(lambda: {
    "transcript": "",
    "decisions": [],
    "action_items": [],
    "risks": [],
    "summary": ""
})
