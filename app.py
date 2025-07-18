from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 🌟 Configure Gemini API key
genai.configure(api_key="AIzaSyCZWG8_RdD0kzcPABm66svhO7lNDCxkD3A")  # Replace with your API key

# 🚀 Load Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")


# 🔍 Gemini Vision image-to-text function
def gemini_get_text_from_image(image_file, prompt):
    image = Image.open(image_file).convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()

    response = model.generate_content(
        contents=[{
            "role": "user",
            "parts": [
                {"text": prompt},
                {"inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                }}
            ]
        }]
    )
    return response.text


# 🧾 Generate PDF helper
def make_pdf(lines, title):
    buf = BytesIO()
    p = canvas.Canvas(buf)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, title)
    p.setFont("Helvetica", 12)
    y = 770
    for idx, text in enumerate(lines, 1):
        p.drawString(60, y, f"{text}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.save()
    buf.seek(0)
    return buf


# 🏠 Home route (homepage with "Start" button)
@app.route('/')
def home():
    return render_template('home.html')


# 📤 Upload interface (actual app functionality)
@app.route('/upload')
def upload():
    return render_template('index.html')


# 🧠 Generate grocery list from image
@app.route('/generate', methods=['POST'])
def generate_ingredients():
    if 'file' not in request.files:
        return jsonify(success=False, error="No file provided.")
    img = request.files['file']
    try:
        response_text = gemini_get_text_from_image(
            img,
            "Based on this food image, provide a full and detailed grocery list "
            "including all main and sub-ingredients that might be used to prepare the dish. "
            "List items in bullet points and include common spices, sauces, or oils typically used. "
            "Don't explain or describe — just list all ingredients clearly."
        )
        items = [line.strip("•- ").strip() for line in response_text.split('\n') if line.strip()]
        return jsonify(success=True, items=items)
    except Exception as e:
        return jsonify(success=False, error=str(e))


# 👩‍🍳 Generate recipe steps from image
@app.route('/get-recipe-steps', methods=['POST'])
def get_steps():
    if 'file' not in request.files:
        return jsonify(success=False, error="No file provided.")
    img = request.files['file']
    try:
        response_text = gemini_get_text_from_image(
            img,
            "Write detailed, step-by-step cooking instructions for this dish for 2 people. Include quantities of ingredients in each step."
        )
        steps = [line.strip("•- 1234567890.").strip() for line in response_text.split('\n') if line.strip()]
        return jsonify(success=True, steps=steps)
    except Exception as e:
        return jsonify(success=False, error=str(e))


# 📥 Download grocery list as PDF
@app.route('/download-pdf', methods=['POST'])
def download_list_pdf():
    items = request.get_json().get('items', [])
    buf = make_pdf([f"• {it}" for it in items], "Grocery List")
    return send_file(buf, as_attachment=True, download_name='grocery_list.pdf', mimetype='application/pdf')


# 📥 Download recipe steps as PDF
@app.route('/download-steps-pdf', methods=['POST'])
def download_steps_pdf():
    steps = request.get_json().get('steps', [])
    buf = make_pdf([f"{i}. {s}" for i, s in enumerate(steps, 1)], "Recipe Steps")
    return send_file(buf, as_attachment=True, download_name='recipe_steps.pdf', mimetype='application/pdf')


# 🚀 Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)