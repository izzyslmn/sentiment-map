# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    df = pd.read_csv("Completed_Sentiments_CLEAN.csv")

    # Create author gender combination
    def combine_genders(g1, g2):
        genders = sorted(filter(None, [str(g1).strip().lower(), str(g2).strip().lower()]))
        if not genders:
            return "Unknown"
        if len(genders) == 1:
            return genders[0].capitalize()
        combo = " + ".join(g.capitalize() if g != "unknown" else "Unknown" for g in genders)
        return combo

    df["author_gender_combo"] = df.apply(lambda row: combine_genders(row.get("author1_gender", ""), row.get("author2_gender", "")), axis=1)

    # Derive fiction/non-fiction category
    if "Genre 1" in df.columns:
        def infer_genre_type(genre):
            if pd.isna(genre):
                return "Unknown"
            genre_lower = genre.lower()
            if "fiction" in genre_lower or genre_lower in ["novel", "fantasy", "drama"]:
                return "Fiction"
            elif "non-fiction" in genre_lower or genre_lower in ["memoir", "biography", "essay"]:
                return "Non-Fiction"
            return "Unknown"
        df["genre_type"] = df["Genre 1"].apply(infer_genre_type)

    return df

def main():
    df = load_data()

    st.title("🧭 A Sentimental City: Mapping How Literature Felt About Edinburgh")
    st.markdown("This tool lets you explore how different places in Edinburgh were emotionally represented in literary texts. Use the filters to discover how sentiment changes across genre, time, gender, and geography.")

    st.sidebar.header("Filter Options")

    # Year filtering
    if "pubyear" in df.columns:
        valid_years = df["pubyear"].dropna().astype(int)
        if not valid_years.empty:
            min_year, max_year = valid_years.min(), valid_years.max()
            if min_year == max_year:
                st.sidebar.markdown(f"All data from year: {min_year}")
                df = df[df["pubyear"] == min_year]
            else:
                year_range = st.sidebar.slider("Publication Year Range", min_year, max_year, (min_year, max_year))
                df = df[(df["pubyear"] >= year_range[0]) & (df["pubyear"] <= year_range[1])]
        else:
            st.sidebar.warning("No valid year data available.")
    else:
        st.sidebar.warning("'pubyear' column missing. Year filter skipped.")

    # Genre filtering
    genre_options = pd.unique(df[["Genre 1", "Genre 2"]].values.ravel("K")) if "Genre 1" in df.columns else []
    selected_genres = st.sidebar.multiselect("Select Genre(s)", [g for g in genre_options if pd.notna(g)])

    # Fiction/Non-Fiction filter
    if "genre_type" in df.columns:
        selected_type = st.sidebar.selectbox("Fiction or Non-Fiction", ["All", "Fiction", "Non-Fiction"])
        if selected_type != "All":
            df = df[df["genre_type"] == selected_type]

    # Author Gender filter
    gender_options = sorted(df["author_gender_combo"].dropna().unique())
    selected_gender = st.sidebar.selectbox("Author Gender Combination", ["All"] + gender_options)
    if selected_gender != "All":
        df = df[df["author_gender_combo"] == selected_gender]

    # Sentiment filtering
    sentiment_options = df["final_sentiment"].unique().tolist() if "final_sentiment" in df.columns else []
    selected_sentiments = st.sidebar.multiselect("Select Sentiment(s)", sentiment_options, default=sentiment_options)
    if "final_sentiment" in df.columns:
        df = df[df["final_sentiment"].isin(selected_sentiments)]

    # Apply genre filters
    if selected_genres and "Genre 1" in df.columns and "Genre 2" in df.columns:
        df = df[df["Genre 1"].isin(selected_genres) | df["Genre 2"].isin(selected_genres)]

    # Generate map
    m = folium.Map(location=[55.9533, -3.1883], zoom_start=12)

    for _, row in df.iterrows():
        if pd.notnull(row.get("lat")) and pd.notnull(row.get("lon")):
            tooltip = (
                f"<b>Sentence:</b> {row.get('text', '')}<br>"
                f"<b>Book:</b> {row.get('title', 'Unknown')}<br>"
                f"<b>Author:</b> {row.get('author1', 'Unknown')}<br>"
                f"<b>Sentiment:</b> {row.get('final_sentiment', 'N/A')}<br>"
                f"<b>Year:</b> {row.get('pubyear', 'N/A')}"
            )
            color = {"Positive": "green", "Neutral": "lightgray", "Negative": "red"}.get(row.get("final_sentiment", ""), "gray")
            folium.CircleMarker(
                location=(row["lat"], row["lon"]),
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.7,
                tooltip=tooltip
            ).add_to(m)

    st_folium(m, width=700, height=500)
    st.markdown("---")
    st.markdown("Developed for exploring sentiment and emotion in Edinburgh's literary geography.")

if __name__ == "__main__":
    main()
