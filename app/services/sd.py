import base64
import os
import re
import subprocess
import requests
from typing import List
from PIL import Image, ImageDraw
from loguru import logger

from app.models.schema import VideoAspect
from app.utils import utils
from app.config import config

def parse_srt(subtitle_path: str) -> list:
    """
    Parses a SRT file and returns a list of segments: (index, start_seconds, end_seconds, text)
    """
    segments = []
    if not os.path.exists(subtitle_path):
        logger.error(f"SRT file not found: {subtitle_path}")
        return segments
        
    with open(subtitle_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        
    # Split by empty lines
    blocks = re.split(r'\n\s*\n', content)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if len(lines) >= 3:
            try:
                idx = int(lines[0].strip())
                time_line = lines[1].strip()
                text = " ".join([l.strip() for l in lines[2:]])
                
                # Parse times: 00:00:01,000 --> 00:00:04,500
                times = time_line.split("-->")
                if len(times) == 2:
                    start_str = times[0].strip().replace(",", ".")
                    end_str = times[1].strip().replace(",", ".")
                    
                    def to_seconds(t_str):
                        parts = t_str.split(":")
                        h = float(parts[0])
                        m = float(parts[1])
                        s = float(parts[2])
                        return h * 3600 + m * 60 + s
                        
                    start_sec = to_seconds(start_str)
                    end_sec = to_seconds(end_str)
                    segments.append((idx, start_sec, end_sec, text))
            except Exception as e:
                logger.error(f"failed to parse srt block: {block} => {str(e)}")
    return segments

def generate_fallback_image(text: str, width: int, height: int, output_path: str):
    """
    Generates a cute cartoon Burmese cat explaining beer procedurally when A1111 is offline.
    """
    try:
        # Create a nice warm cozy background
        img = Image.new("RGB", (width, height), color=(245, 235, 220)) # Light cream/beige
        draw = ImageDraw.Draw(img)
        
        # Draw a cute Burmese cat!
        # Burmese cats are a rich warm brown (Sable / chocolate)
        sable_color = (93, 64, 55) # Hex #5D4037
        dark_sable = (62, 39, 35) # Hex #3E2723
        eye_color = (255, 214, 0) # Rich gold/yellow eyes
        pink_nose = (240, 98, 146) # Soft pink
        
        # Center coordinates for head
        cx = width // 2
        cy = height // 2 - 100
        r = 120 # Head radius
        
        # Ears (triangles)
        # Left ear
        draw.polygon([(cx - r + 10, cy - r + 40), (cx - r - 20, cy - r - 60), (cx - r + 90, cy - r + 10)], fill=dark_sable)
        # Right ear
        draw.polygon([(cx + r - 10, cy - r + 40), (cx + r + 20, cy - r - 60), (cx + r - 90, cy - r + 10)], fill=dark_sable)
        
        # Ear inner (pinkish)
        draw.polygon([(cx - r + 25, cy - r + 30), (cx - r - 5, cy - r - 35), (cx - r + 70, cy - r + 15)], fill=(255, 205, 210))
        draw.polygon([(cx + r - 25, cy - r + 30), (cx + r + 5, cy - r - 35), (cx + r - 70, cy - r + 15)], fill=(255, 205, 210))
        
        # Face/Head (circle)
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=sable_color)
        
        # Cheeks (snout overlay - slightly lighter brown)
        draw.ellipse([(cx - 60, cy + 10), (cx, cy + 70)], fill=(111, 78, 67))
        draw.ellipse([(cx, cy + 10), (cx + 60, cy + 70)], fill=(111, 78, 67))
        
        # Eyes (golden circles)
        eye_r = 30
        # Left eye
        draw.ellipse([(cx - 65 - eye_r, cy - 20 - eye_r), (cx - 65 + eye_r, cy - 20 + eye_r)], fill=eye_color, outline=dark_sable, width=3)
        # Right eye
        draw.ellipse([(cx + 65 - eye_r, cy - 20 - eye_r), (cx + 65 + eye_r, cy - 20 + eye_r)], fill=eye_color, outline=dark_sable, width=3)
        
        # Pupils (slits or black circles)
        draw.ellipse([(cx - 65 - 10, cy - 20 - 15), (cx - 65 + 10, cy - 20 + 15)], fill=(10, 10, 10))
        draw.ellipse([(cx + 65 - 10, cy - 20 - 15), (cx + 65 + 10, cy - 20 + 15)], fill=(10, 10, 10))
        # Eye shines
        draw.ellipse([(cx - 65 - 8, cy - 20 - 8), (cx - 65 + 2, cy - 20 + 2)], fill=(255, 255, 255))
        draw.ellipse([(cx + 65 - 8, cy - 20 - 8), (cx + 65 + 2, cy - 20 + 2)], fill=(255, 255, 255))
        
        # Nose (pink triangle)
        draw.polygon([(cx - 15, cy + 20), (cx + 15, cy + 20), (cx, cy + 35)], fill=pink_nose)
        
        # Mouth
        draw.arc([(cx - 30, cy + 30), (cx, cy + 50)], start=0, end=180, fill=dark_sable, width=3)
        draw.arc([(cx, cy + 30), (cx + 30, cy + 50)], start=0, end=180, fill=dark_sable, width=3)
        
        # Whiskers
        # Left whiskers
        draw.line([(cx - 70, cy + 35), (cx - 140, cy + 25)], fill=dark_sable, width=2)
        draw.line([(cx - 70, cy + 45), (cx - 150, cy + 45)], fill=dark_sable, width=2)
        draw.line([(cx - 70, cy + 55), (cx - 135, cy + 65)], fill=dark_sable, width=2)
        # Right whiskers
        draw.line([(cx + 70, cy + 35), (cx + 140, cy + 25)], fill=dark_sable, width=2)
        draw.line([(cx + 70, cy + 45), (cx + 150, cy + 45)], fill=dark_sable, width=2)
        draw.line([(cx + 70, cy + 55), (cx + 135, cy + 65)], fill=dark_sable, width=2)
        
        # Draw a little beer mug next to the cat!
        # Mug body
        draw.rectangle([(cx - 50, cy + 120), (cx + 50, cy + 220)], fill=(255, 193, 7)) # Gold beer
        # Mug handle
        draw.arc([(cx + 30, cy + 140), (cx + 70, cy + 200)], start=270, end=90, fill=(255, 193, 7), width=8)
        # Foam on top
        draw.ellipse([(cx - 60, cy + 100), (cx - 20, cy + 130)], fill=(255, 255, 255))
        draw.ellipse([(cx - 30, cy + 95), (cx + 10, cy + 125)], fill=(255, 255, 255))
        draw.ellipse([(cx, cy + 95), (cx + 40, cy + 125)], fill=(255, 255, 255))
        draw.ellipse([(cx + 20, cy + 100), (cx + 60, cy + 130)], fill=(255, 255, 255))
        
        # Write text nicely wrapped at the bottom
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 36)
        except Exception:
            font = None
            
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            if len(" ".join(current_line + [word])) <= 25:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        text_y = cy + 260
        for line in lines[:4]: # Max 4 lines
            draw.text((cx, text_y), line, fill=(62, 39, 35), anchor="mm", font=font)
            text_y += 50
            
        img.save(output_path)
        logger.success(f"Beautiful Burmese Cat fallback image saved to: {output_path}")
    except Exception as e:
        logger.error(f"failed to generate fallback image: {str(e)}")
        # Ultimate fallback - write empty file or simple solid color
        img = Image.new("RGB", (width, height), color=(0, 0, 0))
        img.save(output_path)

