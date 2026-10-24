from states import volatileStateSet

import random

def reply_smartly(message: str) -> str | None:
    """
    Take a message and search for trigger words to reply a certain way.
    Replies are read from `external/message_templates/smart_replies.json`.
    An example `smart_replies.json` file is included in the repository.
    It can specify the trigger word, the reply, and the trigger chance (0-100%).

    Args:
        message (str): The message that the bot will potentially reply to.

    Returns:
        str: A reply selected based on the message's content and reply rules.
            If the message did not contain any remarkable content, returns None instead.
    """

    replies = volatileStateSet().smartReplies

    for replyRecipe in replies:
        triggers = replyRecipe["trigger"].split("|||")
        reply = replyRecipe["reply"]
        chance = replyRecipe["chance"]

        if any(trigger.lower() in message.lower() for trigger in triggers) and random.randrange(0,100) < chance:
            return reply

    return None