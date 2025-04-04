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
    # Remove leading spaces in categorical columns
    for col in ['test_type', 'job_levels', 'languages']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Create input form
    st.subheader("Enter Your Requirements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        organization_name = st.text_input("Name of Organization")
        
        # Get unique values from the dataset for test_type
        test_types = sorted(df['test_type'].unique().tolist())
        test_type = st.selectbox("Type of Test", test_types)
    
    with col2:
        # Get unique values from the dataset for job_levels
        job_levels = sorted(df['job_levels'].unique().tolist())
        experience = st.selectbox("Experience of candidates to be tested", job_levels)
        
        # Get unique values from the dataset for languages
        languages = sorted(df['languages'].unique().tolist())
        language = st.selectbox("Languages To be conducted in", languages)
    
    # Button to trigger recommendation
    if st.button("Get Recommendations"):
        if not organization_name:
            st.warning("Please enter organization name")
        else:
            # Filter DataFrame based on selections
            filtered_df = df.copy()
            
            if test_type:
                filtered_df = filtered_df[filtered_df['test_type'] == test_type]
            
            if experience:
                filtered_df = filtered_df[filtered_df['job_levels'] == experience]
            
            if language:
                filtered_df = filtered_df[filtered_df['languages'] == language]
            
            # If we have filtered results, show them
            if not filtered_df.empty:
                st.success(f"Found {len(filtered_df)} matching courses for {organization_name}")
                
                # If we have more than 3 results, use content-based filtering to get top 3
                if len(filtered_df) > 3:
                    # Create a simple content-based filtering
                    # Combine relevant features for similarity calculation
                    filtered_df['combined_features'] = filtered_df['title'] + ' ' + \
                                                     filtered_df['test_type'] + ' ' + \
                                                     filtered_df['job_levels'] + ' ' + \
                                                     filtered_df['languages'] + ' ' + \
                                                     filtered_df['description'].fillna('')
                    
                    # Create TF-IDF vectorizer
                    tfidf = TfidfVectorizer(stop_words='english')
                    tfidf_matrix = tfidf.fit_transform(filtered_df['combined_features'])
                    
                    # Calculate similarity scores between courses
                    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
                    
                    # Get the indices of the top courses based on average similarity
                    course_similarity = cosine_sim.mean(axis=1)
                    top_indices = course_similarity.argsort()[-3:][::-1]
                    recommended_df = filtered_df.iloc[top_indices]
                else:
                    recommended_df = filtered_df
                
                # Display recommendations
                st.subheader("Top Recommendations")
                
                for i, (_, row) in enumerate(recommended_df.iterrows(), 1):
                    st.markdown(f"### {i}. {row['title']}")
                    st.markdown(f"**Course ID:** {row['course_id']}")
                    if 'description' in row and pd.notna(row['description']):
                        st.markdown(f"**Description:** {row['description']}")
                    
                    if 'product_url' in row and pd.notna(row['product_url']):
                        st.markdown(f"[Go to Course]({row['product_url']})")
                    
                    st.markdown("---")
            else:
                st.warning("No courses found matching your criteria. Try changing some filters.")
else:
    st.error("Could not load the course data. Please check if the file exists and is valid.")

# Add some information at the bottom
st.markdown("---")
st.markdown("© 2025 Course Recommendation System")