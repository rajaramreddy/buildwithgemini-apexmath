import os
import time
import glob
import subprocess
from playwright.sync_api import sync_playwright

RECORDINGS_DIR = "/tmp/demo_recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# Clean up any old recordings
for f in glob.glob(f"{RECORDINGS_DIR}/*"):
    os.remove(f)

print("Starting Playwright recording...")
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=RECORDINGS_DIR,
        record_video_size={"width": 1280, "height": 720}
    )
    page = context.new_page()

    # 1. Load the frontend
    print("Navigating to http://localhost:8080...")
    page.goto("http://localhost:8080", wait_until="networkidle")
    time.sleep(2.0)

    # 2. Prompt 1: Show what the app does best (Practice problems + hints via A2UI)
    prompt1 = "Can you give me an AP Calculus practice problem on Derivatives with a hint?"
    print(f"Typing Prompt 1: {prompt1}")
    page.click("#input")
    for ch in prompt1:
        page.keyboard.type(ch, delay=35)
    time.sleep(0.6)
    
    # Submit and wait for input to be disabled
    page.keyboard.press("Enter")
    print("Submitted Prompt 1...")
    try:
        page.wait_for_selector("#input:disabled", timeout=5000)
    except Exception:
        pass
    
    # Wait for response to finish rendering
    page.wait_for_selector("#input:not(:disabled)", timeout=90000)
    print("Received Prompt 1 reply!")
    time.sleep(5.0)

    # 3. Prompt 2: Richer prompt showing tool calls, database lookup, and image generation
    prompt2 = "Check my student progress scorecard from the database and generate a visual concept diagram of the unit circle to review key trigonometry angles."
    print(f"Typing Prompt 2: {prompt2}")
    page.click("#input")
    for ch in prompt2:
        page.keyboard.type(ch, delay=30)
    time.sleep(0.6)

    # Submit and wait for input to be disabled
    page.keyboard.press("Enter")
    print("Submitted Prompt 2, waiting for database lookup and diagram generation...")
    try:
        page.wait_for_selector("#input:disabled", timeout=5000)
    except Exception:
        pass

    # Wait for response to finish rendering
    page.wait_for_selector("#input:not(:disabled)", timeout=120000)
    print("Received Prompt 2 reply!")

    # Wait for the diagram image to appear and load
    try:
        page.wait_for_selector("img.a2img", timeout=30000)
        print("Diagram image element found in A2UI card!")
    except Exception as e:
        print(f"Note on image selector: {e}")

    time.sleep(2.0)

    # Smoothly scroll down so the scorecard and unit circle diagram are in full view
    print("Scrolling to display the scorecard and generated diagram...")
    page.evaluate("""
        const log = document.getElementById('log');
        log.scrollTo({ top: log.scrollHeight, behavior: 'smooth' });
    """)
    time.sleep(8.0)

    # Finish recording
    print("Closing browser context to finalize video...")
    page.close()
    context.close()
    browser.close()

# Find the recorded webm file
recordings = glob.glob(f"{RECORDINGS_DIR}/*.webm")
if not recordings:
    raise RuntimeError("No recording found in " + RECORDINGS_DIR)

raw_video = recordings[0]
print(f"Raw video saved at: {raw_video}")

# Mux with upbeat lo-fi background music
audio_path = "/config/Desktop/BuildWithGemini/lofi_beat.wav"
output_mp4 = "/config/Desktop/BuildWithGemini/apexmath_demo.mp4"
artifact_mp4 = "/config/.gemini/antigravity/brain/a94ad83d-b412-49cc-b0dd-f449443824e4/apexmath_demo.mp4"

print("Muxing video with upbeat lo-fi background music using ffmpeg...")
cmd = [
    "ffmpeg", "-y",
    "-i", raw_video,
    "-stream_loop", "-1",
    "-i", audio_path,
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "medium",
    "-crf", "20",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    output_mp4
]
subprocess.check_call(cmd)
print(f"Demo video generated successfully at: {output_mp4}")

# Copy to artifacts directory
subprocess.check_call(["cp", output_mp4, artifact_mp4])
print(f"Copied demo video to artifact directory: {artifact_mp4}")
