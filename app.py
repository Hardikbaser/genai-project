from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from google import genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
import uuid

app = Flask(__name__)
CORS(app)

# 🔐 Store API key securely in environment variable in real projects
client = genai.Client(api_key="AIzaSyDU9yP1G30td0igXFPcGVigkhuHAyfkxxo")

# Folder to store generated reports
OUTPUT_FOLDER = "generated_reports"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# 🔹 Main Page Route
@app.route("/")
def home():
    return render_template("index.html")


# 🔹 Generate PDF Function
def create_pdf(title, content):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(OUTPUT_FOLDER, f"{file_id}.pdf")

    doc = SimpleDocTemplate(file_path)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(content.replace("\n", "<br/>"), styles["Normal"]))

    doc.build(elements)

    return file_path, file_id


# 🔹 API Route
@app.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.json
    notes = data.get("notes")
    doc_type = data.get("docType")

    if not notes or not doc_type:
        return jsonify({"error": "Missing notes or document type"}), 400

    # 🎯 Structured Prompt Based on Type
    prompt = f"""
    Convert the following site notes into a professional {doc_type}.

    Use proper headings and structured formatting.
    Use construction industry terminology.

    Notes:
    {notes}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    report_text = response.text

    # 🔹 Generate PDF
    file_path, file_id = create_pdf(doc_type, report_text)

    return jsonify({
        "report": report_text,
        "download_url": f"/download/{file_id}"
    })


# 🔹 Download Route
@app.route("/download/<file_id>")
def download_file(file_id):
    file_path = os.path.join(OUTPUT_FOLDER, f"{file_id}.pdf")

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404


if __name__ == "__main__":
    app.run(debug=True)
