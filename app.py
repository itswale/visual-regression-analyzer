import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
from io import BytesIO
import time
import base64
from streamlit_drawable_canvas import st_canvas
from playwright.sync_api import sync_playwright
import os
import subprocess

# Ensure Playwright browsers are installed without Streamlit commands
playwright_dir = os.path.expanduser("~/.cache/ms-playwright")
if not os.path.exists(playwright_dir) or not os.listdir(playwright_dir):
    print("Installing Playwright browsers...")  # Use print instead of st.write
    subprocess.run(["playwright", "install", "chromium"], check=True)
    print("Browsers installed!")

# ========== Configuration ==========
COLORS = {
    "primary": "#00A9FF",
    "secondary": "#FF007A",
    "accent": "#39FF14",
    "background": "#252740",
    "text": "#E0E0E0",
    "success": "#39FF14",
    "warning": "#FFC107",
    "error": "#FF4040"
}

# ========== Core Functions ==========
def compare_images(baseline_img, new_img, tolerance=50):
    try:
        if not isinstance(baseline_img, Image.Image):
            baseline_img = Image.open(baseline_img)
        if not isinstance(new_img, Image.Image):
            new_img = Image.open(new_img)

        baseline_img = baseline_img.convert('RGB')
        new_img = new_img.convert('RGB')

        if baseline_img.size != new_img.size:
            st.warning(f"Image sizes differ: Baseline {baseline_img.size}, New {new_img.size}. Resizing new image to match baseline.")
            new_img = new_img.resize(baseline_img.size, Image.Resampling.LANCZOS)

        baseline_np = np.array(baseline_img)
        new_np = np.array(new_img)

        if baseline_np.shape != new_np.shape:
            st.error(f"Shape mismatch after resize: Baseline {baseline_np.shape}, New {new_np.shape}")
            return None, None, None

        diff_np = cv2.absdiff(baseline_np, new_np)
        gray_diff = cv2.cvtColor(diff_np, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_diff, tolerance, 255, cv2.THRESH_BINARY)
        
        diff_pixels = np.count_nonzero(thresh)
        total_pixels = thresh.size
        diff_percent = (diff_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        contours_data = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours_data[0] if len(contours_data) == 2 else contours_data[1]
        
        highlighted = baseline_np.copy()
        for contour in contours:
            if cv2.contourArea(contour) > 0:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(highlighted, (x, y), (x+w, y+h), (255, 71, 87), 2)
        
        return (
            Image.fromarray(highlighted),
            Image.fromarray(diff_np),
            round(diff_percent, 2)
        )
    except Exception as e:
        st.error(f"Image processing error: {str(e)}")
        return None, None, None

def capture_screenshot(url, width=1280, height=720):
    try:
        with sync_playwright() as p:
            st.write("Launching browser...")  # Debug
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": width, "height": height})
            page.goto(url, wait_until="networkidle")
            screenshot_bytes = page.screenshot(full_page=False)
            browser.close()
            st.write("Screenshot captured successfully!")  # Debug
            return Image.open(BytesIO(screenshot_bytes))
    except Exception as e:
        st.error(f"Screenshot capture failed: {str(e)}")
        return None

# ========== Utility Functions ==========
def handle_history():  # Unchanged
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    if 'current_result' in st.session_state and st.session_state.current_result:
        result = st.session_state.current_result
        history_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "diff_percent": result['diff_percent'],
            "baseline": image_to_base64(result['baseline']),
            "new_image": image_to_base64(result['new_image']),
            "highlighted": image_to_base64(result['highlighted']),
            "annotations": result.get('annotations', [])
        }
        st.session_state.history.insert(0, history_entry)
        st.session_state.history = st.session_state.history[:10]

def image_to_base64(image):  # Unchanged
    try:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception:
        return ""

def base64_to_image(base64_str):  # Unchanged
    try:
        return Image.open(BytesIO(base64.b64decode(base64_str)))
    except Exception:
        return None

def annotation_tool(image):  # Unchanged
    try:
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image) if isinstance(image, np.ndarray) else Image.open(image)
        
        if not hasattr(image, 'size') or image.size[0] == 0 or image.size[1] == 0:
            raise ValueError("Invalid image dimensions")
        
        canvas_key = f"canvas_{int(time.time()*1000)}"
        return st_canvas(
            fill_color="rgba(57, 255, 20, 0.3)",
            stroke_width=2,
            stroke_color=COLORS['secondary'],
            background_image=image,
            height=image.size[1],
            width=image.size[0],
            drawing_mode="rect",
            key=canvas_key,
            update_streamlit=True
        )
    except Exception as e:
        st.error(f"Annotation error: {str(e)}")
        return None

