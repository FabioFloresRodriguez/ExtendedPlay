from django import forms
from .models import AlbumInfo, Review

class AlbumForm(forms.ModelForm):
    class Meta:
        model = AlbumInfo
        fields = ['name','spotify_id']
        labels = {
            'name':'', 
            'spotify_id':'',
            }
        
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['star_rating','text']
        widgets = {
            'star_rating': forms.NumberInput(attrs={'step':'0.5'}),
            'text': forms.Textarea(attrs={
                'class': 'form-control w-100', 
                'rows': 5,                      
                'placeholder': 'Write your review here...',
                'style': 'background-color: #2b2b2b; color: white;',
            })}