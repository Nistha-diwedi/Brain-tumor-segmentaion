from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, MRIReport


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    list_display = ('username', 'email', 'full_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'gender')
    search_fields = ('username', 'full_name', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'dob', 'gender', 'phone_number', 'address')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'dob', 'gender', 'phone_number', 'address')
        }),
    )


@admin.register(MRIReport)
class MRIReportAdmin(admin.ModelAdmin):
    """Admin for MRI Report model"""
    list_display = ('user', 'upload_date', 'model_confidence', 'has_diagnosis')
    list_filter = ('upload_date', 'user')
    search_fields = ('user__username', 'user__full_name', 'diagnosis_summary')
    readonly_fields = ('upload_date',)
    
    def has_diagnosis(self, obj):
        return bool(obj.diagnosis_summary)
    has_diagnosis.boolean = True
    has_diagnosis.short_description = 'Has Diagnosis'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user',)
        }),
        ('Images', {
            'fields': ('uploaded_image', 'predicted_mask')
        }),
        ('Analysis Results', {
            'fields': ('diagnosis_summary', 'model_confidence', 'upload_date')
        }),
    )