# ========== UI Components ==========
def main_interface():  # Unchanged
    st.title("Visual Regression Analyzer")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Baseline Image")
        st.markdown('<div class="file-container">', unsafe_allow_html=True)
        baseline_file = st.file_uploader("Upload reference image", 
                                        type=["png", "jpg", "jpeg"], 
                                        key="baseline",
                                        label_visibility="collapsed")
        if baseline_file:
            with st.spinner("Loading..."):
                try:
                    st.session_state.baseline_img = Image.open(baseline_file)
                    st.image(st.session_state.baseline_img, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to load baseline image: {str(e)}")
                    st.session_state.baseline_img = None
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("New Version")
        st.markdown('<div class="file-container">', unsafe_allow_html=True)
        capture_option = st.radio("Input Method:", ("Upload", "URL"), 
                                 horizontal=True,
                                 label_visibility="collapsed")
        
        if capture_option == "Upload":
            new_file = st.file_uploader("Upload comparison image", 
                                       type=["png", "jpg", "jpeg"], 
                                       key="new",
                                       label_visibility="collapsed")
            if new_file:
                with st.spinner("Loading..."):
                    try:
                        st.session_state.new_img = Image.open(new_file)
                        st.image(st.session_state.new_img, use_container_width=True)
                    except Exception as e:
                        st.error(f"Failed to load new image: {str(e)}")
                        st.session_state.new_img = None
        else:
            url = st.text_input("Enter URL", placeholder="https://example.com")
            with st.expander("Capture Settings"):
                width = st.number_input("Width", min_value=320, max_value=3840, value=1280, step=10)
                height = st.number_input("Height", min_value=240, max_value=2160, value=720, step=10)
                aspect_ratio = st.checkbox("Lock Aspect Ratio (16:9)", value=False)
                if aspect_ratio:
                    height = int(width / 16 * 9)
                    st.write(f"Height adjusted to: {height}px (16:9)")
            
            if st.button("🌐 Capture Screenshot"):
                if url:
                    with st.spinner("Capturing screenshot..."):
                        new_img = capture_screenshot(url, width, height)
                        if new_img:
                            st.session_state.new_img = new_img
                            st.image(new_img, use_container_width=True)
                        else:
                            st.session_state.new_img = None
                else:
                    st.warning("Please enter a valid URL.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚀 Run Visual Analysis", use_container_width=True):
        baseline_img = st.session_state.get('baseline_img')
        new_img = st.session_state.get('new_img')
        
        if baseline_img and new_img:
            with st.spinner("Analyzing..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress.progress(i + 1)
                highlighted_img, diff_img, diff_percent = compare_images(
                    baseline_img, new_img, st.session_state.tolerance
                )
                progress.empty()
                
                if highlighted_img:
                    st.session_state.current_result = {
                        'baseline': baseline_img,
                        'new_image': new_img,
                        'highlighted': highlighted_img,
                        'diff_img': diff_img,
                        'diff_percent': diff_percent,
                        'annotations': []
                    }
                    handle_history()
                    show_results()
        else:
            st.warning("Please upload both images or capture a screenshot.")

def show_results():
    result = st.session_state.get('current_result')
    if not result:
        return
    
    diff = result['diff_percent']
    tolerance = st.session_state.tolerance
    use_thresholds = st.session_state.get('use_thresholds', False)
    pass_th = st.session_state.get('pass_threshold', 10)
    fail_th = st.session_state.get('fail_threshold', 70)

    # Summary Section
    st.markdown("### Comparison Summary")
    st.write(f"**Difference**: {diff}% of pixels changed with tolerance {tolerance}.")
    if diff == 0:
        st.success("🎉 No differences found—images match perfectly!")
    else:
        st.write(f"Out of {result['baseline'].size[0]*result['baseline'].size[1]} pixels, {int(diff/100 * result['baseline'].size[0]*result['baseline'].size[1])} changed.")
        if tolerance == 0:
            st.info("ℹ️ Tolerance is 0: Every tiny change counts (e.g., a 1-point color shift).")
        else:
            st.info(f"ℹ️ Tolerance is {tolerance}: Only changes bigger than {tolerance} (out of 255) are counted.")
        
        if use_thresholds:
            if diff <= pass_th:
                st.success(f"✅ PASS: {diff}% is below your {pass_th}% limit—looks good!")
            elif diff >= fail_th:
                st.error(f"❌ FAIL: {diff}% exceeds your {fail_th}% limit—major issues detected!")
            else:
                severity_ratio = (diff - pass_th) / (fail_th - pass_th)
                if severity_ratio < 0.33:
                    st.warning(f"⚠️ MINOR: {diff}% is slightly above {pass_th}%. Small tweaks detected.")
                elif severity_ratio < 0.67:
                    st.warning(f"⚠️⚠️ MODERATE: {diff}% is midway to {fail_th}%. Noticeable changes.")
                else:
                    st.error(f"🚨 CRITICAL: {diff}% is close to {fail_th}%. Urgent review needed!")
        else:
            st.write("Toggle 'Use Thresholds' in Settings to set your own pass/fail limits.")

    tab1, tab2, tab3, tab4 = st.tabs(["Side-by-Side", "Differences", "Heatmap", "Guide"])
    
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.image(result['baseline'], caption="Baseline", use_container_width=True)
        with col_b:
            st.image(result['new_image'], caption="New Version", use_container_width=True)
    
    with tab2:
        canvas_result = annotation_tool(result['highlighted'])
        if canvas_result and hasattr(canvas_result, 'json_data') and canvas_result.json_data:
            result['annotations'] = canvas_result.json_data.get("objects", [])
        st.image(result['highlighted'], caption="Differences Highlighted", use_container_width=True)
        st.caption("Red boxes show where the new image differs from the baseline.")
        if st.button("💾 Save to History"):
            handle_history()
            st.success("Saved!")

    with tab3:
        st.image(result['diff_img'], use_container_width=True)
        st.caption("Heatmap: Bright spots show bigger differences.")

    with tab4:
        st.markdown("""
        ### Your Visual Regression Guide
        This tool compares your *baseline* (the original) to a *new version* and shows how much changed.

        #### What Does {diff}% Mean?
        - **{diff}% of pixels** differ by more than {tolerance} (out of 255) in color.
        - **Example**: If you saw 40% at tolerance 50, it meant 40% of the image had noticeable changes (e.g., text or shapes shifted). At tolerance 0, it shows *every* difference, even tiny ones—like a 1-point color tweak.

        #### How Tolerance Works
        - **0**: Catches *everything*. Use this if you need exact matches (like you did!).
        - **50**: Ignores small changes (e.g., slight color shifts). Good for most tests.
        - **100+**: Only flags big changes (e.g., missing elements). Try this for rough checks.
        - **Tune it**: Slide it in Settings until the % matches what you see as "different."

        #### Is {diff}% Okay?
        - **0–10%**: Usually fine—minor or no issues.
        - **10–40%**: Check the red boxes. Could be okay (e.g., text edits) or a problem (e.g., layout shift).
        - **40%+**: Likely significant. Look at 'Differences' to decide.
        - **Your Call**: Toggle 'Use Thresholds' in Settings to set what’s “pass” or “fail” for your project.

        #### Tips
        - **Start at 0**: See every change, then raise tolerance to filter noise.
        - **Check Highlights**: The 'Differences' tab shows *where* it changed.
        - **Set Limits**: Use thresholds (e.g., Pass < 10%, Fail > 70%) to automate decisions.
        """.format(diff=diff, tolerance=tolerance))

    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    col_metrics = st.columns(3)
    with col_metrics[0]:
        st.markdown(f"<div class='metric-card'><h3>📈 Difference</h3><h1>{diff}%</h1></div>", unsafe_allow_html=True)
    with col_metrics[1]:
        st.markdown(f"<div class='metric-card'><h3>⚖️ Tolerance</h3><h1>{tolerance}</h1></div>", unsafe_allow_html=True)
    with col_metrics[2]:
        st.markdown(f"<div class='metric-card'><h3>📐 Dimensions</h3><h1>{result['baseline'].size[0]}x{result['baseline'].size[1]}</h1></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("💾 Export Results"):
        col_dl = st.columns(2)
        with col_dl[0]:
            buf = BytesIO()
            result['highlighted'].save(buf, format="PNG")
            st.download_button("Download Highlighted", buf.getvalue(), "differences.png", type="primary")
        with col_dl[1]:
            buf = BytesIO()
            result['diff_img'].save(buf, format="PNG")
            st.download_button("Download Heatmap", buf.getvalue(), "heatmap.png", type="primary")

def sidebar_content():
    with st.sidebar:
        st.header("⚙️ Settings")
        st.session_state.tolerance = st.slider("Tolerance", 0, 255, 50, help="Set how big a change counts (0 = every difference, 255 = huge changes only).")
        st.session_state.performance_mode = st.checkbox("🚀 Performance Mode", value=False)
        
        st.subheader("Thresholds")
        st.session_state.use_thresholds = st.checkbox("Use Pass/Fail Thresholds", value=False, help="Turn on to set your own pass/fail limits.")
        if st.session_state.use_thresholds:
            st.session_state.pass_threshold = st.number_input("Pass Below (%)", 0, 100, 10, step=1)
            st.session_state.fail_threshold = st.number_input("Fail Above (%)", 0, 100, 70, step=1)
        
        st.markdown("---")
        st.header("📘 Quick Guide")
        st.markdown("""
        1. Upload your baseline image (the “perfect” version).
        2. Upload a new version or grab a screenshot.
        3. Click “Run Visual Analysis.”
        4. See the % difference and where it changed.

        **Tolerance**: 
        - 0 = Show every tiny change.
        - 50 = Good default, skips small stuff.
        - Adjust it to match what you care about.

        **Thresholds**: Toggle on to set pass/fail % limits.
        """)
        
        st.markdown("---")
        st.header("🕒 History")
        if st.session_state.get('history'):
            for entry in st.session_state.history[:3]:
                with st.expander(f"{entry['timestamp']} - {entry['diff_percent']}%"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(base64_to_image(entry['baseline']), caption="Baseline")
                    with col2:
                        st.image(base64_to_image(entry['highlighted']), caption="Differences")
                    if entry['annotations']:
                        st.markdown("**Annotations:**")
                        st.json(entry['annotations'])
        else:
            st.info("No history yet")

# ========== Main App ==========
def main():
    st.set_page_config(
        page_title="Visual Regression Analyzer",
        layout="wide",
        page_icon="🔍",
        initial_sidebar_state="expanded"
    )
    
    st.markdown(f"""
    <style>
    :root {{
        --primary: {COLORS['primary']}; --secondary: {COLORS['secondary']};
        --accent: {COLORS['accent']}; --background: {COLORS['background']};
        --text: {COLORS['text']};
    }}
    .stApp {{
        background: var(--background);
        color: var(--text);
    }}
    .sidebar .sidebar-content {{
        background: #252740;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    .metric-card {{
        background: #2A2E4A;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid var(--primary);
        color: var(--text);
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }}
    .metrics-container {{
        padding: 10px 0;
    }}
    .file-container {{
        padding: 15px;
        border-radius: 8px;
        background: #2A2E4A;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    div[data-testid="stFileUploader"] {{
        padding: 0;
    }}
    div[data-testid="stFileUploader"] button {{
        background-color: var(--primary);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        margin-top: 10px;
        transition: background-color 0.3s;
    }}
    div[data-testid="stFileUploader"] button:hover {{
        background-color: var(--secondary);
    }}
    div[data-testid="stFileUploader"] .st-emotion-cache-10y5sf6 {{
        color: #A0A0A0;
    }}
    .stButton > button {{
        background-color: var(--primary);
        color: white;
        border-radius: 4px;
        padding: 10px 20px;
        transition: background-color 0.3s;
    }}
    .stButton > button:hover {{
        background-color: var(--secondary);
    }}
    .stDownloadButton > button {{
        background-color: var(--primary);
        color: white;
        border-radius: 4px;
    }}
    .stDownloadButton > button:hover {{
        background-color: var(--secondary);
    }}
    .stSuccess {{ background-color: rgba(57, 255, 20, 0.1); }}
    .stWarning {{ background-color: rgba(255, 193, 7, 0.1); }}
    .stError {{ background-color: rgba(255, 64, 64, 0.1); }}
    </style>
    """, unsafe_allow_html=True)

    defaults = {
        'performance_mode': False,
        'tolerance': 50,
        'baseline_img': None,
        'new_img': None,
        'current_result': None,
        'history': [],
        'use_thresholds': False,
        'pass_threshold': 10,
        'fail_threshold': 70
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    sidebar_content()
    main_interface()

if __name__ == "__main__":
    main()