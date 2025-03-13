import pandas as pd
import base64

try:
    # Sample DataFrame
    df = pd.DataFrame({
        'Provider Id': ['wbd.max', 'wbd.max', 'wbd.max', 'wbd.max', 'wbd.max', 'wbd.max'],
        'Series Name': ['Harry Potter'] * 6,
        'Title': [
            'Harry Potter and the Sorcerers Stone',
            'Harry Potter and the Chamber of Secrets',
            'Harry Potter and the Prisoner of Askaban',
            'Harry Potter and the Goblet of Fire',
            'Harry Potter and the Order of Phoenix',
            'Harry Potter and the Half Blood Prince'
        ],
        'Season Number': [1] * 6,
        'Episode Number': [1, 2, 3, 4, 5, 6],
        'Source Asset Id': ['HP00100001', 'HP00100002', 'HP00100003', 'HP00100004', 'HP00100005', 'HP00100006'],
        'LWED': ['8/29/2024'] * 6
    })

    # Debugging: Notify script is running
    print("Script execution started.")

    # Save to Excel
    excel_filename = 'assets_replacement1.xlsx'
    print(f"Saving DataFrame to {excel_filename}...")
    df.to_excel(excel_filename, index=False)
    print(f"File saved as {excel_filename}.")

    # Read the Excel file and convert it to base64
    print(f"Reading the file {excel_filename} and converting to base64...")
    with open(excel_filename, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()

    # Debugging: Output a message
    print("Base64 encoding completed.")

    # Output the base64 encoded string
    print("Base64 Encoded String:")
    print(encoded_string)

except Exception as e:
    print(f"An error occurred: {e}")
