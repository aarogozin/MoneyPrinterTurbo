import sys
import os
import uuid
import subprocess
from loguru import logger

# Add project root to path
sys.path.append("/Users/tonyr/git/moneyprinterturbo")

from app.config import config
from app.models.schema import VideoParams, VideoAspect
from app.services import task

def main():
    print("=== Launching Easy English Video Generation Pipeline ===")
    
    # 1. Configure oMLX and Stable Diffusion parameters programmatically
    config.app["llm_provider"] = "omlx"
    # API key is loaded automatically from config.toml (which is gitignored)
    config.app["omlx_model_name"] = "Qwen3.6-35B-A3B-UD-MLX-4bit"
    config.app["omlx_base_url"] = "http://127.0.0.1:8000/v1"
    
    # Enable Stable Diffusion and set Burmese Cat Pixar style prompt prefix
    config.app["video_source"] = "stable-diffusion"
    config.app["sd_prompt_prefix"] = "A masterpiece 3D cartoon Burmese cat character in Pixar style, Disney animation, highly detailed, cute expressive eyes, soft studio lighting, subsurface scattering, octane render, 8k, sharp focus"
    config.app["sd_negative_prompt"] = "nsfw, ugly, deformed, blurry, low quality, bad anatomy, text, watermark, signature, realistic, photographic, worst quality, low quality"
    config.app["sd_model_checkpoint"] = "DisneyPixar.safetensors"
    config.app["sd_steps"] = 24
    config.app["sd_cfg_scale"] = 8.0
    config.app["sd_sampler_name"] = "DPM++ 2M Karras"
    config.app["sd_adetailer_enabled"] = True
    config.app["sd_adetailer_model"] = "face_yolov8n.pt"
    config.app["sd_adetailer_prompt"] = "cute cartoon cat face, expressive eyes, detailed whiskers, soft rendering"
    config.app["sd_animatediff_enabled"] = True
    config.app["sd_animatediff_video_length"] = 16
    config.app["sd_animatediff_fps"] = 8

    
    # 2. Configure video parameters
    task_id = f"easy-english-{str(uuid.uuid4())[:8]}"
    params = VideoParams(
        video_subject="Easy English: A Burmese cat talks about beer.",
        video_language="en",
        video_aspect=VideoAspect.portrait.value, # Portrait 9:16 for smartphones
        video_source="stable-diffusion",
        voice_name="local:Samantha-en_US", # Local macOS Samantha voice for clear English
        subtitle_enabled=True,
        paragraph_number=2, # 2 paragraphs for ~30 seconds duration
        video_clip_duration=5,
        video_count=1
    )
    
    print(f"Task ID: {task_id}")
    print(f"Subject: {params.video_subject}")
    print(f"Voice: {params.voice_name}")
    print(f"Aspect Ratio: {params.video_aspect} (portrait)")
    
    # Run the generation pipeline
    try:
        result = task.start(task_id, params)
        if result:
            print("\n=== Video Generation Succeeded! ===")
            print(f"Generated Script:\n{result.get('script')}")
            print(f"Final Videos: {result.get('videos')}")
            
            # Open the output folder in Finder
            task_dir = os.path.abspath(os.path.join("/Users/tonyr/git/moneyprinterturbo/storage/tasks", task_id))
            print(f"Opening output folder: {task_dir}")
            subprocess.run(["open", task_dir], check=False)
        else:
            print("\n=== Video Generation Failed ===")
    except Exception as e:
        logger.exception(f"Error executing pipeline: {str(e)}")

if __name__ == "__main__":
    main()
