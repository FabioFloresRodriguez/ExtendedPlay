from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Artist (models.Model):
    """Artist information"""
    name = models.CharField(max_length=200)
    spotify_id = models.CharField(max_length=200)
    pfp = models.CharField(max_length=500, blank=True, null=True)
    genres = models.JSONField(default=list)

    def __str__(self):
        """Return name of artist"""
        return f"{self.name}"

class ArtistInfo(models.Model):
    name = models.CharField(max_length=200)
    spotify_id = models.CharField(max_length=200)
    pfp = models.CharField(max_length=500, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        """Return name of artist"""
        return f"{self.name}"

class Album(models.Model):
    """Album that the user is looking at."""
    name = models.CharField(max_length=200)
    artist_name = models.CharField(max_length=200)#saving the name
    artist_id = models.CharField(max_length=200) #saving the id
    spotify_id = models.CharField(max_length=200) #Change this to be 22 max, thats the size of a spotify id
    cover_url = models.CharField(max_length=500, blank=True, null=True)
    release_date = models.CharField(max_length=100)
    tracklist = models.JSONField(default=list)

    def __str__(self):
        """Return the name of the album"""
        return f"{self.name} by {self.artist}."

class AlbumInfo(models.Model):
    name = models.CharField(max_length=200)
    artist_name = models.CharField(max_length=200)#saving the name
    artist_id = models.CharField(max_length=200) #saving the id
    spotify_id = models.CharField(max_length=22) #Change this to be 22 max, thats the size of a spotify id
    cover_url = models.CharField(max_length=500, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the name of the album"""
        return f"{self.name}"

class Review(models.Model):
    """User's review of an album"""
    album = models.OneToOneField(AlbumInfo, on_delete=models.CASCADE, related_name="review")
    date_added = models.DateTimeField(auto_now_add=True)
    star_rating = models.FloatField()
    text = models.TextField(max_length=500, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete= models.CASCADE)

    class Meta():
        verbose_name_plural = 'Reviews'

    def get_star_breakdown(self):
        """Returns a dict with counts for full, half, and empty stars"""
        rating = self.star_rating or 0.0
        full_stars  = int(rating)
        has_half = (rating - full_stars) >= 0.5

        if has_half:
            empty_stars = 5 - full_stars - 1
        else:
            empty_stars = 5 - full_stars

        return {
            'full' : range(full_stars),
            'half' : has_half,
            'empty' : range(empty_stars)
        }
    
    def __str__(self):
        """Return information about the review"""
        return f"{self.album.name} got a {self.star_rating} star rating."
    