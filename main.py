import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Database setup
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Create books table
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

# Initialize database
init_db()

# Helper functions
def add_book(title, author, isbn, genre, pages, published_year, notes):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO books 
                 (title, author, isbn, genre, pages, published_year, date_added, notes, status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (title, author, isbn, genre, pages, published_year, date_added, notes, 'Available'))
    conn.commit()
    conn.close()

def get_all_books():
    conn = sqlite3.connect('library.db')
    df = pd.read_sql('SELECT * FROM books ORDER BY title', conn)
    conn.close()
    return df

def update_book(book_id, field, new_value):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute(f'UPDATE books SET {field} = ? WHERE id = ?', (new_value, book_id))
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()

# Streamlit UI
def main():
    st.set_page_config(page_title="Personal Library Manager", layout="wide")
    
    st.title("📚 Personal Library Manager")
    
    # Sidebar for adding new books
    with st.sidebar:
        st.header("Add New Book")
        with st.form("add_book_form"):
            title = st.text_input("Title*", max_chars=100)
            author = st.text_input("Author", max_chars=50)
            isbn = st.text_input("ISBN", max_chars=20)
            genre = st.selectbox("Genre", ["", "Fiction", "Non-Fiction", "Science Fiction", 
                                          "Fantasy", "Mystery", "Biography", "History", 
                                          "Self-Help", "Other"])
            pages = st.number_input("Pages", min_value=1, max_value=5000, value=300)
            published_year = st.number_input("Published Year", min_value=1800, 
                                            max_value=datetime.now().year, 
                                            value=datetime.now().year)
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Add Book")
            if submitted:
                if title:
                    add_book(title, author, isbn, genre, pages, published_year, notes)
                    st.success("Book added successfully!")
                else:
                    st.error("Title is required!")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["All Books", "Search", "Statistics"])
    
    with tab1:
        st.header("Your Book Collection")
        books_df = get_all_books()
        
        if not books_df.empty:
            # Display editable table
            edited_df = st.data_editor(
                books_df,
                column_config={
                    "id": None,
                    "title": "Title",
                    "author": "Author",
                    "isbn": "ISBN",
                    "genre": "Genre",
                    "pages": "Pages",
                    "published_year": "Year",
                    "date_added": st.column_config.DatetimeColumn("Date Added"),
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Available", "Reading", "Finished", "Lent", "Lost"]
                    ),
                    "rating": st.column_config.NumberColumn(
                        "Rating (1-5)",
                        min_value=1,
                        max_value=5,
                        step=1
                    ),
                    "notes": "Notes"
                },
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic"
            )
            
            # Save changes button
            if st.button("Save Changes"):
                # Compare original and edited dataframes
                for index, row in edited_df.iterrows():
                    book_id = row['id']
                    original_row = books_df[books_df['id'] == book_id].iloc[0]
                    
                    # Check for changes in each field
                    for col in edited_df.columns:
                        if col != 'id' and row[col] != original_row[col]:
                            update_book(book_id, col, row[col])
                
                st.success("Changes saved!")
            
            # Delete selected books
            if st.button("Delete Selected Books"):
                selected_ids = edited_df[edited_df['_selected']]['id'].tolist()
                for book_id in selected_ids:
                    delete_book(book_id)
                st.success(f"Deleted {len(selected_ids)} books!")
                st.experimental_rerun()
        else:
            st.info("Your library is empty. Add some books using the sidebar!")
    
    with tab2:
        st.header("Search Your Library")
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            search_term = st.text_input("Search by title or author")
        
        with search_col2:
            genre_filter = st.selectbox("Filter by genre", ["All"] + list(books_df['genre'].unique()))
        
        if search_term or genre_filter != "All":
            search_results = books_df.copy()
            
            if search_term:
                search_results = search_results[
                    search_results['title'].str.contains(search_term, case=False) | 
                    search_results['author'].str.contains(search_term, case=False)
                ]
            
            if genre_filter != "All":
                search_results = search_results[search_results['genre'] == genre_filter]
            
            st.dataframe(
                search_results,
                column_config={
                    "id": None,
                    "title": "Title",
                    "author": "Author",
                    "genre": "Genre",
                    "status": "Status",
                    "rating": "Rating"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Enter search terms or select a genre to filter")
    
    with tab3:
        st.header("Library Statistics")
        
        if not books_df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Books", len(books_df))
                st.metric("Total Pages", books_df['pages'].sum())
            
            with col2:
                avg_pages = int(books_df['pages'].mean())
                st.metric("Average Pages per Book", avg_pages)
                
                oldest_book = books_df['published_year'].min()
                st.metric("Oldest Book Year", oldest_book)
            
            with col3:
                status_counts = books_df['status'].value_counts()
                st.metric("Available Books", status_counts.get('Available', 0))
                
                avg_rating = books_df['rating'].mean()
                if not pd.isna(avg_rating):
                    st.metric("Average Rating", f"{avg_rating:.1f}/5")
            
            # Genre distribution chart
            st.subheader("Genre Distribution")
            genre_counts = books_df['genre'].value_counts()
            st.bar_chart(genre_counts)
            
            # Status distribution pie chart
            st.subheader("Status Distribution")
            status_counts = books_df['status'].value_counts()
            st.pyplot(status_counts.plot.pie(autopct='%1.1f%%', figsize=(8, 8)).figure)
        else:
            st.info("No statistics available - your library is empty")

if __name__ == "__main__":
    main()