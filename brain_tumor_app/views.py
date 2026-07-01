from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .forms import CustomUserCreationForm, MRIUploadForm
from .models import MRIReport
from .ml_processing import process_mri_scan


def landing_page(request):
    """Landing page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'brain_tumor_app/landing.html')


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'brain_tumor_app/auth/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard')


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('landing')


class RegisterView(CreateView):
    """User registration view"""
    form_class = CustomUserCreationForm
    template_name = 'brain_tumor_app/auth/register.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f'Welcome {self.object.full_name or self.object.username}! Your account has been created successfully.')
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    """Dashboard view showing recent uploads and quick stats"""
    recent_reports = MRIReport.objects.filter(user=request.user)[:5]
    total_scans = MRIReport.objects.filter(user=request.user).count()
    
    # Calculate some basic stats
    processed_scans = MRIReport.objects.filter(
        user=request.user, 
        predicted_mask__isnull=False
    ).count()
    
    context = {
        'recent_reports': recent_reports,
        'total_scans': total_scans,
        'processed_scans': processed_scans,
        'upload_form': MRIUploadForm(),
    }
    return render(request, 'brain_tumor_app/dashboard.html', context)


@login_required
def upload_mri(request):
    """MRI upload page with drag and drop functionality"""
    if request.method == 'POST':
        form = MRIUploadForm(request.POST, request.FILES)
        if form.is_valid():
            mri_report = form.save(commit=False)
            mri_report.user = request.user
            mri_report.save()
            
            # Process the MRI scan asynchronously (in a real app, use Celery)
            # For now, we'll process it synchronously
            try:
                success = process_mri_scan(mri_report)
                if success:
                    messages.success(
                        request, 
                        'MRI scan uploaded and processed successfully! Check your results below.'
                    )
                    return redirect('view_report', report_id=mri_report.id)
                else:
                    messages.warning(
                        request, 
                        'MRI scan uploaded but processing failed. Please try again or contact support.'
                    )
            except Exception as e:
                messages.error(
                    request, 
                    'An error occurred during processing. Please try again.'
                )
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MRIUploadForm()
    
    return render(request, 'brain_tumor_app/upload_mri.html', {'form': form})


@login_required
def medical_history(request):
    """Medical history page showing all user's MRI reports (with filters)."""
    reports_list = MRIReport.objects.filter(user=request.user)

    # --- Filters (wired to the filter form on the page) ---
    search = request.GET.get('search', '').strip()
    date_filter = request.GET.get('date_filter', '')
    confidence_filter = request.GET.get('confidence_filter', '')

    if search:
        reports_list = reports_list.filter(diagnosis_summary__icontains=search)

    if date_filter:
        now = timezone.now()
        ranges = {
            'today': now - timedelta(days=1),
            'week': now - timedelta(days=7),
            'month': now - timedelta(days=30),
            'year': now - timedelta(days=365),
        }
        if date_filter in ranges:
            reports_list = reports_list.filter(upload_date__gte=ranges[date_filter])

    if confidence_filter == 'high':
        reports_list = reports_list.filter(model_confidence__gte=0.8)
    elif confidence_filter == 'medium':
        reports_list = reports_list.filter(model_confidence__gte=0.6, model_confidence__lt=0.8)
    elif confidence_filter == 'low':
        reports_list = reports_list.filter(model_confidence__lt=0.6)

    # Pagination
    paginator = Paginator(reports_list, 10)  # Show 10 reports per page
    page_number = request.GET.get('page')
    reports = paginator.get_page(page_number)

    context = {
        'reports': reports,
        'total_reports': reports_list.count(),
    }
    return render(request, 'brain_tumor_app/medical_history.html', context)


@login_required
def view_report(request, report_id):
    """View individual MRI report details"""
    report = get_object_or_404(MRIReport, id=report_id, user=request.user)
    
    context = {
        'report': report,
    }
    return render(request, 'brain_tumor_app/view_report.html', context)


@login_required
def delete_report(request, report_id):
    """Delete an MRI report"""
    report = get_object_or_404(MRIReport, id=report_id, user=request.user)
    
    if request.method == 'POST':
        # Delete associated files
        if report.uploaded_image:
            report.uploaded_image.delete()
        if report.predicted_mask:
            report.predicted_mask.delete()
        
        report.delete()
        messages.success(request, 'MRI report deleted successfully.')
        return redirect('medical_history')
    
    return render(request, 'brain_tumor_app/confirm_delete.html', {'report': report})


