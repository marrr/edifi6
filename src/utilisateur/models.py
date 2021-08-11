from django.db import models
from django.contrib.auth.models import User
from PIL import Image

class Profile(models.Model):
    SimpleUser = 1
    ManagerUser = 2
    AdminUser = 3
    ROLES = (
        (SimpleUser, 'Agent'),
        (ManagerUser, 'Gestionnaire'),
        (AdminUser, 'Administrateur'),
        )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.PositiveSmallIntegerField(choices=ROLES, blank=True, null=True)
    image = models.ImageField(default='default.jpg', upload_to='avatars/')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (150, 150)
            img.thumbnail(output_size)
            img.save(self.image.path)
