from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os


# Create Flask app instance
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Used for flashing messages

# Black Duck API URL (replace with your Black Duck instance URL)
BLACKDUCK_URL = "https://blackduck.philips.com"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    api_token = request.form.get('api_token')
    url = f"{BLACKDUCK_URL}/api/tokens/authenticate"
    payload = {}
    headers = {
        "Authorization": f"token {api_token}",
        "Accept": "application/vnd.blackducksoftware.user-4+json"
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        token_data = response.json()
        session['bearerToken'] = token_data['bearerToken']
        return redirect(url_for('projects'))
    else:
        flash("Failed to authenticate with the provided token. Please try again.")
        return redirect(url_for('home'))

@app.route('/projects')
def projects():
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))
    url = f"{BLACKDUCK_URL}/api/projects"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        projects_data = response.json().get('items', [])
        return render_template('projects.html', projects=projects_data)
    else:
        flash("Failed to fetch projects. Please try again.")
        return redirect(url_for('home'))

@app.route('/projects/<project_id>')
def get_project_versions(project_id):
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))
    url = f"{BLACKDUCK_URL}/api/projects/{project_id}/versions"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        project_versions = response.json().get('items', [])
        component_overview = []
        seen_components = set()
        for version in project_versions:
            version_href = version['_meta']['href']
            component_overview = get_version_components(version_href, component_overview, seen_components)
        return {'status': 'success', 'data': component_overview}
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}

def get_version_components(versionIds, component_overview, seen_components):
    filters = 'filter=bomInclusion:false&filter=bomMatchInclusion:false&filter=bomMatchReviewStatus:reviewed&filter=securityRisk:high&filter=securityRisk:medium&limit=100&offset=0'
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))
    url = f"{versionIds}/components?{filters}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
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
    url = f"{param}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        description = response.json().get('description', [])
        return description
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}

def get_component_version_details(param):
    vulnerabilities = '/vulnerabilities?limit=100&offset=0&sort=overallScore%20DESC'
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))
    url = f"{param}{vulnerabilities}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    vulnerabilities = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        component_version_details = response.json()
        if component_version_details.get('totalCount', 0) > 0:
            for component_version_details in component_version_details.get('items', []):
                if component_version_details.get('severity', 'No severity found') in ['HIGH', 'MEDIUM']:
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
@app.route('/generate_excel_report/<project_id>', methods=['POST'])
def generate_excel_report(project_id):
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))
    url = f"{BLACKDUCK_URL}/api/projects/{project_id}/versions"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        project_versions = response.json().get('items', [])
        component_overview = []
        seen_components = set()
        for version in project_versions:
            version_href = version['_meta']['href']
            component_overview = get_version_components(version_href, component_overview, seen_components)

        # Extract and parse content from tab1 for title page
        tab1_content = request.json.get('tab1Content', '')
        soup = BeautifulSoup(tab1_content, 'html.parser')
        parsed_tab1_content = []
        for section in soup.find_all(['h2', 'p']):
            parsed_tab1_content.append({
                'Tag': section.name,
                'Content': section.get_text(strip=True)
            })

        # Ensure the download directory exists
        download_dir = 'download'
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        file_path = os.path.join(download_dir, 'component_overview.xlsx')
        save_to_excel(component_overview, file_path, parsed_tab1_content)
        return send_file(file_path, as_attachment=True)
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}


def save_to_excel(component_overview, file_path='component_overview.xlsx', tab1_content=[]):
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        wrap_format = workbook.add_format({'text_wrap': True})
        justify_format = workbook.add_format({'text_wrap': True, 'align': 'justify'})

        # Title Page
        title_page_data = []
        for item in tab1_content:
            title_page_data.append(item['Content'])

        title_page_df = pd.DataFrame(title_page_data, columns=['Purpose'])
        title_page_df.to_excel(writer, sheet_name='Title Page', index=False)
        worksheet = writer.sheets['Title Page']
        for col_num, col in enumerate(title_page_df.columns):
            worksheet.set_column(col_num, col_num, 150, wrap_format)

        # Component Overview
        component_overview_df = pd.DataFrame(
            [{k: v for k, v in item.items() if k != 'componentVersion'} for item in component_overview])
        component_overview_df.to_excel(writer, sheet_name='Component Overview', index=False)
        worksheet = writer.sheets['Component Overview']
        for col_num, col in enumerate(component_overview_df.columns):
            worksheet.set_column(col_num, col_num, 30, wrap_format)

        # Analysis
        analysis_data = []
        for item in component_overview:
            for version in item['componentVersion']:
                analysis_data.append({
                    'Review date (YYYY-MM-DD)': version['vulnerabilityUpdatedDate'],
                    'Component name': item['componentName'],
                    'Component version': item['componentVersionName'],
                    'Vulnerability ID (e.g. CVE)': version['vulnerabilityName'],
                    'Description': version['description'],
                    'Base score': version['baseScore'],
                    'Exploitability': version['exploitabilitySubscore'],
                    'Impact': version['impactSubscore'],
                    'Remediation status': version.get('remediationStatus', ''),
                    'Remediation comment': version.get('remediationComment', ''),
                    'Severity rating': version['severity'],
                    'Update PSSD?': 'No',
                    'Manage Defect requested?': 'No'
                })
        analysis_df = pd.DataFrame(analysis_data)
        analysis_df.to_excel(writer, sheet_name='Analysis', index=False)
        worksheet = writer.sheets['Analysis']
        for col_num, col in enumerate(analysis_df.columns):
            worksheet.set_column(col_num, col_num, 30, wrap_format)

        # Document Revision History
        revision_history_df = pd.DataFrame([{'Revision': '1.0', 'Date': '2023-10-01', 'Description': 'Initial version'}])
        revision_history_df.to_excel(writer, sheet_name='Document Revision History', index=False)
        worksheet = writer.sheets['Document Revision History']
        for col_num, col in enumerate(revision_history_df.columns):
            worksheet.set_column(col_num, col_num, 20, wrap_format)

        # Terminology & Abbreviations
        abbreviations_df = pd.DataFrame([{'Term': 'PSSD', 'Definition': 'Product Security Software Development'}])
        abbreviations_df.to_excel(writer, sheet_name='Terminology & Abbreviations', index=False)
        worksheet = writer.sheets['Terminology & Abbreviations']
        for col_num, col in enumerate(abbreviations_df.columns):
            worksheet.set_column(col_num, col_num, 20, wrap_format)

        # References
        references_df = pd.DataFrame([{'Reference': 'Black Duck API Documentation', 'Link': 'https://blackducksoftware.github.io/'}])
        references_df.to_excel(writer, sheet_name='References', index=False)
        worksheet = writer.sheets['References']
        for col_num, col in enumerate(references_df.columns):
            worksheet.set_column(col_num, col_num, 20, wrap_format)


if __name__ == '__main__':
    app.run(debug=True)