from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)

# Load the dataset
def load_data():
    try:
        df = pd.read_csv("shl_data.csv")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# Global variable for the dataset
df = load_data()

# Clean up the data
if df is not None:
    for col in ['title', 'test_type', 'job_levels', 'languages', 'description']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    
    # Pre-compute the combined features
    df['combined_features'] = (
        df['title'] + ' ' + 
        df['test_type'] + ' ' + 
        df['job_levels'] + ' ' + 
        df['languages'] + ' ' + 
        df['description']
    )

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Course Recommendation API is running. Use /recommend endpoint with a query parameter."
    })

@app.route('/recommend', methods=['GET'])
def recommend():
    if df is None:
        return jsonify({
            "status": "error",
            "message": "Dataset could not be loaded."
        }), 500
    
    # Get query from request parameters
    query = request.args.get('query', '')
    
    if not query.strip():
        return jsonify({
            "status": "error",
            "message": "Please provide a query parameter."
        }), 400
    
    try:
        # Vectorize and calculate similarity
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['combined_features'])
        user_vec = tfidf.transform([query])
        similarity_scores = cosine_similarity(user_vec, tfidf_matrix).flatten()
        
        # Get the top 3 recommendations
        top_indices = similarity_scores.argsort()[-3:][::-1]
        recommended_df = df.iloc[top_indices]
        
        # Convert to Python float first, then format as percentage string
        percentages = [float(score * 100) for score in similarity_scores[top_indices]]
        
        # Build the response
        recommendations = []
        for i, (_, row) in enumerate(recommended_df.iterrows()):
            rec = {
                "rank": i + 1,
                "title": row['title'],
                "course_id": row['course_id'],
                "match_score": round(percentages[i], 2),
                "test_type": row['test_type'] if 'test_type' in row else "",
                "job_levels": row['job_levels'] if 'job_levels' in row else "",
                "languages": row['languages'] if 'languages' in row else "",
                "description": row['description'] if 'description' in row else ""
            }
            
            if 'product_url' in row and row['product_url']:
                rec["product_url"] = row['product_url']
                
            recommendations.append(rec)
            
        return jsonify({
            "status": "success",
            "query": query,
            "recommendations": recommendations
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)