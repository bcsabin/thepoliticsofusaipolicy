import os
import fitz  # PyMuPDF
import pandas as pd
import concurrent.futures
import time
from tqdm import tqdm  # For progress tracking

# Set up OpenAI API Key (Ensure to store securely)
OPENAI_API_KEY = "your key here"  # Replace with your own API key

# Import OpenAI with error handling for different versions
try:
    # For newer versions of the openai package (>=1.0.0)
    from openai import OpenAI
    
    def analyze_text_with_openai(text, question):
        """Send text to the OpenAI GPT model with a specific question using new client."""
        prompt = f"{question}\n\n{text}"

        try:
            client = OpenAI(api_key=OPENAI_API_KEY)  # Create OpenAI client instance
            response = client.chat.completions.create(
                model="o3-mini",  # Change to "gpt-4-turbo" if needed
                messages=[
                    {"role": "system", "content": "You are an AI assistant analyzing text."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error analyzing text with OpenAI: {e}")
            return None
            
except (ImportError, AttributeError):
    # For older versions of the openai package (<1.0.0)
    import openai
    
    def analyze_text_with_openai(text, question):
        """Send text to the OpenAI GPT model with a specific question using legacy client."""
        prompt = f"{question}\n\n{text}"

        try:
            openai.api_key = OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="o3-mini",  # Change to "gpt-4-turbo" if needed
                messages=[
                    {"role": "system", "content": "You are an AI assistant analyzing text."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error analyzing text with OpenAI: {e}")
            return None

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

def read_prompt_from_file(prompt_file):
    """Read the AI call prompt from a text file."""
    try:
        with open(prompt_file, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: Prompt file '{prompt_file}' not found.")
        return None

def process_pdf(pdf_path, question):
    """Process a single PDF file and return its analysis results."""
    pdf_name = os.path.basename(pdf_path)
    text = extract_text_from_pdf(pdf_path)
    if text:
        response = analyze_text_with_openai(text, question)
        return {"PDF File": pdf_name, "Response": response}
    return {"PDF File": pdf_name, "Response": None}

def main():
    start_time = time.time()
    documents_path = os.path.expanduser("your file location here")
    output_path = os.path.expanduser("your file location here")
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    pdf_files = [f for f in os.listdir(documents_path) if f.endswith(".pdf")]
    
    prompt_file = "your text file location here"
    question = read_prompt_from_file(prompt_file)

    if not question:
        print("No prompt available. Exiting.")
        return

    results = []
    total_files = len(pdf_files)
    
    print(f"Processing {total_files} PDF files in parallel...")
    
    # Using ThreadPoolExecutor for I/O bound operations (PDF reading, API calls)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of futures
        future_to_pdf = {
            executor.submit(process_pdf, os.path.join(documents_path, pdf), question): pdf 
            for pdf in pdf_files
        }
        
        # Process as they complete
        for future in tqdm(concurrent.futures.as_completed(future_to_pdf), total=total_files, desc="Processing PDFs"):
            pdf = future_to_pdf[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as exc:
                print(f"{pdf} generated an exception: {exc}")
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    
    elapsed_time = time.time() - start_time
    print(f"Results saved to {output_path}")
    print(f"Total processing time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()