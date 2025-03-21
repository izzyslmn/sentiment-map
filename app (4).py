# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Load the dataset
@st.cache_data
def load_data():
    df = pd.read_csv("Completed Sentiments(Sheet 1).csv")
    if "pubyear" in df.columns:
        df["pubyear"] = pd.to_numeric(df["pubyear"], errors="coerce")
        df = df.dropna(subset=["pubyear"])
        df["pubyear"] = df["pubyear"].astype(int)
    return df

df = load_data()

st.title("📍 Interactive Map of Sentiment by Location")

# Sidebar filters
st.sidebar.header("Filter Options")

# Safe defaults
year_range = (None, None)

# ✅ Safe year filtering logic
if "pubyear" in df.columns and not df["pubyear"].isnull().all():
    try:
        min_year = int(df["pubyear"].min())
        max_year = int(df["pubyear"].max())

        if min_year == max_year:
            st.sidebar.markdown(f"All data from year: {min_year}")
            df = df[df["pubyear"] == min_year]
        else:
            year_range = st.sidebar.slider(
                "Publication Year Range",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
            )
            df = df[(df["pubyear"] >= year_range[0]) & (df["pubyear"] <= year_range[1])]
    except Exception as e:
        st.sidebar.warning("Year filter disabled due to invalid data.")

else:
    st.sidebar.markdown("⚠️ No valid year data found. Year filter disabled.")

# Genre filter
genre_options = pd.unique(df[["Genre 1", "Genre 2"]].values.ravel("K")) if "Genre 1" in df.columns else []
selected_genres = st.sidebar.multiselect("Select Genre(s)", options=[g for g in genre_options if pd.notna(g)])

# Sentiment filter
sentiment_options = df["final_sentiment"].unique().tolist() if "final_sentiment" in df.columns else []
selected_sentiments = st.sidebar.multiselect("Select Sentiment(s)", options=sentiment_options, default=sentiment_options)

# Filter by sentiment and genre
if "final_sentiment" in df.columns:
    df = df[df["final_sentiment"].isin(selected_sentiments)]

if selected_genres and "Genre 1" in df.columns and "Genre 2" in df.columns:
    df = df[df["Genre 1"].isin(selected_genres) | df["Genre 2"].isin(selected_genres)]

# Create folium map
m = folium.Map(location=[55.9533, -3.1883], zoom_start=12)

for _, row in df.iterrows():
    if pd.notnull(row["lat"]) and pd.notnull(row["lon"]):
        tooltip = f"<b>{row['text']}</b><br>Sentiment: {row.get('final_sentiment', 'N/A')}<br>Score: {row.get('sentiment_score', 'N/A')}<br>Genre: {row.get('Genre 1', '')}, {row.get('Genre 2', '')}<br>Year: {row.get('pubyear', 'N/A')}"
        color = {
            "Positive": "green",
            "Neutral": "blue",
            "Negative": "red"
        }.get(row.get("final_sentiment", ""), "gray")

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
