from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager



class UserManager(BaseUserManager):
    def create_email(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is Required")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role","admin")        
        return self.create_email(email, password, **extra_fields)
    



class User(AbstractBaseUser, PermissionsMixin):
    Role_choices = (
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("sales", "sales"),
    )

    email = models.EmailField(unique= True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role_choices)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)

    object = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email