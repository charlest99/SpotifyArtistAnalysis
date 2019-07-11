import spotipy
import spotipy.util as util
import os
from json.decoder import JSONDecodeError
import pandas as pd

# localhost for personal use / development
redirect_url = 'https://localhost:8080'
#get token
scope = 'user-library-read'

#DEFINE USER AND KEYS HERE
user_keys = {'user':'', 'client_id':'', 'client_secret':''}

#CHOOSE ARTIST URI HERE
artistUri = ''

birdy_uri = 'spotify:artist:' + artistUri

#Creates an instance of the spotify api with your user authentication
def createAPIConnection():
	try:
	    token = util.prompt_for_user_token(user_keys['user'], scope, 
	                                       client_id=user_keys['client_id'], 
	                                       client_secret=user_keys['client_secret'], 
	                                       redirect_uri=redirect_url)
	    
	except (AttributeError, JSONDecodeError):
	    os.remove(f".cache-{user_keys['user']}")
	    token = util.prompt_for_user_token(user_keys['user'], scope, 
	                                       client_id=user_keys['client_id'], 
	                                       client_secret=user_keys['client_secret'], 
	                                       redirect_uri=redirect_url)

	sp = spotipy.Spotify(auth=token)
	return sp

#returns a list of albums and ids for a given artist uri
def findAlbumsForArtist(sp):
	results = sp.artist_albums(birdy_uri, album_type='album')
	albums = results['items']
	while results['next']:
	    results = sp.next(results)
	    albums.extend(results['items'])
	return albums

#returns a dataframe with all audio features of all tracks on each album
def getTrackInfo(albums, sp):
	trackids = []
	trackNames = []
  
  #finds the popularity by song
	popularity = []
	for album in albums:
	    tracksres = sp.album_tracks(album['id'])
	    tracklist = tracksres['items']
	    for track in tracklist:
	        trackids.append(track['id'])
	        trackNames.append(track['name'])
	        pop = sp.track(track['uri'])
	        popularity.append(pop['popularity'])

  #finds the audio features for each track per album
	dance = []
	energy = []
	loud = []
	speech = []
	acoustic = []
	instrument = []
	live = []
	valence = []
	for trackid in trackids:
	    response = sp.audio_features(trackid)
	    r = response[0]
	    dance.append(r['danceability'])
	    energy.append(r['energy'])
	    loud.append(r['loudness'])
	    speech.append(r['speechiness'])
	    acoustic.append(r['acousticness'])
	    instrument.append(r['instrumentalness'])
	    live.append(r['liveness'])
	    valence.append(r['valence'])

  #creates a dataframe from the features found
	songdata_df = pd.DataFrame({'name':trackNames,'id': trackids, 'dance': dance, 'energy': energy, 
	                            'loud': loud, 'speech': speech, 
	                            'acoustic': acoustic, 'instrument': instrument, 
	                            'live': live, 'valence': valence, 'popularity':popularity})

  #finds the last feature for the data, whether a track is top 10 for an artist
	songdata_df['top10ForArtist'] = 0
	klTopTracks = sp.artist_top_tracks(birdy_uri)
	topIds = []
	for track in klTopTracks['tracks']:
	    topIds.append(track['id'])
	for songId in topIds:
	    songdata_df.loc[songdata_df['id'] == songId,'top10ForArtist'] = 1
	return songdata_df

#cleans the dataframe to get it into final form
def cleanSongDf(songdata_df):
	songdata_df = songdata_df.sort_values(['name', 'popularity'])
	songdata_df = songdata_df.drop_duplicates(subset='name', keep='last').reset_index(drop=True)
	return songdata_df

#returns the dataframe of song info
#Use this function to get the dataframe in one call
def getArtistTrackInfo():
	sp = createAPIConnection()
	albums = findAlbumsForArtist(sp)
	songdata = getTrackInfo(albums, sp)
	df = cleanSongDf(songdata)
	return df
