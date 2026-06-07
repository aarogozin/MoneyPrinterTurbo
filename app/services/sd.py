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
    Generates a fallback colored placeholder image when A1111 is offline.
    """
    try:
        # Create a nice dark background
        img = Image.new("RGB", (width, height), color=(33, 37, 41))
        draw = ImageDraw.Draw(img)
        # Draw some decorative text
        draw.text((20, height // 2 - 20), f"[AI Image Fallback]\n{text[:40]}...", fill=(200, 200, 200))
        img.save(output_path)
    except Exception as e:
        logger.error(f"failed to generate fallback image: {str(e)}")
        # Ultimate fallback - write empty file or simple solid color
        img = Image.new("RGB", (width, height), color=(0, 0, 0))
        img.save(output_path)

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
        
    payload = {
        "prompt": f"{prompt}, high quality, detailed, photorealistic, highly detailed",
        "negative_prompt": "nsfw, ugly, deformed, blurry, low quality, bad anatomy, text, watermark, signature",
        "steps": 20,
        "cfg_scale": 7.5,
        "width": sd_width,
        "height": sd_height,
        "batch_size": 1
    }
    
    try:
        logger.info(f"sending txt2img prompt to SD: '{prompt}'")
        response = requests.post(api_endpoint, json=payload, timeout=90)
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                image_data = base64.b64decode(images[0])
                with open(output_path, "wb") as f:
                    f.write(image_data)
                logger.success(f"SD image saved to: {output_path}")
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
    Parses the subtitle file, generates images for each segment via Stable Diffusion,
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
    
    for idx, start_sec, end_sec, text in segments:
        duration = max(end_sec - start_sec, 0.5)
        logger.info(f"processing segment {idx}: duration={duration:.2f}s, text='{text}'")
        
        image_path = os.path.join(cache_dir, f"img_{idx}.png")
        video_path = os.path.join(cache_dir, f"vid_{idx}.mp4")
        
        # 1. Generate SD image (or fallback)
        success = generate_sd_image(text, video_aspect, image_path)
        if not success:
            logger.warning(f"using fallback image placeholder for segment {idx}")
            generate_fallback_image(text, 512, 512, image_path)
            
        # 2. Convert image to video clip of exact segment duration
        # command: ffmpeg -y -loop 1 -i image.png -c:v libx264 -t duration -pix_fmt yuv420p -r 25 -vf scale=width:height video.mp4
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
