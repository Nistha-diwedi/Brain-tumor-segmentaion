from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Custom user model extending AbstractUser"""
    full_name = models.CharField(max_length=255, blank=True)
    dob = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.full_name if self.full_name else self.username


class MRIReport(models.Model):
    """Model to store MRI reports and segmentation results"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mri_reports'
    )
    uploaded_image = models.ImageField(
        upload_to='mri_images/%Y/%m/%d/',
        help_text="Upload MRI scan image"
    )
    predicted_mask = models.ImageField(
        upload_to='segmentation_masks/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="AI-generated segmentation mask"
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    diagnosis_summary = models.TextField(
        null=True,
        blank=True,
        help_text="AI-generated diagnosis summary"
    )
    model_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Model confidence score (0-1)"
    )

    class Meta:
        ordering = ['-upload_date']
        verbose_name = "MRI Report"
        verbose_name_plural = "MRI Reports"

    def __str__(self):
        return f"MRI Report for {self.user.username} - {self.upload_date.strftime('%Y-%m-%d %H:%M')}"

    def get_confidence_percentage(self):
        """Return confidence as percentage"""
        if self.model_confidence is not None:
            return round(self.model_confidence * 100, 2)
        return None