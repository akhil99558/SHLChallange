# SHL -Course Recommender App


The first part of this project was to **scrape data** from SHL website using two scraping bots and storing it in the shl_data.csv. The second and most important part is a **Streamlit web application** that provides **personalized SHL course recommendations** based on user-selected criteria such as organization name, test type, experience level, and language. It uses **content-based filtering** with **TF-IDF and cosine similarity** to suggest the most relevant courses.


---

## 🚀 Features

- User-friendly interface to select:
  - ✅ **Organization Name**
  - ✅ **Test Type** (dropdown from dataset)
  - ✅ **Experience Level** (dropdown from dataset)
  - ✅ **Language** (dropdown from dataset)
- Intelligent **recommendation engine** using:
  - 📚 Content-based filtering
  - 📊 TF-IDF vectorization
  - 📏 Cosine similarity
- Displays **top 3 recommended courses** with:
  - 📌 Titles
  - 🔗 Clickable URLs
- Robust handling for:
  - ❌ Empty search results
  - ⚠️ Data loading errors
  - 🧩 Missing values in the dataset

---

## 🛠 Setup Instructions

1. **Clone the repository** or download the script:

   ```bash
   git clone https://github.com/yourusername/course-recommender.git
   cd course-recommender
   ```
Install required dependencies:

bash
Copy
Edit
```
pip install streamlit pandas scikit-learn numpy
```
Place your dataset file (shl_data.csv) in the same directory as the script.

Run the application:

bash
Copy
Edit
```
streamlit run recommender.py
```

The app will open automatically in your browser.

---

## 🧾 Dataset Format

The dataset (`shl_data.csv`) should contain the following relevant columns:
- `organization_name`
- `test_type`
- `experience_level`
- `language`
- `course_title`
- `course_url`

Make sure the dataset is clean and formatted properly for best results.

---

## ❓ Example Use Case

1. Select your **organization name** from the input field.
2. Choose your **test type** from the dropdown.
3. Pick your **experience level** (e.g., Junior, Mid, Senior).
4. Select the **language** of instruction (e.g., English, Spanish).
5. Get a list of **top 3 personalized course recommendations**!

---

## 🧯 Error Handling

- Displays a user-friendly message if:
  - No matching results are found.
  - The dataset is missing or improperly formatted.
  - Any dropdown has missing values.


---

## 👨‍💻 Author

Developed with ❤️ using Streamlit, pandas, and scikit-learn.

Feel free to contribute or suggest improvements!
