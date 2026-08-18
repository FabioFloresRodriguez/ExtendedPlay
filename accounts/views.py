from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .models import Profile
from .forms import ProfileForm
from extended_play.models import Album, AlbumInfo, Review, Artist, ArtistInfo
from extended_play.forms import ReviewForm
from friendship.models import Friend, FriendshipRequest, Follow, Block
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
def register(request):
    """Register a new user."""
    if request.method != 'POST':
        #Display a blank registration form
        form = UserCreationForm()
    else:
        #Process completed form.
        form = UserCreationForm(data=request.POST)

        if form.is_valid():
            new_user = form.save()
            #Log the new user in and then redirect to home page
            login(request, new_user)
            return redirect('extended_play:index')

    context = {'form': form}
    return render(request, 'registration/register.html', context)

#profile page
def profile(request,username=None):
    """Profile view"""
    is_friends = False
    sent_request = False
    received_request = False
    if username:
        user_obj = get_object_or_404(User, username=username)

        if Friend.objects.are_friends(user1=request.user, user2=user_obj):
            is_friends = True
        elif FriendshipRequest.objects.filter(from_user=request.user, to_user=user_obj):
            sent_request = True
        elif FriendshipRequest.objects.filter(from_user=user_obj, to_user=request.user):
            received_request = True
    else:
        user_obj = request.user

    artists = ArtistInfo.objects.filter(owner=user_obj).all()[:4]
    albums = AlbumInfo.objects.filter(owner=user_obj).order_by('-date_added')[:4]
    friends = Friend.objects.friends(user=request.user)[:4]

    context = {
        'username' : username,
        'user_obj' : user_obj,
        'is_friends' : is_friends,
        'sent_request' : sent_request,
        'received_request' : received_request,
        'artists' : artists,
        'albums' : albums,
        'friends' : friends,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """Edit profile"""
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method != 'POST':
        form = ProfileForm(instance=profile)
    else:
        form = ProfileForm(data=request.POST, files=request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')

    context = {'form': form}
    return render(request, 'accounts/edit-profile.html', context)

def find_profile(request):
    """Find profiles using account name"""
    query = request.GET.get('q','')
    profiles = None

    if query:
        profiles = Profile.objects.filter(user__username__iexact=query) #finds all the ones with that name, regardless of case sensitivity

    context = {
        'query': query,
        'profiles': profiles
    }

    return render(request, 'accounts/find-profile.html', context)

#Friends section
@login_required
def friends(request):
    """Display all your friends"""
    friends = Friend.objects.friends(user=request.user)

    context = {'friends' : friends}

    return render(request, 'accounts/friends.html', context)

@login_required
def friend_requests(request):
    """Display friend requests"""
    friend_requests = FriendshipRequest.objects.filter(
        to_user=request.user,
        rejected__isnull=True
        )

    context = {'friend_requests' : friend_requests}
    return render(request, 'accounts/friend-requests.html', context)

@login_required
def send_request(request, username):
    other_user = get_object_or_404(User, username=username)
    name = other_user.profile.user.username

    Friend.objects.add_friend(
        from_user=request.user,
        to_user=other_user
    )

    csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')
    return HttpResponse(
        f'<button hx-post="/friends/cancel-request/{ name }" '
        f'hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' '
        f'hx-vals=\'{{"name": "{name}"}}\' '
        f'hx-swap="outerHTML" class="btn btn-danger">Cancel Request</button>'
        ) 

@login_required
def cancel_request(request,username):
    other_user = get_object_or_404(User, username=username)
    
    name = other_user.profile.user.username
    if FriendshipRequest.objects.filter(from_user=request.user, to_user=other_user):
        friend_request = get_object_or_404(FriendshipRequest, from_user=request.user, to_user=other_user)
        friend_request.cancel()

        csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')
        return HttpResponse(
            f'<button hx-post="/friends/send-request/{ name }" '
            f'hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' '
            f'hx-vals=\'{{"name": "{name}"}}\' '
            f'hx-swap="outerHTML" class="btn btn-custom">Send Friend Request</button>'
            ) 

@login_required
def accept_request(request,username):
    other_user = get_object_or_404(User, username=username)
    friend_request = FriendshipRequest.objects.get(
        from_user = other_user,
        to_user=request.user
    )

    friend_request.accept()
    return HttpResponse('<button class="btn btn-success" disabled>Accepted</button>')

@login_required
def deny_request(request, username):
    other_user = get_object_or_404(User, username=username)
    friend_request = FriendshipRequest.objects.get(
        from_user = other_user,
        to_user=request.user
    )

    if friend_request:
        friend_request.delete()
    return HttpResponse('')

@login_required
def remove_friend(request,username):
    other_user = get_object_or_404(User, username=username)
    name = other_user.profile.user.username

    Friend.objects.remove_friend(
        from_user=request.user,
        to_user=other_user
    )

    csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')
    return HttpResponse(
        f'<button hx-post="/friends/send-request/{ name }" '
        f'hx-headers=\'{{"X-CSRFToken": "{csrf_token}"}}\' '
        f'hx-vals=\'{{"name": "{name}"}}\' '
        f'hx-swap="outerHTML" class="btn btn-custom">Send Friend Request</button>'
    ) 
