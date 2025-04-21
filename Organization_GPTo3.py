import os
import fitz  # PyMuPDF
import pandas as pd
import openai
import concurrent.futures
import time

# Set up OpenAI API Key (Ensure to store securely)
OPENAI_API_KEY = "yourkeyhere"
openai.api_key = OPENAI_API_KEY

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

def analyze_text_with_openai(text, question):
    """Send text to the OpenAI model with a specific question."""
    try:
        response = openai.ChatCompletion.create(
            model="o3-mini",  # o3-mini equivalent
            messages=[
                {"role": "user", "content": f"{question}\n\n{text}"}
            ],
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error analyzing text with OpenAI: {e}")
        return None

def process_pdf(pdf_file, documents_path):
    """Process a single PDF file and return its analysis results."""
    pdf_path = os.path.join(documents_path, pdf_file)
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return {"PDF File": pdf_file, "Org Title": "N/A", "Main Function": "N/A", "Org Category": "N/A", "Industry": "N/A"}
    
    # Prompt for Org Title
    org_title_question = """Please identify the title of the organization that wrote the feedback message to the government agency. If the feedback message is not written on behalf of an organization, please respond with “N/A”.

    Output Format: If the name is not listed in the text that follows, please respond with “N/A”. If the name is available, please respond with the name. Do not respond with any text besides the name.
    """
    
    analysis_results = {"PDF File": pdf_file}
    
    # Step 1: Extract Org Title
    org_title = analyze_text_with_openai(text, org_title_question)
    analysis_results["Org Title"] = org_title
    
    if org_title and org_title != "N/A":
        # Step 2: Determine Main Function
        main_function_question = f"""This is the name of the organization: {org_title}
       In one sentence, please describe the main function of this organization.

    Output Format: If the organization is titled “N/A” then please respond with “N/A”. Do not include any text besides a sentence about the main function.
    """
        
        main_function = analyze_text_with_openai(text, main_function_question)
        
        # Step 3: Determine Org Category
        org_category_question = f"""This is the name of the organization: {org_title}
        The main function of this organization is: {main_function}
    Please identify which category this organization falls under:
    * University. Definition: An institution of higher education and research that grants academic degrees in various fields of study. Examples: Stanford University’s Human-Centered Artificial Intelligence (HAI), the University of Michigan, or the Stanford RegLab.
    * Research Lab. A dedicated facility where systematic investigation, experimentation, and analysis are conducted to advance knowledge in a specific field. Examples: a political think tank or non-profit organization researching AI.
    * Consortium. Definition: an organization of multiple companies to represent their political beliefs. Examples: AI-Enabled ICT Workforce, TechNet, or the American Association for Independent Music.
    * Corporation. Definition: A company that sells goods or services to customers, conducts business, and generates profit. Examples: OpenAI, Meta, Google, and IBM.
    * Government. Definition: Official organizational unit within a government that is responsible for implementing policies, enforcing laws, and delivering public services. Examples: The European Commission, the U.S. Federal Trade Commission (FTC), or the National Institute of Standards and Technology (NIST).

    Which of the five possible categories - University, Research Lab, Consortium, Corporation, or Government - is this given organization?

    Output Format: If the organization is titled “N/A”, then please respond with “N/A”. Do not include any text besides the category title.
"""
        
        org_category = analyze_text_with_openai(text, org_category_question)

        # Step 4: Determine Industry
        industry_question = f"""This is the name of the organization: {org_title}
        The main function of this organization is: {main_function}
        Please identify which Industry this organization falls under:
*Technology. Definition: Organizations that develop, manufacture, or provide technology solutions, including software, hardware, AI, cloud computing, and emerging digital innovations. This could also include research labs, consortiums, or universities with an explicit focus on Artificial Intelligence or Technology. Examples: Microsoft, Google, IBM, NVIDIA, OpenAI, Stanford HAI, Citizens and Technology Lab at Cornell.


*Military Contractors and National Defense. Definition: Companies and agencies involved in the development, manufacturing, and supply of defense-related products, services, and intelligence. Examples: Lockheed Martin, Northrop Grumman, Raytheon Technologies, BAE Systems, Boeing Defense, DARPA.


*Cyber Security. Definition: Organizations focused on protecting digital systems, networks, and sensitive data from cyber threats, hacking, and unauthorized access. This could also include research labs, consortiums, or universities with an explicit focus on Cybersecurity. Examples: CrowdStrike, Palo Alto Networks, FireEye, Fortinet, Cybersecurity & Infrastructure Security Agency (CISA).


*Telecommunications. Definition: Companies that provide communication infrastructure, internet services, mobile networks, and data transmission solutions. Examples: Verizon, AT&T, T-Mobile, Nokia, Huawei, Qualcomm, USTelecom – The Broadband Association.


*Consulting and Research. Definition: Firms and institutions that provide strategic guidance, data analysis, and policy recommendations across industries. Examples: McKinsey & Company, Boston Consulting Group (BCG), RAND Corporation, Center for Security and Emerging Technology (CSET), Gartner.


*Media and Entertainment. Definition: Companies involved in content creation, broadcasting, digital media, gaming, and film production. Examples: Disney, Warner Bros. Discovery, Netflix, Sony Entertainment, Universal Music Group, Verance Corporation.


*Financial Services. Definition: Businesses providing banking, investment, insurance, and financial technology (FinTech) solutions. Examples: JPMorgan Chase, Goldman Sachs, Visa, PayPal, BlackRock, Square.


*Healthcare. Definition: Organizations involved in medical research, pharmaceuticals, biotechnology, and healthcare services. Examples: Pfizer, Moderna, Mayo Clinic, UnitedHealth Group, Johns Hopkins Center for Health Security.


*Education. Definition: Institutions and organizations involved in academic research, training, and education technology (EdTech). This does not include academic institutions with an explicit focus on technology research, or any other specific domain. Examples: Harvard University, MIT, Coursera, Khan Academy, National Science Foundation.


*Government and Policy. Definition: Public institutions, regulatory bodies, and think tanks shaping national and international policies. Examples: U.S. Department of Defense (DoD), European Commission, Brookings Institution, Center for a New American Security (CNAS).


*Legal. Definition: Law firms, regulatory compliance agencies, and organizations specializing in legal consulting, litigation, and policy enforcement. Examples: American Bar Association, LegalTech startups, or individual law firms.


*Other.

For this prompt, an organization can only be in one industry. What industry is this organization focused on?

Output Format: If the organization is titled “N/A” then please respond with “N/A”. Do not include any text besides the category titled.
"""
        
        industry = analyze_text_with_openai(text, industry_question)
    else:
        # If "Org Title" is "N/A", set all values to "N/A" without making API calls
        main_function = "N/A"
        org_category = "N/A"
        industry = "N/A"
    
    # Store results
    analysis_results["Main Function"] = main_function
    analysis_results["Org Category"] = org_category
    analysis_results["Industry"] = industry
    
    print(f"Processed {pdf_file}")
    return analysis_results

def main():
    documents_path = os.path.expanduser("your file location here")
    pdf_files = [f for f in os.listdir(documents_path) if f.endswith(".pdf")]
    
    results = []
    start_time = time.time()
    
    # Use ThreadPoolExecutor for parallel processing
    # Adjust max_workers based on your system and API rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all PDF processing tasks
        future_to_pdf = {executor.submit(process_pdf, pdf, documents_path): pdf for pdf in pdf_files}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_pdf):
            pdf = future_to_pdf[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f'{pdf} generated an exception: {exc}')
    
    # Convert results to DataFrame and save
    df = pd.DataFrame(results)
    # Reorder columns to match the original order
    df = df[["PDF File", "Org Title", "Org Category", "Industry", "Main Function"]]
    output_path = os.path.join("your file location here")
    df.to_csv(output_path, index=False)
    
    elapsed_time = time.time() - start_time
    print(f"Results saved to {output_path}")
    print(f"Total processing time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()