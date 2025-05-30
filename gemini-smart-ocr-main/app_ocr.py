import os
import google.generativeai as genai
import json
from time import sleep

image_dir = "extracted_images"
output_file = "extracted_images_info.json"

API_KEY3 = ""
def upload_to_gemini(file_path, mime_type=None):
    """Uploads a file to Gemini and returns the file object."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        file = genai.upload_file(file_path, mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

generation_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
    # model_name="gemini-2.0-pro-exp-02-05",
    # model_name="gemini-2.0-flash-exp",
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if not image_files:
    print("No images found in the directory.")
    exit()

if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        try:
            results = json.load(f)
            if not isinstance(results, list):
                results = []
        except json.JSONDecodeError:
            results = []
else:
    results = []
count = 0

for image in image_files:
    genai.configure(api_key=API_KEY3)
    sleep(4)
        
    file_path = os.path.join(image_dir, image)

    uploaded_file = upload_to_gemini(file_path, mime_type="image/png")

    if not uploaded_file:
        print(f"Skipping {image} due to upload failure.")
        continue

    chat_session = model.start_chat(history=[{"role": "user", "parts": [uploaded_file]}])

    prompt = f"""Analyze the document and extract all the details I need to upload in my database in sets of each bond. Identify the type of document and structure the response in the following JSON format:

    {{
      "document_type": "Corporate Bonds List",
      "metadata": {{
        "full_name": "Extracted Name (if applicable)",
        "date": "Extracted Date (if applicable)",
        "document_number": "Extracted Document Number (if applicable)",
        "issuer": "Issuing Authority or Organization (if available)"
      }},
      "content": {{
        "summary": "Brief summary of the document",
        "key_details": {{
          "field_1": "Extracted Value",
          "field_2": "Extracted Value",
          "...": "..."
        }}
      }}
    }}

    If you are given a table make sure you can identify merged cells and assign same value to all the fields the value is applicable.
    Ensure the response is strictly in JSON format.
    """

    response = chat_session.send_message(prompt)
    try:
        response_json = json.loads(response.text)
        
        if isinstance(response_json, list):
            for item in response_json:
                if isinstance(item, dict):
                    item["document_name"] = image
                    results.append(item)
        elif isinstance(response_json, dict):
            response_json["document_name"] = image
            results.append(response_json)
        else:
            print(f"Unexpected JSON format for {image}: {response_json}")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"Processed {image} successfully and saved results.")
    except json.JSONDecodeError:
        print(f"Invalid JSON response for {image}: {response.text}")


print(f"All processing completed. Results saved in {output_file}.")
