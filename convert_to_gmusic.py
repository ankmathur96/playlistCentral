from gmusicapi import Mobileclient
from spotifyInfo import playlist_map
import re
import datetime
import getpass

# is t1 in t2 +- 1
def plusminus(t1, t2, delta):
    return t2 - delta < t1 and t1 < t2 + delta

def canonicalizeArtist(a):
    return a.lower().strip()

def canonicalizeSong(delims, trackTitle):
    trackTitle = trackTitle.lower()
    canon = [x.decode('utf-8') if isinstance(x, str) else x for x in re.split(delims, trackTitle)]
    for s in canon:
        if isinstance(s, str):
            print 'didnt convert'
    feat = [u'featuring', u'Featuring', u'Feat', u'feat.']
    for i in range(len(canon)):
        if canon[i] in feat:
            canon[i] = u'feat'
    return canon

def findMatch(results, song, duration):
    tokens = song.split('~')
    songName, artistTokens = tokens[0], tokens[1]
    artists = [canonicalizeArtist(a.decode('utf-8')) if isinstance(a, str) else canonicalizeArtist(a) for a in artistTokens.split('|') if a != '' and a != ' ']
    delims = re.compile('[().-]')
    canonSong = canonicalizeSong(delims, songName)
    nameFilter = []
    for result in results:
        canonResult = canonicalizeSong(delims, result['track']['title'])
        shorter = canonSong if len(canonSong) < len(canonResult) else canonResult
        ismatch = True
        for elem in shorter:
            if elem not in canonResult:
                ismatch = False
        if ismatch:
            nameFilter.append(result['track'])
    nameArtistFilter = []
    if len(nameFilter) > 0:
        for match in nameFilter:
            if canonicalizeArtist(match['artist']) in artists:
                nameArtistFilter.append(match)
    finalMatches = []
    if len(nameArtistFilter) > 0:
        for s in nameArtistFilter:
            if plusminus(int(s['durationMillis']), duration, 1000):
                finalMatches.append(s)
    # this filter is potentially to costly. same song could differ by a couple milliseconds.
    if len(finalMatches) == 0:
        finalMatches = nameArtistFilter
    allartists = ''
    for artist in artists:
        allartists += artist + ','
    allartists = allartists[:-1]
    song = songName + ' by ' + allartists + ' - ' + str(datetime.timedelta(milliseconds=duration)) + '\n'
    if len(finalMatches) > 1:
        options, counter = 'Could not make a definitive guess. For the following track: ' + song, 1
        for match in finalMatches:
            options += str(counter) + '. ' + match['title'] + ' by ' + match['artist'] + ' - ' + str(datetime.timedelta(milliseconds=int(match['durationMillis']))) + '\n'
            counter += 1
        choice = int(raw_input(options)) - 1
        return finalMatches[choice]['nid']
    else:
        if len(finalMatches) == 0:
            print 'could not find ' + song
            return None
        return finalMatches[0]['nid']

api = Mobileclient()
uname = raw_input('What is your Google username?\n')
pword = getpass.getpass('Please enter your password. If you have 2-factor enabled, you will need to create a app-specific password and enter that here.\n')
logged_in = api.login(uname, pword, Mobileclient.FROM_MAC_ADDRESS) #'qrwxkctezunyuuiq'
if not logged_in:
	raise Exception('login failed')
for k in playlist_map:
	newPID = api.create_playlist(k)
	playlist_songs = playlist_map[k]
	for song in playlist_songs:
		special_char = song.find('\\')
		while special_char >= 0:
			song = song[:special_char] + song[special_char+1:]
			special_char = song.find('\\')
		sTokens = song.split('`')
		song, duration = sTokens[0], int(sTokens[1])
		results = api.search_all_access(song, 10)
		trackResults = results['song_hits']
		song_id = findMatch(trackResults, song, duration)
		if song_id is not None:
			api.add_songs_to_playlist(newPID, song_id)




