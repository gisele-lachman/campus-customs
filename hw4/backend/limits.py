"""Every limit and cap for the shop agent, in one place.

Change a number here to tune the agent. Two can also be overridden from the
environment for testing (CC_MAX_TOOL_CALLS, CC_MAX_MODEL_REQUESTS).
"""

import os

# ---- Loop limits: per shopper message ----
MAX_TOOL_CALLS_PER_MESSAGE = int(os.getenv("CC_MAX_TOOL_CALLS", "6"))  # tool calls before we stop
MAX_MODEL_REQUESTS_PER_MESSAGE = int(os.getenv("CC_MAX_MODEL_REQUESTS", "8"))  # model round trips

# ---- Input caps ----
MAX_MESSAGE_LENGTH = 2000  # characters in one chat message
MAX_TOOL_INPUT_CHARS = 200  # characters of a product name or search query passed to a tool
AGENT_HISTORY_LIMIT = 12  # earlier messages the agent sees (about 6 back-and-forths)
HISTORY_LIMIT = 50  # saved messages shown when the chat window reloads

# ---- Result caps: what a tool may hand back to the model ----
MAX_MATCHES = 8  # candidates when a name is ambiguous
MAX_SUGGESTIONS = 3  # "did you mean" names when nothing matches
MAX_SEARCH_RESULTS = 12  # cards shown for one search
MAX_RELATED = 4  # "something close" items when a search finds nothing
MAX_COMPARE = 3  # products in one comparison
MAX_DESCRIPTION_CHARS = 500  # product description text returned by a tool

# ---- Audit trail (output/audit_trail.json) ----
AUDIT_ARGS_CHARS = 80  # length cap for the logged tool arguments
AUDIT_RESULT_CHARS = 120  # length cap for the logged tool result
