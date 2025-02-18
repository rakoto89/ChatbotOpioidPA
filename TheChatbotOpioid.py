from flask import Flask, request, jsonify, render_template
import openai
import os
import pdfplumber

# Get API key from Render's environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Path to the PDF file (assuming it is in the same directory as the script)
PDF_PATH = os.path.join(os.path.dirname(__file__), "OpioidInfo.pdf")


def extract_text_from_pdf(pdf_path):
    """Extract text from the provided PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return "Error extracting text from PDF."
    
    return text.strip()


# Load PDF text once at startup
pdf_text = extract_text_from_pdf(PDF_PATH)


def is_question_relevant(question):
    """Determines if a user's question is related to opioids and related topics."""
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
    except openai.OpenAIError as e:
        print(f"OpenAI API Error: {e}")  # Logs the error for debugging
        return False


def get_gpt3_response(question, context):
    """Generates a response from OpenAI using the extracted PDF context."""
    opioid_context = (
        "Assume the user is always asking about opioids or related topics like overdose, addiction, withdrawal, "
        "painkillers, fentanyl, heroin, and narcotics, even if they don't explicitly mention 'opioids'."
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
    except openai.OpenAIError as e:
        return f"OpenAI API Error: {str(e)}"


@app.route("/")
def index():
    """Render the chatbot web interface."""
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    """Handle user questions and return chatbot responses."""
    user_question = request.form.get("question", "").strip()

    if not user_question:
        return jsonify({"answer": "Please ask a valid question."})

    if is_question_relevant(user_question):
        answer = get_gpt3_response(user_question, pdf_text)
    else:
        answer = "Sorry, I can only answer questions related to opioids, addiction, overdose, or withdrawal."

    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Allows external access