def set_sd_model(model_name: str) -> bool:
    """
    Sets the active Stable Diffusion checkpoint model via the Options API.
    """
    url = config.app.get("sd_api_url", "http://127.0.0.1:7860").strip()
    if url.endswith("/"):
        url = url[:-1]
    
    # Refresh checkpoints first so SD scans the directory for the new file
    try:
        requests.post(f"{url}/sdapi/v1/refresh-checkpoints", timeout=30)
    except Exception as e:
        logger.warning(f"Failed to refresh SD checkpoints: {str(e)}")
        
    api_endpoint = f"{url}/sdapi/v1/options"
    payload = {
        "sd_model_checkpoint": model_name
    }
    try:
        logger.info(f"Setting SD checkpoint model to: {model_name}")
        response = requests.post(api_endpoint, json=payload, timeout=30)
        if response.status_code == 200:
            logger.success(f"Successfully set SD checkpoint model to {model_name}")
            return True
        logger.warning(f"Failed to set SD checkpoint model, status code {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to communicate with SD Options API: {str(e)}")
    return False

def generate_sd_image(prompt: str, aspect: VideoAspect, output_path: str) -> bool:
    """
    Sends a txt2img request to local Stable Diffusion API and saves the image.
    """
    url = config.app.get("sd_api_url", "http://127.0.0.1:7860").strip()
    if url.endswith("/"):
        url = url[:-1]
    
    api_endpoint = f"{url}/sdapi/v1/txt2img"
    
    # Resolve dimensions
    video_width, video_height = aspect.to_resolution()
    
    # Scale down for SD 1.5 performance and formatting (keeps the aspect ratio)
    if video_width > video_height: # Landscape 16:9
        sd_width = 768
        sd_height = 432
    else: # Portrait 9:16
        sd_width = 432
        sd_height = 768
        
    prefix = config.app.get("sd_prompt_prefix", "").strip()
    suffix = config.app.get("sd_prompt_suffix", "").strip()
    
    full_prompt = prompt
    if prefix:
        full_prompt = f"{prefix}, {full_prompt}"
    if suffix:
        full_prompt = f"{full_prompt}, {suffix}"
    else:
        if not prefix and not suffix:
            full_prompt = f"{full_prompt}, high quality, detailed, photorealistic, highly detailed"
            
    steps = config.app.get("sd_steps", 20)
    cfg_scale = config.app.get("sd_cfg_scale", 7.5)
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": config.app.get("sd_negative_prompt", "nsfw, ugly, deformed, blurry, low quality, bad anatomy, text, watermark, signature"),
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": sd_width,
        "height": sd_height,
        "batch_size": 1
    }
    
    sampler_name = config.app.get("sd_sampler_name", "").strip()
    if sampler_name:
        payload["sampler_name"] = sampler_name
        
    animatediff_enabled = config.app.get("sd_animatediff_enabled", False)
    if animatediff_enabled:
        if "sd_steps" not in config.app:
            payload["steps"] = 16  # Reduce steps slightly for speed with AnimateDiff
        payload["alwayson_scripts"] = {
            "AnimateDiff": {
                "args": [
                    {
                        "enable": True,
                        "model": config.app.get("sd_animatediff_model", "mm_sd_v15_v2.ckpt"),
                        "video_length": config.app.get("sd_animatediff_video_length", 16),
                        "fps": config.app.get("sd_animatediff_fps", 8),
                        "format": ["GIF"],
                        "loop_number": 0,
                        "closed_loop": "R-P"
                    }
                ]
            }
        }
        
    adetailer_enabled = config.app.get("sd_adetailer_enabled", False)
    if adetailer_enabled:
        payload.setdefault("alwayson_scripts", {})
        payload["alwayson_scripts"]["ADetailer"] = {
            "args": [
                True,
                {
                    "ad_model": config.app.get("sd_adetailer_model", "face_yolov8n.pt"),
                    "ad_prompt": config.app.get("sd_adetailer_prompt", "cute cartoon cat eyes, detailed whiskers, soft rendering"),
                    "ad_denoising_strength": config.app.get("sd_adetailer_denoising_strength", 0.35)
                }
            ]
        }
    
    try:
        logger.info(f"sending txt2img prompt to SD: '{full_prompt}'")
        # Increase timeout for heavy AnimateDiff video generation requests
        timeout = 600 if animatediff_enabled else 90
        response = requests.post(api_endpoint, json=payload, timeout=timeout)
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                image_data = base64.b64decode(images[0])
                with open(output_path, "wb") as f:
                    f.write(image_data)
                logger.success(f"SD file saved to: {output_path}")
                return True
        logger.warning(f"SD API returned status code {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"failed to communicate with Stable Diffusion API: {str(e)}")
        
    return False

def generate_videos_from_subtitles(
    task_id: str,
    subtitle_path: str,
    video_aspect: VideoAspect,
    max_clip_duration: int = 5
) -> List[str]:
    """
    Parses the subtitle file, generates images or videos for each segment via Stable Diffusion,
    converts them to video clips matching each segment's duration, and returns the video paths.
    """
    video_paths = []
    segments = parse_srt(subtitle_path)
    if not segments:
        logger.error("No subtitle segments found. Cannot generate SD videos.")
        return video_paths
        
    task_dir = utils.task_dir(task_id)
    cache_dir = os.path.join(task_dir, "sd_materials")
    os.makedirs(cache_dir, exist_ok=True)
    
    video_width, video_height = video_aspect.to_resolution()
    ffmpeg_binary = utils.get_ffmpeg_binary()
    animatediff_enabled = config.app.get("sd_animatediff_enabled", False)
    
    # Configure model checkpoint if requested
    model_name = config.app.get("sd_model_checkpoint", "").strip()
    if model_name:
        set_sd_model(model_name)
    
    for idx, start_sec, end_sec, text in segments:
        duration = max(end_sec - start_sec, 0.5)
        logger.info(f"processing segment {idx}: duration={duration:.2f}s, text='{text}'")
        
        ext = "gif" if animatediff_enabled else "png"
        image_path = os.path.join(cache_dir, f"img_{idx}.{ext}")
        video_path = os.path.join(cache_dir, f"vid_{idx}.mp4")
        
        # 1. Generate SD image/video (or fallback)
        success = generate_sd_image(text, video_aspect, image_path)
        if not success:
            logger.warning(f"using fallback image placeholder for segment {idx}")
            # Generate static fallback image
            static_image_path = os.path.join(cache_dir, f"img_{idx}.png")
            generate_fallback_image(text, 512, 512, static_image_path)
            image_path = static_image_path
            segment_animated = False
        else:
            segment_animated = animatediff_enabled
            
        # 2. Convert image/GIF to video clip of exact segment duration
        if segment_animated:
            # Loop the animated GIF
            cmd = [
                ffmpeg_binary, "-y",
                "-ignore_loop", "0",
                "-i", image_path,
                "-c:v", "libx264",
                "-t", f"{duration:.3f}",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                "-vf", f"scale={video_width}:{video_height}",
                video_path
            ]
        else:
            # Loop the static image
            cmd = [
                ffmpeg_binary, "-y",
                "-loop", "1",
                "-i", image_path,
                "-c:v", "libx264",
                "-t", f"{duration:.3f}",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                "-vf", f"scale={video_width}:{video_height}",
                video_path
            ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0 and os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                logger.success(f"segment video clip generated: {video_path}")
                video_paths.append(video_path)
            else:
                logger.error(f"failed to convert image to video using ffmpeg: {result.stderr}")
        except Exception as e:
            logger.error(f"ffmpeg exception: {str(e)}")
            
    return video_paths
