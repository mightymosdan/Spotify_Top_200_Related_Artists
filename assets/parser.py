import pandas as pd
import spotipy
import csv
from spotipy.oauth2 import SpotifyClientCredentials

def parseAllUniqueArtists(path: str) -> dict:
    """
    Parses all unique artists within a .csv file with artists as a column.

    Returns a dictionary of unique artists with '' as it's value.
    """
    data = pd.read_csv(path)
    # Get all unique entries
    artistList = []
    for artist in data.Artist:
        if artist not in artistList:
            artistList.append(artist)

    print(f'Number of unique artists(including features): {len(artistList)}')
    print("Filtering out features")
    # Filter out features
    artistDict = {}
    for artist in artistList:
        mainArtist = artist.split(',')[0]
        artistDict[mainArtist] = ""

    print(f'Number of unique artists after removing features: {len(artistDict.keys())}')

    artists = list(artistDict.keys())
    artists.sort()
    # for artist in artists:
        # print(artist)

    return artistDict

def getSpotifyArtistData(artist: str, sp: spotipy.Spotify) -> dict:
    """
    Searches Spotify for the artist passed in
    using the Spotify API.
    The top result(assumed to be the artist being searched for)
    will be artist whose data will be returned.

    Returns a dict containing the artist's data.
    """
    try:
        artistData = sp.search(q='artist:' + artist, type='artist')
        # Return the top result
        return artistData['artists']['items'][0]

    except BaseException:
        print("Usage show_related.py [artist-name]")

def getSpotifyArtistRelatedArtists(artist:str, sp: spotipy.Spotify) -> set:
    """
    Gets the list of related artists for the artist passed in.

    Returns a set of related artists.
    """

    artistData = getSpotifyArtistData(artist, sp)
    # Get URI for the artist. This will be used to get related artists.
    artistURI = artistData['uri']

    # Get related artists using the URI
    relatedArtists = sp.artist_related_artists(artistURI)
    relatedArtistsSet = set()
    for artist in relatedArtists['artists']:
        relatedArtistsSet.add(artist['name'])
        # print(f'Adding: {artist["name"]}')

    return relatedArtistsSet

def updateArtistDictWithRelatedArtists(artistDict: dict, sp: spotipy.Spotify) ->dict:
    """
    Updates the artistDict with the related artists.
    The related artists can only be added if they are also keys
    within the artist dictionary
    """

    allArtists = list(artistDict.keys())
    allArtistsSet = set(allArtists)

    for artist in allArtists:
        relatedArtists = getSpotifyArtistRelatedArtists(artist, sp)
        relatedArtists = relatedArtists & allArtistsSet
        artistDict[artist] = list(relatedArtists)

    return artistDict

def writeToCSV(data: dict):
    # Create Nodes sheet
    node_header = ['Id', 'Artist']
    node_rows = []
    artists = list(data.keys())
    artists.sort()

    for x in range(len(artists)):
        node_rows.append([x, artists[x]])

    # print(node_header)
    # print(node_rows)

    # Create Edges sheet
    type = 'Undirected'
    weight = 1
    edges_header = ['Source', 'Target', 'Type', 'Weight']
    edges_rows = []

    for x in artists:
        for y in data[x]:
            edges_rows.append([x, y, type, weight])

    # print(edges)

    with open('nodes.csv', 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)

        # Write the header
        writer.writerow(node_header)

        # Write rows
        writer.writerows(node_rows)

    with open('edges.csv', 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)

        # Write the header
        writer.writerow(edges_header)

        # Write rows
        writer.writerows(edges_rows)


if __name__ == '__main__':
    # Parse the CSV file and get all unique artists
    artistDict = parseAllUniqueArtists("spotify_dataset.csv")

    # Initialize spotipy classes - used to interface with Spotify API
    # Must register a project/app on https://developer.spotify.com and set
    # SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET as env vaariables on your machine
    client_credentials_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    artistDictWithRelatedArtists = updateArtistDictWithRelatedArtists(artistDict, sp)

    # Write the data to the files
    writeToCSV(artistDictWithRelatedArtists)

    # for k, v in artistDictWithRelatedArtists.items():
    #     print(f'Artist is: {k}')
    #     print(f'Related artists for {k}: {v}')
    #
    #     print("\n")















