from PIL import Image
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=500, blank=True, null=True)
    pfp = models.ImageField(upload_to='pfps/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.user.username

        super().save(*args,**kwargs)

        if self.pfp:
            img = Image.open(self.pfp.path)
            if img.height > 300 or img.width > 300:
                output_size = (300,300)
                img.thumbnail(output_size)
                img.save(self.pfp.path)  

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)