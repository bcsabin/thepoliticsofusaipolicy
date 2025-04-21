import os
import pandas as pd
import PyPDF2
import google.generativeai as genai
from tqdm import tqdm
import concurrent.futures
from functools import partial

def extract_text_from_pdf(pdf_path):
    """
    Extracts all text content from a PDF file.
    
    Args:
        pdf_path (str): The full path to the PDF file
        
    Returns:
        str: The extracted text content from all pages of the PDF
    """
    text = ""
    try:
        # Open the PDF file in binary mode
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            # Iterate through each page in the PDF
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                # Extract text from the current page and append to the result
                text += page.extract_text()
    except Exception as e:
        # Handle any errors that occur during PDF processing
        print(f"Error extracting text from {pdf_path}: {e}")
    return text

def analyze_with_gemini(text, api_key):
    """
    Sends the extracted PDF text to Google's Gemini AI for analysis.
    
    Args:
        text (str): The extracted text content from the PDF
        api_key (str): The Gemini API key for authentication
        
    Returns:
        str: The analysis results containing main arguments identified in the text
    """
    # Configure the Gemini API with the provided key
    genai.configure(api_key=api_key)
    # Initialize the Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Craft the prompt for Gemini to analyze the text
    prompt = f"""
   Context: In October 2023, President Biden signed Executive Order (EO) 14110 titled, “Executive Order on Safe, Secure, and Trustworthy Development and Use of Artificial Intelligence”. This Executive Order called on many agencies in the U.S. Government to request comments from the  U.S. public for feedback on the Executive Order. The text that follows is one of the feedback comments from the an organization or individual to the National Telecommunications and Information Administration (NTIA) government agency.

   Prompt: Please identify the topics and arguments that the author prioritizes in the document. These topics and arguments are evident in the number of times the author makes a mention, the depth of evidence and commentary to back it up, and the level of emphasis in the author's verbiage.

   Output Format: List the main arguments in concise bullet points, with each point representing a complete thought or position. Separate each bullet point with a newline. Don’t include any text besides the sentences with the arguments. Only the substantial topics in the document are relevant, so do not include secondary topics.

    Text for analysis:
    {text}
    """
    
    try:
        # Send the prompt to Gemini and get the response
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Handle any API errors that occur during analysis
        print(f"API Error: {e}")
        return "Error analyzing document"

def process_pdf(pdf_file, pdf_directory, api_key):
    """
    Process a single PDF file: extract text, analyze with Gemini, and return results.
    
    Args:
        pdf_file (str): The name of the PDF file to process
        pdf_directory (str): The directory containing the PDF file
        api_key (str): The Gemini API key
        
    Returns:
        dict: A dictionary containing the filename and main arguments found in the PDF
    """
    # Construct the full path to the PDF file
    pdf_path = os.path.join(pdf_directory, pdf_file)
    
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Skip processing if no text was extracted
    if not text:
        print(f"No text extracted from {pdf_file}, skipping.")
        return None
    
    # Analyze the extracted text with Gemini
    arguments = analyze_with_gemini(text, api_key)
    
    # Create a dictionary with the results
    result = {
        'Filename': pdf_file,
        'Main Arguments': arguments
    }
    return result

def main():
    """
    Main function that coordinates the processing of all PDF files.
    Handles file discovery, parallel processing, and output generation.
    """
    # Define the directory containing PDF files
    pdf_directory = "your file location"
    # Define the output directory for results
    desktop_path = "your file location"
    
    # Try to get the API key from environment variables
    api_key = os.environ.get("GEMINI_API_KEY")
    # If not found in environment, prompt the user
    if not api_key:
        api_key = input("Enter your Gemini API key: ")
    
    # Check if the PDF directory exists
    if not os.path.exists(pdf_directory):
        print(f"Directory not found: {pdf_directory}")
        return
    
    # Find all PDF files in the directory
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    
    # Exit if no PDF files were found
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    # Set the maximum number of parallel worker threads
    max_workers = 5
    
    # Create a partial function with fixed arguments to simplify parallel processing
    process_pdf_with_args = partial(process_pdf, pdf_directory=pdf_directory, api_key=api_key)
    
    # List to store the processing results
    results = []
    
    # Use ThreadPoolExecutor for parallel processing of PDF files
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all PDF files for processing
        future_to_pdf = {executor.submit(process_pdf_with_args, pdf_file): pdf_file for pdf_file in pdf_files}
        
        # Track progress of the processing tasks
        for future in tqdm(concurrent.futures.as_completed(future_to_pdf), total=len(pdf_files), desc="Processing PDFs"):
            pdf_file = future_to_pdf[future]
            try:
                # Get the result of the processing
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                # Handle any errors that occur during processing
                print(f"Error processing {pdf_file}: {e}")
    
    # Create a DataFrame from the results
    df = pd.DataFrame(results)
    
    # Define output file paths
    output_csv = os.path.join(desktop_path, "arguments_NTIA_Gem2.csv")
    output_excel = os.path.join(desktop_path, "arguments_NTIA_Gem2.xlsx")
    
    # Save results to CSV
    df.to_csv(output_csv, index=False)
    
    # Save results to Excel with formatting
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # Write the data to the Excel file
        df.to_excel(writer, index=False, sheet_name='Arguments')
        
        # Auto-adjust column widths for better readability
        worksheet = writer.sheets['Arguments']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))  # No maximum length limit
                except:
                    pass
            adjusted_width = (max_length + 2)  # Add some padding
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # Print confirmation and output file locations
    print(f"Analysis complete. Results saved to:")
    print(f"- CSV: {output_csv}")
    print(f"- Excel: {output_excel}")

# Standard Python idiom to check if the script is being run directly (not imported)
if __name__ == "__main__":
    main()