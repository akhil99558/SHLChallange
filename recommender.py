import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set page title and description
st.set_page_config(page_title="Course Recommendation System", layout="wide")
st.title("Course Recommendation System")
st.write("Find the best courses based on your requirements")

# Load the dataset
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("shl_data.csv")
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

if df is not None:
    # Clean up the data
    for col in ['title', 'test_type', 'job_levels', 'languages', 'description']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

    # Simple plaintext input area
    st.subheader("What are you looking for?")
    user_input = st.text_area(
        "Describe your needs in plain language:",
        placeholder="Example: I need a personality assessment for senior managers in English",
        height=100
    )

    if st.button("Get Recommendations"):
        if not user_input.strip():
            st.warning("Please enter a description of your requirements.")
        else:
            with st.spinner("Finding the best matches..."):
                # Combine relevant features into one string for better matching
                df['combined_features'] = (
                    df['title'] + ' ' + 
                    df['test_type'] + ' ' + 
                    df['job_levels'] + ' ' + 
                    df['languages'] + ' ' + 
                    df['description']
                )

                # Vectorize and calculate similarity
                tfidf = TfidfVectorizer(stop_words='english')
                tfidf_matrix = tfidf.fit_transform(df['combined_features'])
                user_vec = tfidf.transform([user_input])
                similarity_scores = cosine_similarity(user_vec, tfidf_matrix).flatten()
                
                # Get the top 3 recommendations
                top_indices = similarity_scores.argsort()[-3:][::-1]
                recommended_df = df.iloc[top_indices]

                # Display recommendations in a visually appealing format
                st.subheader("Top 3 Recommendations")
                
                for i, (_, row) in enumerate(recommended_df.iterrows(), 1):
                    # Create a card-like structure for each recommendation
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"### {i}. {row['title']}")
                        
                        # Display key information
                        if 'test_type' in row and row['test_type']:
                            st.markdown(f"**Type:** {row['test_type']}")
                            
                        if 'job_levels' in row and row['job_levels']:
                            st.markdown(f"**Suitable for:** {row['job_levels']}")
                            
                        if 'languages' in row and row['languages']:
                            st.markdown(f"**Available in:** {row['languages']}")
                            
                        if 'description' in row and row['description']:
                            st.markdown(f"**Description:** {row['description']}")
                    
                    with col2:
                        st.markdown(f"**Course ID:** {row['course_id']}")
                        
                        if 'product_url' in row and row['product_url']:
                            st.markdown(f"[View Details]({row['product_url']})")
                    
                    st.markdown("---")
                
                # Add similarity score information - FIXED to avoid NumPy type error
                with st.expander("Match Details"):
                    # Convert to Python float first, then format as percentage string
                    percentages = [f"{float(score * 100):.2f}%" for score in similarity_scores[top_indices]]
                    match_info = pd.DataFrame({
                        'Course': recommended_df['title'].values,
                        'Match Score': percentages
                    })
                    st.table(match_info)
else:
    st.error("Could not load the course data. Please check if the file exists and is valid.")

# Footer
st.markdown("---")
st.markdown("© 2025 Course Recommendation System")