# Resumind AI ✦

An intelligent, AI-powered resume analyzer, ATS compatibility auditor, and career readiness platform built with **Streamlit**, **Custom PyTorch Neural Networks**, and modern semantic skill matching algorithms.

100% self-contained: works out-of-the-box on CPU or GPU without external API keys or background services.

---

## 🌟 Overview

Resumind evaluates candidate resumes against target job descriptions with precision. It identifies matched and missing competencies, calculates ATS-style compatibility scores, assesses resume completeness, and provides deep qualitative feedback and recommendations powered by custom PyTorch neural networks.

### Key Capabilities
- **Resume Intelligence**: Automatically extracts candidate contact information, education, experience, projects, certifications, and languages from text-based PDFs.
- **Neural Skill Recognition**: Custom PyTorch neural network (`SkillNet`) trained to recognize over 30+ core industry skills across IT and non-IT disciplines.
- **Neural & Deterministic Job Match**: Blends exact keyword taxonomy mapping with neural semantic matching (`ResumindMatchNet`) to assess job compatibility.
- **Visual Analytics**: Interactive Plotly charts breaking down matched vs. missing skills and domain taxonomy distribution.
- **Executive PDF Audit Report**: Downloadable formal PDF audit report generated instantly with ReportLab.
- **Pure Crisp Light Mode**: High-contrast, accessibility-first design with clean card hierarchy.

---

## 🚀 Running on Any Laptop or Sharing with Everyone

You have three easy ways to run this project:

### Method 1: Deploy to the Web for Free (Best for Sharing with Everyone)
Deploy to **Streamlit Community Cloud** so anyone can use it from any laptop, phone, or tablet via a public link (e.g. `https://your-app.streamlit.app`) without installing Python:

1. Go to **[share.streamlit.io](https://share.streamlit.io/)** and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository: `souradeepsaha007/ResuMind`.
4. Branch: `main`
5. Main file path: `app.py`
6. Click **"Deploy!"**
7. Your app is now live 24/7 on the internet! Share the link with anyone.

---

### Method 2: One-Click Run on Another Laptop (Local)

#### On Windows:
1. Clone or download the repository:
   ```bash
   git clone https://github.com/souradeepsaha007/ResuMind.git
   cd ResuMind
   ```
2. Double-click **`run.bat`** (or run `.\run.bat` in Command Prompt / PowerShell).
   - It will automatically create a virtual environment, install the dependencies, and launch the app in your browser at `http://localhost:8501`.

#### On macOS / Linux:
1. Clone or download the repository:
   ```bash
   git clone https://github.com/souradeepsaha007/ResuMind.git
   cd ResuMind
   ```
2. Make `start.sh` executable and run it:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

---

### Method 3: Manual Command Line Setup

```bash
# 1. Clone repository
git clone https://github.com/souradeepsaha007/ResuMind.git
cd ResuMind

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Launch the app
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

### Method 4: Share with Devices on the Same Wi-Fi Network
If you are running the app on your laptop and want a friend or colleague in the same room / office / Wi-Fi network to test it on their laptop or phone:
1. Start the app: `streamlit run app.py`
2. Check your Network URL printed in the terminal (for example `http://192.168.1.X:8501` or `http://10.X.X.X:8501`).
3. Anyone connected to the same Wi-Fi can open that URL in their browser!

---

## 🛠️ Tech Stack

- **Frontend & UI**: Streamlit (Light Mode Design System)
- **Deep Learning / Neural Engine**: PyTorch (`SkillNet` & `ResumindMatchNet` with CPU & GPU support)
- **PDF Extraction**: PyMuPDF (`fitz`)
- **Machine Learning**: Scikit-Learn (`TfidfVectorizer`), NumPy, Pandas
- **Visualization**: Plotly Graph Objects
- **Report Engine**: ReportLab PDF Generator

---

## 📄 License
MIT License. Crafted for career excellence.
