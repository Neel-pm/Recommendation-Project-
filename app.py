import pickle
import streamlit as st
import requests
import time

st.header('🎬 Movie Recommender System')

# -----------------------------
# 🔹 Load Data
# -----------------------------
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# -----------------------------
# 🔹 Fetch Poster (Cached)
# -----------------------------
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=a094ba6df7e5851c047115b2ae1c77ad&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()

        poster_path = data.get('poster_path')
        if not poster_path:
            return "https://via.placeholder.com/500x750?text=No+Poster+Available"

        full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
        return full_path

    except requests.exceptions.RequestException as e:
        print("Error fetching poster:", e)
        # Return fallback image
        return "https://via.placeholder.com/500x750?text=Error+Fetching+Poster"

# -----------------------------
# 🔹 Recommend Movies (Cached)
# -----------------------------
@st.cache_data(show_spinner=False)
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].id
        name = movies.iloc[i[0]].title
        poster = fetch_poster(movie_id)
        recommended_movie_names.append(name)
        recommended_movie_posters.append(poster)
        time.sleep(0.2)  # small delay to avoid rate limits

    return recommended_movie_names, recommended_movie_posters

# -----------------------------
# 🔹 Streamlit UI
# -----------------------------
movie_list = movies['title'].values
selected_movie = st.selectbox(
    "🎥 Type or select a movie from the dropdown:",
    movie_list
)

if st.button('🎯 Show Recommendation'):
    with st.spinner("Fetching recommendations..."):
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

        # Display 5 movie recommendations
        cols = st.columns(5)
        for col, name, poster in zip(cols, recommended_movie_names, recommended_movie_posters):
            with col:
                st.image(poster, use_container_width=True)
                st.text(name)

# -----------------------------
# 🔹 Optional: Clear cache button
# -----------------------------
if st.button("♻️ Clear Cache"):
    st.cache_data.clear()
    st.success("Cache cleared successfully!")
