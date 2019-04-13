# Import dependencies
# spotipy is a library with methods that call the Spotify API

import glob, os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from sqlalchemy import create_engine
import pymysql
pymysql.install_as_MySQLdb()
%matplotlib inline
from matplotlib.ticker import StrMethodFormatter
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import client_id, secret, sql_pw

### EXTRACT AND ANALYZE DATA ###
#------------------------------#

# Establish connection to Spotify

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Create empty lists to store data from API calls

artist_name = []
track_name = []
track_id = []
popularity = []
artist_id = []

# Run a for loop to call the API multiple times for a list of tracks
# Starter code from a similar project:
# https://tgel0.github.io/blog/spotify-data-project-part-1-from-data-retrieval-to-first-insights/

# i represents each call of the Spotify search API, range is maximum results, step 50 represents 50 results per search
for i in range(0,1000,50):
    
    # Save results of each search as a variable. Limit search to 50 results, use offset to skip previous result of iteration
    track_results = sp.search(q='year:2019', type='track', limit=50,offset=i)
    
    # Loop through each result to find values for selected fields
    # Enumerate creates a tuple of each track result for iteration. Example: (0, J. Cole), (1, Ariana Grande), etc.
    for i, t in enumerate(track_results['tracks']['items']):
        artist_id.append(t['artists'][0]['id'])
        artist_name.append(t['artists'][0]['name'])
        track_name.append(t['name'])
        track_id.append(t['id'])
        popularity.append(t['popularity'])

# Create empty list for genre of each artist
genres = []

# Loop through artist id list, calling API for each artist id
for artist in range(0,1000):
    
    # sp.artist calls Spotify API using spotipy library to find artist
    artist_results = sp.artist(artist_id[artist])
    
    # Append list of genres from results to genres list
    genres.append(artist_results["genres"])

# Create empty lists to store audio feature values
danceability = []
energy = []
loudness = []
valence = []
tempo = []

# Loop through track id list to find audio features for each track
for track in range(0,1000):
    
    # Append selected values to corresponding lists
    try:
        audio_features = sp.audio_features(track_id[track])
        danceability.append(audio_features[0]["danceability"])
        energy.append(audio_features[0]["energy"])
        loudness.append(audio_features[0]["loudness"])
        valence.append(audio_features[0]["valence"])
        tempo.append(audio_features[0]["tempo"])
    
    # Error results if there are no features available. Use try/except to set value to 0 when there is an error
    except TypeError:
        danceability.append(0)
        energy.append(0)
        loudness.append(0)
        valence.append(0)
        tempo.append(0)

# Create datarframe from lists populated by loops
features_df = pd.DataFrame({"Track ID": track_id, "Artist Name": artist_name, "Track Name":track_name,
                            "Danceability":danceability, "Energy":energy, "Loudness":loudness,
                            "Valence":valence, "Tempo": tempo, "Popularity": popularity})

# Sort by Popularity score in descending order
features_df = features_df.sort_values(by=["Popularity"], ascending=False)

# Save to csv
features_df.to_csv("Resources/audio_features.csv", index=False)

# To remove tracks that have no audio features:

# Cast dataframe as list and remove columns that do not show audio feature values
col_list= list(features_df)
col_list.remove("Track ID")
col_list.remove("Artist Name")
col_list.remove("Track Name")
col_list.remove("Popularity")

# Use .loc to filter. Tracks with no audio features available were set to 0, so sum will be 0.
# This filters out tracks with no features available, but leaves in those that may have 0 for a certain value.
features_df.loc[features_df[col_list].sum(axis=1) > 0]

# Genres in artist results were stored in a list because artists can be classified to more than one genre
# Individual genres must be split to determine average popularity
# Create empty list for individuals genres split from lists
split_genres = []

# Splitting genres will result in multiple entries for each artist, track, and popularity score
# Must create empty lists to store split artists, tracks, and popularity
split_artists = []
split_track = []
split_popularity = []

# Loop through list of genre lists
for x in range(len(genres)):
    
    # Nested loop to append artist names, tracks, and popularity
    for y in genres[x]:
        split_genres.append(y)
        split_artists.append(artist_name[x])
        split_track.append(track_name[x])
        split_popularity.append(popularity[x]) 

# Create Dataframe for split genres
split_df = pd.DataFrame({"Artist Name": split_artists, "Track Name": split_track,
                         "Genre": split_genres, "Popularity Score": split_popularity})

# Remove genres with Popularity of 0
split_df = split_df.loc[split_df["Popularity Score"] >= 1]

# Save to csv
split_df.to_csv("Resources/split_genre.csv", index=False)

# Group by genre and visualize with .mean() to get average popularity
avg_pop_df = split_df.groupby("Genre").mean()

# Group by genre and visualize with .count() to find total occurences of each genre
count_pop_df = split_df.groupby("Genre").count()

