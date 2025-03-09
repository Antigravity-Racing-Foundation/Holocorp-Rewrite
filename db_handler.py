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
    Insert a new topic into the database.

    Args:
        topicName (str): The name of the topic.

    Returns:
        None.
    
    Raises:
        ValueError: If creation of an existing topic is attempted.
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
    """
    Add a new entry into an existing topic.
    
    Args:
        topicName (str): The name of the topic.
        entryName (str): The name of the entry.
        entryText (str): The contents of the entry.

    Returns:
        None.

    Raises:
        ValueError: If the specified `topicName` couldn't be found.
    """
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
    """
    Fetch all topics.

    Args:
        None.

    Returns:
        list: A list of dictionaries that contain the topics' ID's and names.

    Raises:
        None.
    """
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics;")
    topics = cursor.fetchall()
    conn.close()
    return [{"id": topic[0], "name": topic[1]} for topic in topics]


def getEntriesByTopic(topicName: str) -> list:
    """
    Fetch all entries under a specific topic.
    
    Args:
        topicName (str): The name of the topic.
    
    Returns:
        list: A list of dictionaries that contain the entries' names and contents.

    Raises:
        ValueError: If the `topicName` couldn't be found.
    """
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM topics WHERE name = ?;", (topicName,))
    topic = cursor.fetchone()
    if not topic:
        conn.close()
        raise ValueError(f"[getEntriesByTopic] Topic {topicName} not found.")
        return []

    topicId = topic[0]
    cursor.execute("SELECT name, text FROM entries WHERE topic_id = ?;", (topicId,))
    entries = cursor.fetchall()
    conn.close()

    return [{"name": entry[0], "text": entry[1]} for entry in entries]


def getEntryContent(topicName: str, entryName: str) -> str:
    """
    Fetch the contents of a specific entry under a topic.
    
    Args:
        topicName (str): The name of the topic.
        entryName (str): The name of the entry.
    
    Returns:
        str: The entry's contents.
    
    Raises:
        None.
    """
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