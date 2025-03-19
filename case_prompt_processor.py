from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from utils import retrieve_resolution_steps,get_canned_response, check_partner_access, get_required_fields
from vertex_ai import process_email_content,generate_operator_response,summarize_case_log,extract_case_and_asset_details
import uuid, json

app = Flask(__name__)

# Allow CORS for specific origins (e.g., localhost:4200 for Angular)
CORS(app, origins=["http://localhost:4200"], supports_credentials=True)  # Allow CORS for your front-end origin

# Setup Flask-SocketIO with CORS allowed for frontend
socketio = SocketIO(app, cors_allowed_origins="http://localhost:4200")  # Allow CORS for WebSocket connections

# Load configuration file with case details
with open('case_config.json', encoding='utf-8') as config_file:
    case_config = json.load(config_file)

# Load configuration file with mock partner table
with open('mock_partner_table.json', encoding='utf-8') as config_file:
    partners_config = json.load(config_file)

@app.route('/process_email', methods=['POST'])
def process_email():
    # Step 1: Extract email data from the request
    email_data = request.json.get('email_data')

    if not email_data:
        return jsonify({"error": "No email data provided."}), 400

    # Step 2: Ensure the email contains the 'content' field
    content = email_data.get('content')
    if not content:
        return jsonify({"error": "'content' field is missing in email data."}), 400

    # Step 3: Read the system instruction from the file and process the email content
    system_instruction_file = r"C:\Users\fernan.flores\OneDrive - Accenture\Documents\Case Log Summary (First Email).txt"  # Provide the correct file path

    result = process_email_content(email_data, system_instruction_file)
    if "error" in result:
        return jsonify({"error": result["error"]}), 400

    # Step 4: Extract cleaned content and case type
    cleaned_content = result["cleaned_content"]
    case_type = result["case_type"]
    print(f"Case Type: {case_type}")  # For debugging purpose

    # Step 5: LLM Summarize the case log
    case_summary = summarize_case_log(cleaned_content)

    # Step 6: LLM extract essential details from cleaned content
    extracted_data = extract_case_and_asset_details(cleaned_content)
    print(f"Extracted Data:\n {extracted_data}") # for debugging purpose

    # Step 1: Extract data from the frontend input (from Chrome Extension)
    is_regenerate = request.json.get('isRegenerate', 'false')
    if is_regenerate:
        case_log = request.json.get('case_log')  # {"case_number", "case_title", "email_content"}
        case_type = request.json.get('category')  # "VODC7-2", etc.
        package_id = request.json.get('package_id')
        network_id = request.json.get('network_id')
        alid = request.json.get('alid')
        partner_id = request.json.get('partner_id')
    else:
        # case_log= case_summary
        if case_type in ['VODC7-1', 'VODC7-2', 'VODC7-3']:
            category = 'VODC7'
        elif case_type in ['VODG9', 'VODB6', 'VODE6', 'VODJ7']:
            category = case_type

        package_id = extracted_data.get("Package ID", "Not Found")
        network_id = extracted_data.get("Network ID", "Not Found")
        alid = extracted_data.get("ALID", "Not Found")
        partner_id = extracted_data.get("Partner ID", "Not Found")

    # Initialize a list to store the missing fields
    missing_fields = []
    asset_link_list = []    
    # Step 7: Handle unsupported case types and respond with canned response
    partner_actionable_response = ""  # Initialize the variable before using it
    if case_type not in ['VODC7-1', 'VODC7-2', 'VODC7-3','VODG9', 'VODB6', 'VODE6', 'VODJ7']:
        operator_actionable_response = generate_operator_response(case_summary)
        partner_actionable_response = "General Query Response"
        return jsonify({"message": operator_actionable_response})
    else:
        # If case type is valid, retrieve resolution steps from the database
        resolution_steps = retrieve_resolution_steps(case_type)

        # Build the operator actionable response based on the resolution steps
        operator_actionable_response = f"Resolution Steps:\n {resolution_steps}"
        if not is_regenerate:
            if check_partner_access(case_type):
                # Assuming  ‘Content Delivery Enabled’ and ‘Programs and Manifest Enabled’ are in mock_partner_table
                if partner_id in partners_config:
                    partner_data = partners_config[partner_id]
                    # Step 3: Check if 'Content Delivery Enabled' and 'Programs and Manifest Enabled' are both true
                    if partner_data.get('Content Delivery Enabled') == True and partner_data.get('Programs and Manifest Enabled') == True:
                        # Step 4: Generate the canned response [Unsupported Partner Response]
                        partner_actionable_response = "Unsupported Partner Response: Partner should use the Studio based on case type."
                        return jsonify({
                            "case_number": case_number,
                            "case_title": case_title,
                            "category": case_type,
                            "package_id": package_id,
                            "network_id": network_id,
                            "alid": alid,
                            "partner_id": partner_id,
                            "response_id1": "Response id 1",
                            "case_summary": case_summary,
                            "response_id2": "Response id 2",
                            "operator_response": operator_actionable_response,
                            "response_id3": "Response id 3",
                            "partner_response": partner_actionable_response
                        })
        
        
        asset_details= extracted_data[asset_details]

        # Loop through each asset and check required fields
        for asset in asset_details:
            # Retrieve the required fields for the case type
            case_required_fields = get_required_fields(case_type)

            # Check if required fields are provided and not empty
            if case_required_fields and case_required_fields != "":
                # Iterate through each required field and check the conditions
                for required_field in case_required_fields:
                    # Handle cases where we need to check either PAID/ALID or Network Name/Provider ID
                    if required_field in ["PAID/ALID", "Network Name or Provider ID"]:
                        # Check if at least one of the subfields is filled in
                        if required_field == "PAID/ALID":
                            alid = extracted_data.get("alid", "")
                            paid = extracted_data.get("paid", "")
                        # If both ALID and PAID are empty or null, consider it missing
                        if not alid and not paid:
                            missing_fields.append("PAID/ALID")
                        elif required_field == "Network Name or Provider ID":
                                network_id = extracted_data.get("network_id", "")
                                provider_id = extracted_data.get("provider_id", "")
                                # If both Network Name and Provider ID are empty or null, consider it missing
                                if not network_id and not provider_id:
                                    missing_fields.append("Network Name or Provider ID")
                    else:
                        # For other fields, simply check if they are empty or null
                        if not extracted_data.get(required_field, ""):
                            missing_fields.append(required_field)

                # Output the missing fields if any
                if missing_fields:
                    print(f"Missing Fields: {missing_fields}")
                    partner_actionable_response += f"Missing Fields Response: {asset} {missing_fields} \n"
                else:
                    print("All required fields are present.")
                    asset_link = f"https://hades.corp.google.com/cms/entity_type_program/{asset['source_asset_id']}/details"
                    asset_link_list.append(asset_link)
                    canned_response = get_canned_response(case_type) 
                    partner_actionable_response += canned_response

    # Check for missing fields and add to the missing_fields list if "Not Found"
    case_number = extracted_data.get("case_number", "Not Found")
    case_title = extracted_data.get("case_title", "Not Found")
    package_id = extracted_data.get("Package ID", "Not Found")
    network_id = extracted_data.get("Network ID", "Not Found")
    alid = extracted_data.get("ALID", "Not Found")
    partner_id = extracted_data.get("Partner ID", "Not Found")
 
    return jsonify({
        "case_number": case_number,
        "case_title": case_title,
        "category": category,
        "package_id": package_id,
        "network_id": network_id,
        "alid": alid,
        "partner_id": partner_id,
        "response_id1": "Response id 1",
        "case_summary": case_summary,
        "response_id2": "Response id 2",
        "operator_response": operator_actionable_response,
        "response_id3": "Response id 3",
        "partner_response": partner_actionable_response,
        "asset_link": asset_link_list
    })