# Drop non-numerical columns
count_pop_df = count_pop_df.drop(columns=["Artist Name", "Track Name"])

# Sort by Popularity in descending order and include only the top 20
count_pop_df = count_pop_df.sort_values(by=["Popularity Score"], ascending=False).nlargest(20, "Popularity Score")

# Merge avg and count Dataframes to show occurences of each genre and average popularity
genre_popularity_df = pd.merge(count_pop_df, avg_pop_df, on="Genre", how="left")

# Rename columns to specify which column corresponds to each measurement
genre_popularity_df = genre_popularity_df.rename(columns={"Popularity Score_x": "Genre Count",
                                                       "Popularity Score_y": "Average Popularity Score"})

# Sort by Average score in descending order
genre_popularity_df = genre_popularity_df.sort_values(by="Average Popularity Score")

# Set range for barh y axis
y = np.arange(0, len(genre_popularity_df))

# Assign ticks for y axis
ticks = genre_popularity_df.index

# Set width of bar for each genre to it's average popularity
width = genre_popularity_df["Average Popularity Score"]

# Create horizontal bar plot, setting bars to color of the Spotify logo
genre_plot = plt.barh(y, width, color="#1DB954")

# Set values and labels for y ticks
plt.yticks(ticks=y, labels=ticks)

# Set range and interval for x ticks
plt.xticks(ticks=np.arange(0, genre_popularity_df["Average Popularity Score"].max()+1, 5))

# Apply ticks to y axis
plt.tick_params(axis="y")

# Set x and y limits
plt.ylim(-0.8, 19.8)
plt.xlim(0, 76)

# Change figsize
plt.rcParams["figure.figsize"] = (20,12)

# Add title and axis labels
plt.title("Top 20 Most Popular Genres on Spotify")
plt.xlabel("Average Popularity Score")
plt.ylabel("Genre")

# Add vertical gridlines
plt.grid(axis="x")

# Increase font size
plt.rcParams.update({'font.size': 16})

# Save as png
plt.savefig("Images/top-20_genres.png")

