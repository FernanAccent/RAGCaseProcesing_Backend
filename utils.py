import re
from models import CasesCannedResponse, CaseTypeScenario
from database import get_db
from sqlalchemy.orm import Session
from vertex_ai import generate_sql_query


# Clean up HTML content by removing tags
def clean_html_content(html_content: str) -> str:
    if not html_content:
        return ""
    clean_text = re.sub(r'<[^>]*>', '', html_content)  # Removing HTML tags
    return clean_text

# Check if required email fields are present
def check_email_fields(email_data: dict, required_fields: list) -> list:
    missing_fields = []
    if not email_data:
        return required_fields  # If email data itself is missing, all fields are missing
    
    for field in required_fields:
        if field not in email_data or not email_data[field]:
            missing_fields.append(field)
    
    return missing_fields

# Extract case information such as case number, title, and asset details
def extract_case_info(email_content: str) -> dict:
    case_info = {
        'case_number': None,
        'case_title': None,
        'assets': []
    }

    if not email_content:
        return case_info
    
    case_info['case_number'] = re.search(r'Case Number: (\d+)', email_content)
    if case_info['case_number']:
        case_info['case_number'] = case_info['case_number'].group(1)

    case_info['case_title'] = re.search(r'Case Title: (.*)', email_content)
    if case_info['case_title']:
        case_info['case_title'] = case_info['case_title'].group(1)

    # Update this to return a list of dictionaries, each representing an asset
    assets = re.findall(r'Asset ID: (\w+)', email_content)
    for asset_id in assets:
        # Create a dictionary for each asset
        asset_dict = {
            "Asset ID": asset_id,
            "Name": f"Asset {asset_id}",  # Example: name could be generated based on the ID or parsed from email
        }
        case_info['assets'].append(asset_dict)

    return case_info


# Extract Category, Package ID, Network ID, AL ID, Partner ID for the first asset
def extract_asset_details(asset):
    # Placeholder logic for extracting details from the asset
    asset_details = {
        "Provider ID": "Provider123",  # Example, replace with real extraction logic
        "ALID/PAID": "AL12345",        # Example, replace with real extraction logic
        "Title": "Asset Title",         # Example, replace with real extraction logic
    }
    return asset_details

# Summarize the case log using a LLM (AI model)
def summarize_case_log(content):
    # Placeholder logic for summarizing case log
    return f"Summary of the case: {content[:100]}..."  # Simple truncation as an example

# Generate actionable response for Operator
def generate_operator_response(summary):
    # Placeholder logic for generating response
    return {
        "role": "Operator",
        "message": f"Operator actionable response based on the case: {summary}"
    }

def generate_actionable_response(role: str, message: str) -> dict:
    """
    Generate a structured actionable response with a role and message.
    
    :param role: The role responsible for the action (e.g., 'Operator', 'Partner').
    :param message: The actionable message to be communicated.
    :return: A dictionary representing the actionable response.
    """
    return {
        "role": role,
        "message": message
    }

def get_canned_response(case_type, scenario):
    """
    Retrieve the canned response based on case_type and scenario using SQLAlchemy ORM.

    :param case_type: The type of the case.
    :param scenario: The scenario associated with the case.
    :return: The canned response if found, or a default message if not.
    """
    try:
        # Get the database session using SQLAlchemy ORM
        db: Session = next(get_db())

        # Query the database for the canned response using SQLAlchemy ORM
        response = db.query(CasesCannedResponse.canned_response).filter(
            CasesCannedResponse.case_type == case_type,
            CasesCannedResponse.scenario == scenario
        ).first()

        # Return the canned response if found, otherwise a default message
        return response[0] if response else "No canned response found."
    
    except Exception as e:
        print(f"Error fetching canned response: {e}")
        return "Error fetching canned response."

def get_case_type_scenarios(case_type: str):
    """
    Retrieve resolution steps from the database based on the given case_type.
    
    :param case_type: The case type for which the scenarios are fetched.
    :return: A list of scenarios (prompt_type, system_prompt) for the given case_type.
    """
    try:
        # Get the database session using SQLAlchemy ORM
        db: Session = next(get_db())
        
        # Query the database using SQLAlchemy ORM
        scenarios = db.query(CaseTypeScenario).filter(CaseTypeScenario.case_type == case_type).order_by(CaseTypeScenario.prompt_number).all()

        # Format the results into a list of dictionaries
        formatted_scenarios = [
            {"prompt_type": scenario.prompt_type, "system_prompt": scenario.system_prompt}
            for scenario in scenarios
        ]
        
        return formatted_scenarios

    except Exception as e:
        print(f"Error fetching case type scenarios: {e}")
        return []


# Process assets based on resolution steps
def process_assets(case_details, case_type):
    resolution_steps = get_case_type_scenarios(case_type)

    valid_assets = []
    invalid_assets = []
    successful_output_list = []
    unsuccessful_output_list = []

    for asset in case_details["assets"]:
        for step in resolution_steps:
            if step['prompt_type'] == 'Asset Validation':
                result = generate_sql_query(step['system_prompt'], asset)
                if result == 0:
                    invalid_assets.append(asset)
                else:
                    valid_assets.append(asset)

            elif step['prompt_type'] == 'Output' and asset not in invalid_assets:
                result = generate_sql_query(step['system_prompt'], asset)
                if result == 1:
                    successful_output_list.append(asset)
                else:
                    unsuccessful_output_list.append(asset)

    return valid_assets, invalid_assets, successful_output_list, unsuccessful_output_list


# Validate asset information
def validate_asset(assets: list) -> dict:
    """
    Validate the given assets based on specific criteria.
    :param assets: List of assets to be validated.
    :return: A dictionary with 'valid' as a boolean key, indicating if all assets are valid.
    """
    valid_assets = []
    missing_fields_list = []

    if not assets or len(assets) == 0:
        return {"valid": False, "error": "No assets provided."}

    # Validate each asset
    for asset in assets:
        if not asset.get("Asset ID"):
            missing_fields_list.append(f"Asset ID missing for {asset.get('Name', 'Unknown Asset')}")
        else:
            valid_assets.append(asset)

    # If missing fields found, return invalid
    if missing_fields_list:
        return {"valid": False, "error": missing_fields_list}
    
    return {"valid": True}
