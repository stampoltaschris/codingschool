import json
import sqlite3
import streamlit as st
from typing import List, Dict, Any, Optional

DB_NAME = "exercises.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_chapters() -> List[str]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT chapter FROM exercises ORDER BY chapter")
        rows = cursor.fetchall()
        return [row["chapter"] for row in rows]
    finally:
        conn.close()

def fetch_questions_by_chapter(chapter: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exercises WHERE chapter = ? ORDER BY id", (chapter,))
        rows = cursor.fetchall()
        questions = []
        for r in rows:
            q = dict(r)
            if q["options"]:
                try:
                    q["options_list"] = json.loads(q["options"])
                except Exception:
                    q["options_list"] = None
            else:
                q["options_list"] = None
            questions.append(q)
        return questions
    finally:
        conn.close()

def main():
    st.set_page_config(
        page_title="Διαδραστική Μαθησιακή Εφαρμογή - Αριθμητικές Παραστάσεις",
        page_icon="📐",
        layout="centered"
    )

    st.title("📐 Μαθηματικά Γυμνασίου / Λυκείου")
    st.subheader("Εξάσκηση στις Αριθμητικές Παραστάσεις & Πράξεις")

    # Fetch available chapters
    chapters = fetch_chapters()
    if not chapters:
        st.warning("Δεν βρέθηκαν κεφάλαια στη βάση δεδομένων. Παρακαλώ τρέξτε πρώτα το 'db_installer.py'.")
        return

    # Sidebar Filter
    st.sidebar.header("🎯 Επιλογές Μάθησης")
    selected_chapter = st.sidebar.selectbox("Επιλέξτε Κεφάλαιο:", chapters)

    # Initialize / Reset state when chapter changes
    if "current_chapter" not in st.session_state or st.session_state.current_chapter != selected_chapter:
        st.session_state.current_chapter = selected_chapter
        st.session_state.questions = fetch_questions_by_chapter(selected_chapter)
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.answers_submitted = {}  # index -> dict(user_answer, is_correct, checked)

    questions = st.session_state.questions
    total_questions = len(questions)

    if total_questions == 0:
        st.info("Δεν υπάρχουν διαθέσιμες ασκήσεις για αυτό το κεφάλαιο.")
        return

    # Chapter Header & Progress
    st.markdown(f"### {selected_chapter}")
    curr_idx = st.session_state.current_index

    # Live score and progress bar
    progress_val = (curr_idx + 1) / total_questions if total_questions > 0 else 0
    st.progress(progress_val)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption(f"Ερώτηση **{curr_idx + 1}** από **{total_questions}**")
    with col2:
        st.metric("Σκορ", f"{st.session_state.score} / {total_questions}")

    st.divider()

    # Current Question
    question = questions[curr_idx]
    st.write(f"**{question['question_text']}**")

    # Key for form state management
    q_key = f"q_{selected_chapter}_{curr_idx}"

    # Answer widget
    options_list = question.get("options_list")

    if options_list:
        user_answer = st.radio("Επιλέξτε τη σωστή απάντηση:", options_list, key=f"radio_{q_key}")
    else:
        user_answer = st.text_input("Πληκτρολογήστε την απάντησή σας (π.χ. 17 ή 4.6):", key=f"input_{q_key}")

    # Check if already answered in state
    answered_info = st.session_state.answers_submitted.get(curr_idx)

    # Submit button
    submit_clicked = st.button("Αποστολή / Έλεγχος", type="primary", key=f"submit_{q_key}")

    if submit_clicked:
        if user_answer is None or str(user_answer).strip() == "":
            st.warning("Παρακαλώ συμπληρώστε ή επιλέξτε μια απάντηση πριν την αποστολή.")
        else:
            clean_user = str(user_answer).strip().replace(',', '.')
            clean_correct = str(question["correct_answer"]).strip().replace(',', '.')

            is_correct = False
            try:
                # Compare as float if numeric
                if float(clean_user) == float(clean_correct):
                    is_correct = True
            except ValueError:
                if clean_user.lower() == clean_correct.lower():
                    is_correct = True

            if not answered_info:
                st.session_state.answers_submitted[curr_idx] = {
                    "user_answer": user_answer,
                    "is_correct": is_correct
                }
                if is_correct:
                    st.session_state.score += 1
                answered_info = st.session_state.answers_submitted[curr_idx]
                st.rerun()

    # Display Feedback if answered
    if answered_info:
        if answered_info["is_correct"]:
            st.success("🎉 Σωστή Απάντηση! Μπράβο!")
        else:
            st.error("❌ Λάθος Απάντηση.")
            st.markdown("#### 💡 Αναλυτική Λύση - Βήμα προς Βήμα:")
            st.info(question["explanation"])

    st.divider()

    # Navigation buttons (Next / Previous / Reset)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])

    with nav_col1:
        if st.button("⬅️ Προηγούμενη", disabled=(curr_idx == 0)):
            st.session_state.current_index -= 1
            st.rerun()

    with nav_col2:
        if st.button("🔄 Επανεκκίνηση Κεφαλαίου"):
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answers_submitted = {}
            st.rerun()

    with nav_col3:
        if st.button("Επόμενη ➡️", disabled=(curr_idx == total_questions - 1)):
            st.session_state.current_index += 1
            st.rerun()

if __name__ == "__main__":
    main()