# Use subplots to arrange plots for audio features into two rows of three columns with shared y axis
fig, ((ax1, ax2, ax3),(ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, sharey=True)

# Only measuring five features, but we cannot set an odd number of subplots, so we delete ax6
fig.delaxes(ax6)

# Set x values for each plot and y value shared by all plots
dance_x = features_df["Danceability"]
energy_x = features_df["Energy"]
loudness_x = features_df["Loudness"]
valence_x = features_df["Valence"]
tempo_x = features_df["Tempo"]
y = features_df["Popularity"]

# Create danceability plot
ax1.scatter(dance_x, y, color="#1DB954")
ax1.set_title("Popularity vs. Danceability")
ax1.set_xlabel("Danceability Rating")
ax1.grid()

# Create energy plot
ax2.scatter(energy_x, y, color="#1DB954")
ax2.set_title("Popularity vs. Energy")
ax2.set_xlabel("Energy Rating")
ax2.grid()

# Create valence plot
ax3.scatter(valence_x, y, color="#1DB954")
ax3.set_title("Popularity vs. Valence")
ax3.set_xlabel("Valence Rating")
ax3.grid()

# Create loudness plot
ax4.scatter(loudness_x, y, color="#1DB954")
ax4.set_title("Popularity vs. Loudness")
ax4.set_xlabel("Decibel Level (db)")
ax4.grid()

# Create tempo plot
ax5.scatter(tempo_x, y, color="#1DB954")
ax5.set_title("Popularity vs. Tempo")
ax5.set_xlabel("Beats per Minute (BPM)")
ax5.grid()

# Change figsize and font size for all plots
plt.rcParams["figure.figsize"] = (20,12)
plt.rcParams.update({'font.size': 16})

# Use tight layout to reduce overlap between labels for each plot
plt.tight_layout()

# Add master title for all plots
fig.suptitle("Popularity vs. Spotify Audio Features")

# Adjust suptitle so it does not overlap with top row titles
plt.subplots_adjust(top=0.90)
plt.savefig("Images/all_plots.png")

# Need to save individual plots for website, so each plot must be re-entered individually
plt.scatter(dance_x, y, color="#1DB954")
plt.title("Popularity vs. Danceability")
plt.xlabel("Danceability Rating")
plt.ylabel("Popularity Score")
plt.grid()
plt.rcParams["figure.figsize"] = (20,12)
plt.rcParams.update({'font.size': 16})
plt.savefig("Images/danceability.png")

plt.scatter(energy_x, y, color="#1DB954")
plt.title("Popularity vs. Energy")
plt.xlabel("Energy Rating")
plt.ylabel("Popularity Score")
plt.rcParams["figure.figsize"] = (20,12)
plt.rcParams.update({'font.size': 16})
plt.savefig("Images/energy.png")

plt.scatter(valence_x, y, color="#1DB954")
plt.title("Popularity vs. Valence")
plt.xlabel("Valence Rating")
plt.ylabel("Popularity Score")
plt.rcParams["figure.figsize"] = (20,12)
plt.rcParams.update({'font.size': 16})
plt.savefig("Images/valence.png")

plt.scatter(loudness_x, y, color="#1DB954")
plt.title("Popularity vs. Loudness")
plt.xlabel("Decibel Level (db)")
plt.ylabel("Popularity Score")
plt.grid()
plt.rcParams["figure.figsize"] = (20,12)
plt.rcParams.update({'font.size': 16})
plt.savefig("Images/loudness.png")

plt.scatter(tempo_x, y, color="#1DB954")
plt.title("Popularity vs. Tempo")
plt.xlabel("Beats per Minute (BPM)")
plt.ylabel("Popularity Score")
plt.grid()
plt.rcParams["figure.figsize"] = (20,12)
plt.rcParams.update({'font.size': 16})
plt.savefig("Images/tempo.png")

### PREPARE DATA TO LOAD INTO DATABASE ###
#----------------------------------------#

#Store CSV into a dataframe
csv_file = "Resources/Spotify_Data2019.csv"
tracks_data_df = pd.read_csv(csv_file)
tracks_data_df.head()

# We create a new Dataframe with selected columns to perform our analysis
new_track_data_df = tracks_data_df[['Track_ID', 'Artist_ID', 'Artist_Name', 'Track_Name', 'Danceability', 'Loudness', 'Valence', 
                                    'Tempo', 'Popularity_Score' ]].copy()

# Clean the data by dropping duplicates and setting the index
new_track_data_df.drop_duplicates("Track_ID", inplace=True)
new_track_data_df.set_index("Track_ID", inplace=True)

#Connect to local database
connection_string = "root:Cuba@1105@localhost/spotify_db"
engine = create_engine(f'mysql://{connection_string}')

#Check for tables
engine.table_names()

#Use pandas to load csv converted DataFrame into database

new_track_data_df.to_sql(name='tracks_details', con=engine, if_exists='append', index=True)

#Confirm data has been added by querying the tracks_det table
pd.read_sql_query('select * from tracks_details', con=engine).head()

### FURTHER ANALYSIS ###
#----------------------#

# create new dataframe df_top ordered consisting of the 100 most popular tracks
df_top = new_track_data_df.sort_values('Popularity_Score', ascending=False)

# show the first 10 results
df_top[['Artist_Name', 'Track_Name', 'Popularity_Score']].head(10)

#Set the index to Artist Name
df_top.set_index("Artist_Name", inplace=True)

# Spotify Top Tracks 
toptracks = df_top.groupby('Track_Name')['Popularity_Score'].mean().sort_values().tail(10)

#Create a Barh Chart to visualize Spotify top tracks for 2019
toptracks.plot(kind='barh')
ax = toptracks.plot(kind='barh', figsize=(8, 10), color='#1DB954', zorder=2, width=0.60)

  # Despine
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

  # Switch off ticks
ax.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")

  # Draw vertical axis lines
vals = ax.get_xticks()
for tick in vals:
    ax.axvline(x=tick, linestyle='dashed', alpha=0.4, color='black', zorder=1)

  # Set x-axis label
ax.set_xlabel("Popularity", labelpad=20, weight='bold', size=12)

  # Set y-axis label
ax.set_ylabel("Track", labelpad=20, weight='bold', size=12)
 # Set the tittle
ax.set_title("Top 10 Spotify Most Popular Tracks 2019", fontsize=18)
  # Format y-axis label
ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,g}'))
plt.savefig("Top_10_Tracks.png")

#Filter Tracks for Popularity > 90
top_artist = new_track_data_df.loc[new_track_data_df["Popularity_Score"] > 90]

# Group Tracks > 90 by Artist mean
top_artist_group = top_artist[['Artist_Name','Popularity_Score']].groupby('Artist_Name').mean().sort_values('Popularity_Score')

#Create a Barh Chart to visualize Artists for Top Tracks
ax = top_artist_group.plot(kind='barh', figsize=(8, 10), color='#1DB954', zorder=2, width=0.60)

  # Despine
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

  # Switch off ticks
ax.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")

  # Draw vertical axis lines
vals = ax.get_xticks()
for tick in vals:
    ax.axvline(x=tick, linestyle='dashed', alpha=0.4, color='black', zorder=1)

  # Set x-axis label
ax.set_xlabel("Popularity", labelpad=20, weight='bold', size=12)

  # Set y-axis label
ax.set_ylabel("Artist", labelpad=20, weight='bold', size=12)
 # Set the tittle
ax.set_title("Top Artists for Spotify Most Popular Tracks 2019", fontsize=18)
  # Format y-axis label
ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,g}'))
ax.get_legend().remove()
plt.savefig("Top_Artist_Tracks.png")