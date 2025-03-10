from difflib import unified_diff

from states import firmStateSet

from io_handler import ioScopes
from io_handler import ioRead

import sqlite3
import logging
import time
import os

def initDB():
    """
    Initialize the database at `dbFilePath` from `dbSchemaPath`.

    Args, Returns, Raises:
        None.
    """
    with open(firmStates.dbSchemaPath, "r") as file:
        schema = file.read()

    logging.debug(f"[initDB] Schema path is {firmStates.dbSchemaPath}")
    if schema:
        logging.debug(f"[initDB] Schema fetched!")
    else:
        logging.debug(f"[initDB] Unable to fetch the scheme.")

    conn = sqlite3.connect(firmStates.dbFilePath)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    logging.info("[initDB] Database initialized")


def addEntry(entryName, entryText):
    """
    Add a new entry into the databank.
    
    Args:
        entryName (str): The name of the entry.
        entryText (str): The contents of the entry.

    Returns:
        None.

    Raises:
        ValueError: if the entry already exists.
    """
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO entries (name, text) VALUES (?, ?);",
            (entryName, entryText),
        )
        conn.commit()
        logging.info(f"[addEntry] `{entryName}` added!")
    except sqlite3.IntegrityError:
        raise ValueError(f"[addEntry] `{entryName}` already exists.")
    finally:
        conn.close()


def editEntry(entryName: str, newText: str, editorID: str = "0"):
    oldText = getEntryContent(entryName)
    
    diff = unified_diff(oldText.splitlines(), newText.splitlines(), lineterm='')
    diff = "\n".join(list(diff))

    if not diff:
        diff = "[No changes...]"

    timestamp = int(time.time())

    if editorID == "0":
        logging.info("[editEntry] Making an anonymous edit...")
    else:
        logging.info(f"[editEntry] `{editorID}` requested an edit...")

    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()

    query = """
    UPDATE entries
    SET text = ?
    WHERE name = ?; 
    """
    cursor.execute(query, (newText, entryName,))

    cursor.execute("""
        SELECT entries.id FROM entries
        WHERE entries.name = ?;""",
        (entryName,)
    )
    entryID = cursor.fetchone()
    if not entryID:
        logging.error(f"[editEntry] Entry `{entryName}` not found!")
        conn.close()
        return
    entryID = entryID[0]

    cursor.execute(
        "INSERT INTO edits (entry_id, editor, date, diff) VALUES (?, ?, ?, ?);",
        (entryID, editorID, timestamp, diff,)
    )

    conn.commit()
    conn.close()

    logging.info(f"[editEntry] `{entryName}` edited by {editorID}.")


# TODO review this, this isn't a good way of doing this
def getEdits() -> list:
    """
    Fetch all edits of the databank.
    
    Args:
        None.
    
    Returns:
        list: A list of edits that were made.

    Raises:
        None.
    """
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()

    cursor.execute("SELECT entry_id, editor, date, diff FROM edits;",)
    entries = cursor.fetchall()
    conn.close()

    return [{"entry_id": entry[0], "editor": entry[1], "date": entry[2], "diff": entry[3]} for entry in entries]


def getEntries() -> list:
    """
    Fetch all entries from the databank.
    
    Args:
        None.
    
    Returns:
        list: A list of dictionaries that contain the entries' names and contents.

    Raises:
        None.
    """
    conn = sqlite3.connect(firmStates.dbFilePath)
    cursor = conn.cursor()

    cursor.execute("SELECT name, text FROM entries;",)
    entries = cursor.fetchall()
    conn.close()

    return [{"name": entry[0], "text": entry[1]} for entry in entries]


def getEntryContent(entryName: str) -> str:
    """
    Fetch the contents of a specific entry.
    
    Args:
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
    WHERE entries.name = ?;
    """
    cursor.execute(query, (entryName,))
    entry = cursor.fetchone()
    conn.close()

    if not entry:
        logging.info(f"[getEntryDescription] Unable to fetch entry `{entryName}`.")
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