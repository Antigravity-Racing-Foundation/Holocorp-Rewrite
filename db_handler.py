from states import firmStateSet
from io_handler import ioScopes
from io_handler import ioRead
import sqlite3
import logging
import os

def initDB():
    """
    Initialize the database at `dbFilePath` from `dbSchemaPath`.

    Args, Returns, Raises:
        None.
    """
    with open(firmStates.dbSchemaPath, "r") as file:
        schema = file.read()

    conn = sqlite3.connect(firmStates.dbFilePath)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    logging.info("[initDB] Database initialized")


def addTopic(topicName):
    """
    Insert a new topic.
    
    """
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO topics (name) VALUES (?);", (topicName,))
        conn.commit()
        logging.info(f"[addTopic] Added topic `{topicName}`")
    except sqlite3.IntegrityError:
        raise ValueError(f"[addTopic] Topic {topicName} already exists!")
    finally:
        conn.close()


def addEntry(topicName, entryName, entryText):
    """Insert a new entry under a topic."""
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM topics WHERE name = ?;", (topicName,))
    topic = cursor.fetchone()
    if not topic:
        raise ValueError(f"[addEntry] Topic `{topicName}` not found.")
        conn.close()
        return
    
    topicId = topic[0]

    try:
        cursor.execute(
            "INSERT INTO entries (topic_id, name, text) VALUES (?, ?, ?);",
            (topicId, entryName, entryText),
        )
        conn.commit()
        logging.info(f"[addEntry] `{entryName}` of `{topicName}` added!")
    except sqlite3.IntegrityError:
        raise ValueError(f"[addEntry] `{entryName}` of `{topicName}` already exists.")
    finally:
        conn.close()


def getTopics():
    """Fetch all topics."""
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics;")
    topics = cursor.fetchall()
    conn.close()
    return [{"id": topic[0], "name": topic[1]} for topic in topics]


def getEntriesByTopic(topicName):
    """Fetch all entries under a specific topic."""
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM topics WHERE name = ?;", (topicName,))
    topic = cursor.fetchone()
    if not topic:
        raise ValueError(f"[getEntriesByTopic] Topic {topicName} not found.")
        conn.close()
        return []

    topicId = topic[0]
    cursor.execute("SELECT name, text FROM entries WHERE topic_id = ?;", (topicId,))
    entries = cursor.fetchall()
    conn.close()

    return [{"name": entry[0], "text": entry[1]} for entry in entries]


def getEntryContent(topicName, entryName):
    """Fetch the description of a specific entry under a topic."""
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()

    query = """
    SELECT entries.text FROM entries
    JOIN topics ON topics.id = entries.topic_id
    WHERE topics.name = ? AND entries.name = ?;
    """
    cursor.execute(query, (topicName, entryName))
    entry = cursor.fetchone()
    conn.close()

    if not entry:
        logging.info(f"[getEntryDescription] Unable to fetch entry `{entryName}` of topic `{topicName}`")
        return None
    return entry[0]


logging.debug("[db_handler Initialization] Started")

firmStates = firmStateSet()
logging.debug("[db_handler Initialization] Linked firmStates")

if not firmStates.dbSchemaPath:
    logging.warning(f"[db_handler Initialization] Can't find schema at {firmStates.dbSchemaPath}, expect initDB to fail!")

if not os.path.isfile(firmStates.dbFilePath):
    logging.debug(f"[db_handler Initialization] {firmStates.dbFilePath} does not exist, creating one now...")
    initDB()

logging.info(f"[db_handler Initialization] Finished with schema at {firmStates.dbSchemaPath} and database at {firmStates.dbFilePath}")