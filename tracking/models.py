from django.db import models

class ClientLocation(models.Model):
    client = models.ForeignKey(
        'rentals.Client',
        on_delete=models.CASCADE,
        related_name='locations'
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)
    is_sharing = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.client} - {self.latitude},{self.longitude}"


class ChatMessage(models.Model):
    SENDER_CHOICES = [('client', 'Client'), ('employee', 'Employee'), ('bot', 'Bot')]
    client = models.ForeignKey(
        'rentals.Client',
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.client} [{self.sender}]: {self.message[:50]}"