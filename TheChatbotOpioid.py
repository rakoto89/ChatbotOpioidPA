from flask import Flask, request, jsonify, render_template
import openai
import os
import pdfplumber
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Adjust the PDF path after moving TheChatbotOpioid.py under templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of TheChatbotOpioid.py
PDF_PATH = os.path.join(BASE_DIR, "..", "PDFs", "OpioidInfo.pdf")  # Move up one level, then into PDFs

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except FileNotFoundError:
        text = "Error: PDF file not found."
    return text.strip()

pdf_text = extract_text_from_pdf(PDF_PATH)

def is_question_relevant(question):
    relevance_prompt = (
        "Determine if the following question is related to opioids OR related topics such as overdose, withdrawal, "
        "prescription painkillers, fentanyl, narcotics, analgesics, opiates, opioid crisis, addiction, naloxone, or rehab. "
        "Respond with 'yes' if it is related and 'no' if it is not.\n\n"
        f"Question: {question}"
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": relevance_prompt}],
            max_tokens=10,
            temperature=0,
        )
        return response['choices'][0]['message']['content'].strip().lower() == "yes"
    except openai.AuthenticationError:
        return False  # Return False if there is an authentication issue
    except Exception as e:
        return False  # Catch other errors and return False

def get_gpt3_response(question, context):
    opioid_context = (
        "Assume the user is always asking about opioids or related topics like overdose, addiction, withdrawal, "
        "painkillers, fentanyl, heroin, and narcotics, even if they don't explicitly mention 'opioids.'"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[ 
                {"role": "system", "content": opioid_context},
                {"role": "user", "content": f"Here is the document content:\n{context}\n\nQuestion: {question}"}
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.AuthenticationError:
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

    if is_question_relevant(user_question):
        answer = get_gpt3_response(user_question, pdf_text)
    else:
        answer = "Sorry, I can only answer questions related to opioids, addiction, overdose, or withdrawal."

    return jsonify({"answer": answer})

# Ensure Gunicorn can find the application
application = app  

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
