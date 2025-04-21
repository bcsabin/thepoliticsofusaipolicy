import os  # Provides functions for interacting with the operating system
import pandas as pd  # Used for data manipulation and analysis
import PyPDF2  # Library for reading and extracting text from PDF files
import openai  # OpenAI Python library to interact with GPT models
from tqdm import tqdm  # Provides a progress bar for loops
import concurrent.futures  # For parallel execution using threads
from functools import partial  # Allows partial function application

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.

    Parameters:
        pdf_path (str): The file path to the PDF.

    Returns:
        str: Extracted text from all pages of the PDF.
    """
    text = ""
    try:
        # Open the PDF file in binary read mode
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            # Loop through each page and extract text
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        # Print an error message if extraction fails
        print(f"Error extracting text from {pdf_path}: {e}")
    return text

def analyze_with_gpt(text, api_key):
    """
    Sends the extracted text to the GPT o3 mini model using OpenAI's API for analysis and retrieves the response.

    Parameters:
        text (str): The text extracted from the PDF.
        api_key (str): API key for authentication with the OpenAI service.

    Returns:
        str: The text response from the GPT model.
    """
    # Set the OpenAI API key
    openai.api_key = api_key
    
    # Define the prompt with context, instructions, and the text for analysis.
    # The output should include percentages for Testing, Privacy, Governance, Auth, Global, Labor, Ethics, Energy, and Other that sum to 100.
    prompt = f"""
    Context: In October 2023, President Biden signed Executive Order (EO) 14110 titled, "Executive Order on Safe, Secure, and Trustworthy Development and Use of Artificial Intelligence". This Executive Order called on many agencies in the U.S. government to ask the U.S. public for feedback on how they think the Executive Order should be improved. The text that follows is one of the feedback messages from the public to the National Institute of Standards and Technology (NIST) government agency. 

