import os
from django.conf import settings

# NOTE: Heavy ML dependencies (torch, torchvision) are imported lazily inside
# the functions that need them. This keeps the web app (auth, dashboard,
# history, etc.) working even if the ML stack isn't installed — only the actual
# scan-processing step requires it.

FILTERS = [16, 32, 64, 128, 256]

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "saved_models",
    "UNet-[16, 32, 64, 128, 256].pt"
)

_model = None  # lazy-loaded model


# =====================================================
# 2. Load model safely (only once)
# =====================================================

def get_device():
    """Return the torch device (CUDA if available, else CPU)."""
    import torch
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_model():
    """
    Loads the UNet model only once and reuses it.
    """
    global _model

    if _model is None:
        import torch
        from bts.model import DynamicUNet

        device = get_device()
        model = DynamicUNet(FILTERS).to(device)
        model.load_state_dict(
            torch.load(MODEL_PATH, map_location=device)
        )
        model.eval()
        _model = model
        print(f"[INFO] UNet model loaded on {device}")

    return _model


# =====================================================
# 3. Image preprocessing
# =====================================================

def preprocess_image(image_path):
    """
    Load and preprocess MRI image.
    """
    import torchvision.transforms as transforms
    import torchvision.transforms.functional as TF
    from PIL import Image

    transform = transforms.Compose([
        transforms.Grayscale(),
        transforms.Resize((512, 512))
    ])

    image = Image.open(image_path)
    image = transform(image)

    tensor = TF.to_tensor(image)
    tensor = tensor.unsqueeze(0).to(get_device())  # (1, 1, 512, 512)

    return tensor


# =====================================================
# 4. Run segmentation
# =====================================================

def run_segmentation(image_path, report_id):
    """
    Runs UNet segmentation and saves output mask.
    Returns relative path of saved mask.
    """
    import torch
    import numpy as np
    from PIL import Image

    model = get_model()
    image_tensor = preprocess_image(image_path)

    with torch.no_grad():
        output = model(image_tensor)
        output = output.squeeze().cpu().numpy()

    # Binary mask
    mask = (output > 0.5).astype(np.uint8) * 255
    mask_image = Image.fromarray(mask, mode="L")

    # Save mask
    output_dir = os.path.join(settings.MEDIA_ROOT, "segmentation_masks")
    os.makedirs(output_dir, exist_ok=True)

    file_name = f"mask_{report_id}.png"
    full_path = os.path.join(output_dir, file_name)

    mask_image.save(full_path)

    # Return path relative to MEDIA_ROOT
    return os.path.join("segmentation_masks", file_name)


# =====================================================
# 5. Main entry function (called from views)
# =====================================================

def process_mri_scan(mri_report):
    """
    Main function called by Django view.
    Takes MRIReport instance, processes image,
    and updates database fields.
    """
    try:
        # Run AI segmentation
        mask_relative_path = run_segmentation(
            image_path=mri_report.uploaded_image.path,
            report_id=mri_report.id
        )

        # Update DB
        mri_report.predicted_mask.name = mask_relative_path
        mri_report.diagnosis_summary = (
            "The AI model detected abnormal regions in the MRI scan. "
            "Please consult a medical professional for confirmation."
        )
        mri_report.model_confidence = 0.87  # placeholder (can be improved)
        mri_report.save()

        print(f"[SUCCESS] MRI processed for report ID {mri_report.id}")
        return True

    except Exception as e:
        print(f"[ERROR] MRI processing failed: {e}")
        return False


# import os
# import random
# from PIL import Image, ImageDraw, ImageFilter
# from django.core.files.base import ContentFile
# from django.core.files.storage import default_storage
# import io


# def run_segmentation(uploaded_image):
#     """
#     Placeholder function for ML model integration.
    
#     This function should be replaced with your actual ML model implementation.
#     Currently returns a mock segmentation mask and confidence score.
    
#     Args:
#         uploaded_image: Django ImageField instance
        
#     Returns:
#         tuple: (segmented_mask_file, confidence_score)
#             - segmented_mask_file: Django File object containing the segmentation mask
#             - confidence_score: Float between 0 and 1 representing model confidence
#     """
    
