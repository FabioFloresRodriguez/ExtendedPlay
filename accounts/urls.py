"""Defines URL patterns for accounts."""

from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    #Include default auth urls.
    path('', include('django.contrib.auth.urls')),

    #Registration Page
    path('register/', views.register, name='register'),

    #profile
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('find-profile/', views.find_profile, name='find_profile'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='profile'),

    #friends
    path('friends/', views.friends, name='friends'),
    path('friends/requests/', views.friend_requests, name='friend_requests'),
    path('friends/requests/accept_request/<str:username>', views.accept_request, name='accept_request'),
    path('friends/requests/deny-request/<str:username>', views.deny_request, name='deny_request'),
    path('friends/send-request/<str:username>', views.send_request, name='send_request'),
    path('friends/cancel-request/<str:username>', views.cancel_request, name='cancel_request'),
    path('friends/remove-friend/<str:username>', views.remove_friend, name='remove_friend'),
]