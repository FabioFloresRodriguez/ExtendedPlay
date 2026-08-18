"""Defines URL patterns for extended_play"""

from django.urls import path

from . import views

app_name = "extended_play"
urlpatterns = [
    #always put static urls before dynamic urls

    #Home page
    path('', views.index, name = 'index'),

    #search
    path('search/', views.search, name='search'),
    
    #album-log pages (this will MOST LIKELY be like profile liked/reviewed albums) 
    path('album-log/add-album/', views.add_album, name="add_album"),
    path('album-log/add-review/<str:spotify_id>/', views.add_review, name='add_review'),
    path('album-log/edit-review/<str:spotify_id>/', views.edit_review, name="edit_review"),
    path('album-log/', views.album_log, name='album_log'),
    path('album-log/<str:username>', views.album_log, name='album_log'),
    path('find-album/', views.find_album, name='find_album'),
    path('album/<str:spotify_id>/', views.album, name="album"),

    #artists pages
    path('followed-artists/', views.followed_artists, name='followed_artists'),
    path('followed-artists/follow-artist/', views.follow_artist, name='follow_artist'),
    path('followed-artist/unfollow-artist/', views.unfollow_artist, name='unfollow_artist'),
    path('followed-artists/<str:username>', views.followed_artists, name='followed_artists'),

    #artist dynamic
    path('artists/<str:spotify_id>/', views.artist, name='artist'),
    path('artists/<str:spotify_id>/albums/', views.artist_albums, name="artist_albums"),
    path('find-artist/', views.find_artist, name='find_artist'),


]   