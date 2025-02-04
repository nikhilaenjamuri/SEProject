from flask import Flask, render_template, request, jsonify
import pandas as pd
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib import colors
import os
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.utils import formataddr
from os import getenv
import config

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
TEMPLATE_FOLDER = 'templates'
OUTPUT_FOLDER = 'output'

email_password = config.EMAIL_PASSWORD
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPLATE_FOLDER'] = TEMPLATE_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'kris777india@gmail.com'
app.config['MAIL_PASSWORD'] =  email_password # Use environment variable for password

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_template', methods=['POST'])
def upload_template():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    file_path = os.path.join(app.config['TEMPLATE_FOLDER'], file.filename)
    file.save(file_path)
    return jsonify({"message": "Template uploaded successfully"}), 200

@app.route('/upload_data', methods=['POST'])
def upload_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    return jsonify({"message": "Data uploaded successfully"}), 200

@app.route('/generate_pdfs', methods=['POST'])
def generate_pdfs():
    try:
        template_name = request.form.get('template_name')
        data_file_name = request.form.get('data_file_name')

        if not template_name or not data_file_name:
            return jsonify({"error": "Template name and data file name are required"}), 400

        template_path = os.path.join(app.config['TEMPLATE_FOLDER'], template_name)
        data_path = os.path.join(app.config['UPLOAD_FOLDER'], data_file_name)

        if not os.path.exists(template_path):
            return jsonify({"error": "Template file not found"}), 404

        if not os.path.exists(data_path):
            return jsonify({"error": "Data file not found"}), 404

        df = pd.read_excel(data_path)

        # Generate PDFs for each row and store the file paths
        pdf_paths = []
        for _, row in df.iterrows():
            pdf_filename = generate_pdf(template_path, row.to_dict())
            pdf_paths.append(pdf_filename)

        return jsonify({"message": "PDFs generated successfully", "pdf_paths": pdf_paths}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send_emails', methods=['POST'])
def send_emails():
    try:
        pdf_paths = request.json.get('pdf_paths')
        data_file_name = request.json.get('data_file_name')

        if not pdf_paths or not data_file_name:
            return jsonify({"error": "PDF paths and data file name are required"}), 400

        # Read the Excel file for emails and loop through to send emails
        data_path = os.path.join(app.config['UPLOAD_FOLDER'], data_file_name)
        df = pd.read_excel(data_path)

        for index, row in df.iterrows():
            if pd.isna(row['Email']):  # Skip rows with missing emails
                print(f"Email missing for {row.get('EMPLOYEE_NAME', 'Unnamed')}, skipping.")
                continue
            
            pdf_path = pdf_paths[index]  # Get corresponding PDF for the row
            send_email_with_attachment(row['Email'], pdf_path)

        return jsonify({"message": "Emails sent successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_pdf(template_path, data):
    doc = Document(template_path)

    # Prepare the PDF buffer
    pdf_buffer = io.BytesIO()
    doc_pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    # Create a list of story elements (paragraphs)
    story = []

    styles = getSampleStyleSheet()

    custom_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.black,
        spaceAfter=12
    )

    for paragraph in doc.paragraphs:
        for key, value in data.items():
            if f'{{{{{key}}}}}' in paragraph.text:
                paragraph.text = paragraph.text.replace(f'{{{{{key}}}}}', str(value))

        paragraph_text = paragraph.text.strip()
        if paragraph_text:
            story.append(Paragraph(paragraph_text, custom_style))

    doc_pdf.build(story)

    filename = f"{data.get('EMPLOYEE_NAME', 'Unnamed')}_{data.get('POSITION', 'Unnamed')}.pdf"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)

    with open(output_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())

    return output_path

def send_email_with_attachment(to_email, pdf_path):
    try:
        from_email = 'kris777india@gmail.com'
        password = email_password  # Get password from environment variable

        msg = MIMEMultipart()
        msg['From'] = formataddr(('Batchgenproj', from_email))
        msg['To'] = to_email
        msg['Subject'] = 'Job Offer from ABC Company'

        body = 'Dear Sir/Madam, Please find attached the generated PDF document.'
        msg.attach(MIMEText(body, 'plain'))

        with open(pdf_path, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
            msg.attach(attach)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()

    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
