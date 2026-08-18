from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from accounts.models import Profile
from accounts.forms import ProfileForm
from .models import Album, AlbumInfo, Review, Artist, ArtistInfo
from .forms import ReviewForm
from friendship.models import Friend, FriendshipRequest, Follow, Block
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials(client_id=settings.SPOTIFY_CLIENT_ID, client_secret=settings.SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Create your views here.
#home page
def index(request):
    """The home page of extended play"""
    recent_albs = []
    friend_recs = []

    if request.user.is_authenticated:
        arts = ArtistInfo.objects.filter(owner=request.user).all()[:4]

        for art in arts:
            # Build a unique cache key for each artist
            cache_key = f"spotify_recent_album_{art.id}"
            alb = cache.get(cache_key)

            if not alb:
                results = sp.search(q=art.name, type='artist', limit=1)
                items = results.get('artists', {}).get('items', [])
                
                if items:
                    art_data = items[0]
                    albums = sp.artist_albums(art_data['id'], album_type='album', limit=1).get('items', [])
                    if albums:
                        alb = albums[0]
                        # Cache the album data for 24 hours (86400 seconds)
                        cache.set(cache_key, alb, 86400)

            if alb:
                recent_albs.append(alb)

        friends = Friend.objects.friends(user=request.user)[:4]

        for friend in friends:
            album = AlbumInfo.objects.filter(owner=friend).order_by('-date_added').first()

            if album:
                friend_recs.append(album)
        
    context = {
        'recent_albs' : recent_albs,
        'friend_recs' : friend_recs
        }
    return render(request, 'extended_play/index.html', context)

#search view
def search(request):
    """Search function"""
    query = request.GET.get('q', '')
    artists = []
    albums = []

    if query:
        results = sp.search(q=query, type='artist,album', limit=8)

        art_res = results.get('artists',{}).get('items',[])
        alb_res = results.get('albums', {}).get('items',[])

        for art in art_res:
            pfp_url =''
            images = art.get('images', [])
            if images:
                pfp_url = images[0]['url']

            artist = Artist(
                name=art['name'], 
                pfp=pfp_url,
                spotify_id=art['id']
            )

            artists.append(artist)

        for alb in alb_res:
            cover_url = ''
            images = alb.get('images', [])
            if images:
                cover_url = images[0]['url']

            album = Album(
                name = alb['name'],
                artist_id = alb['artists'][0]['id'],
                artist_name=alb['artists'][0]['name'],
                cover_url = cover_url,
                spotify_id = alb['id'],
            )

            albums.append(album)

    context = {
        'query': query,
        'artists': artists,
        'albums': albums,
    }

    return render(request, 'extended_play/search.html', context)

#artists views
#Gonna be liked artists list
@login_required
def followed_artists(request, username=None):
    "Show liked artists"
    if username:
        user_obj = get_object_or_404(User, username=username)
    else:
        user_obj = request.user

    artists = ArtistInfo.objects.filter(owner=user_obj)

    context = {
        'user_obj':user_obj,
        'artists':artists,
        }
    return render(request, 'extended_play/followed-artists.html', context)

#Artist Page
def artist(request,spotify_id):
    "Show artist information"
    cache_key = f"spotify_artist_{spotify_id}"
    cached_data = cache.get(cache_key)

    if not cached_data:
        art_data = sp.artist(spotify_id)

        pfp_url = None
        images = art_data.get('images', [])

        if images:
            pfp_url = images[0]['url']

        artist = Artist(
            name=art_data['name'], 
            pfp=pfp_url,
            spotify_id=art_data['id']
        )

        albums = sp.artist_albums(spotify_id, album_type='album', limit=4).get('items',[]) #artist albums gets the album metadata, get items gets the actual albums

        cache.set(cache_key, (artist, albums), 86400)
    else:
        artist, albums = cached_data

    is_following = False

    if request.user.is_authenticated:
        is_following = ArtistInfo.objects.filter(owner=request.user, spotify_id=spotify_id).exists()
    
    context = {
        'artist' : artist,
        'albums' : albums,
        'is_following': is_following
    }

    return render(request, 'extended_play/artist.html', context)

def find_artist(request):
    """Find the artist being searched"""
    query = request.GET.get('q', '')
    artists = []

    if query:
        results = sp.search(q=query, type='artist', limit=8)

        art_res = results.get('artists', {}).get('items',[])

        for art in art_res:
            pfp = ''
            images = art.get('images', [])
            if images:
                pfp = images[0]['url']

            artist = Artist(
                name = art['name'],
                pfp = pfp,
                spotify_id = art['id']
            )

            artists.append(artist)

    context = {
        'query': query,
        'artists': artists,
    }

    return render(request, 'extended_play/find-artist.html', context)

def artist_albums(request,spotify_id): #Rework to limit api calls and also work with an offset, will rewrite artist-albums.html after
    """Show all albums made by an artist"""
    lim = 8
    offset = int(request.GET.get('offset', 0))

    cache_key = f"artist_albums_{spotify_id}_{offset}_{lim}"
    cached_data = cache.get(cache_key)

    if not cached_data:
        results = sp.artist_albums(spotify_id, album_type='album', limit=lim, offset=offset)

        cache.set(cache_key, results, 86400)
    else:
        results = cached_data

    albums = results.get('items', [])
    artist_name = results.get('items', [])[0]['artists'][0]['name']
    artist_id = results.get('items', [])[0]['artists'][0]['id']

    context = {
        'artist_name' : artist_name,
        'artist_id' : artist_id,
        'albums' : albums,
        'next_offset': offset + lim,
        'has_next' : bool(results.get('next')),
        'back_offset': max(0, offset - lim),
        'has_back' : bool(results.get('previous')),
    }

    return render(request, 'extended_play/artist-albums.html', context)

@login_required
@require_POST
def follow_artist(request): 
    """Follow artist"""
    name = request.POST.get('name')
    pfp = request.POST.get('pfp')
    spotify_id = request.POST.get('spotify_id')

    artist, created = ArtistInfo.objects.get_or_create(
        name=name,
        pfp = pfp,
        spotify_id=spotify_id,
        owner=request.user,
    )

    csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')
    return HttpResponse(
        f'<button hx-post="/followed-artist/unfollow-artist/" '
        f'hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' '
        f'hx-vals=\'{{"name": "{name}", "spotify_id": "{spotify_id}", "pfp": "{pfp}"}}\' '
        f'hx-swap="outerHTML" class="btn btn-secondary">Unfollow</button>'
    )

@login_required
@require_POST
def unfollow_artist(request): 
    """Follow artist"""
    name = request.POST.get('name')
    pfp = request.POST.get('pfp')
    spotify_id = request.POST.get('spotify_id')

    ArtistInfo.objects.filter(name=name, pfp=pfp, spotify_id=spotify_id, owner=request.user).delete()

    csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')
    return HttpResponse(
        f'<button hx-post="/followed-artists/follow-artist/" '
        f'hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' '
        f'hx-vals=\'{{"name": "{name}", "spotify_id": "{spotify_id}", "pfp": "{pfp}"}}\' '
        f'hx-swap="outerHTML" class="btn btn-custom">Follow</button>'
    ) 

#albums/reviews views
@login_required
def album_log(request, username=None):
    """Show all liked albums """
    if username:
        user_obj = get_object_or_404(User, username=username)
    else:
        user_obj = request.user

    albums = AlbumInfo.objects.filter(owner=user_obj).all()

    context = {
        'user_obj' : user_obj,
        'albums' : albums}
    
    return render(request, 'extended_play/album-log.html', context)

def album(request, spotify_id):
    """Show a single album and all its information"""
    cache_key = f"spotify_album_{spotify_id}"
    album = cache.get(cache_key)

    if not album:
        alb_data = sp.album(spotify_id)

        tracks = alb_data.get('tracks',{}).get('items', [])

        album = Album(
            name = alb_data['name'],
            artist_name = alb_data['artists'][0]['name'],
            artist_id = alb_data['artists'][0]['id'],
            spotify_id = spotify_id,
            cover_url = alb_data['images'][0]['url'],
            release_date = alb_data['release_date'],
            tracklist = tracks
        )

        cache.set(cache_key, album, 86400)

    review = None
    logged = None
    if request.user.is_authenticated:
        db_album = AlbumInfo.objects.filter(owner=request.user, spotify_id=spotify_id).first()
        logged = bool(db_album)

        if db_album:
            review = Review.objects.filter(owner=request.user).filter(album=db_album).first()
    

    context = {
        'album': album, 
        'review': review,
        'logged': logged
        }
    
    return render(request, 'extended_play/album.html', context)

@login_required
def find_album(request):
    """Find the album being searched"""
    query = request.GET.get('q', '')
    albums = []

    if query:
        results = sp.search(q=query, type='album', limit=8)

        alb_res = results.get('albums', {}).get('items',[])

        for alb in alb_res:
            cover_url = ''
            images = alb.get('images', [])
            if images:
                cover_url = images[0]['url']

            album = Album(
                name = alb['name'],
                artist_name = alb['artists'][0]['name'],
                artist_id = alb['artists'][0]['id'],
                cover_url = cover_url,
                spotify_id = alb['id'],
            )

            albums.append(album)

    context = {
        'query': query,
        'albums': albums,
    }

    return render(request, 'extended_play/find-album.html', context)

@login_required
@require_POST
def add_album(request): 
    """Add album"""
    name = request.POST.get('name')
    artist_name = request.POST.get('artist_name')
    artist_id = request.POST.get('artist_id')
    spotify_id = request.POST.get('spotify_id')
    cover_url = request.POST.get('cover_url')

    album, created = AlbumInfo.objects.get_or_create(
        name=name,
        artist_name=artist_name,
        artist_id=artist_id,
        cover_url=cover_url,
        spotify_id=spotify_id,
        owner=request.user,
    )

    if created:
        return HttpResponse('<button class="btn btn-secondary" disabled>Logged</button>')
    else:
        return HttpResponse('<button class="btn btn-secondary" disabled>Already in your album log</button>')

@login_required
def add_review(request,spotify_id):
    """Review an album"""
    album = AlbumInfo.objects.get(spotify_id=spotify_id)

    if request.method != 'POST':
        #No data submitted; create a blank form.
        form = ReviewForm()
    else:
        #POST data submitted; process data.
        form = ReviewForm(data=request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.album = album
            review.owner = request.user
            review.save()
            return redirect('extended_play:album', spotify_id=spotify_id)
        
    #Display a blank or invalid form.
    context = {'album': album, 'form': form}
    return render(request, 'extended_play/add-review.html', context)

@login_required
def edit_review(request, spotify_id):
    """Edit an existing review"""
    album = AlbumInfo.objects.filter(owner=request.user).get(spotify_id=spotify_id)
    review = Review.objects.filter(owner=request.user).get(album=album)

    if request.method != 'POST':
        #Initial request; pre-fill form with the current entry.
        form = ReviewForm(instance=review)
    else:
        #POST data submitted; process data.
        form = ReviewForm(instance=review, data=request.POST)
        if form.is_valid():
            review_edit = form.save(commit=False)
            review_edit.album = album
            review_edit.owner = request.user
            review_edit.save()
            return redirect('extended_play:album', spotify_id=spotify_id)
        
    context = {'review': review, 'album': album, 'form': form}
    return render(request, 'extended_play/edit-review.html', context)

