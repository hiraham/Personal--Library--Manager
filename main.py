import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Database setup
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS books 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 title TEXT NOT NULL,
                 author TEXT,
                 isbn TEXT,
                 genre TEXT,
                 pages INTEGER,
                 published_year INTEGER,
                 date_added TEXT,
                 status TEXT DEFAULT 'Available',
                 rating INTEGER,
                 notes TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

def add_book(title, author, isbn, genre, pages, published_year, notes):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    date_added = datetime.now().strftime("%Y-%m-%d")
    c.execute('''INSERT INTO books 
                 (title, author, isbn, genre, pages, published_year, date_added, notes, status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (title, author, isbn, genre, pages, published_year, date_added, notes, 'Available'))
    conn.commit()
    conn.close()
    
    # Check for special book types
    if genre == "Poetry":
        st.session_state.special_notification = f"A poetry book '{title}' has been added to the library!"
    elif genre == "Science Fiction":
        st.session_state.special_notification = f"New sci-fi arrival: '{title}'!"
    elif "cook" in title.lower() or genre == "Cookbook":
        st.session_state.special_notification = f"New cooking resource added: '{title}'"

def get_all_books():
    conn = sqlite3.connect('library.db')
    df = pd.read_sql('SELECT * FROM books ORDER BY title', conn)
    conn.close()
    if not df.empty and 'date_added' in df.columns:
        df['date_added'] = pd.to_datetime(df['date_added']).dt.date
    return df

# ... [keep all other existing functions unchanged] ...

def main():
    st.set_page_config(page_title="Personal Library Manager", layout="wide")
    
    # Initialize session state for notifications
    if 'special_notification' not in st.session_state:
        st.session_state.special_notification = None
    
    st.title("📚 Personal Library Manager")
    
    # Display special notification if exists
    if st.session_state.special_notification:
        st.success(st.session_state.special_notification)
        # Clear the notification after displaying
        st.session_state.special_notification = None
    
    # ... [keep all existing UI code unchanged until the add book form] ...
    
    with st.sidebar:
        st.header("Add New Book")
        with st.form("add_book_form"):
            title = st.text_input("Title*", max_chars=100)
            author = st.text_input("Author", max_chars=50)
            isbn = st.text_input("ISBN", max_chars=20)
            genre = st.selectbox("Genre", ["", "Fiction", "Non-Fiction", "Science Fiction", 
                                          "Fantasy", "Mystery", "Biography", "History", 
                                          "Self-Help", "Poetry", "Cookbook", "Other"])
            pages = st.number_input("Pages", min_value=1, max_value=5000, value=300)
            published_year = st.number_input("Published Year", min_value=1800, 
                                            max_value=datetime.now().year, 
                                            value=datetime.now().year)
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Add Book")
            if submitted:
                if title:
                    add_book(title, author, isbn, genre, pages, published_year, notes)
                    # The notification will be handled within add_book()
                else:
                    st.error("Title is required!")

    # ... [keep all remaining code unchanged] ...

if __name__ == "__main__":
    main()