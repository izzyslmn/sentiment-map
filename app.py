# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    return df

def main():
    df = load_data()

    st.title("A Sentimental City: Mapping How Literature Felt About Edinburgh")
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
            tooltip = f"<b>{row.get('text', '')}</b><br>Sentiment: {row.get('final_sentiment', 'N/A')}<br>Score: {row.get('sentiment_score', 'N/A')}<br>Genre: {row.get('Genre 1', '')}, {row.get('Genre 2', '')}<br>Year: {row.get('pubyear', 'N/A')}"
            color = {"Positive": "green", "Neutral": "blue", "Negative": "red"}.get(row.get("final_sentiment", ""), "gray")
            folium.CircleMarker(
                location=(row["lat"], row["lon"]),
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=folium.Popup(tooltip, max_width=300)
            ).add_to(m)

    st_folium(m, width=700, height=500)
    st.markdown("---")
    st.markdown("Developed for visualising sentiment in Edinburgh locations.")

if __name__ == "__main__":
    main()
