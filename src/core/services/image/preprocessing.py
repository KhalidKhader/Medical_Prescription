"""
Image preprocessing service for handwritten prescription enhancement.
Provides image quality improvement for better OCR and vision processing.
"""

import base64
import io
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
from langfuse import observe
from src.core.settings.config import settings
from src.core.settings.logging import logger


class PrescriptionImagePreprocessor:
    """Service for preprocessing prescription images to improve OCR accuracy"""
    
    def __init__(self):
        self.supported_formats = {'JPEG', 'PNG', 'TIFF', 'BMP', 'WEBP'}
        self.max_dimension = 2048  # Maximum width or height
        self.quality_threshold = 0.7  # Minimum quality score
        
    @observe(name="image_preprocessing", as_type="generation", capture_input=True, capture_output=True)
    def preprocess_prescription_image(
        self, 
        image_base64: str,
        enhancement_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Preprocess prescription image for better OCR and vision processing.
        
        Args:
            image_base64: Base64 encoded image
            enhancement_level: "minimal", "standard", or "aggressive"
            
        Returns:
            Dictionary containing processed image and metadata
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            logger.info(f"Processing image: {image.format}, {image.size}, {image.mode}")
            
            # Store original metadata
            original_metadata = {
                "format": image.format,
                "size": image.size,
                "mode": image.mode,
                "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            # Quality assessment
            quality_score = self._assess_image_quality(image)
            
            # Apply preprocessing based on enhancement level
            processed_image = self._apply_enhancements(image, enhancement_level, quality_score)
            
            # Convert back to base64
            processed_base64 = self._image_to_base64(processed_image)
            
            # Generate processing metadata
            processing_metadata = {
                "original_metadata": original_metadata,
                "processed_size": processed_image.size,
                "processed_mode": processed_image.mode,
                "quality_score": quality_score,
                "enhancement_level": enhancement_level,
                "enhancements_applied": self._get_applied_enhancements(enhancement_level, quality_score),
                "size_reduction_ratio": len(processed_base64) / len(image_base64),
                "processing_success": True
            }
            
            return {
                "processed_image_base64": processed_base64,
                "processing_metadata": processing_metadata,
                "quality_improved": quality_score < self.quality_threshold
            }
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            return {
                "processed_image_base64": image_base64,  # Return original on failure
                "processing_metadata": {
                    "processing_success": False,
                    "error": str(e),
                    "enhancement_level": enhancement_level
                },
                "quality_improved": False
            }
    
    def _assess_image_quality(self, image: Image.Image) -> float:
        """
        Assess image quality for prescription processing.
        
        Args:
            image: PIL Image object
            
        Returns:
            Quality score between 0 and 1 (higher is better)
        """
        quality_factors = []
        
        # Resolution assessment
        width, height = image.size
        total_pixels = width * height
        
        # Higher resolution generally better for OCR
        resolution_score = min(total_pixels / (1024 * 768), 1.0)  # Normalize to 1024x768
        quality_factors.append(resolution_score * 0.3)
        
        # Aspect ratio assessment (prescriptions are usually rectangular)
        aspect_ratio = max(width, height) / min(width, height)
        aspect_score = 1.0 if 1.2 <= aspect_ratio <= 2.0 else 0.7
        quality_factors.append(aspect_score * 0.2)
        
        # Color mode assessment
        mode_score = 1.0 if image.mode in ('RGB', 'L') else 0.8
        quality_factors.append(mode_score * 0.1)
        
        # Brightness and contrast assessment
        if image.mode != 'L':
            grayscale = image.convert('L')
        else:
            grayscale = image
        
        # Calculate histogram for brightness distribution
        histogram = grayscale.histogram()
        
        # Good contrast means values spread across the range
        contrast_score = self._calculate_contrast_score(histogram)
        quality_factors.append(contrast_score * 0.4)
        
        return sum(quality_factors)
    
    def _calculate_contrast_score(self, histogram: list) -> float:
        """Calculate contrast score from histogram"""
        total_pixels = sum(histogram)
        if total_pixels == 0:
            return 0.0
        
        # Calculate standard deviation of pixel intensities
        mean_intensity = sum(i * count for i, count in enumerate(histogram)) / total_pixels
        variance = sum(count * (i - mean_intensity) ** 2 for i, count in enumerate(histogram)) / total_pixels
        std_dev = variance ** 0.5
        
        # Normalize standard deviation to 0-1 range
        return min(std_dev / 64.0, 1.0)  # 64 is good contrast threshold
    
    def _apply_enhancements(
        self, 
        image: Image.Image, 
        enhancement_level: str, 
        quality_score: float
    ) -> Image.Image:
        """
        Apply image enhancements based on level and quality assessment.
        
        Args:
            image: Original image
            enhancement_level: Enhancement level
            quality_score: Current quality score
            
        Returns:
            Enhanced image
        """
        enhanced = image.copy()
        
        # Convert to RGB if needed (for consistent processing)
        if enhanced.mode not in ('RGB', 'L'):
            enhanced = enhanced.convert('RGB')
        
        # Resize if too large
        enhanced = self._resize_if_needed(enhanced)
        
        # Apply enhancements based on level
        if enhancement_level == "minimal":
            enhanced = self._apply_minimal_enhancements(enhanced, quality_score)
        elif enhancement_level == "standard":
            enhanced = self._apply_standard_enhancements(enhanced, quality_score)
        elif enhancement_level == "aggressive":
            enhanced = self._apply_aggressive_enhancements(enhanced, quality_score)
        
        return enhanced
    
    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """Resize image if dimensions exceed maximum"""
        width, height = image.size
        
        if width <= self.max_dimension and height <= self.max_dimension:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * self.max_dimension / width)
        else:
            new_height = self.max_dimension
            new_width = int(width * self.max_dimension / height)
        
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized image from {image.size} to {resized.size}")
        
        return resized
    
    def _apply_minimal_enhancements(self, image: Image.Image, quality_score: float) -> Image.Image:
        """Apply minimal enhancements - only if quality is very poor"""
        if quality_score < 0.5:
            # Only basic contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
        
        return image
    
    def _apply_standard_enhancements(self, image: Image.Image, quality_score: float) -> Image.Image:
        """Apply standard enhancements for typical prescription images"""
        enhanced = image
        
        # Contrast enhancement
        if quality_score < 0.7:
            contrast_enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = contrast_enhancer.enhance(1.3)
        
        # Brightness adjustment
        if quality_score < 0.6:
            brightness_enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = brightness_enhancer.enhance(1.1)
        
        # Sharpness enhancement for text clarity
        if quality_score < 0.8:
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.2)
        
        # Noise reduction
        if quality_score < 0.6:
            enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
        
        return enhanced
    
    def _apply_aggressive_enhancements(self, image: Image.Image, quality_score: float) -> Image.Image:
        """Apply aggressive enhancements for poor quality images"""
        enhanced = image
        
        # Strong contrast enhancement
        contrast_enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = contrast_enhancer.enhance(1.5)
        
        # Brightness adjustment
        brightness_enhancer = ImageEnhance.Brightness(enhanced)
        enhanced = brightness_enhancer.enhance(1.2)
        
        # Strong sharpness enhancement
        sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = sharpness_enhancer.enhance(1.5)
        
        # Advanced noise reduction
        enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
        enhanced = enhanced.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Auto-level adjustment
        enhanced = ImageOps.autocontrast(enhanced, cutoff=2)
        
        return enhanced
    
    def _get_applied_enhancements(self, enhancement_level: str, quality_score: float) -> list:
        """Get list of enhancements that were applied"""
        enhancements = []
        
        if enhancement_level == "minimal":
            if quality_score < 0.5:
                enhancements.append("basic_contrast")
        
        elif enhancement_level == "standard":
            if quality_score < 0.7:
                enhancements.append("contrast_enhancement")
            if quality_score < 0.6:
                enhancements.extend(["brightness_adjustment", "noise_reduction"])
            if quality_score < 0.8:
                enhancements.append("sharpness_enhancement")
        
        elif enhancement_level == "aggressive":
            enhancements.extend([
                "strong_contrast", "brightness_adjustment", "strong_sharpness",
                "advanced_noise_reduction", "auto_level"
            ])
        
        return enhancements
    
    def _image_to_base64(self, image: Image.Image, format: str = 'JPEG', quality: int = 90) -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        
        # Convert RGBA to RGB for JPEG
        if image.mode == 'RGBA' and format == 'JPEG':
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
            image = background
        
        image.save(buffer, format=format, quality=quality, optimize=True)
        image_data = buffer.getvalue()
        
        return base64.b64encode(image_data).decode('utf-8')
    
    def validate_image(self, image_base64: str) -> Dict[str, Any]:
        """
        Validate prescription image for processing.
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            Validation results
        """
        try:
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            validation_results = {
                "is_valid": True,
                "format": image.format,
                "size": image.size,
                "mode": image.mode,
                "file_size_mb": len(image_data) / (1024 * 1024),
                "quality_score": self._assess_image_quality(image),
                "recommendations": []
            }
            
            # Add recommendations based on assessment
            if validation_results["file_size_mb"] > settings.max_image_size_mb:
                validation_results["recommendations"].append(
                    f"Image size ({validation_results['file_size_mb']:.1f}MB) exceeds maximum ({settings.max_image_size_mb}MB)"
                )
            
            if validation_results["quality_score"] < self.quality_threshold:
                validation_results["recommendations"].append(
                    "Image quality is below optimal threshold - consider using 'standard' or 'aggressive' enhancement"
                )
            
            width, height = image.size
            if width < 800 or height < 600:
                validation_results["recommendations"].append(
                    "Image resolution is low - may affect OCR accuracy"
                )
            
            if image.format not in self.supported_formats:
                validation_results["recommendations"].append(
                    f"Image format {image.format} may not be optimal - consider JPEG or PNG"
                )
            
            return validation_results
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "recommendations": ["Unable to process image - check format and encoding"]
            }


# Global preprocessor instance
image_preprocessor = PrescriptionImagePreprocessor()
