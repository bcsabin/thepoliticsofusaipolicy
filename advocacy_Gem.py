import os
import fitz  # PyMuPDF
import pandas as pd
import google.generativeai as genai
import concurrent.futures
from functools import partial

# Set up Google Gemini API Key (Ensure to store securely)
GENAI_API_KEY = "your api key"
genai.configure(api_key=GENAI_API_KEY)

# Define categories
CATEGORIES = ["Testing", "Privacy", "Governance", "Auth", "Global", "Labor", "Ethics", "Energy"]

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text

def analyze_text_with_gemini(text, question):
    """Send text to the Gemini model with a specific question."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"{question}\n\n{text}"
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error analyzing text with Gemini: {e}")
        return None

def load_question(question_file):
    """Load a question from a text file."""
    with open(question_file, "r", encoding="utf-8") as file:
        return file.read().strip()

def process_pdf(pdf, documents_path, questions):
    """Process a single PDF file with multiple questions."""
    pdf_path = os.path.join(documents_path, pdf)
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return {"PDF File": pdf, **{category: None for category in CATEGORIES}}
    
    results = {"PDF File": pdf}
    
    # Process each question separately, ensuring AI memory is cleared per file
    for category, question in questions.items():
        result = analyze_text_with_gemini(text, question)
        results[category] = result
    
    return results

def main():
    documents_path = os.path.expanduser("path to your file")  # Set your path
    output_path = os.path.expanduser("path to your file")  # Set your path
    
    # Define file paths for each question category
    question_paths = {category: os.path.expanduser(f"path to your file {category}_Question.txt") for category in CATEGORIES}
    
    pdf_files = [f for f in os.listdir(documents_path) if f.endswith(".pdf")]
    
    # Load questions from respective files
    questions = {category: load_question(path) for category, path in question_paths.items()}
    
    results = []
    
    # Process PDFs sequentially (ensuring memory is cleared per file)
    for pdf in pdf_files:
        result = process_pdf(pdf, documents_path, questions)
        results.append(result)
    
    # Convert results to DataFrame and save
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
