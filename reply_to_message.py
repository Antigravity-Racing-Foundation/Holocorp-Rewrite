from states import volatileStateSet

import logging
import random

def reply_smartly(message: str) -> str | None:
    """
    Take a message and search for trigger words to reply a certain way.
    Replies are read from `external/message_templates/smart_replies.json`.
    An example `smart_replies.json` file is included in the repository.
    It can specify the trigger word, the reply, the trigger chance (0-100%),
    and exception words, which will prevent a reply if they are in the original message.

    Args:
        message (str): The message that the bot will potentially reply to.

    Returns:
        str: A reply selected based on the message's content and reply rules.
            If the message did not contain any remarkable content, returns None instead.
    """

    logging.debug(f"[reply_smartly] Trying to reply to message `{message}`")

    # FIXME this isn't optimized, would be better to store parsed items in volatileStates
    replies = volatileStateSet().smartReplies

    for replyRecipe in replies:
        triggers = replyRecipe["trigger"].split("|||")
        reply = replyRecipe["reply"]
        exceptions = [
            e for e in replyRecipe["ignore_if_includes"].split("|||")
            if e
        ]
        chance = replyRecipe["chance"]

        logging.debug(f"[reply_smartly] Trying trigger `{replyRecipe["trigger"]}`")

        if random.randrange(0,100) < chance \
        and any(trigger.lower() in message.lower() for trigger in triggers) \
        and not any(exception.lower() in message.lower() for exception in exceptions):
            logging.debug(f"[reply_smartly] Hit! Replying `{reply}`")
            return reply

    logging.debug(f"[reply_smartly] No hits...")
    return None