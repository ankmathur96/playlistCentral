var express = require('express'); // Express web server framework
var request = require('request'); // "Request" library
var querystring = require('querystring');
var cookieParser = require('cookie-parser');
var async = require('async');
// var winston = require('winston');
// var logger = new (winston.Logger)({
//   transports: [
//     new (winston.transports.Console()),
//     new (winston.transports.File)({filename : 'trackList.log'})
//   ]
// })


var client_id = '6846427bd95949cfa5b89ec4205d9606';
var client_secret = 'fb0f8e63157146858d267dd0e93dffdd';
var redirect_uri = 'http://localhost:8888/callback';

/**
 * Generates a random string containing numbers and letters
 * @param  {number} length The length of the string
 * @return {string} The generated string
 */
var generateRandomString = function(length) {
  var text = '';
  var possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

  for (var i = 0; i < length; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
};

var stateKey = 'spotify_auth_state';

var app = express();

app.use(express.static(__dirname + '/public'))
   .use(cookieParser());

app.get('/login', function(req, res) {

  var state = generateRandomString(16);
  res.cookie(stateKey, state);

  // application requests authorization
  var scope = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative';
  res.redirect('https://accounts.spotify.com/authorize?' +
    querystring.stringify({
      response_type: 'code',
      client_id: client_id,
      scope: scope,
      redirect_uri: redirect_uri,
      state: state
    }));
});

app.get('/callback', function(req, res) {

  var code = req.query.code || null;
  var state = req.query.state || null;
  var storedState = req.cookies ? req.cookies[stateKey] : null;

  if (state === null || state !== storedState) {
    res.redirect('/#' +
      querystring.stringify({
        error: 'state_mismatch'
      }));
  } else {
    res.clearCookie(stateKey);
    var authOptions = {
      url: 'https://accounts.spotify.com/api/token',
      form: {
        code: code,
        redirect_uri: redirect_uri,
        grant_type: 'authorization_code'
      },
      headers: {
        'Authorization': 'Basic ' + (new Buffer(client_id + ':' + client_secret).toString('base64'))
      },
      json: true
    };

    request.post(authOptions, function(error, response, body) {
      if (!error && response.statusCode === 200) {

        var access_token = body.access_token,
            refresh_token = body.refresh_token;

        var options = {
          url: 'https://api.spotify.com/v1/me',
          headers: { 'Authorization': 'Bearer ' + access_token },
          json: true
        };

        // use the access token to access the Spotify Web API
        request.get(options, function(error, response, body) {
          var playlists = {
          url: 'https://api.spotify.com/v1/users/' + body.id + '/playlists',
          headers: { 'Authorization': 'Bearer ' + access_token },
          json: true
          };
          request.get(playlists, function(error, response, allPlayLists) {
            function getAllTracks(offset, maxTracks, tracksURI, access, previousTracks, action) {
              if (offset < maxTracks) {
                var tracksGet = {
                  url: tracksURI + '?offset='+offset+'&limit=100',
                  headers: {'Authorization': 'Bearer ' + access },
                  json: true
                };
                request.get(tracksGet, function(error, response, tracks) {
                  for (var tIndex = 0; tIndex < tracks.items.length; tIndex++) {
                    artistList = '';
                    for (var aIndex = 0; aIndex < tracks.items[tIndex].track.artists.length; aIndex++) {
                      artistList += tracks.items[tIndex].track.artists[aIndex].name + '|'
                    }
                    previousTracks.push(tracks.items[tIndex].track.name +' ~ ' + artistList);
                  }
                  getAllTracks(offset + 100, maxTracks, tracksURI, access, previousTracks, action);
                });
              } else {
                action(previousTracks)
              }
            }
            function logList(l) {
              console.log(l)
            }
            map = {}
            async.forEachOfSeries(allPlayLists.items, function(playlist, key, callback) {
              getAllTracks(0, playlist.tracks.total, playlist.tracks.href, access_token, new Array(), function(results) {
                if (results) {
                  map[playlist.name] = results
                  callback();
                } else {
                  console.log('error');
                }
              });
            }, function(err) {
              if (err) {
                console.log('error in final callback');
              } else {
                console.log('# -*- coding: utf-8 -*-')
                process.stdout.write('playlist_map = ')
                console.log(map);
              }
            });
          });
        });

        // we can also pass the token to the browser to make requests from there
        res.redirect('/#' +
          querystring.stringify({
            access_token: access_token,
            refresh_token: refresh_token
          }));
      } else {
        res.redirect('/#' +
          querystring.stringify({
            error: 'invalid_token'
          }));
      }
    });
  }
});

app.get('/refresh_token', function(req, res) {

  // requesting access token from refresh token
  var refresh_token = req.query.refresh_token;
  var authOptions = {
    url: 'https://accounts.spotify.com/api/token',
    headers: { 'Authorization': 'Basic ' + (new Buffer(client_id + ':' + client_secret).toString('base64')) },
    form: {
      grant_type: 'refresh_token',
      refresh_token: refresh_token
    },
    json: true
  };
  
  request.post(authOptions, function(error, response, body) {
    if (!error && response.statusCode === 200) {
      var access_token = body.access_token;
      res.send({
        'access_token': access_token
      });
    }
  });
});

app.listen(8888);