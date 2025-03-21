# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Load the dataset
@st.cache_data
def load_data():
    df = pd.read_csv("Completed Sentiments(Sheet 1).csv")
    df["pubyear"] = pd.to_numeric(df["pubyear"], errors="coerce")
    df = df.dropna(subset=["pubyear"])
    df["pubyear"] = df["pubyear"].astype(int)
    return df

df = load_data()

st.title("📍 Interactive Map of Sentiment by Location")

# Make sure there's valid year data
if df.empty or df["pubyear"].isnull().all():
    st.error("No valid publication year data available.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filter Options")

# Year filter (safe fallback)
min_year = df["pubyear"].min()
max_year = df["pubyear"].max()
if min_year == max_year:
    year_range = (min_year, max_year)
    st.sidebar.markdown(f"All data from year: {min_year}")
else:
    year_range = st.sidebar.slider("Publication Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))

# Genre filter
genre_options = pd.unique(df[["Genre 1", "Genre 2"]].values.ravel("K"))
selected_genres = st.sidebar.multiselect("Select Genre(s)", options=[g for g in genre_options if pd.notna(g)])

# Sentiment filter
sentiment_options = df["final_sentiment"].unique().tolist()
selected_sentiments = st.sidebar.multiselect("Select Sentiment(s)", options=sentiment_options, default=sentiment_options)

# Filter dataset
filtered_df = df[
    (df["pubyear"] >= year_range[0]) &
    (df["pubyear"] <= year_range[1]) &
    (df["final_sentiment"].isin(selected_sentiments))
]

if selected_genres:
    filtered_df = filtered_df[
        filtered_df["Genre 1"].isin(selected_genres) | filtered_df["Genre 2"].isin(selected_genres)
    ]

# Create folium map
m = folium.Map(location=[55.9533, -3.1883], zoom_start=12)

for _, row in filtered_df.iterrows():
    tooltip = f"<b>{row['text']}</b><br>Sentiment: {row['final_sentiment']}<br>Score: {row['sentiment_score']}<br>Genre: {row['Genre 1']}, {row['Genre 2']}<br>Year: {row['pubyear']}"
    color = {
        "Positive": "green",
        "Neutral": "blue",
        "Negative": "red"
    }.get(row["final_sentiment"], "gray")

    folium.CircleMarker(
        location=(row["lat"], row["lon"]),
        radius=5,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(tooltip, max_width=300)
    ).add_to(m)

# Display map
st_folium(m, width=700, height=500)

st.markdown("---")
st.markdown("Developed for visualising sentiment in Edinburgh locations.")
