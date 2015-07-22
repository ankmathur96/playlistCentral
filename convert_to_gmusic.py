from gmusicapi import Mobileclient
from spotifyInfo import playlist_map
import re
import getpass

def canonicalize(delims, trackTitle):
	trackTitle = trackTitle.lower()
	canon = re.split(delims, trackTitle)
	feat = ['featuring', 'Featuring', 'Feat', 'feat.']
	for i in range(len(canon)):
		if canon[i] in feat:
			canon[i] = 'feat'
	return canon

def findMatch(results, song):
	tokens = song.split('~')
	songName, artistTokens = tokens[0], tokens[1]
	artists = [x for x in artistTokens.split('|') if x != '' and x != ' ']
	delims = re.compile('[().-]')
	canonSong = canonicalize(delims, songName)
	nameMatches = []
	for result in results:
		canonResult = canonicalize(delims, result['track']['title'])
		shorter = canonSong if len(canonSong) < canonResult else canonResult
		ismatch = True
		for elem in shorter:
			if elem not in canonResult:
				ismatch = False
		if ismatch:
			nameMatches.append(result['track'])
	finalMatches = []
	if len(nameMatches) > 0:
		for match in nameMatches:
			if match['artist'] in artists:
				finalMatches.append(match)
	allartists = ''
	for artist in artists:
		allartists += artist + ','
	allartists = allartists[:-1]
	song = songName + ' by ' + allartists + '\n'
	if len(finalMatches) > 1:
		options, counter = 'Could not make a definitive guess. For the following track: ' + song, 1
		for match in finalMatches:
			options += match['title'] + ' by ' + match['artist'] + '\n'
		choice = int(raw_input(options))
		return match['nid']
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
		results = api.search_all_access(song, 10)
		trackResults = results['song_hits']
		song_id = findMatch(trackResults, song)
		if song_id is not None:
			api.add_songs_to_playlist(newPID, song_id)




