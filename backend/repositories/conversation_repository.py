## func to get the conversation from database

import uuid
from backend.database import get_connection


def get_messages(conversation_id: str) -> list:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
        SELECT id, role, content, intent, document_id, created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY id
        """

        cursor.execute(query, (conversation_id,))
        messages = cursor.fetchall()

        return messages

    finally:
        cursor.close()
        connection.close()




def create_conversation(title: str = "New Chat") -> str:
    conversation_id = str(uuid.uuid4())

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        INSERT INTO conversations (id, title)
        VALUES (%s, %s)
        """

        cursor.execute(query, (conversation_id, title))
        connection.commit()

        return conversation_id

    finally:
        cursor.close()
        connection.close()




def save_message(
    conversation_id: str,
    role: str,
    content: str,
    intent: str | None = None,
    document_id: str | None = None
) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        INSERT INTO messages
            (conversation_id, role, content, intent, document_id)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            conversation_id,
            role,
            content,
            intent,
            document_id
        )

        cursor.execute(query, values)
        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()





def get_all_conversations() -> list:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
        """

        cursor.execute(query)
        conversations = cursor.fetchall()

        return conversations

    finally:
        cursor.close()
        connection.close()



def conversation_exists(conversation_id):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            SELECT 1
            FROM conversations
            WHERE id = %s
            LIMIT 1

  
             """
        cursor.execute(query, (conversation_id,))

        return cursor.fetchone() is not None

    finally:
        cursor.close()
        connection.close()


## new titile fun

def update_conversation_title(conversation_id: str, title: str) -> bool:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            UPDATE conversations
            SET title = %s
            WHERE id = %s
        """
        cursor.execute(query, (title, conversation_id))
        connection.commit()

        return cursor.rowcount > 0

    finally:
        cursor.close()
        connection.close()



## database fucntions
# Document database functions

def create_document(document_id: str, filename: str, status: str = "processing") -> None:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO documents (id, filename, status)
            VALUES (%s, %s, %s)
        """

        cursor.execute(query, (document_id, filename, status))
        connection.commit()

    finally:
        cursor.close()
        connection.close()


def update_document_status(document_id: str, status: str) -> None:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            UPDATE documents
            SET status = %s
            WHERE id = %s
        """

        cursor.execute(query, (status, document_id))
        connection.commit()

    finally:
        cursor.close()
        connection.close()


def get_all_documents() -> list:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT id, filename, status, created_at
            FROM documents
            ORDER BY created_at DESC
        """

        cursor.execute(query)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()