# API endpoint for AJAX file upload (for drag and drop)
@login_required
def upload_mri_ajax(request):
    """AJAX endpoint for MRI upload"""
    if request.method == 'POST':
        form = MRIUploadForm(request.POST, request.FILES)
        if form.is_valid():
            mri_report = form.save(commit=False)
            mri_report.user = request.user
            mri_report.save()
            
            # Process the scan
            try:
                success = process_mri_scan(mri_report)
                return JsonResponse({
                    'success': True,
                    'message': 'MRI scan uploaded and processed successfully!',
                    'report_id': mri_report.id,
                    'redirect_url': f'/report/{mri_report.id}/'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': 'Upload successful but processing failed. Please try again.'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file. Please upload a valid image file.',
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def profile(request):
    """User profile page"""
    reports = MRIReport.objects.filter(user=request.user)
    context = {
        'user': request.user,
        'total_scans': reports.count(),
        'processed_scans': reports.filter(predicted_mask__isnull=False).exclude(predicted_mask='').count(),
        'recent_reports': reports[:5],
    }
    return render(request, 'brain_tumor_app/profile.html', context)

from django.shortcuts import render
from django.conf import settings
import google.generativeai as genai
from django.views.decorators.http import require_POST

@login_required
@require_POST
def generate_ai_analysis_ajax(request, report_id):
    report = get_object_or_404(MRIReport, id=report_id, user=request.user)

    if not report.predicted_mask:
        return JsonResponse({
            "success": False,
            "text": "AI analysis is not available because segmentation has not been completed."
        })

    if not settings.GENERATIVE_API_KEY:
        return JsonResponse({
            "success": False,
            "text": "AI analysis is not configured. Please set GENERATIVE_API_KEY in your environment."
        })

    genai.configure(api_key=settings.GENERATIVE_API_KEY)

    generation_config = {
        "temperature": 0.3,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2060,
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config
    )

    prompt =  """
You are an AI medical assistant functioning as a clinical support system for brain MRI tumor segmentation analysis.

The MRI brain scan has already been processed using a deep learning–based segmentation model.
A segmentation mask identifying regions that differ from typical brain tissue is available.

Your task is to generate a SERIOUS, DETAILED, and CLINICALLY ORIENTED medical report
that explains the segmentation results in a manner similar to how a neurologist or radiologist
would explain findings to a patient during a consultation.

IMPORTANT WRITING RULES:
- Do NOT use markdown symbols, bullet points, asterisks, or decorative separators
- Use professional medical language, but keep it understandable for a patient
- Avoid sounding generic, promotional, or overly simplified
- Focus strongly on segmentation findings, not general MRI theory
- Do NOT give a final diagnosis or name any disease
- Do NOT say “this could be cancer” or similar statements
- Write with authority, clarity, and seriousness

Write the report using the following section titles as plain text:

AI Segmentation Analysis Report

Clinical Overview of the MRI Segmentation:
Explain that the MRI images were reviewed using an advanced segmentation model designed
to detect structural and signal-based differences within brain tissue.
Clarify that this analysis assists doctors by highlighting regions that visually differ
from expected healthy brain patterns.

Detailed Segmentation Findings:
Describe whether the segmentation model identified any abnormal or atypical regions.
Explain the findings in detail, including:
- The general location within the brain in non-technical terms
- Whether the segmented region appears localized or spread out
- The nature of its boundaries (well-defined, irregular, or diffuse)
- How the region visually contrasts with surrounding brain tissue
- The relative extent or size of the segmented area

Explain these findings as observations, not conclusions.

Clinical Interpretation of the Segmented Region:
Interpret what the segmentation highlights from a clinical perspective.
Explain that such regions indicate tissue characteristics that differ from surrounding areas
and therefore require expert medical review.
Discuss how doctors typically correlate segmentation findings with patient history,
symptoms, and additional imaging before reaching any conclusions.

Model Confidence and Analytical Strength:
Explain how the AI model identifies patterns based on extensive training on medical imaging data.
Clarify what model confidence represents in simple terms.
Emphasize that AI confidence reflects pattern recognition strength, not medical certainty.

Limitations of Segmentation-Based AI Analysis:
Explain limitations clearly and professionally, including:
- The AI does not assess symptoms, history, or laboratory results
- Segmentation highlights differences but does not determine cause
- Normal anatomical variations or non-significant changes may be highlighted
- Human medical expertise is essential for accurate interpretation

Recommended Clinical Next Steps:
Advise that the segmentation results should be reviewed by a qualified radiologist
or neurologist along with the original MRI images.
Encourage discussion with a healthcare professional who can correlate these findings
with clinical information and determine whether further evaluation or monitoring is required.

LENGTH REQUIREMENTS:
- Minimum length: 900–1200 words
- Each section must be detailed and explanatory
- Do NOT stop early or summarize briefly

End the report in a calm, professional, and reassuring medical tone,
similar to a real hospital consultation explanation.
"""

    try:
        response = model.generate_content(prompt)
        return JsonResponse({
            "success": True,
            "text": response.text
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "text": str(e)
        })