# SocketIO event handling
@socketio.on('process_email_event')
def handle_process_email(data):
    # Step 1: Extract email data from the data argument
    email_data = data.get('email_data')

    if not email_data:
        emit('process_email_response', {"error": "No email data provided."})
        return

    # Step 2: Ensure the email contains the 'content' field
    content = email_data.get('content')
    if not content:
        emit('process_email_response', {"error": "'content' field is missing in email data."})
        return

    # Step 3: Read the system instruction from the file and process the email content
    system_instruction_file = r"C:\Users\fernan.flores\OneDrive - Accenture\Documents\Case Log Summary (First Email).txt"  # Provide the correct file path

    result = process_email_content(email_data, system_instruction_file)
    if "error" in result:
        emit('process_email_response', {"error": result["error"]})
        return

    # Step 4: Extract cleaned content and case type
    cleaned_content = result["cleaned_content"]
    case_type = result["case_type"]
    print(f"Case Type: {case_type}")  # For debugging purpose

    # Step 5: LLM Summarize the case log
    case_summary = summarize_case_log(cleaned_content)

    # Step 6: LLM extract essential details from cleaned content
    extracted_data = extract_case_and_asset_details(cleaned_content)
    print(f"Extracted Data:\n {extracted_data}")  # For debugging purpose

    # Step 1: Extract data from the frontend input (from Chrome Extension)
    is_regenerate = data.get('isRegenerate', 'false')
    if is_regenerate:
        case_log = data.get('case_log')  # {"case_number", "case_title", "email_content"}
        case_type = data.get('category')  # "VODC7-2", etc.
        package_id = data.get('package_id')
        network_id = data.get('network_id')
        alid = data.get('alid')
        partner_id = data.get('partner_id')
    else:
        if case_type in ['VODC7-1', 'VODC7-2', 'VODC7-3']:
            category = 'VODC7'
        elif case_type in ['VODG9', 'VODB6', 'VODE6', 'VODJ7']:
            category = case_type

        package_id = extracted_data.get("Package ID", "Not Found")
        network_id = extracted_data.get("Network ID", "Not Found")
        alid = extracted_data.get("ALID", "Not Found")
        partner_id = extracted_data.get("Partner ID", "Not Found")

    # Initialize a list to store the missing fields
    missing_fields = []
    asset_link_list = []
    partner_actionable_response = ""  # Initialize the variable before using it

    if case_type not in ['VODC7-1', 'VODC7-2', 'VODC7-3', 'VODG9', 'VODB6', 'VODE6', 'VODJ7']:
        operator_actionable_response = generate_operator_response(case_summary)
        partner_actionable_response = "General Query Response"
        emit('process_email_response', {"message": operator_actionable_response})
        return

    else:
        # If case type is valid, retrieve resolution steps from the database
        resolution_steps = retrieve_resolution_steps(case_type)

        # Build the operator actionable response based on the resolution steps
        operator_actionable_response = f"Resolution Steps:\n {resolution_steps}"
        if not is_regenerate:
            if check_partner_access(case_type):
                # Assuming ‘Content Delivery Enabled’ and ‘Programs and Manifest Enabled’ are in mock_partner_table
                if partner_id in partners_config:
                    partner_data = partners_config[partner_id]
                    # Step 3: Check if 'Content Delivery Enabled' and 'Programs and Manifest Enabled' are both true
                    if partner_data.get('Content Delivery Enabled') == True and partner_data.get('Programs and Manifest Enabled') == True:
                        # Step 4: Generate the canned response [Unsupported Partner Response]
                        partner_actionable_response = "Unsupported Partner Response: Partner should use the Studio based on case type."
                        emit('process_email_response', {
                            "case_number": extracted_data.get("case_number", "Not Found"),
                            "case_title": extracted_data.get("case_title", "Not Found"),
                            "category": case_type,
                            "package_id": package_id,
                            "network_id": network_id,
                            "alid": alid,
                            "partner_id": partner_id,
                            "response_id1": "Response id 1",
                            "case_summary": case_summary,
                            "response_id2": "Response id 2",
                            "operator_response": operator_actionable_response,
                            "response_id3": "Response id 3",
                            "partner_response": partner_actionable_response
                        })
                        return
        
        asset_details = extracted_data.get("asset_details", [])

        # Loop through each asset and check required fields
        for asset in asset_details:
            # Retrieve the required fields for the case type
            case_required_fields = get_required_fields(case_type)

            # Check if required fields are provided and not empty
            if case_required_fields and case_required_fields != "":
                # Iterate through each required field and check the conditions
                for required_field in case_required_fields:
                    # Handle cases where we need to check either PAID/ALID or Network Name/Provider ID
                    if required_field in ["PAID/ALID", "Network Name or Provider ID"]:
                        # Check if at least one of the subfields is filled in
                        if required_field == "PAID/ALID":
                            alid = extracted_data.get("alid", "")
                            paid = extracted_data.get("paid", "")
                        # If both ALID and PAID are empty or null, consider it missing
                        if not alid and not paid:
                            missing_fields.append("PAID/ALID")
                        elif required_field == "Network Name or Provider ID":
                                network_id = extracted_data.get("network_id", "")
                                provider_id = extracted_data.get("provider_id", "")
                                # If both Network Name and Provider ID are empty or null, consider it missing
                                if not network_id and not provider_id:
                                    missing_fields.append("Network Name or Provider ID")
                    else:
                        # For other fields, simply check if they are empty or null
                        if not extracted_data.get(required_field, ""):
                            missing_fields.append(required_field)

                # Output the missing fields if any
                if missing_fields:
                    print(f"Missing Fields: {missing_fields}")
                    partner_actionable_response += f"Missing Fields Response: {asset} {missing_fields} \n"
                else:
                    print("All required fields are present.")
                    asset_link = f"https://hades.corp.google.com/cms/entity_type_program/{asset['source_asset_id']}/details"
                    asset_link_list.append(asset_link)
                    canned_response = get_canned_response(case_type) 
                    partner_actionable_response += canned_response

    # Check for missing fields and add to the missing_fields list if "Not Found"
    case_number = extracted_data.get("case_number", "Not Found")
    case_title = extracted_data.get("case_title", "Not Found")
    package_id = extracted_data.get("Package ID", "Not Found")
    network_id = extracted_data.get("Network ID", "Not Found")
    alid = extracted_data.get("ALID", "Not Found")
    partner_id = extracted_data.get("Partner ID", "Not Found")

    emit('process_email_response', {
        "case_number": case_number,
        "case_title": case_title,
        "category": category,
        "package_id": package_id,
        "network_id": network_id,
        "alid": alid,
        "partner_id": partner_id,
        "response_id1": "Response id 1",
        "case_summary": case_summary,
        "response_id2": "Response id 2",
        "operator_response": operator_actionable_response,
        "response_id3": "Response id 3",
        "partner_response": partner_actionable_response,
        "asset_link": asset_link_list
    })

if __name__ == '__main__':
    socketio.run(app, debug=True)
