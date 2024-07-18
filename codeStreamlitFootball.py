import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

#set page configuration
st.set_page_config(page_title="International Football Results Dashboard", layout="wide")

#custom CSS for styling
st.markdown("""
<style>
    .custom-metric {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
        text-align: center;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .custom-metric h3 {
        margin-bottom: 5px;
        color: #31333F;
        font-size: 14px;
    }
    .custom-metric p {
        font-size: 22px;
        font-weight: bold;
        color: #0068c9;
        margin: 0;
    }
    .made-by {
        font-size: 18px;
        color: #888;
        font-style: italic;
        margin-top: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# load and preprocess the data
@st.cache_data
def load_data():
    df = pd.read_csv("all_matches.csv")
    df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True)
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# dashboard title and author
st.title("International Football Results Dashboard")
st.markdown('<div class="made-by">Made by Pranav Verma</div>', unsafe_allow_html=True)

# sidebar for filtering
st.sidebar.header("Filters")
year_range = st.sidebar.slider("Select Year Range", min_value=df['date'].dt.year.min(), max_value=df['date'].dt.year.max(), value=(df['date'].dt.year.min(), df['date'].dt.year.max()))
selected_countries = st.sidebar.multiselect(
    "Select Countries", 
    options=sorted(df['country'].unique()), 
    default=['India', 'Brazil', 'Spain', 'Argentina']
)


#filter the dataframe
filtered_df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1]) & (df['country'].isin(selected_countries))]

#kpi section
st.header("Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

total_matches = filtered_df.shape[0]
col1.markdown(
    f"""
    <div class="custom-metric">
        <h3>Total Matches</h3>
        <p>{total_matches}</p>
    </div>
    """,
    unsafe_allow_html=True
)

avg_home_score = filtered_df['home_score'].mean()
col2.markdown(
    f"""
    <div class="custom-metric">
        <h3>Avg Home Score</h3>
        <p>{avg_home_score:.2f}</p>
    </div>
    """,
    unsafe_allow_html=True
)

avg_away_score = filtered_df['away_score'].mean()
col3.markdown(
    f"""
    <div class="custom-metric">
        <h3>Avg Away Score</h3>
        <p>{avg_away_score:.2f}</p>
    </div>
    """,
    unsafe_allow_html=True
)

total_goals = filtered_df['home_score'].sum() + filtered_df['away_score'].sum()
col4.markdown(
    f"""
    <div class="custom-metric">
        <h3>Total Goals</h3>
        <p>{total_goals}</p>
    </div>
    """,
    unsafe_allow_html=True
)

avg_goals_per_match = total_goals / total_matches
col5.markdown(
    f"""
    <div class="custom-metric">
        <h3>Avg Goals per Match</h3>
        <p>{avg_goals_per_match:.2f}</p>
    </div>
    """,
    unsafe_allow_html=True
)

#visualizations
st.header("Visualizations")

#create two columns for line chart and stacked bar chart
col1, col2 = st.columns(2)

#matches per year
with col1:
    matches_per_year = filtered_df.groupby(filtered_df['date'].dt.year).size().reset_index(name='count')
    fig_matches = px.line(matches_per_year, x='date', y='count', title="Matches per Year")
    fig_matches.update_layout(
        xaxis_title="Year",
        yaxis_title="Number of Matches",
        legend_title="Legend",
        font=dict(size=12)
    )
    fig_matches.add_scatter(x=matches_per_year['date'], y=matches_per_year['count'], mode='lines', name='Matches')
    st.plotly_chart(fig_matches, use_container_width=True)

# tournament distribution with stacked bar chart
with col2:
    tournament_counts = filtered_df.groupby('tournament').agg({
        'home_score': 'sum',
        'away_score': 'sum'
    }).reset_index()

    tournament_counts['total_score'] = tournament_counts['home_score'] + tournament_counts['away_score']
    tournament_counts = tournament_counts.sort_values('total_score', ascending=True)

    fig_tournaments = go.Figure(data=[
        go.Bar(name='Home Scores', y=tournament_counts['tournament'], x=tournament_counts['home_score'], orientation='h'),
        go.Bar(name='Away Scores', y=tournament_counts['tournament'], x=tournament_counts['away_score'], orientation='h')
    ])

    fig_tournaments.update_layout(
        barmode='stack',
        title="Tournament Distribution - Home vs Away Scores",
        yaxis_title="Tournament",
        xaxis_title="Total Goals",
        legend_title="Score Type"
    )
    st.plotly_chart(fig_tournaments, use_container_width=True)

#top 10 highest-scoring matches (Heatmap)
highest_scoring = filtered_df.copy()
highest_scoring['total_score'] = highest_scoring['home_score'] + highest_scoring['away_score']
highest_scoring = highest_scoring.sort_values('total_score', ascending=False).head(10)
highest_scoring['match'] = highest_scoring['home_team'] + ' vs ' + highest_scoring['away_team']

fig_high_scoring = px.imshow(
    highest_scoring[['home_score', 'away_score']].T,
    x=highest_scoring['match'],
    y=['Home Score', 'Away Score'],
    color_continuous_scale='Viridis',
    title="Top 10 Highest Scoring Matches"
)
fig_high_scoring.update_traces(
    hovertemplate="Match: %{x}<br>Type: %{y}<br>Score: %{z}<extra></extra>"
)
fig_high_scoring.update_layout(xaxis_title="Match", yaxis_title="Score Type")
st.plotly_chart(fig_high_scoring, use_container_width=True)

#create two columns for pie charts
col1, col2 = st.columns(2)

#win VS loss pie chart (corrected)
with col1:
    wins = 0
    losses = 0
    draws = 0

    for _, row in filtered_df.iterrows():
        if row['home_team'] in selected_countries:
            if row['home_score'] > row['away_score']:
                wins += 1
            elif row['home_score'] < row['away_score']:
                losses += 1
            else:
                draws += 1
        if row['away_team'] in selected_countries:
            if row['away_score'] > row['home_score']:
                wins += 1
            elif row['away_score'] < row['home_score']:
                losses += 1
            else:
                draws += 1

    fig_win_loss = go.Figure(data=[go.Pie(labels=['Wins', 'Losses', 'Draws'], 
                                          values=[wins, losses, draws],
                                          hole=.3,
                                          marker_colors=['#00CC96', '#EF553B', '#636EFA'])])
    fig_win_loss.update_layout(title="Win vs Loss Distribution for Selected Countries")
    st.plotly_chart(fig_win_loss, use_container_width=True)

#home vs away wins
with col2:
    home_wins = filtered_df[filtered_df['home_score'] > filtered_df['away_score']].shape[0]
    away_wins = filtered_df[filtered_df['home_score'] < filtered_df['away_score']].shape[0]
    draws = filtered_df[filtered_df['home_score'] == filtered_df['away_score']].shape[0]

    fig_wins = go.Figure(data=[go.Pie(labels=['Home Wins', 'Away Wins', 'Draws'], 
                                      values=[home_wins, away_wins, draws],
                                      hole=.3)])
    fig_wins.update_layout(title="Home vs Away Wins")
    st.plotly_chart(fig_wins, use_container_width=True)

#world map and Filtered Dataset side by side
st.header("Selected Countries and Filtered Dataset")
col1, col2 = st.columns([1, 1])

with col1:
    world = px.data.gapminder().query("year==2007")
    fig_world = px.choropleth(world, locations="iso_alpha",
                              color=[1 if country in selected_countries else 0 for country in world['country']],
                              hover_name="country",
                              color_continuous_scale=px.colors.sequential.Viridis,
                              projection="natural earth")
    fig_world.update_layout(coloraxis_showscale=False, height=400, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_world, use_container_width=True)

with col2:
    st.dataframe(filtered_df.style.format({
        'date': lambda x: x.strftime('%Y-%m-%d'),
        'home_score': '{:.0f}',
        'away_score': '{:.0f}'
    }), height=400)

# footer 
st.markdown("---")
st.markdown("Data source: International football results from 1872 to 2023")