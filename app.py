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

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

    # Check if the request was successful
    if response.status_code == 200:
        token_data = response.json()
        session['bearerToken'] = token_data['bearerToken']  # Store the token in the session
        return redirect(url_for('projects'))  # Redirect to the projects page
    else:
        # If authentication fails, flash an error message and redirect to the login page
        flash("Failed to authenticate with the provided token. Please try again.")
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
                component_overview.append({
                    'componentName': component_name,
                    'componentVersionName': component.get('componentVersionName', 'No name found'),
                    'componentDescription': get_component_details(component.get('component')),
                    'componentVersion': get_component_version_details(component.get('componentVersion'))
                })

        return component_overview
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}

def get_component_details(param):
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

def get_component_version_details(param):
    vulnerabilities = '/vulnerabilities?limit=100&offset=0&sort=overallScore%20DESC'
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))

    # Black Duck API endpoint to get project versions
    url = f"{param}{vulnerabilities}"

    # Set up headers for the API request
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    vulnerabilities = []
    # Make the request to the Black Duck API to fetch project versions
    response = requests.get(url, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        component_version_details = response.json()
        if component_version_details.get('totalCount', 0) > 0:
            for component_version_details in component_version_details.get('items', []):
                vulnerabilities.append({
                    'vulnerabilityUpdatedDate': component_version_details.get('publishedDate', 'No date found'),
                    'vulnerabilityName': component_version_details.get('name', 'No name found'),
                    'description': component_version_details.get('description', 'No description found'),
                    'baseScore': component_version_details.get('cvss3',{}).get('baseScore', 'No score found'),
                    'impactSubscore': component_version_details.get('cvss3',{}).get('impactSubscore', 'No score found'),
                    'exploitabilitySubscore': component_version_details.get('cvss3',{}).get('exploitabilitySubscore', 'No score found'),
                    'severity': component_version_details.get('severity', 'No severity found')
                })
        return vulnerabilities
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