1. Model Security and Vulnerability Testing: Concerns about AI's impact on personal privacy, the effectiveness of data protection strategies, and alternatives for securing sensitive data.
2. Data Privacy and Protection Mechanisms: Concerns about AI's impact on personal privacy, the effectiveness of data protection strategies, and alternatives for securing sensitive data.
3. AI Governance Frameworks: The document may express a strong opinion on AI governance, risk classification, and regulatory oversight.
4. Content Authenticity: Deepfake Detection, and Digital Provenance Advocacy: Strategies for verifying AI-generated content, tracking content origins, and mitigating misinformation risks.
5. Global Standards and International Cooperation: The need for AI regulations to align with global standards while balancing national security interests, geopolitical dynamics, and equitable participation among global stakeholders.
6. Industry, Labor, and Intellectual Property: Industry-specific concerns about AI disrupting labor markets, creative industries, and intellectual property rights.
7. Ethical Development and Societal Impact: Broader concerns about AI's societal implications, including fairness, bias, and ethical design principles.
8. Energy and Environmental Sustainability: Concerns about the long-term impact on natural resources, ecosystems, and energy consumption.
9. Other (anything not fitting the above categories)

    You will evaulate the percent of each document that is discussing each of these main topics. The percentages must sum to exactly 100%. 

    Provide ONLY the percentages as whole numbers (e.g., 13 not 12.5%) in this exact format:
    Testing: A
    Privacy: B
    Governance: C
    Auth: D
    Global: E
    Labor: F
    Ethics: G
    Energy: H
    Other: I

    Text for analysis:
    {text}
    """
    try:
        # Use OpenAI's ChatCompletion endpoint to generate the content
        response = openai.ChatCompletion.create(
            model="o3-mini",  # Specify the GPT o3 mini model
            messages=[
                {"role": "user", "content": prompt}
            ],

        )
        # Extract the content from the response
        return response['choices'][0]['message']['content']
    except Exception as e:
        # In case of API errors, print an error message and return a default response
        print(f"API Error: {e}")
        # Default response with Energy set to 0 and Other adjusted so the sum is 100
        return "Testing: 0\nPrivacy: 0\nGovernance: 0\nAuth: 0\nGlobal: 0\nLabor: 0\nEthics: 0\nEnergy: 0\nOther: 100"

def parse_percentages(response_text):
    """
    Parses the GPT model's response and extracts percentage values for each category.

    Parameters:
        response_text (str): The text output from the GPT model.

    Returns:
        dict: A dictionary with categories as keys and their respective percentage values as integers.
    """
    try:
        lines = response_text.strip().split('\n')
        result = {}
        # Process each line of the response
        for line in lines:
            if ':' in line:
                category, value = line.split(':', 1)
                category = category.strip()
                try:
                    # Remove any percentage symbol and convert the value to an integer
                    value = int(value.strip().replace('%', ''))
                    result[category] = value
                except ValueError:
                    # If conversion fails, default the value to 0
                    result[category] = 0
        
        # Define the expected categories including the new 'Energy'
        categories = ['Testing', 'Privacy', 'Governance', 'Auth', 'Global', 'Labor', 'Ethics', 'Energy', 'Other']
        for category in categories:
            # Ensure every expected category is present in the dictionary
            if category not in result:
                result[category] = 0
        
        # Adjust percentages so that their sum is exactly 100
        current_sum = sum(result.values())
        difference = 100 - current_sum
        if difference != 0:
            # Sort categories by their value (largest first) to adjust percentages proportionally
            sorted_values = sorted(result, key=result.get, reverse=True)
            for val in sorted_values:
                if difference > 0:
                    result[val] += 1
                    difference -= 1
                elif difference < 0:
                    result[val] -= 1
                    difference += 1
                if difference == 0:
                    break
        return result
    except Exception as e:
        print(f"Error parsing response: {e}")
        # Return a default set of percentages if parsing fails
        return {'Testing': 0, 'Privacy': 0, 'Governance': 0, 'Auth': 0, 'Global': 0, 'Labor': 0, 'Ethics': 0, 'Energy': 0, 'Other': 100}

def process_pdf(pdf_file, pdf_directory, api_key):
    """
    Processes a single PDF file:
      - Extracts text from the PDF.
      - Analyzes the text with the GPT o3 mini model.
      - Parses the response for percentage data.
      - Returns a dictionary of results for that PDF.

    Parameters:
        pdf_file (str): The name of the PDF file.
        pdf_directory (str): The directory where the PDF file is located.
        api_key (str): The API key for the OpenAI service.

    Returns:
        dict or None: A dictionary containing the filename and category percentages, or None if extraction fails.
    """
    # Build the full file path for the PDF
    pdf_path = os.path.join(pdf_directory, pdf_file)
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"No text extracted from {pdf_file}, skipping.")
        return None
    # Analyze the extracted text with the GPT model
    response = analyze_with_gpt(text, api_key)
    # Parse the GPT response to extract percentage values
    percentages = parse_percentages(response)
    # Organize the results into a dictionary, including the new 'Energy' category
    result = {
        'Filename': pdf_file,
        'Testing': percentages.get('Testing', 0),
        'Privacy': percentages.get('Privacy', 0),
        'Governance': percentages.get('Governance', 0),
        'Auth': percentages.get('Auth', 0),
        'Global': percentages.get('Global', 0),
        'Labor': percentages.get('Labor', 0),
        'Ethics': percentages.get('Ethics', 0),
        'Energy': percentages.get('Energy', 0),
        'Other': percentages.get('Other', 0)
    }
    return result

def main():
    """
    Main function to:
      - Set up paths and API key.
      - Process all PDF files in the specified directory concurrently.
      - Save the analysis results to both CSV and Excel formats on the desktop.
    """
    # Directory containing PDF files to analyze
    pdf_directory = "path to your file"
    # Path to the desktop where results will be saved
    desktop_path = "path to your file"
    # Retrieve the API key from environment variables or prompt the user
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Enter your OpenAI API key: ")
    
    # Check if the specified PDF directory exists
    if not os.path.exists(pdf_directory):
        print(f"Directory not found: {pdf_directory}")
        return
    
    # List all PDF files in the directory (case-insensitive match for .pdf extension)
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    # Maximum number of worker threads for concurrent processing
    max_workers = 5
    # Use partial to fix pdf_directory and api_key arguments for the process_pdf function
    process_pdf_with_args = partial(process_pdf, pdf_directory=pdf_directory, api_key=api_key)
    results = []
    
    # Process PDF files concurrently using a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map each PDF file to a future for concurrent processing
        future_to_pdf = {executor.submit(process_pdf_with_args, pdf_file): pdf_file for pdf_file in pdf_files}
        # Use tqdm to show a progress bar as futures complete
        for future in tqdm(concurrent.futures.as_completed(future_to_pdf), total=len(pdf_files), desc="Processing PDFs"):
            pdf_file = future_to_pdf[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
    
    # Create a DataFrame from the list of results
    df = pd.DataFrame(results)
    # Define paths for output CSV and Excel files
    output_csv = os.path.join(desktop_path, "analysis_resultsGPT.csv")
    output_excel = os.path.join(desktop_path, "analysis_resultsGPT.xlsx")
    # Ensure numeric columns are treated as integers, including the new 'Energy' column
    numeric_columns = ['Testing', 'Privacy', 'Governance', 'Auth', 'Global', 'Labor', 'Ethics', 'Energy', 'Other']
    df[numeric_columns] = df[numeric_columns].astype(int)
    # Save the DataFrame to CSV
    df.to_csv(output_csv, index=False)
    # Save the DataFrame to an Excel file with number formatting for numeric columns
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
        worksheet = writer.sheets['Results']
        # Format numeric columns to display numbers without decimals
        for col in range(2, 11):  # Columns 2 to 10 correspond to the numeric values in the Excel sheet
            for row in range(2, len(df) + 2):
                cell = worksheet.cell(row=row, column=col)
                cell.number_format = '0'
    
    # Print confirmation messages with the output file paths
    print(f"Analysis complete. Results saved to:")
    print(f"- CSV: {output_csv}")
    print(f"- Excel: {output_excel}")

if __name__ == "__main__":
    # Execute the main function when the script is run directly
    main()
