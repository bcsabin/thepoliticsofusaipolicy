import os
import fitz  # PyMuPDF
import pandas as pd
import google.generativeai as genai
import concurrent.futures
from functools import partial
from absl import app
from absl import logging

# Initialize Abseil logging
logging.set_verbosity(logging.INFO)

# Set up Google Gemini API Key (Ensure to store securely)
GENAI_API_KEY = "yourkeyhere"  # Load API key from environment variable
genai.configure(api_key=GENAI_API_KEY)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
    return text

def read_prompt_from_file(prompt_file):
    """Read the AI call prompt from a text file."""
    try:
        with open(prompt_file, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.error(f"Error: Prompt file '{prompt_file}' not found.")
        return None

def analyze_text_with_gemini(text, question):
    """Send text to the Gemini model with a specific question."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"{question}\n\n{text}"
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error analyzing text with Gemini: {e}")
        return None

def process_pdf(pdf, documents_path, question):
    """Process a single PDF file."""
    pdf_path = os.path.join(documents_path, pdf)
    text = extract_text_from_pdf(pdf_path)
    if text:
        analysis_results = {"PDF File": pdf}
        response = analyze_text_with_gemini(text, question)
        analysis_results["Response"] = response
        return analysis_results
    return None

def main(_):
    documents_path = os.path.expanduser("path to your file")
    output_path = os.path.expanduser("path to your file")
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    pdf_files = [f for f in os.listdir(documents_path) if f.endswith(".pdf")]
    
    prompt_file = "path to your prompt"  # Path to the text file containing the prompt
    question = read_prompt_from_file(prompt_file)

    if not question:
        logging.error("No prompt available. Exiting.")
        return

    results = []
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a partial function with the fixed arguments
        process_func = partial(process_pdf, documents_path=documents_path, question=question)
        
        # Process PDFs in parallel
        for result in executor.map(process_func, pdf_files):
            if result:
                results.append(result)
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logging.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    app.run(main)