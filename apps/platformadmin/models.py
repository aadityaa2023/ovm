from django.db import models
from django.utils import timezone
import hashlib
import os


class PlatformAdmin(models.Model):
    """Platform administrators for OVM management."""

    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=256)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['username']
        verbose_name = 'Platform Admin'
        verbose_name_plural = 'Platform Admins'

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    def set_password(self, raw_password):
        """Hash and store password using PBKDF2-SHA256."""
        salt = os.urandom(16).hex()
        hashed = hashlib.pbkdf2_hmac('sha256', raw_password.encode(), salt.encode(), 260000)
        self.password_hash = f"pbkdf2_sha256${salt}${hashed.hex()}"

    def check_password(self, raw_password):
        """Verify raw password against stored hash."""
        try:
            algo, salt, stored_hash = self.password_hash.split('$')
            hashed = hashlib.pbkdf2_hmac('sha256', raw_password.encode(), salt.encode(), 260000)
            return hashed.hex() == stored_hash
        except Exception:
            return False

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
