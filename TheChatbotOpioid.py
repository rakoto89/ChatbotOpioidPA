from flask import Flask, request, jsonify, render_template
import openai
import os
import pdfplumber
from dotenv import load_dotenv

# Load OpenAI API Key from Environment Variables (Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Ensure the PDF file is correctly located
PDF_PATH = os.path.join(os.path.dirname(__file__), "OpioidInfo.pdf")

def extract_text_from_pdf(pdf_path):
    text = ""
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
    return text.strip()

pdf_text = extract_text_from_pdf(PDF_PATH)

def get_gpt3_response(question, context):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Answer the user's question based on the provided document content."},
                {"role": "user", "content": f"Here is the document content:\n{context}\n\nQuestion: {question}"}
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.AuthenticationError:
        return "Authentication error: Check your OpenAI API key."
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route("/")
def index():
    return render_template("index.html")  

@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.form.get("question", "")

    if not user_question:
        return jsonify({"answer": "Please ask a valid question."})

    answer = get_gpt3_response(user_question, pdf_text)

    return jsonify({"answer": answer})

# Render requires 0.0.0.0 with dynamic port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
