from difflib import unified_diff

from states import firmStateSet

from io_handler import ioScopes
from io_handler import ioRead

from contextlib import closing
from enum import Enum
import sqlite3
import logging
import time
import os

# TODO add rename function command

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
    with closing(sqlite3.connect(firmStates.dbFilePath)) as conn:
        with closing(conn.cursor()) as cursor:
            try:
                cursor.execute(
                    "INSERT INTO entries (name, text) VALUES (?, ?);",
                    (entryName, entryText),
                )
                conn.commit()
                logging.info(f"[addEntry] `{entryName}` added!")
            except sqlite3.IntegrityError:
                raise ValueError(f"[addEntry] `{entryName}` already exists.")


def editEntry(entryName: str, newText: str, editorID: str = "0"):
    """
    Changes an existing entry's contents to `newText` and logs the changes in the `edits` table.
    Upon an entry edit, the differences between the new text and the old text will be logged, along with the `editorID` (intended to be a Discord account ID) and the UNIX timestamp at which the edit occurred.

    Args:
        entryName (str): The name of the entry.
        newText (str): The new contents of the entry.
        editorID (str): The ID of the editor. Defaults to 0.

    Returns:
        str: A status message:
            - "NoEntry": If the entry doesn't exist in the database. 
            - "EntryGone": If the entry exists in the database but has been marked as deleted, making it unavailable to edit.
            - For other situations, nothing is returned.

    Raises:
        None.
    """
    oldText = getEntryContent(entryName)

    # not ideal but cba to do enums or custom exceptions yet
    if oldText == "NoEntry" or oldText == "EntryGone":
        return oldText
    
    diff = unified_diff(oldText.splitlines(), newText.splitlines(), lineterm='')
    diff = "\n".join(list(diff))
    if not diff:
        diff = "[No changes...]"

    timestamp = int(time.time())

    if editorID == "0":
        logging.info("[editEntry] Making an anonymous edit...")
    else:
        logging.info(f"[editEntry] `{editorID}` requested an edit...")

    with closing(sqlite3.connect(firmStates.dbFilePath)) as conn:
        with closing(conn.cursor()) as cursor:
            query = """
            UPDATE entries
            SET text = ?
            WHERE name = ?; 
            """
            cursor.execute(query, (newText, entryName,))

            query = """
            SELECT entries.id FROM entries
            WHERE entries.name = ?;
            """
            cursor.execute(query, (entryName,))
            entryID = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO edits (entry_id, editor, date, diff) VALUES (?, ?, ?, ?);",
                (entryID, editorID, timestamp, diff,)
            )
            conn.commit()

    logging.info(f"[editEntry] `{entryName}` edited by {editorID}.")


class Visibility(Enum):
    DELETE = 1
    RESTORE = 0

def changeEntryVisibility(entryName: str, action: Visibility):
    """
    Changes the state of the entry between being hidden and being available by changing the `is_deleted` column of an entry.
    If `entryName` does not exist, no operation is performed.

    Args:
        entryName (str): The name of the entry.
        action (Visibility): The new state of the entry:
            - Visibility.DELETE: Will set the `is_deleted` flag to True, effectively removing the entry. Includes the operation date in the entry's `deleted_date` column.
            - Visibility.RESTORE: Will set the `is_deleted` flag to False, making a deleted entry visible. Removes the operation date in the entry's `deleted_date` column, if present.

    Returns:
        None.

    Raises:
        None.
    """
    with closing(sqlite3.connect(firmStates.dbFilePath)) as conn:
        with closing(conn.cursor()) as cursor:
            query = """
            UPDATE entries
            SET is_deleted = ?
            WHERE name = ?;
            """
            cursor.execute(query, (action.value, entryName,))
            conn.commit()


def getEdits(entryName: str = None) -> list:
    """
    Fetch a list of edits that were made to the databank.
    Behavior changes based on the args passed:
    - If `entryName` is not passed, a list of all edits ever made to the database is returned.
    - If `entryName` is passed, a list of all edits ever made to the specified entry is returned.
    
    Args:
        entryName (str): The name of an entry to see edits of.
    
    Returns:
        list: An appropriate list of edits.

    Raises:
        None.
    """
    with closing(sqlite3.connect(firmStates.dbFilePath)) as conn:
        with closing(conn.cursor()) as cursor:
            if entryName:
                query = "SELECT id FROM entries WHERE name = ?;"
                cursor.execute(query, (entryName,))
                entryID = cursor.fetchone()[0]

                query = "SELECT editor, date, diff FROM edits WHERE entry_id = ?;"
                cursor.execute(query, (entryID,))
                edits = cursor.fetchall()

                return [(entryName, edit[0], edit[1], edit[2]) for edit in edits]
            else:
                cursor.execute("""
                SELECT entries.name, edits.editor, edits.date, edits.diff
                FROM edits
                JOIN entries ON edits.entry_id = entries.id;
                """)
                return cursor.fetchall()


def getEntries() -> list:
    """
    Fetch all entries from the databank. Entries marked as removed are not returned.
    
    Args:
        None.
    
    Returns:
        list: A list of dictionaries that contain the entries' names and contents.

    Raises:
        None.
    """
    with closing(sqlite3.connect(firmStates.dbFilePath)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT name, text FROM entries WHERE is_deleted = FALSE;",)
            entries = cursor.fetchall()
            return [{"name": entry[0], "text": entry[1]} for entry in entries]


def getEntryContent(entryName: str) -> str:
    """
    Fetch the contents of a specific entry.
    
    Args:
        entryName (str): The name of the entry.
    
    Returns:
        str: The entry's contents OR a status code:
            - "NoEntry": If an entry with the specified name does not exist.
            - "EntryGone": If the entry with the specified name has been marked as deleted. 
    
    Raises:
        None.
    """
    with closing(sqlite3.connect(firmStates.dbFilePath)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT is_deleted, text FROM entries WHERE name = ?", (entryName,))
            response = cursor.fetchone()

            if not response:
                logging.error(f"[getEntryDescription] Unable to fetch entry `{entryName}`.")
                return "NoEntry"

            if response[0] == 1:
                logging.error(f"[editEntry] Entry `{entryName}` has been removed.")
                return "EntryGone"

            return response[1]


logging.debug("[db_handler Initialization] Started")

firmStates = firmStateSet()
logging.debug("[db_handler Initialization] Linked firmStates")

if not firmStates.dbSchemaPath:
    logging.warning(f"[db_handler Initialization] Can't find schema at {firmStates.dbSchemaPath}, expect initDB to fail!")

if not os.path.isfile(firmStates.dbFilePath):
    logging.debug(f"[db_handler Initialization] {firmStates.dbFilePath} does not exist, creating one now...")
    initDB()

logging.info(f"[db_handler Initialization] Finished with schema at {firmStates.dbSchemaPath} and database at {firmStates.dbFilePath}")