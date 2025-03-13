from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from utils import clean_html_content, check_email_fields, extract_case_info, get_canned_response, generate_actionable_response, get_case_type_scenarios, process_assets, extract_asset_details, validate_asset
from vertex_ai import process_email_content,generate_operator_response,summarize_case_log
import uuid

app = Flask(__name__)

# Allow CORS for specific origins (e.g., localhost:4200 for Angular)
CORS(app, origins=["http://localhost:4200"], supports_credentials=True)  # Allow CORS for your front-end origin

# Setup Flask-SocketIO with CORS allowed for frontend
socketio = SocketIO(app, cors_allowed_origins="http://localhost:4200")  # Allow CORS for WebSocket connections

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

    # Step 5: Handle unsupported case types and respond with canned response
    if case_type not in ['VODC7', 'VODG9', 'VODB6', 'VODE6', 'VODJ7']:
        scenario = "Unsupported Case Response"
        canned_response = get_canned_response("General", scenario)
        if not canned_response:
            canned_response = "The case type is not supported in the current release."  # Default message if no canned response is found
    else:
        scenario = "Successful Operation Response"
        canned_response = get_canned_response(case_type, scenario)
        if not canned_response:
            canned_response = f"No canned response found for {case_type} and scenario {scenario}"

    # Step 6: Check if required fields are missing
    required_fields = ["PEM", "Partner POC", "To", "CC"]
    missing_fields = check_email_fields(email_data, required_fields)
    if missing_fields:
        response = generate_actionable_response("Partner", f"Missing required fields: {', '.join(missing_fields)}")
        return jsonify({"message": response})

    # Step 7: Extract case details
    case_details = extract_case_info(content)

    # Step 8: Asset validation based on case type
   # asset_validation_result = validate_asset(case_details["assets"])
   # if not asset_validation_result["valid"]:
   #     response = generate_actionable_response("Partner", "Asset validation failed.")
   #     return jsonify({"message": response})

    # Step 9: Retrieve and process resolution steps from Case Type Scenarios
    valid_assets, invalid_assets, successful_output_list, unsuccessful_output_list = process_assets(case_details, case_type)

    # Step 10: Extract Category, Package ID, Network ID, AL ID, and Partner ID from the first asset
    first_asset = case_details["assets"][0] if case_details["assets"] else None
    asset_details = extract_asset_details(first_asset)

    # Step 11: Summarize the case log
    case_summary = summarize_case_log(cleaned_content)

    # Step 12: Generate actionable response based on the unstructured data (case details)
    operator_response = generate_operator_response(case_summary)

    # Step 13: Generate responses based on lists
    partner_response = ""
    if invalid_assets:
        partner_response = generate_actionable_response("Partner", "Assets not found")
    elif valid_assets:
        partner_response = generate_actionable_response("Partner", "Assets processed successfully")

    # Step 14: Return the responses and logs
    return jsonify({
        "case_number": case_details["case_number"],
        "case_title": case_details["case_title"],
        "partner_response": partner_response,
        "operator_response": operator_response,
        "valid_asset_list": valid_assets,
        "invalid_asset_list": invalid_assets,
        "successful_output_list": successful_output_list,
        "unsuccessful_output_list": unsuccessful_output_list,
        "asset_details": asset_details,
        "case_summary": case_summary,
        "message": canned_response
    })

# SocketIO event handling
@socketio.on('process_email_event')
def handle_process_email(data):
    email_data = data.get('email_data')

    if not email_data:
        emit('response', {'message': 'No email data provided.'})
        return

    # Ensure the email contains the 'content' field
    content = email_data.get('content')
    if not content:
        emit('response', {'message': "'content' field is missing in email data."})
        return

    # Processing the email as before
    system_instruction_file = r"C:\Users\fernan.flores\OneDrive - Accenture\Documents\Case Log Summary (First Email).txt"

    # Call the vertex_ai function to process the email content and return cleaned content and case type
    result = process_email_content(email_data, system_instruction_file)
    if "error" in result:
        emit('response', {'message': result["error"]})
        return

    cleaned_content = result["cleaned_content"]
    case_type = result["case_type"]

    # Handle unsupported case types
    if case_type not in ['VODC7', 'VODG9', 'VODB6', 'VODE6', 'VODJ7']:
        canned_response = get_canned_response(case_type, "Unsupported Case Response")
        emit('response', {'message': canned_response})
        return

    required_fields = ["PEM", "Partner POC", "To", "CC"]
    missing_fields = check_email_fields(email_data, required_fields)
    if missing_fields:
        response = generate_actionable_response("Partner", f"Missing required fields: {', '.join(missing_fields)}")
        emit('response', {'message': response})
        return

    case_details = extract_case_info(content)
    #asset_validation_result = validate_asset(case_details["assets"])
    #if not asset_validation_result["valid"]:
    #    response = generate_actionable_response("Partner", "Asset validation failed.")
    #    emit('response', {'message': response})
    #    return

    # Process assets based on resolution steps
    valid_assets, invalid_assets, successful_output_list, unsuccessful_output_list = process_assets(case_details, case_type)

    partner_response = ""
    if invalid_assets:
        partner_response = generate_actionable_response("Partner", "Assets not found")
    elif valid_assets:
        partner_response = generate_actionable_response("Partner", "Assets processed successfully")

    operator_response = generate_operator_response(cleaned_content)

    # Emit the results back to the client
    emit('response', {
        "case_number": case_details["case_number"],
        "case_title": case_details["case_title"],
        "partner_response": partner_response,
        "operator_response": operator_response,
        "valid_asset_list": valid_assets,
        "invalid_asset_list": invalid_assets,
        "successful_output_list": successful_output_list,
        "unsuccessful_output_list": unsuccessful_output_list
    })

if __name__ == '__main__':
    socketio.run(app, debug=True)
