import json

from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests

# Create Flask app instance
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Used for flashing messages

# Black Duck API URL (replace with your Black Duck instance URL)
BLACKDUCK_URL = "https://blackduck.philips.com"

# Define the route for the homepage (login form)
@app.route('/')
def home():
    return render_template('index.html')


# Define the route to authenticate and get projects
@app.route('/authenticate', methods=['POST'])
def authenticate():
    # Get the API token from the form
    api_token = request.form.get('api_token')

    # Black Duck API endpoint to authenticate and get the bearer token
    url = f"{BLACKDUCK_URL}/api/tokens/authenticate"
    payload = {}
    # Set up headers for the API request
    headers = {
        "Authorization": f"token {api_token}",
        "Accept": "application/vnd.blackducksoftware.user-4+json"
    }

    # Make the request to the Black Duck API to authenticate
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        token_data = response.json()
        session['bearerToken'] = token_data['bearerToken']
        return redirect(url_for('projects'))

    except requests.exceptions.HTTPError as http_err:
        flash(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError:
        flash("Network error: Unable to connect to Black Duck server.")
    except requests.exceptions.Timeout:
        flash("Network error: The request timed out.")
    except requests.exceptions.RequestException as req_err:
        flash(f"An error occurred: {req_err}")
    except json.JSONDecodeError:
        flash("Failed to parse the response from the server.")
    except KeyError:
        flash("Unexpected response format from the server.")
    except Exception as e:
        flash(f"An unexpected error occurred: {e}")

    return redirect(url_for('home'))



# Define the route to get projects


@app.route('/projects')
def projects():
    # Get the bearer token from the session
    bearer_token = session.get('bearerToken')

    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))

    # Black Duck API endpoint to get projects
    url = f"{BLACKDUCK_URL}/api/projects"

    # Set up headers for the API request
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }

    # Make the request to the Black Duck API to fetch projects
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        projects_data = response.json().get('items', [])  # Extract projects from the response
        return render_template('projects.html', projects=projects_data)  # Pass data to the template
    else:
        # If fetching projects fails, flash an error message and redirect to the login page
        flash("Failed to fetch projects. Please try again.")
        return redirect(url_for('home'))

@app.route('/projects/<project_id>')
def get_project_versions(project_id):
    # Get the bearer token from the session
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))

    # Black Duck API endpoint to get project versions
    url = f"{BLACKDUCK_URL}/api/projects/{project_id}/versions"

    # Set up headers for the API request
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }

    # Make the request to the Black Duck API to fetch project versions
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        project_versions = response.json().get('items', [])
        component_overview = []
        seen_components = set()
        for version in project_versions:
            print(version.get('versionName', 'No name found'))
            version_href = version['_meta']['href']
            print(version_href)
            get_version_components(version_href, component_overview, seen_components)
            print(component_overview)
        return {'status': 'success', 'data': component_overview}
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}


def get_version_components(versionIds, component_overview, seen_components):
    filters = '?filter=bomInclusion:false&filter=bomMatchInclusion:false&filter=bomMatchReviewStatus:reviewed&filter=securityRisk:high&filter=securityRisk:medium&limit=100&offset=0'
    # Get the bearer token from the session
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))

    # Black Duck API endpoint to get project versions
    url = f"{versionIds}/components{filters}"

    # Set up headers for the API request
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }

    # Make the request to the Black Duck API to fetch project versions
    response = requests.get(url, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        filtered_components = response.json().get('items', [])
        for component in filtered_components:
            component_name = component.get('componentName', 'No name found')
            if component_name not in seen_components:
                seen_components.add(component_name)

                # if component.get('component') is not None:
                #     print(component.get('component'))
                component_overview.append({
                    'componentName': component_name,
                    'componentVersionName': component.get('componentVersionName', 'No name found'),
                    'componentDescription': get_component_details(component.get('component'), component_overview)
                })
            # if component.get('component') is not None:
            #     print(component.get('component'))
                # component_overview.append('component',
                #                           get_component_details(component.get('component'), component_overview))
        return component_overview
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}

def get_component_details(param, component_overview):
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))

    # Black Duck API endpoint to get project versions
    url = f"{param}"

    # Set up headers for the API request
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }

    # Make the request to the Black Duck API to fetch project versions
    response = requests.get(url, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        description = response.json().get('description', [])
        print(description)
        return description
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
