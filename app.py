import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF
import subprocess
import os
import shutil

# --- 1. Page Configuration (MUST BE FIRST) ---
st.set_page_config(
    page_title="CodeSync Pro - Lab Record Generator", 
    page_icon="⚡", 
    layout="centered"
)

# --- 2. Google Search Console Verification ---
verification_code = "iIpXtbxW2ZgJICukZXTEE2C43F4bSskvC7ruq7ceHKE"

# Method A: Direct Head Injection
st.markdown(
    f"""
    <meta name="google-site-verification" content="{verification_code}" />
    """,
    unsafe_allow_html=True
)

# Method B: Javascript Fallback
components.html(f"""
    <script>
        var meta = document.createElement('meta');
        meta.name = "google-site-verification";
        meta.content = "{verification_code}";
        document.getElementsByTagName('head')[0].appendChild(meta);
    </script>
""", height=0, width=0)


# --- 3. Light Mode Styling (CSS) ---
def set_custom_design():
    st.markdown("""
        <style>
        /* 1. Main Background & Text (WHITE MODE) */
        .stApp {
            background-color: #FFFFFF;
            color: #1F2937; /* Dark Grey Text */
        }
        
        /* 2. Headings */
        h1 {
            color: #0077B6; /* Strong Blue */
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 700;
        }
        h2, h3 {
            color: #333333;
        }
        
        /* 3. Buttons */
        div.stButton > button {
            background: linear-gradient(45deg, #00B4D8, #0077B6);
            color: white;
            border: none;
            padding: 10px 24px;
            font-size: 16px;
            border-radius: 8px;
            width: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 119, 182, 0.3);
        }

        /* 4. Input Fields (Light Grey Background) */
        .stTextInput > div > div > input {
            background-color: #F0F2F6;
            color: #1F2937;
            border: 1px solid #D1D5DB;
        }
        .stTextArea > div > div > textarea {
            background-color: #F0F2F6;
            color: #1F2937;
            border: 1px solid #D1D5DB;
        }
        
        /* 5. File Uploader */
        .stFileUploader {
            background-color: #F9FAFB;
            border: 1px dashed #0077B6;
            border-radius: 10px;
            padding: 15px;
        }

        /* 6. Footer Divider */
        hr {
            margin-top: 30px;
            margin-bottom: 30px;
            border-color: #E5E7EB; /* Light Grey Divider */
        }
        </style>
        """, unsafe_allow_html=True)

# Apply the design
set_custom_design()


# --- 4. The PDF Engine ---
class PDF(FPDF):
    def __init__(self, header_title):
        super().__init__()
        self.header_title = header_title

    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, self.header_title, border=False, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def add_chapter(self, title, code_content, output_content):
        self.add_page()
        
        # Chapter Title
        self.set_font("courier", 'B', 12)
        self.cell(0, 10, title, ln=True, border='B')
        self.ln(5)
        
        # Code Section
        self.set_font("courier", 'B', 10)
        self.cell(0, 5, "CODE:", ln=True)
        self.set_font("courier", size=10)
        safe_code = code_content.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, safe_code)
        self.ln(10)
        
        # Output Section
        self.set_font("courier", 'B', 10)
        self.cell(0, 5, "OUTPUT:", ln=True)
        self.set_font("courier", size=10)
        
        if output_content:
            safe_output = output_content.encode('latin-1', 'replace').decode('latin-1')
            self.multi_cell(0, 5, safe_output)
        else:
            self.cell(0, 5, "[No Output or Execution Failed]", ln=True)


# --- 5. The Execution Engine ---
def run_code(file_path, language, auto_inputs):
    try:
        if language == "python":
            command = ["python", file_path]
            result = subprocess.run(
                command, 
                input=auto_inputs, 
                capture_output=True, 
                text=True, 
                timeout=5 
            )
            return result.stdout + result.stderr

        elif language == "cpp" or language == "c":
            exe_name = file_path.replace(".cpp", ".exe").replace(".c", ".exe")
            compile_cmd = ["g++", file_path, "-o", exe_name]
            subprocess.run(compile_cmd, check=True)
            
            result = subprocess.run(
                [exe_name], 
                input=auto_inputs, 
                capture_output=True, 
                text=True,
                timeout=5
            )
            return result.stdout + result.stderr
            
    except subprocess.TimeoutExpired:
        return "Error: Execution Timed Out"
    except Exception as e:
        return f"Execution Error: {str(e)}"
    return "Unsupported Language"


# --- 6. Main Application UI ---
st.title("CodeSync Pro ⚡")
st.markdown("**Automated Lab Record Generator & Code Runner**")

# Sidebar
st.sidebar.header("Document Settings")
user_title = st.sidebar.text_input("PDF Header Title", value="Lab Record Final")

naming_mode = st.sidebar.radio(
    "Naming Strategy",
    ('Use Original Filename', 'Auto-Numbering')
)

custom_prefix = "Assignment"
if naming_mode == 'Auto-Numbering':
    custom_prefix = st.sidebar.text_input("Prefix", value="Assignment")

st.sidebar.markdown("---")
st.sidebar.header("Execution Settings")
st.sidebar.info("📱 Mobile Users: Tap arrow at top-left for settings.")

default_input = st.sidebar.text_area(
    "Auto-Input Values", 
    value="10\n20\n", 
    help="Enter values here if your code asks for user input."
)

# Main Input
uploaded_files = st.file_uploader(
    "Upload Python (.py) or C++ (.cpp) files", 
    type=['py', 'cpp', 'c'], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Compile & Generate PDF"):
        pdf = PDF(user_title)
        progress_bar = st.progress(0)
        
        if not os.path.exists("temp_run"):
            os.makedirs("temp_run")

        try:
            for i, uploaded_file in enumerate(uploaded_files):
                file_path = os.path.join("temp_run", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                lang = "python" if uploaded_file.name.endswith(".py") else "cpp"
                code_content = uploaded_file.getvalue().decode("utf-8")
                output_content = run_code(file_path, lang, default_input)
                
                if naming_mode == 'Use Original Filename':
                    final_chapter_name = f"Source: {uploaded_file.name}"
                else:
                    final_chapter_name = f"{custom_prefix} {i + 1}"

                pdf.add_chapter(final_chapter_name, code_content, output_content)
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            st.success("✅ Success! Your Lab Record is ready.")
            st.download_button(
                label="⬇️ Download PDF Now",
                data=pdf_bytes,
                file_name="lab_record_final.pdf",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
        
        finally:
            if os.path.exists("temp_run"):
                shutil.rmtree("temp_run")

# --- 7. Footer ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Created by <strong>Md Faisal Hayat</strong>co-created by <strong>Reyan Ahmed</strong> <br>
        📧 Contact: <a href="mailto:55mdfaisalhayat@gmail.com" style="color: #0077B6; text-decoration: none;">55mdfaisalhayat@gmail.com</a>
    </div>
    """,
    unsafe_allow_html=True
)

