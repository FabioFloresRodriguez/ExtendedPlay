from django.contrib import admin
from .models import ArtistInfo, AlbumInfo, Review

# Register your models here.
admin.site.register(ArtistInfo)
admin.site.register(AlbumInfo)
admin.site.register(Review)