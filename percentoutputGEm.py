import os
import pandas as pd
import PyPDF2
import google.generativeai as genai
from tqdm import tqdm
import concurrent.futures
from functools import partial

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return text

def analyze_with_gemini(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    Context: In October 2023, President Biden signed Executive Order (EO) 14110 titled, "Executive Order on Safe, Secure, and Trustworthy Development and Use of Artificial Intelligence". This Executive Order called on many agencies in the U.S. government to ask the U.S. public for feedback on how they think the Executive Order should be improved. The text that follows is one of the feedback messages from the public to the National Institute of Standards and Technology (NIST) government agency. 

1. Model Security and Vulnerability Testing: Concerns about AI's impact on personal privacy, the effectiveness of data protection strategies, and alternatives for securing sensitive data.
2. Data Privacy and Protection Mechanisms: Concerns about AI's impact on personal privacy, the effectiveness of data protection strategies, and alternatives for securing sensitive data.
3. AI Governance Frameworks: The document may express a strong opinion on AI governance, risk classification, and regulatory oversight.
4. Content Authenticity: Deepfake Detection, and Digital Provenance Advocacy: Strategies for verifying AI-generated content, tracking content origins, and mitigating misinformation risks.
5. Global Standards and International Cooperation: The need for AI regulations to align with global standards while balancing national security interests, geopolitical dynamics, and equitable participation among global stakeholders.
6. Industry, Labor, and Intellectual Property: Industry-specific concerns about AI disrupting labor markets, creative industries, and intellectual property rights.
7. Ethical Development and Societal Impact: Broader concerns about AI's societal implications, including fairness, bias, and ethical design principles.
8. Energy and Environmental Sustainability: Broader concerns about AI’s long-term impact on natural resources, ecosystems, and energy consumption.
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
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"API Error: {e}")
        return "Testing: 0\nPrivacy: 0\nGovernance: 0\nAuth: 0\nGlobal: 0\nLabor: 0\nEthics: 0\nEnergy: 0\nOther: 100"

def parse_percentages(response_text):
    try:
        lines = response_text.strip().split('\n')
        result = {}
        for line in lines:
            if ':' in line:
                category, value = line.split(':', 1)
                category = category.strip()
                try:
                    value = int(value.strip().replace('%', ''))
                    result[category] = value
                except ValueError:
                    result[category] = 0
        categories = ['Testing', 'Privacy', 'Governance', 'Auth', 'Global', 'Labor', 'Ethics', 'Energy', 'Other']
        for category in categories:
            if category not in result:
                result[category] = 0
        
        # Ensure the sum is exactly 100
        current_sum = sum(result.values())
        difference = 100 - current_sum
        if difference != 0:
            sorted_values = sorted(result, key=result.get, reverse=True)
            for cat in sorted_values:
                if difference > 0:
                    result[cat] += 1
                    difference -= 1
                elif difference < 0:
                    result[cat] -= 1
                    difference += 1
                if difference == 0:
                    break
        return result
    except Exception as e:
        print(f"Error parsing response: {e}")
        return {'Testing': 0, 'Privacy': 0, 'Governance': 0, 'Auth': 0, 'Global': 0, 'Labor': 0, 'Ethics': 0, 'Energy': 0, 'Other': 100}

def process_pdf(pdf_file, pdf_directory, api_key):
    pdf_path = os.path.join(pdf_directory, pdf_file)
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"No text extracted from {pdf_file}, skipping.")
        return None
    response = analyze_with_gemini(text, api_key)
    percentages = parse_percentages(response)
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
    pdf_directory = "path to your file"
    desktop_path = "path to your file"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = input("Enter your Gemini API key: ")
    if not os.path.exists(pdf_directory):
        print(f"Directory not found: {pdf_directory}")
        return
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    max_workers = 5
    process_pdf_with_args = partial(process_pdf, pdf_directory=pdf_directory, api_key=api_key)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pdf = {executor.submit(process_pdf_with_args, pdf_file): pdf_file for pdf_file in pdf_files}
        for future in tqdm(concurrent.futures.as_completed(future_to_pdf), total=len(pdf_files), desc="Processing PDFs"):
            pdf_file = future_to_pdf[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
    df = pd.DataFrame(results)
    output_csv = os.path.join(desktop_path, "analysis_resultsGEM.csv")
    output_excel = os.path.join(desktop_path, "analysis_resultsGEM.xlsx")
    numeric_columns = ['Testing', 'Privacy', 'Governance', 'Auth', 'Global', 'Labor', 'Ethics', 'Energy', 'Other']
    df[numeric_columns] = df[numeric_columns].astype(int)
    df.to_csv(output_csv, index=False)
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
        worksheet = writer.sheets['Results']
        # Apply number format for each numeric column
        for col in range(2, 11):  # columns 2 to 10 (inclusive) correspond to our numeric columns
            for row in range(2, len(df) + 2):
                cell = worksheet.cell(row=row, column=col)
                cell.number_format = '0'
    print(f"Analysis complete. Results saved to:")
    print(f"- CSV: {output_csv}")
    print(f"- Excel: {output_excel}")

if __name__ == "__main__":
    main()
