import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash,  make_response
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import secrets
akey = secrets.token_hex(16)
print(akey)


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = akey  # Replace with your own secret key

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# ----- Florence2 Model or OCR Extraction Implementation -----
# In this example, we use pytesseract to extract text.
# If you have a Florence 2 model with different extraction capabilities,
# replace the code inside extract_features accordingly.
class Florence2Model:
    @classmethod
    def load_pretrained(cls, model_path_or_identifier):
        # In your real implementation, load the Florence2 model here.
        print("Loading Florence2 Model (or initializing OCR)...")
        return cls()
    
    def preprocess(self, image: Image.Image):
        # Convert image to RGB (if needed) and perform any other preprocessing
        return image.convert("RGB")
    
    def extract_features(self, preprocessed_image: Image.Image):
        # Use pytesseract to extract text from the image
        text = pytesseract.image_to_string(preprocessed_image)
        # If no text is found, you might want to return a default message
        return text.strip() if text.strip() else "No text found"

# Load the Florence2 model / OCR once at startup
model = Florence2Model.load_pretrained("florence2_pretrained_model_identifier")

# ----- Routes -----
@app.route('/')
def index():
    return redirect(url_for('upload_pdf'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_pdf():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['pdf_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and file.filename.lower().endswith('.pdf'):
            # Save the uploaded PDF file with a unique filename
            filename = f"{uuid.uuid4()}.pdf"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Process the PDF and extract text from each page
            extracted_results = process_pdf(filepath)
            
            # Create text file content from the extracted results
            content = ""
            for item in extracted_results:
                content += f"Page {item['page']}:\n{item['data']}\n{'-'*40}\n"
            
            # Prepare the text file as a downloadable response
            response = make_response(content)
            response.headers["Content-Disposition"] = "attachment; filename=results.txt"
            response.headers["Content-Type"] = "text/plain"
            return response
        else:
            flash('Please upload a valid PDF file.')
            return redirect(request.url)
    return render_template('upload.html')

def process_pdf(pdf_path):
    try:
        # Convert PDF pages to images with a high dpi for clarity
        pages = convert_from_path(pdf_path, dpi=300)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return [{"page": 0, "data": "Failed to convert PDF to images"}]
    
    results = []
    for i, page in enumerate(pages):
        # Preprocess the image for Florence2 model / OCR
        preprocessed_image = model.preprocess(page)
        # Extract text from the image
        extracted_data = model.extract_features(preprocessed_image)
        results.append({
            "page": i + 1,
            "data": extracted_data
        })
    return results

if __name__ == '__main__':
    app.run(debug=True)