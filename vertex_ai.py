import os
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, HttpOptions
from dotenv import load_dotenv
import config  # Import the config file
import json
from bs4 import BeautifulSoup

def initialize_genai_client():
    if not config.PROJECT_ID or not config.LOCATION:
        raise ValueError("Both GOOGLE_PROJECT_ID and GOOGLE_REGION must be set in the config.")
    
    client = genai.Client(
        vertexai=True,
        project=config.PROJECT_ID,
        location=config.LOCATION,
        http_options=types.HttpOptions(api_version='v1')
    )
    return client

# Function to read the system instruction from a text file
def read_file(file_path: str) -> str:
    """
    Read the system instruction from a file.

    :param file_path: Path to the text file containing the system instruction
    :return: The content of the file as a string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"System instruction file '{file_path}' not found.")
    
    with open(file_path, 'r') as file:
        return file.read()

# Function to clean the HTML content using a system instruction
def clean_html_content_with_instruction(html_content: str, system_instruction: str) -> str:
    """
    Clean the HTML content by using a system instruction and returning the text content.
    This function will parse the HTML content, extract the meaningful text, and clean it.

    :param html_content: The raw HTML content as a string
    :param system_instruction: The system instruction to guide the cleaning of the HTML content
    :return: The cleaned plain text
    """
    if not html_content:
        return ""

    # Use BeautifulSoup to clean the HTML content and extract text
    soup = BeautifulSoup(html_content, 'html.parser')

    # Debugging step 1: Print raw parsed content
    print("Raw parsed HTML:", soup.prettify())
    
    # Extract text from paragraphs
    paragraphs = soup.find_all('p')
    cleaned_paragraphs = "\n".join([para.get_text(strip=True) for para in paragraphs])

    # Debugging step 2: Check extracted paragraphs
    print("Cleaned paragraphs:", cleaned_paragraphs)

    # Get tables as well (in markdown format)
    tables = soup.find_all('table')
    table_markdown = ""
    for table in tables:
        table_data = []
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            table_data.append([cell.get_text(strip=True) for cell in cells])

        # Convert table to markdown format
        table_markdown += convert_table_to_markdown(headers, table_data)

    # Combine paragraphs and tables into cleaned content
    cleaned_content = cleaned_paragraphs + "\n" + table_markdown
    
    # Debugging step 3: Print final cleaned content before returning
    print("Final cleaned content:", cleaned_content)

    return cleaned_content

def convert_table_to_markdown(headers, rows):
    """
    Converts a table (headers + rows) into a markdown formatted table string.

    :param headers: List of header values
    :param rows: List of rows, each containing a list of cell values
    :return: String representation of the table in markdown format
    """
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        markdown_table += "| " + " | ".join(row) + " |\n"
    return markdown_table

def construct_prompt(cleaned_content: str, system_instruction: str) -> str:
    """
    Construct the final prompt to send to the model for content cleaning and summarization.
    """
    prompt = f"{system_instruction}\n\nContent to analyze:\n{cleaned_content}\n"
    
    # Debugging step 4: Print the generated prompt
    print("Constructed Prompt:", prompt)

    return prompt

def call_model(prompt: str) -> str:
    """
    Call the model using the prompt, and handle the response.

    :param prompt: The prompt to send to the model for analysis
    :return: The cleaned content from the model's response
    """
    
    client = initialize_genai_client()
    
    try:
        # Calling the model with the prompt and configuration

        cleaned_content_response=client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents='high',
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=1,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT"]
        )
    )


        """
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]


        # Call the model and process the response stream
        for chunk in client.models.generate_content_stream(
            model=config.MODEL_ID,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=8192,
                response_modalities=["TEXT"]
            )
        ):
            cleaned_content = chunk.text.strip()"""

        # Print the full response to inspect the structure
        print(f"Full response: {cleaned_content_response}")
        
        # Extracting the cleaned content from the response (assuming it's stored in a field called 'text' or similar)
        cleaned_content = cleaned_content_response.candidates[0].content.parts[0].text.strip()
        print(f"Cleaned Content: {cleaned_content}")


        # Return the cleaned content
        return cleaned_content

    except Exception as e:
        print(f"Error while generating content: {e}")
        return ""


# Function to categorize the case based on the cleaned content
def categorize_case_with_genai(cleaned_content: str) -> str:
    """
    Categorizes the case type based on the cleaned content using Google GenAI.

    :param cleaned_content: The cleaned content as a string
    :return: The categorized case type as a string
    """
    if not cleaned_content.strip(): # Check if content is empty after cleaning
        return "General"
    
    # Define the system instruction to pass to GenAI
    system_instruction = """
    You are an intelligent assistant that categorizes case types based on the content of the email provided.
    The possible valid case types are:

    1. VODC7
    2. VODG9
    3. VODB6
    4. VODE6
    5. VODJ7

    If the content of the email matches any of these case types, return that case type. 
    If no match is found, return 'General'. 
    Please identify the case type based on the content and respond with the correct case type.
    """

    # Combine the system instruction with the cleaned content
    prompt = f"{system_instruction}\n\nContent: {cleaned_content}\n\nCase Type:"
    print(f"System Prompt: {prompt}")

    # Initialize the GenAI client
    client = initialize_genai_client()

    # Create the content that the model will process
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ]
   
    # Create a request for generating content based on the system instruction and email content
    #prompt = f"{system_instruction}\n\nContent: {cleaned_content}\n\nCase Type:"
    
    # Call Google GenAI to get the case type based on the prompt
    try:
        # Generate content using the correct method
        response = client.models.generate_content(
            model=config.MODEL_ID,
            contents=contents,
            config=GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=50
            )
        )

        # Debugging: Print the response to see its structure
        print(f"GenAI Response: {response}")

        # Extract the case type from the response
        case_type = response.candidates[0].content.parts[0].text.strip()

        # Validate the case type, if it's not in the allowed list, return "General"
        valid_case_types = ['VODC7', 'VODG9', 'VODB6', 'VODE6', 'VODJ7']
        
        if case_type not in valid_case_types:
            return "General"
        
        return case_type

    except Exception as e:
        print(f"Error during GenAI processing: {e}")
        return "General"

# Main function to clean the HTML and categorize the case
def process_email_content(email_data: dict, system_instruction_file: str) -> dict:
    """
    Processes the email content by first cleaning the HTML and then categorizing the case type.

    :param email_data: The email data containing the content to process
    :param system_instruction_file: Path to the txt file containing the system instruction
    :return: A dictionary containing the cleaned content and the categorized case type
    """
    # Step 1: Read the system instruction
    try:
        system_instruction = read_file(system_instruction_file)
    except FileNotFoundError as e:
        return {"error": str(e)}

    # Step 2: Extract the email content
    content = email_data.get('content')
    if not content:
        return {"error": "'content' field is missing in email data."}

    # Step 3: Clean the HTML content using the system instruction
    cleaned_content = clean_html_content_with_instruction(content, system_instruction)

    # Step 4: Construct the final prompt
    prompt = construct_prompt(cleaned_content, system_instruction)

    # Step 5: Call the model with the prompt
    cleaned_content_from_model = call_model(prompt)
    
    # Step 6: Categorize the case based on the cleaned content
    case_type = categorize_case_with_genai(cleaned_content_from_model)

    # Return the result
    return {
        "cleaned_content": cleaned_content_from_model,
        "case_type": case_type
    }

def generate_sql_query(system_prompt: str, case_type: str) -> str:
    try:
        client = initialize_genai_client()
        contents = [
            types.Content(
                role="system",
                parts=[types.Part(text=system_prompt)]
            )
        ]
        
        # Generate content with the AI model
        result = client.models.generate_content(
            model=config.MODEL_ID,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=8192,
                response_modalities=["TEXT"]
            )
        )
        return result.text
    
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None

def summarize_case_log(cleaned_content: str) -> str:
    """
    Summarize the case log using the GenAI's 'gemini-2.0-flash-001' model.

    :param cleaned_content: The cleaned content that needs summarization.
    :return: The summarized case log content.
    """
    client = initialize_genai_client()  # Initialize the GenAI client 

    try:
        # Call the model to summarize the content using the provided client
        response = client.models.generate_content(
            model=config.MODEL_ID,  # Use the specified model ID
            contents=cleaned_content,  # Directly pass the cleaned content here
            config=types.GenerateContentConfig(
                system_instruction="Summarize the case log",
                temperature=1,
                top_p=0.95,
                max_output_tokens=1024,  # Adjust token limits based on the expected summary length
                response_modalities=["TEXT"],
            ),
        )

        # Extract and return the summarized content from the response
        summarized_content = response.candidates[0].content.parts[0].text
        print("Summarized Case Log:", summarized_content)

        return summarized_content

    except Exception as e:
        print(f"Error summarizing case log: {e}")
        return "An error occurred while summarizing the case log."

# Generate operator response based on case summary
def generate_operator_response(summary: str) -> dict:
    """
    Generate an actionable response for an operator based on the case summary.

    :param summary: The summary of the case.
    :return: A dictionary representing the operator's actionable response.
    """
    return {
        "role": "Operator",
        "message": f"Operator actionable response based on the case: {summary}"
    }