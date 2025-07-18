import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Load data once
@st.cache_data
def load_data():
    races = pd.read_csv('f1-data/races.csv')
    laps = pd.read_csv('f1-data/lap_times.csv')
    drivers = pd.read_csv('f1-data/drivers.csv')
    constructors = pd.read_csv('f1-data/constructors.csv')
    results = pd.read_csv('f1-data/results.csv')
    return races, laps, drivers, constructors, results

races, laps, drivers, constructors, results = load_data()

# Get raceId for 2018 Monaco GP
monaco_race = races[(races['year'] == 2018) & (races['name'] == 'Monaco Grand Prix')]
race_id = monaco_race['raceId'].values[0]

# Filter lap times for Monaco 2018
monaco_laps = laps[laps['raceId'] == race_id]

# Merge driver names
monaco_laps = monaco_laps.merge(drivers[['driverId', 'forename', 'surname']], on='driverId')
monaco_laps['driverName'] = monaco_laps['forename'] + ' ' + monaco_laps['surname']

# Prepare lap time in seconds
monaco_laps['lapTimeSeconds'] = monaco_laps['milliseconds'] / 1000

# Get race results to map driver to constructor (team) and final position
race_results = results[(results['raceId'] == race_id)]

# Merge driver and constructor names
race_results = race_results.merge(drivers[['driverId', 'forename', 'surname']], on='driverId')
race_results = race_results.merge(constructors[['constructorId', 'name']], on='constructorId')
race_results['driverName'] = race_results['forename'] + ' ' + race_results['surname']
race_results.rename(columns={'name': 'teamName'}, inplace=True)

# Map teams to colors (sample palette, can customize)
team_colors = {
    'Mercedes': '#00D2BE',
    'Ferrari': '#DC0000',
    'Red Bull': '#1E41FF',
    'Renault': '#FFF500',
    'Haas F1 Team': '#BD9E57',
    'Force India': '#F596C8',
    'Sauber': '#006EFF',
    'McLaren': '#FF8700',
    'Toro Rosso': '#469BFF',
    'Williams': '#37BEDD',
    'Toro Rosso Honda': '#469BFF',
    'Alfa Romeo': '#900000',
    # Add more teams/colors as needed
}

# Merge team colors to laps and results
monaco_laps = monaco_laps.merge(race_results[['driverId', 'teamName']], on='driverId')
monaco_laps['teamColor'] = monaco_laps['teamName'].map(team_colors).fillna('#888888')  # fallback gray

race_results['teamColor'] = race_results['teamName'].map(team_colors).fillna('#888888')

# Sort laps for consistent plotting
monaco_laps = monaco_laps.sort_values(['driverName', 'lap'])

st.title("🏎️ 2018 Monaco GP — Lap Times & Positions Visualizer")

# Driver selection widget
all_drivers = monaco_laps['driverName'].unique()
selected_drivers = st.multiselect(
    "Select drivers to display",
    options=all_drivers,
    default=all_drivers[:5],
)

filtered_data = monaco_laps[monaco_laps['driverName'].isin(selected_drivers)]
filtered_results = race_results[race_results['driverName'].isin(selected_drivers)]

if filtered_data.empty:
    st.warning("Please select at least one driver.")
else:
    # Create subplot figure with 2 rows
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("Lap Times by Driver (seconds)", "Positions by Driver"),
        vertical_spacing=0.15
    )

    # Add lap time traces with team colors
    for driver in selected_drivers:
        df_driver = filtered_data[filtered_data['driverName'] == driver]
        team_color = df_driver['teamColor'].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=df_driver['lap'],
                y=df_driver['lapTimeSeconds'],
                mode='lines+markers',
                name=driver,
                legendgroup=driver,
                line=dict(color=team_color),
                hovertemplate='Driver: %{text}<br>Lap: %{x}<br>Lap Time: %{y:.3f}s',
                text=[driver]*len(df_driver),
            ),
            row=1, col=1
        )

    # Add position traces with team colors
    for driver in selected_drivers:
        df_driver = filtered_data[filtered_data['driverName'] == driver]
        team_color = df_driver['teamColor'].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=df_driver['lap'],
                y=df_driver['position'],
                mode='lines+markers',
                name=driver,
                legendgroup=driver,
                showlegend=False,
                line=dict(color=team_color),
                hovertemplate='Driver: %{text}<br>Lap: %{x}<br>Position: %{y}',
                text=[driver]*len(df_driver),
            ),
            row=2, col=1
        )

    # Invert y-axis on position plot
    fig.update_yaxes(autorange='reversed', row=2, col=1, dtick=1)

    # Set axis labels
    fig.update_xaxes(title_text="Lap Number", row=2, col=1)
    fig.update_yaxes(title_text="Lap Time (seconds)", row=1, col=1)
    fig.update_yaxes(title_text="Position", row=2, col=1)

    fig.update_layout(
        height=850,
        hovermode="x unified",
        legend_title_text="Drivers",
        template="plotly_white",
        legend=dict(
            y=1,
            yanchor='top',
            font=dict(size=10),
            itemclick="toggleothers"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Parse fastestLapTime strings like "1:14.345" into seconds
    def parse_lap_time_str(lap_time_str):
        if pd.isna(lap_time_str):
            return None
        try:
            parts = lap_time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(lap_time_str)
        except:
            return None

    # Race summary stats panel
    st.markdown("### 🏁 Race Summary Stats")

    # Prepare summary table
    summary_df = filtered_results[['driverName', 'teamName', 'position', 'fastestLapTime']].copy()
    summary_df['Best Lap (s)'] = summary_df['fastestLapTime'].apply(parse_lap_time_str)
    summary_df.rename(columns={
        'position': 'Final Position',
        'teamName': 'Team',
        'driverName': 'Driver'
    }, inplace=True)
    summary_df = summary_df[['Driver', 'Team', 'Final Position', 'Best Lap (s)']]
    summary_df = summary_df.sort_values('Final Position')

    st.table(summary_df.style.format({"Best Lap (s)": "{:.3f}"}))


# --- Animated Race Progression Section ---
st.markdown("## 🏁 Animated Race Progression")

# Get max lap number for slider range
max_lap = filtered_data['lap'].max()

# Slider for lap selection
selected_lap = st.slider("Select Lap", min_value=1, max_value=max_lap, value=1)

# Filter data for selected lap and drivers
lap_data = filtered_data[filtered_data['lap'] == selected_lap]

# Sort by position for better visual order
lap_data = lap_data.sort_values('position')

# Create a bar chart showing driver positions (lower position is better, so invert y-axis)
fig = px.bar(
    lap_data,
    x='position',
    y='driverName',
    orientation='h',
    color='teamName',
    color_discrete_map=team_colors,
    title=f"Driver Positions at Lap {selected_lap}",
    labels={'position': 'Position', 'driverName': 'Driver'},
)

# Reverse x-axis so position 1 is on left
fig.update_layout(
    xaxis=dict(autorange='reversed', dtick=1),
    yaxis={'categoryorder':'total ascending'},
    height=600,
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)