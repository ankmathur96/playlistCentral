from gmusicapi import Mobileclient
from spotifyInfo import playlist_map
import getpass

def checkMatch(results, song):
	tokens = song.split('~')
	songName, artistTokens = tokens[0], tokens[1]
	artists = [x for x in artistTokens.split('|') if x != '' and x != ' ']
	canonSong = re.split('[().-]', songName)
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
		match_found = False
		for result in trackResults:
			if result['track']['title'] == song:
				match_found = True
				api.add_songs_to_playlist(newPID, result['track']['nid'])
				break
		if not match_found:
			print 'did not find ' + song + ' in playlist ' + k