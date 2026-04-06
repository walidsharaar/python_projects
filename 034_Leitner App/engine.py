from datetime import datetime, timedelta
import config

class LeitnerEngine:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_vocabulary(self, german, english):
        conn = self.db.get_connection()
        conn.cursor().execute("INSERT INTO Vocab (german, english) VALUES (?, ?)", (german, english))
        conn.close()

    def get_due_words(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, german, english, box FROM Vocab WHERE next_review <= GETDATE()")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "german": r[1], "english": r[2], "box": r[3]} for r in rows]

    def update_word_progress(self, word_id, current_box, was_correct):
        new_box = min(current_box + 1, 5) if was_correct else 1
        days = config.BOX_INTERVALS[new_box]
        next_date = datetime.now() + timedelta(days=days)

        conn = self.db.get_connection()
        conn.cursor().execute("UPDATE Vocab SET box = ?, next_review = ? WHERE id = ?", (new_box, next_date, word_id))
        conn.close()