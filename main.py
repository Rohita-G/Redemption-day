import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load data
races = pd.read_csv('f1-data/races.csv')
laps = pd.read_csv('f1-data/lap_times.csv')
drivers = pd.read_csv('f1-data/drivers.csv')

# Filter 2018 Monaco GP
monaco_race = races[(races['year'] == 2018) & (races['name'] == 'Monaco Grand Prix')]
race_id = monaco_race['raceId'].values[0]
monaco_laps = laps[laps['raceId'] == race_id]

# Merge drivers info
monaco_laps = monaco_laps.merge(drivers[['driverId', 'forename', 'surname']], on='driverId')
monaco_laps['driverName'] = monaco_laps['forename'] + ' ' + monaco_laps['surname']

# Prepare lap time in seconds
monaco_laps['lapTimeSeconds'] = monaco_laps['milliseconds'] / 1000

# Sort data for consistent plotting
monaco_laps = monaco_laps.sort_values(['driverName', 'lap'])

# Create subplot figure: 2 rows, 1 col
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    subplot_titles=("Lap Times by Driver (seconds)", "Positions by Driver"),
    vertical_spacing=0.15
)

drivers_list = monaco_laps['driverName'].unique()

# Add lap time traces (row 1)
for driver in drivers_list:
    df_driver = monaco_laps[monaco_laps['driverName'] == driver]
    fig.add_trace(
        go.Scatter(
            x=df_driver['lap'],
            y=df_driver['lapTimeSeconds'],
            mode='lines+markers',
            name=driver,
            legendgroup=driver,
            hovertemplate='Driver: %{text}<br>Lap: %{x}<br>Lap Time: %{y:.3f}s',
            text=[driver]*len(df_driver)
        ),
        row=1, col=1
    )

# Add position traces (row 2)
for driver in drivers_list:
    df_driver = monaco_laps[monaco_laps['driverName'] == driver]
    fig.add_trace(
        go.Scatter(
            x=df_driver['lap'],
            y=df_driver['position'],
            mode='lines+markers',
            name=driver,
            legendgroup=driver,
            showlegend=False,  # legend only on first plot
            hovertemplate='Driver: %{text}<br>Lap: %{x}<br>Position: %{y}',
            text=[driver]*len(df_driver)
        ),
        row=2, col=1
    )

# Invert y-axis on position plot so 1 is on top
fig.update_yaxes(autorange='reversed', row=2, col=1, dtick=1)

# Set axis labels
fig.update_xaxes(title_text="Lap Number", row=2, col=1)
fig.update_yaxes(title_text="Lap Time (seconds)", row=1, col=1)
fig.update_yaxes(title_text="Position", row=2, col=1)

# Layout adjustments
fig.update_layout(
    height=800,
    title_text="2018 Monaco GP: Lap Times & Positions",
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

fig.show()
