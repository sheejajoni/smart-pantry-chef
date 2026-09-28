import asyncio
import os
import shutil
from playwright.async_api import async_playwright
from google.cloud import storage

GCP_PROJECT_ID = "qwiklabs-gcp-02-07cb7cdcf8d2"
MEDIA_BUCKET_NAME = "smart-pantry-chef-media-07cb7cdcf8d2"
ARTIFACT_DIR = "/config/.gemini/antigravity/brain/ed67182c-c7b4-4c2f-bd80-20f985026480"

async def record():
    os.makedirs("/tmp/demo_video", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir="/tmp/demo_video",
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print("Navigating to http://localhost:8080...")
        await page.goto("http://localhost:8080")
        await page.wait_for_selector("#input")
        await asyncio.sleep(2)

        # 1. First prompt: What the app does best (Pantry recipe recommendations & DB lookup)
        prompt1 = "What delicious, healthy recipes can I cook right now using my pantry ingredients?"
        print(f"Typing prompt 1: {prompt1}")
        await page.fill("#input", prompt1)
        await asyncio.sleep(1)
        await page.press("#input", "Enter")

        # Wait for agent response to prompt 1
        print("Waiting for agent response to prompt 1...")
        await page.wait_for_selector(".msg.agent", timeout=60000)
        await asyncio.sleep(6)

        # 2. Second, richer prompt: Tool call + Image Generation
        prompt2 = "Generate an appetizing food photograph for a Low-Glycemic Wild Salmon & Avocado Salad"
        print(f"Typing prompt 2: {prompt2}")
        await page.fill("#input", prompt2)
        await asyncio.sleep(1)
        await page.press("#input", "Enter")

        # Wait for second bot response
        print("Waiting for agent response to prompt 2...")
        await page.wait_for_function("document.querySelectorAll('.msg.agent').length >= 2", timeout=90000)
        await asyncio.sleep(8)

        # Toggle dark mode to demonstrate theme switcher
        print("Toggling dark mode...")
        theme_btn = await page.query_selector(".theme-toggle-btn")
        if theme_btn:
            await theme_btn.click()
            await asyncio.sleep(3)

        video_path = await page.video.path()
        await context.close()
        await browser.close()
        print(f"Raw video saved at: {video_path}")

        # Save to artifact directory
        target_video = os.path.join(ARTIFACT_DIR, "demo_walkthrough.webm")
        shutil.copy(video_path, target_video)
        print(f"Copied demo video to artifact path: {target_video}")

        # Upload to public Cloud Storage bucket as well
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(MEDIA_BUCKET_NAME)
        blob = bucket.blob("demo_walkthrough.webm")
        with open(target_video, "rb") as f:
            blob.upload_from_file(f, content_type="video/webm")
        public_url = f"https://storage.googleapis.com/{MEDIA_BUCKET_NAME}/demo_walkthrough.webm"
        print(f"Uploaded public demo video URL: {public_url}")

if __name__ == "__main__":
    asyncio.run(record())
