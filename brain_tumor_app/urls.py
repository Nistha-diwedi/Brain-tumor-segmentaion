from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_mri, name='upload_mri'),
    path('history/', views.medical_history, name='medical_history'),
    path('profile/', views.profile, name='profile'),
    
    # Authentication
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
    path('auth/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    
    # Report management
    path('report/<int:report_id>/', views.view_report, name='view_report'),
    path('report/<int:report_id>/delete/', views.delete_report, name='delete_report'),
    
    # AJAX endpoints
    path('api/upload/', views.upload_mri_ajax, name='upload_mri_ajax'),
    path('report/<int:report_id>/ai-analysis/',views.generate_ai_analysis_ajax,name='generate_ai_analysis_ajax'),


]