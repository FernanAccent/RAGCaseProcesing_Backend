import base64

# Encode the file in base64
with open("asset_replacement_details.xlsx", "rb") as file:
    encoded_file = base64.b64encode(file.read()).decode("utf-8")

# Print the base64-encoded string
print(encoded_file)
