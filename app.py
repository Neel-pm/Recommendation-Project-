import pickle
import streamlit as st
import requests
import time

st.header('🎬 Movie Recommender System')

# -----------------------------
# 🔹 Load Movie Data
# -----------------------------
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))


# -----------------------------
# 🔹 Validate Image URL
# -----------------------------
def validate_image_url(url):
    """
    Check if an image URL actually exists (HTTP 200 OK).
    """
    try:
        head = requests.head(url, timeout=5)
        return head.status_code == 200
    except requests.exceptions.RequestException:
        return False


# -----------------------------
# 🔹 Get Movie ID by Title (Fallback)
# -----------------------------
@st.cache_data(show_spinner=False)
def get_movie_id(movie_title):
    """
    Fetch TMDB movie ID by movie title.
    Returns None if not found or on error.
    """
    api_key = "a094ba6df7e5851c047115b2ae1c77ad"
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            return data["results"][0]["id"]
        else:
            print(f"⚠️ No TMDB results found for: {movie_title}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching movie ID for '{movie_title}':", e)
        return None


# -----------------------------
# 🔹 Fetch Poster (With Retry, Validation & Cache)
# -----------------------------
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id, retries=3):
    """
    Fetch movie poster URL from TMDB API.
    Retries failed requests and validates URLs.
    Always returns a valid image (poster or placeholder).
    """
    api_key = "a094ba6df7e5851c047115b2ae1c77ad"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            poster_path = data.get('poster_path')
            if poster_path:
                full_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                if validate_image_url(full_url):
                    return full_url
                else:
                    print(f"⚠️ Poster not found on TMDB CDN for ID {movie_id}")
            else:
                print(f"⚠️ No poster_path for movie ID {movie_id}")

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching poster (attempt {attempt+1}/{retries}): {e}")
            time.sleep(1)

    # 🖼️ Return fallback if all attempts fail
    return "https://via.placeholder.com/500x750?text=Poster+Unavailable"


# -----------------------------
# 🔹 Recommend Movies (Cached)
# -----------------------------
@st.cache_data(show_spinner=False)
def recommend(movie):
    """
    Recommend top 5 similar movies.
    """
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        movie_title = movies.iloc[i[0]].title
        movie_id = movies.iloc[i[0]].get("id", None)

        # Fallback: if ID missing in dataset, fetch dynamically
        if not movie_id:
            movie_id = get_movie_id(movie_title)

        poster_url = fetch_poster(movie_id) if movie_id else "https://via.placeholder.com/500x750?text=No+ID+Found"
        recommended_movie_names.append(movie_title)
        recommended_movie_posters.append(poster_url)
        time.sleep(0.2)  # small delay to avoid rate limit

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
        names, posters = recommend(selected_movie)
        cols = st.columns(5)
        for col, name, poster in zip(cols, names, posters):
            with col:
                st.image(poster, width=150)
                st.text(name)


# -----------------------------
# 🔹 Optional: Clear Cache Button
# -----------------------------
if st.button("♻️ Clear Cache"):
    st.cache_data.clear()
    st.success("Cache cleared successfully!")
