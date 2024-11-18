from django.db import models


from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    google_credentials = models.JSONField(null=True, blank=True)

    def link_google_credentials(self, credentials):
        self.google_credentials = credentials
        self.save()

    def unlink_google_credentials(self):
        self.google_credentials = None
        self.save()

    def get_google_credentials(self):
        """Retrieve Google credentials as a `Credentials` object."""
        from google.oauth2.credentials import Credentials
        if self.google_credentials:
            return Credentials(**self.google_credentials)
        return None
