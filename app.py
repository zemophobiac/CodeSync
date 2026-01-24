import streamlit as st
from fpdf import FPDF
import subprocess
import os
import shutil

# --- 1. The PDF Engine ---
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
        
        # 1. Chapter Title
        self.set_font("courier", 'B', 12)
        self.cell(0, 10, title, ln=True, border='B')
        self.ln(5)
        
        # 2. The Code Section
        self.set_font("courier", 'B', 10)
        self.cell(0, 5, "CODE:", ln=True)
        self.set_font("courier", size=10)
        safe_code = code_content.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, safe_code)
        self.ln(10)
        
        # 3. The Output Section
        self.set_font("courier", 'B', 10)
        self.cell(0, 5, "OUTPUT:", ln=True)
        self.set_font("courier", size=10)
        
        if output_content:
            safe_output = output_content.encode('latin-1', 'replace').decode('latin-1')
            self.multi_cell(0, 5, safe_output)
        else:
            self.cell(0, 5, "[No Output or Execution Failed]", ln=True)

# --- 2. The Execution Engine ---
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

# --- 3. The Web Interface ---
st.set_page_config(page_title="CodeSync Pro - by Faisal Hayat", page_icon="⚡")
st.title("CodeSync Pro: Batch Processor ⚡")

# --- UI: Sidebar Configuration ---
st.sidebar.header("Document Settings")

# 1. Global PDF Title
user_title = st.sidebar.text_input("Main PDF Title", value="Lab Record Final")

# 2. Page Naming Strategy
naming_mode = st.sidebar.radio(
    "How should we name the programs?",
    ('Use Original Filename', 'Auto-Numbering (e.g., Assignment 1)')
)

custom_prefix = "Assignment"
if naming_mode == 'Auto-Numbering (e.g., Assignment 1)':
    custom_prefix = st.sidebar.text_input("Prefix Name", value="Assignment")

# 3. Auto Inputs
st.sidebar.markdown("---")
st.sidebar.header("Execution Settings")
st.sidebar.info("📱 Mobile Users: Tap the arrow at the top-left to see settings.")

default_input = st.sidebar.text_area(
    "Auto-Input Values", 
    value="10\n20\n", 
    help="Inputs for programs requiring user interaction."
)

# --- UI: Main Area ---
uploaded_files = st.file_uploader(
    "Select files (Drag & Drop multiple files)", 
    type=['py', 'cpp', 'c'], 
    accept_multiple_files=True
)

if uploaded_files and st.button("Compile & Generate Lab Record"):
    pdf = PDF(user_title)
    progress_bar = st.progress(0)
    
    if not os.path.exists("temp_run"):
        os.makedirs("temp_run")

    for i, uploaded_file in enumerate(uploaded_files):
        # Save file
        file_path = os.path.join("temp_run", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Run Code
        lang = "python" if uploaded_file.name.endswith(".py") else "cpp"
        code_content = uploaded_file.getvalue().decode("utf-8")
        output_content = run_code(file_path, lang, default_input)
        
        # Title Logic
        if naming_mode == 'Use Original Filename':
            final_chapter_name = f"Source File: {uploaded_file.name}"
        else:
            final_chapter_name = f"{custom_prefix} {i + 1}"

        pdf.add_chapter(final_chapter_name, code_content, output_content)
        progress_bar.progress((i + 1) / len(uploaded_files))

    shutil.rmtree("temp_run")
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    st.success("✅ Processing Complete!")
    st.download_button(
        label="⬇️ Download Lab Record",
        data=pdf_bytes,
        file_name="lab_record_compiled.pdf",
        mime="application/pdf"
    )

# --- 4. Footer Section (NEW) ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: grey;'>
        Built with ❤️ by <strong>Md Faisal Hayat</strong><br>
        📧 Contact: <a href="mailto:55mdfaisalhayat@gmail.com">55mdfaisalhayat@gmail.com</a>
    </div>
    """,
    unsafe_allow_html=True
)
