"""
Image processing module
"""
from PIL import Image
from pathlib import Path
from io import BytesIO
import base64


def load_and_preprocess_image(
    image_path: str,
    target_width: int,
    target_height: int
) -> bytes:
    """
    Load and preprocess image

    Args:
        image_path: Image path
        target_width: Target width
        target_height: Target height

    Returns:
        Preprocessed image bytes
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize image
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            # Save to byte stream
            buf = BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            return buf.read()

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return b""


def image_to_base64(image_bytes: bytes) -> str:
    """
    Convert image bytes to base64 string

    Args:
        image_bytes: Image bytes

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(image_bytes).decode("utf-8")


def get_image_info(image_path: str) -> dict:
    """
    Get basic image info

    Args:
        image_path: Image path

    Returns:
        Image info dict
    """
    try:
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format
            }
    except Exception as e:
        print(f"Error getting image info {image_path}: {e}")
        return {}