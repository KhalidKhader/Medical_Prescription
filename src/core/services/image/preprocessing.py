"""
Image preprocessing service for handwritten prescription enhancement.
Provides image quality improvement for better OCR and vision processing.
"""

import base64
import io
from typing import Dict, Any
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from src.core.settings.logging import logger


class PrescriptionImagePreprocessor:
    """Service for preprocessing prescription images to improve OCR accuracy"""
    
    def __init__(self):
        self.max_dimension = 2048  # Maximum width or height
        
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
            
            # Apply preprocessing based on enhancement level
            processed_image = self._apply_enhancements(image, enhancement_level)
            
            # Convert back to base64
            processed_base64 = self._image_to_base64(processed_image)
            
            return {
                "processed_image_base64": processed_base64,
                "processing_metadata": {
                    "original_size": image.size,
                    "processed_size": processed_image.size,
                    "enhancement_level": enhancement_level,
                    "processing_success": True
                }
            }
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            return {
                "processed_image_base64": image_base64,  # Return original on failure
                "processing_metadata": {
                    "processing_success": False,
                    "error": str(e)
                }
            }
    
    def _apply_enhancements(
        self, 
        image: Image.Image, 
        enhancement_level: str
    ) -> Image.Image:
        """
        Apply image enhancements based on level.
        
        Args:
            image: Original image
            enhancement_level: Enhancement level
            
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
            enhanced = self._apply_minimal_enhancements(enhanced)
        elif enhancement_level == "standard":
            enhanced = self._apply_standard_enhancements(enhanced)
        elif enhancement_level == "aggressive":
            enhanced = self._apply_aggressive_enhancements(enhanced)
        
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
    
    def _apply_minimal_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply minimal enhancements"""
        # Basic contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.1)
    
    def _apply_standard_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply standard enhancements for typical prescription images"""
        enhanced = image
        
        # Contrast enhancement
        contrast_enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = contrast_enhancer.enhance(1.2)
        
        # Sharpness enhancement for text clarity
        sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = sharpness_enhancer.enhance(1.1)
        
        return enhanced
    
    def _apply_aggressive_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply aggressive enhancements for poor quality images"""
        enhanced = image
        
        # Strong contrast enhancement
        contrast_enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = contrast_enhancer.enhance(1.4)
        
        # Strong sharpness enhancement
        sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = sharpness_enhancer.enhance(1.3)
        
        # Noise reduction
        enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
        
        return enhanced
    
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


# Global preprocessor instance
image_preprocessor = PrescriptionImagePreprocessor()
