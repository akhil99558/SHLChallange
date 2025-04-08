from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title="Course Recommendation API")

# Load and preprocess dataset
df = pd.read_csv("shl_data.csv")

# Strip leading/trailing spaces
for col in ['test_type', 'job_levels', 'languages']:
    df[col] = df[col].astype(str).str.strip()

# API request schema
class RecommendationRequest(BaseModel):
    organization_name: str
    test_type: str
    job_level: str
    language: str

@app.post("/recommend")
def recommend_courses(request: RecommendationRequest):
    # Filter the dataset
    filtered_df = df[
        (df['test_type'].str.lower() == request.test_type.lower()) &
        (df['job_levels'].str.lower() == request.job_level.lower()) &
        (df['languages'].str.lower() == request.language.lower())
    ]

    if filtered_df.empty:
        raise HTTPException(status_code=404, detail="No matching courses found.")

    if len(filtered_df) > 3:
        # Create a combined text feature
        filtered_df['combined_features'] = (
            filtered_df['title'] + ' ' +
            filtered_df['test_type'] + ' ' +
            filtered_df['job_levels'] + ' ' +
            filtered_df['languages'] + ' ' +
            filtered_df['description'].fillna('')
        )

        # TF-IDF Vectorization and cosine similarity
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(filtered_df['combined_features'])
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

        # Rank based on average similarity
        course_similarity = cosine_sim.mean(axis=1)
        top_indices = course_similarity.argsort()[-3:][::-1]
        recommended_df = filtered_df.iloc[top_indices]
    else:
        recommended_df = filtered_df

    # Convert to list of dicts for API response
    response = []
    for _, row in recommended_df.iterrows():
        response.append({
            "title": row["title"],
            "course_id": row["course_id"],
            "description": row["description"],
            "product_url": row["product_url"]
        })

    return {
        "organization": request.organization_name,
        "recommendations": response
    }
