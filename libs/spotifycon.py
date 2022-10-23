import os
import spotipy

#SETUP SPOTIFY
spotify_client_id = os.getenv('SPOTIPY_CLIENT_ID')
spotify_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
spotify_redirect_uri = "http://0.0.0.0:8080/"
scope = "user-read-currently-playing app-remote-control streaming"
username = "o9obimakpi51kewtlal1zt20j"
oauth = spotipy.SpotifyOAuth(
	client_id=spotify_client_id,
	client_secret=spotify_secret,
	redirect_uri=spotify_redirect_uri,
	scope=scope,
	open_browser=False
	)
clientcreds = spotipy.SpotifyClientCredentials(
	client_id=spotify_client_id,
	client_secret=spotify_secret
)
#tokeninfo = oauth.get_cached_token()
#token = ""
#token = tokeninfo['access_token']
#spotify = spotipy.Spotify(auth=token, auth_manager=
spotify = spotipy.Spotify(auth_manager=oauth)
#spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

#tokeninfo = oauth.get_cached_token()

#if oauth.is_token_expired(tokeninfo):
#		token = oauth.get_access_token(oauth.get_authorization_code())
#		spotify.set_auth(token)
