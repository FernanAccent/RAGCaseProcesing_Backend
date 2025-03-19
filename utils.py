import re, json
#from models import CaseTypeResolution,ResolutionSteps
#from database import get_db
#from sqlalchemy.orm import Session
from werkzeug.exceptions import HTTPException

# Load case configuration data from the JSON file
with open('case_config.json', encoding='utf-8') as config_file:
    case_config = json.load(config_file)

def retrieve_resolution_steps(case_type: str) -> str:
    """
    Retrieve resolution steps for a given case type from case_config.json.

    :param case_type: The case type to retrieve resolution steps for.
    :return: A string containing the resolution steps.
    """
    # Check if the case_type exists in the case_config
    case_type_config = case_config.get(case_type)

    if not case_type_config or "resolution_steps" not in case_type_config:
        return ""

    # Return the resolution steps for the given case type
    return case_type_config["resolution_steps"]

def get_canned_response(case_type: str) -> str:
    """
    Fetch the canned response based on the case type from case_config.json.

    :param case_type: The case type to retrieve the canned response for.
    :return: The canned response as a string.
    """
    # Check if the case_type exists in the case_config
    case_type_config = case_config.get(case_type)

    if not case_type_config or "canned_response" not in case_type_config:
        raise HTTPException(description="Canned response not found for the given case type.", response=404)

    # Return the canned response for the given case type
    return case_type_config["canned_response"]


def get_required_fields(case_type: str) -> list:
    """
    Get the required fields for a given case type from case_config.json.

    :param case_type: The case type to retrieve the required fields for.
    :return: A list of required fields.
    """
    # Check if the case_type exists in the case_config
    case_type_config = case_config.get(case_type)

    if not case_type_config or "required_fields" not in case_type_config:
        return []

    # Return the required fields for the given case type
    return case_type_config["required_fields"]

def check_partner_access(case_type: str) -> bool:
    """
    Determine if partner access check is required for a given case type.

    :param case_type: The case type to check the partner access for.
    :return: True if partner access is required, otherwise False.
    """
    case_type_config = case_config.get(case_type)
    return case_type_config.get("check_partner_access", False)