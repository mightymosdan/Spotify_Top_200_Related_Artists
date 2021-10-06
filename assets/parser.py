import pandas as pd
import spotipy
import csv
from spotipy.oauth2 import SpotifyClientCredentials

"""
artistDict structure: {
    artist: { 
        relatedArtists: [],
        genres: [],
        followers: [],
        id: ''
        },
    artist: { 
        relatedArtists: [],
        genres: [],
        followers: [],
        id: ''
        },
    .
    .
    .
}

"""

# Used for initial parsing of the kaggle dataset, can call on new csv files with Artist Header
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
        artistDict[mainArtist] = {'relatedArtists': [], 'genres': '', 'followers' : 0, 'id': 0}


    print(f'Number of unique artists after removing features: {len(artistDict.keys())}')

    return artistDict

def getSpotifyArtistData(artist: str, sp: spotipy.Spotify, term: str= None) -> dict:
    """
    This function gets Spotify data based on Artists
    """
    try:
        artistData = sp.search(q='artist:' + artist, type='artist')
        # Select the top result
        artistData = artistData['artists']['items'][0]

        # Check default case
        if not term:
            # print(f'Returning all data on Spotify Artist')
            return artistData

        elif term:
            try:
                return artistData[term]

            except KeyError:
                print(f'The term: {term} is not an key in artistData')
                print(f'Keys in artistData: {artistData.keys()}')

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
        artistDict[artist]['relatedArtists'] = list(relatedArtists)

    return artistDict

def updateArtistDictWithGenres(artistDict: dict, sp: spotipy.Spotify) ->dict:
    """
    Updates the artistDict with the genres.
    """

    allArtists = list(artistDict.keys())

    for artist in allArtists:
        artistGenres = getSpotifyArtistData(artist, sp, 'genres')
        artistDict[artist]['genres'] = list(artistGenres)

    return artistDict

def updateArtistDictWithFollowers(artistDict: dict, sp: spotipy.Spotify) ->dict:
    """
    Updates the artistDict with the followers count.
    """

    allArtists = list(artistDict.keys())

    for artist in allArtists:
        artistData = getSpotifyArtistData(artist, sp, 'followers')
        artistFollowers = artistData['total']
        artistDict[artist]['followers'] = artistFollowers

    return artistDict

def writeToCSV(data: dict):
    # Create Nodes sheet
    node_header = ['Id', 'Artist', 'Genres', 'Followers', 'Related Artist']
    node_rows = []
    artists = list(data.keys())
    artists.sort()

    for x in range(len(artists)):
        # Assign IDs to artists
        data[artists[x]]['id'] = x

        # print(f'Artist ID: {data[artists[x]]["id"]}')
        # print(f'Artist: {artists[x]}')
        # print(f'Genres: {data[artists[x]]["genres"]}')
        # print(f'Followers: {data[artists[x]]["followers"]}')
        allRelatedArtists = ', '.join(data[artists[x]]['relatedArtists'])
        # print(allRelatedArtists)
        node_rows.append([data[artists[x]]['id'], artists[x], data[artists[x]]['genres'], data[artists[x]]['followers'], allRelatedArtists])

    # Create Edges sheet
    type = 'Undirected'
    weight = 1
    edges_header = ['Source', 'Target', 'Type', 'Weight']
    edges_rows = []

    # Create edges based on relatedArtists
    for x in range(len(artists)):
        for y in data[artists[x]]['relatedArtists']:
            # Write the row:
            # Source (Artist ID) | Target (Related Artist ID) | Type(Undirected) | Weight(1)
            edges_rows.append([data[artists[x]]['id'], data[y]['id'], type, weight])

    # print('Writing csv file')
    with open('nodes_and_attributes_updated.csv', 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)

        # Write the header
        writer.writerow(node_header)

        # Write rows
        writer.writerows(node_rows)

    with open('edges_updated.csv', 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)

        # Write the header
        writer.writerow(edges_header)

        # Write rows
        writer.writerows(edges_rows)


if __name__ == '__main__':
    # Parse the CSV file and get all unique artists
    artistDict = parseAllUniqueArtists("nodes.csv")

    # Initialize spotipy classes - used to interface with Spotify API
    # Must register a project/app on https://developer.spotify.com and set
    # SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET as env vaariables on your machine
    client_credentials_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    print('Beginning to update artistDict')
    artistDict = updateArtistDictWithGenres(artistDict, sp)
    print("Genres updated")
    artistDict = updateArtistDictWithFollowers(artistDict, sp)
    print('Followers updated')
    artistDict = updateArtistDictWithRelatedArtists(artistDict, sp)
    print('Related artists updated')

    # Write the data to the files
    print('Writing files')
    writeToCSV(artistDict)
    print('Done writing')























