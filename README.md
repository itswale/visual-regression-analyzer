```markdown
# Visual Regression Analyzer

A Streamlit-based tool for comparing images (e.g., UI screenshots) to detect visual differences, tailored for QA testers and developers. Upload a baseline image and a new version—or capture a screenshot from a URL—and get a detailed analysis with a difference percentage, highlighted changes, and a heatmap.

## Features
- **Image Comparison**: Calculates the percentage of pixels differing between a baseline and new image.
- **Tolerance Control**: Adjust sensitivity (0 = every difference, 255 = major changes only).
- **Custom Thresholds**: Set pass/fail limits (e.g., Pass < 10%, Fail > 70%) with severity ratings (Minor, Moderate, Critical).
- **URL Screenshot Capture**: Capture live screenshots with customizable dimensions.
- **Visual Insights**: View side-by-side comparisons, highlighted differences, and heatmaps.
- **History**: Save up to 10 past comparisons.
- **Export**: Download highlighted differences and heatmaps as PNGs.

## Prerequisites
- **Python**: 3.8 or higher.
- **Operating System**: Windows, macOS, or Linux.
- **Git**: For cloning the repository.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/itswale/visual-regression-analyzer.git
   cd visual-regression-analyzer
   ```

2. **Set Up a Virtual Environment (Recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   Create a `requirements.txt` file with the following content:
   ```
   streamlit>=1.31.0
   opencv-python-headless>=4.9.0.80
   pillow>=10.2.0
   numpy>=1.26.4
   playwright>=1.42.0
   streamlit-drawable-canvas>=0.9.3
   ```

   Install them:
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: If errors occur, update libraries (e.g., `pip install --upgrade streamlit`).

4. **Install Playwright Browsers**:
   Required for URL screenshot capture:
   ```bash
   playwright install
   ```
   This downloads Chromium, Firefox, and Webkit (~200MB).

## Usage
1. **Run the App**:
   ```bash
   streamlit run app.py
   ```
   Open [http://localhost:8501](http://localhost:8501) in your browser.

2. **Basic Workflow**:
   - **Baseline Image**: Upload your reference image (PNG, JPG, JPEG).
   - **New Version**: Upload a comparison image or enter a URL for a screenshot.
   - **Settings**: Adjust tolerance (0–255) and toggle thresholds in the sidebar.
   - **Analyze**: Click "Run Visual Analysis" to see results.

3. **Interpreting Results**:
   - **Difference %**: E.g., 40% means 40% of pixels differ based on tolerance.
   - **Tolerance**: 
     - 0 = Every change counts (exact matches).
     - 50 = Ignores small shifts (default).
     - Adjust in Settings to match your needs.
   - **Thresholds**: Enable to set pass/fail (e.g., Pass < 10%, Fail > 70%) with severity:
     - Minor: Small tweaks.
     - Moderate: Noticeable changes.
     - Critical: Near failure.
   - **Tabs**: 
     - Side-by-Side: Compare images.
     - Differences: Red boxes show changes.
     - Heatmap: Bright spots = bigger differences.
     - Guide: Explains results.

## File Structure
- `app.py`: Main application script.
- `requirements.txt`: Python dependencies (create this file).
- `README.md`: This documentation.

## Dependencies (requirements.txt)
Create a `requirements.txt` file with:
```
streamlit>=1.31.0
opencv-python-headless>=4.9.0.80  # Headless to avoid GUI dependencies
pillow>=10.2.0
numpy>=1.26.4
playwright>=1.42.0
streamlit-drawable-canvas>=0.9.3
```

**Notes**:
- Run `playwright install` after installing playwright.
- Update with `pip install --upgrade <package>` if errors occur.
- Use `opencv-python-headless` to avoid CUDA/GUI issues.

## Troubleshooting Common Errors
- **ModuleNotFoundError: No module named 'cv2'**:
  - **Cause**: OpenCV not installed.
  - **Fix**: `pip install opencv
