import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap

@st.cache_data
def load_data():
    df = pd.read_csv("Completed_Sentiments_CLEAN.csv")

    def combine_genders(g1, g2):
        g_map = {"m": "Male", "f": "Female", "u": "Unknown", "0": "", "nan": "", "": "", None: ""}
        g1_clean = g_map.get(str(g1).strip().lower(), "Unknown")
        g2_clean = g_map.get(str(g2).strip().lower(), "Unknown")
        genders = sorted(set(filter(None, [g1_clean, g2_clean])))
        return " + ".join(genders) if genders else "Unknown"

    df["author_gender_combo"] = df.apply(lambda row: combine_genders(row.get("gender", ""), row.get("2nd Author - Gen", "")), axis=1)

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

    st.title("A Sentimental City: Mapping How Literature Felt About Edinburgh")
    st.markdown("Explore how locations in Edinburgh were described in literature using sentiment analysis. Filter by year, genre, sentiment, and author gender.")

    st.sidebar.header("Filter Options")

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
                if df.empty:
                    st.info("Data Gaps: Some years have little or no literary data shown. This may be due to publication trends, curatorial decisions, availability of digital texts, our sentiment analysis stage, or other reasons that we invite you to consider. This absence is part of the data story too.")

    st.sidebar.markdown("_Note: this filter is based on the year of **publication**, not the year in which a story is set._")

    genre_options = pd.unique(df[["Genre 1", "Genre 2"]].values.ravel("K")) if "Genre 1" in df.columns else []
    selected_genres = st.sidebar.multiselect("Select Genre(s)", [g for g in genre_options if pd.notna(g)])

    if "genre_type" in df.columns:
        selected_type = st.sidebar.selectbox("Fiction or Non-Fiction", ["All", "Fiction", "Non-Fiction"])
        if selected_type != "All":
            df = df[df["genre_type"] == selected_type]

    gender_options = sorted(df["author_gender_combo"].dropna().unique())
    selected_gender = st.sidebar.selectbox("Author Gender Combination", ["All"] + gender_options)
    if selected_gender != "All":
        df = df[df["author_gender_combo"] == selected_gender]

    sentiment_options = df["final_sentiment"].unique().tolist() if "final_sentiment" in df.columns else []
    selected_sentiments = st.sidebar.multiselect("Select Sentiment(s)", sentiment_options, default=sentiment_options)
    if "final_sentiment" in df.columns:
        df = df[df["final_sentiment"].isin(selected_sentiments)]

    if selected_genres:
        df = df[df["Genre 1"].isin(selected_genres) | df["Genre 2"].isin(selected_genres)]

    show_heatmap = st.sidebar.checkbox("Show Heatmap Instead of Markers")

    m = folium.Map(location=[55.9533, -3.1883], zoom_start=12)

    if show_heatmap:
        heat_data = df[["lat", "lon", "final_score"]].dropna().values.tolist()
        HeatMap(heat_data, radius=10, blur=15).add_to(m)
    else:
        for _, row in df.iterrows():
            if pd.notnull(row.get("lat")) and pd.notnull(row.get("lon")):
                popup_html = (
                    f"<b>Sentence:</b> {row.get('text_sentence', '')}<br>"
                    f"<b>Book:</b> {row.get('title', 'Unknown')}<br>"
                    f"<b>Author:</b> {row.get('forename', '')} {row.get('surname', '')}<br>"
                    f"<b>Sentiment:</b> {row.get('final_sentiment', 'N/A')}<br>"
                    f"<b>Year:</b> {row.get('pubyear', 'N/A')}"
                )
                color = {"Positive": "green", "Neutral": "purple", "Negative": "red"}.get(row.get("final_sentiment", ""), "gray")
                folium.CircleMarker(
                    location=(row["lat"], row["lon"]),
                    radius=5,
                    color=color,
                    fill=True,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)

    st_folium(m, width=700, height=500)

    with st.expander("ℹ️ About This Map"):
        st.markdown("**How Sentiment Was Measured**  
"
                    "Our sentiment analysis identifies whether sentences expressed a **positive**, **negative**, or **neutral** feeling **about the mentioned place**, not just the overall tone.")

        st.markdown("**About the Data**  
"
                    "This map uses a subset of the LitLong Edinburgh dataset. All literary locations were tagged and categorised by curators. "
                    "This means genre, inclusion, and classification decisions were made by individuals. "
                    "Further filtering, specific to this project, was applied to analyse sentiment. "
                    "This is therefore not a complete map of the original dataset. Users are encouraged to reflect on what may be missing and why.")

if __name__ == "__main__":
    main()
