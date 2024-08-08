from flask import Flask, request, jsonify
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
from vertexai.generative_models import HarmCategory, HarmBlockThreshold
from flask_cors import CORS
from google.api_core.exceptions import GoogleAPICallError, RetryError


app = Flask(__name__)
CORS(app)


# vertexai.init(project="ivca-ai", location="us-central1")
def authenticate_google_cloud():
    credentials = service_account.Credentials.from_service_account_file(
        'D:/College/IVCA/ivca-431913-762ef784ee23.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform'],
    )
    vertexai.init(project="ivca-431913", location="us-central1", credentials=credentials)

authenticate_google_cloud()


@app.route('/process_command', methods=['POST'])
def process_command():
    data = request.json.get('data', '')
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    response_text = handle_command(data.lower())
    return jsonify({'response': response_text})


def handle_command(text):
    if "google" in text:
        return process_search_command(text, "google")
    elif "youtube" in text:
        return process_search_command(text, "youtube")
    elif "wikipedia" in text:
        return process_search_command(text, "wikipedia")
    elif "spotify" in text:
        return process_search_command(text, "spotify")
    elif "code" in text or "program" in text or "ivca" in text:
        return process_code_generation(text)
    return "No valid command was found in the text."

def process_search_command(text, service):
    try:
        service_index = text.index(service) + len(service)
        search_query = text[service_index:].strip()
        if search_query:
            if service == "google":
                url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            elif service == "youtube":
                url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            elif service == "wikipedia":
                url = f"https://en.wikipedia.org/wiki/{search_query.replace(' ', '_')}"
            elif service == "spotify":
                url = f"https://open.spotify.com/search/{search_query.replace(' ', '%20')}"
            return f"I have generated a URL for {service.capitalize()} search: {url}"
        else:
            return f"You mentioned {service.capitalize()}, but no search query was provided."
    except ValueError:
        return f"The command to search on {service.capitalize()} was not clear."


def process_code_generation(text):
    command_start = max(text.find("code"), text.find("program"), text.find("ivca"))
    query = text[command_start:].split(maxsplit=1)[1] if len(text[command_start:].split()) > 1 else ""
    response = generate_response(query)
    if response:
        return "Here is what I generated: " + response
    else:
        return "I was unable to generate any code."

def generate_response(user_input):
    model = GenerativeModel("gemini-1.5-pro-preview-0409")
    generation_config = {
        "max_output_tokens": 500,
        "temperature": 0.7,
        "top_p": 0.95
    }
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    try:
        response = model.generate_content(
            user_input,
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False
        )
        return response.text
    except GoogleAPICallError as e:
        # Handle errors from the API call itself
        return f"API call error: {e}"
    except RetryError as e:
        # Handle errors during retries
        return f"Retry error: {e}"
    except Exception as e:
        # Handle other possible exceptions
        return f"Error during response generation: {e}"

if __name__ == '__main__':
    app.run(debug=True)