#     try:
#         # Open the uploaded image
#         image = Image.open(uploaded_image.file)
        
#         # Create a mock segmentation mask
#         # In real implementation, this would be your ML model prediction
#         mask = create_mock_segmentation_mask(image)
        
#         # Generate a mock confidence score
#         confidence_score = round(random.uniform(0.75, 0.95), 3)
        
#         # Save mask to memory
#         mask_io = io.BytesIO()
#         mask.save(mask_io, format='PNG')
#         mask_io.seek(0)
        
#         # Create Django file object
#         mask_file = ContentFile(mask_io.read(), name=f'segmentation_mask_{uploaded_image.name.split(".")[0]}.png')
        
#         return mask_file, confidence_score
        
#     except Exception as e:
#         print(f"Error in segmentation: {e}")
#         return None, 0.0


# def create_mock_segmentation_mask(original_image):
#     """
#     Create a mock segmentation mask for demonstration purposes.
    
#     In real implementation, this would be replaced by your trained model.
#     """
#     # Convert to grayscale and resize if needed
#     width, height = original_image.size
    
#     # Create a new image for the mask
#     mask = Image.new('RGB', (width, height), color='black')
#     draw = ImageDraw.Draw(mask)
    
#     # Create some mock tumor regions (white areas)
#     # This simulates what a real segmentation model would output
    
#     # Mock tumor region 1
#     if width > 100 and height > 100:
#         x1, y1 = width // 3, height // 3
#         x2, y2 = x1 + width // 6, y1 + height // 8
#         draw.ellipse([x1, y1, x2, y2], fill='white')
        
#         # Mock tumor region 2 (smaller)
#         x3, y3 = width // 2, height // 2
#         x4, y4 = x3 + width // 12, y3 + height // 12
#         draw.ellipse([x3, y3, x4, y4], fill='white')
    
#     # Apply slight blur to make it look more realistic
#     mask = mask.filter(ImageFilter.GaussianBlur(radius=1))
    
#     return mask


# def generate_diagnosis_summary(confidence_score):
#     """
#     Generate a mock diagnosis summary based on confidence score.
    
#     In real implementation, this would be generated by your ML model
#     or medical AI system.
#     """
    
#     if confidence_score >= 0.9:
#         return """
#         High confidence detection of potential tumor regions. 
#         Multiple areas of abnormal tissue density identified in the brain scan. 
#         Recommend immediate consultation with a neurologist for further evaluation 
#         and additional imaging studies.
#         """
#     elif confidence_score >= 0.8:
#         return """
#         Moderate to high confidence detection of suspicious regions. 
#         Areas of interest identified that may require further investigation. 
#         Recommend follow-up imaging and clinical correlation.
#         """
#     elif confidence_score >= 0.7:
#         return """
#         Possible areas of concern detected with moderate confidence. 
#         Additional imaging or clinical evaluation may be warranted 
#         to rule out any abnormalities.
#         """
#     else:
#         return """
#         Low confidence results. The scan quality or positioning may affect 
#         the analysis accuracy. Consider retaking the scan with better 
#         positioning or consult with a medical professional.
#         """


# # Integration function that combines everything
# def process_mri_scan(mri_report):
#     """
#     Process the uploaded MRI scan and update the report with results.
    
#     Args:
#         mri_report: MRIReport model instance
        
#     Returns:
#         bool: True if processing was successful, False otherwise
#     """
#     try:
#         # Run segmentation
#         mask_file, confidence = run_segmentation(mri_report.uploaded_image)
        
#         if mask_file:
#             # Save the segmentation mask
#             mri_report.predicted_mask.save(
#                 mask_file.name,
#                 mask_file,
#                 save=False
#             )
            
#             # Set confidence score
#             mri_report.model_confidence = confidence
            
#             # Generate diagnosis summary
#             mri_report.diagnosis_summary = generate_diagnosis_summary(confidence)
            
#             # Save the updated report
#             mri_report.save()
            
#             return True
        
#         return False
        
#     except Exception as e:
#         print(f"Error processing MRI scan: {e}")
#         return False