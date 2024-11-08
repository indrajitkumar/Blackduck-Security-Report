from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
import ast

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
        return redirect(url_for('config'))
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
                        'baseScore': component_version_details.get('cvss3', {}).get('baseScore', 'No score found'),
                        'impactSubscore': component_version_details.get('cvss3', {}).get('impactSubscore',
                                                                                         'No score found'),
                        'exploitabilitySubscore': component_version_details.get('cvss3', {}).get(
                            'exploitabilitySubscore', 'No score found'),
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

        file_path = os.path.join(download_dir, 'HSCS Product security vulnerability analysis report.xlsx')
        save_to_excel(component_overview, file_path, parsed_tab1_content)
        return send_file(file_path, as_attachment=True)
    else:
        return {'status': 'error', 'message': 'Failed to fetch project versions'}


def save_to_excel(component_overview, file_path='HSCS Product security vulnerability analysis report.xlsx',
                  tab1_content=[]):
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        wrap_format = workbook.add_format({'text_wrap': True, 'align': 'justify', 'valign': 'top'})
        merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})
        border_format = workbook.add_format({'border': 1})

        # Title Page
        title_page_data = []
        for item in tab1_content:
            title_page_data.append(item['Content'])

        title_page_df = pd.DataFrame(title_page_data, columns=['Purpose'])
        title_page_df.to_excel(writer, sheet_name='Title Page', index=False)
        worksheet = writer.sheets['Title Page']
        worksheet_formater(title_page_df, border_format, worksheet, wrap_format)

        # Component Overview
        component_overview_df = pd.DataFrame(
            [{k: v for k, v in item.items() if k != 'componentVersion'} for item in component_overview])
        component_overview_df.to_excel(writer, sheet_name='Component Overview', index=False)
        worksheet = writer.sheets['Component Overview']
        worksheet_formater(component_overview_df, border_format, worksheet, wrap_format)

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
        worksheet.merge_range('A1:L1',
                              'Unless indicated otherwise the vulnerability severity rating below is assessed using the <CVSS 3.1> scoring methodology.',
                              merge_format)
        worksheet_formater(analysis_df, border_format, worksheet, wrap_format)

        # Document Revision History
        revision_data = session.get('revision_data', {})
        revision = revision_data.get('revision')
        date = revision_data.get('date')
        author = revision_data.get('author')
        attendees = revision_data.get('attendees')
        crReason = revision_data.get('crReason')
        revision_history_df = pd.DataFrame(
            [{'Revision': revision, 'Date': date, 'Author': author, 'Attendees': attendees, 'Reason': crReason}])
        revision_history_df.to_excel(writer, sheet_name='Document Revision History', index=False)
        worksheet = writer.sheets['Document Revision History']
        worksheet.merge_range('A1:E1', 'Document revision history', merge_format)
        worksheet_formater(revision_history_df, border_format, worksheet, wrap_format)

        # Terminology & Abbreviations
        data_list = revision_data.get('terms')
        terms_list = ast.literal_eval(data_list)
        data_dict = {'Terminology & Abbreviations': [], 'Description/Definition': []}
        for item in terms_list:
            if ": " in item:
                key, value = item.split(": ", 1)
                data_dict['Terminology & Abbreviations'].append(key)
                data_dict['Description/Definition'].append(value)
            else:
                print(f"Skipping invalid item: {item}")

        abbreviations_df = pd.DataFrame(data_dict)
        abbreviations_df.to_excel(writer, sheet_name='Terminology & Abbreviations', index=False)
        worksheet = writer.sheets['Terminology & Abbreviations']
        worksheet.merge_range('A1:B1', 'Terminology & Abbreviations', merge_format)
        worksheet_formater(abbreviations_df, border_format, worksheet, wrap_format)

        # References
        referenceNumber = revision_data.get('referenceNumber')
        documentTitle = revision_data.get('documentTitle')
        documentId = revision_data.get('documentId')
        references_df = pd.DataFrame(
            [{'Reference number': referenceNumber, 'Document title': documentTitle, 'Document ID': documentId}]
        )
        references_df.to_excel(writer, sheet_name='References', startrow=1, index=False)
        worksheet = writer.sheets['References']
        worksheet.merge_range('A1:C1', 'References', merge_format)
        worksheet_formater(references_df, border_format, worksheet, wrap_format)


def worksheet_formater(df, border_format, worksheet, wrap_format):
    worksheet.set_header('&CProduct security vulnerability analysis report for HSCS')
    worksheet.set_footer(
        '&CNote: for template information, see custom properties of this document. &RFor Internal Use Only')
    worksheet.set_paper(9)
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 0)
    for col_num, col in enumerate(df.columns):
        worksheet.set_column(col_num, col_num, 30, wrap_format)
    for row_num in range(len(df)):
        for col_num in range(len(df.columns)):
            cell_value = df.iloc[row_num, col_num]
            if isinstance(cell_value, str) and len(cell_value) > 50:  # Assuming text area cells have long text
                worksheet.write(row_num + 1, col_num, cell_value, border_format)
            else:
                worksheet.write(row_num + 1, col_num, cell_value, wrap_format)


@app.route('/save_revision_data', methods=['POST'])
def save_revision_data():
    revision_data = {
        'referenceNumber': request.form.get('referenceNumber'),
        'documentTitle': request.form.get('documentTitle'),
        'documentId': request.form.get('documentId'),
        'revision': request.form.get('revision'),
        'date': request.form.get('date'),
        'author': request.form.get('author'),
        'attendees': request.form.get('attendees'),
        'crReason': request.form.get('crReason'),
        'terms': request.form.get('terms')
    }
    # Save the data to a session or database (for simplicity, using session here)
    session['revision_data'] = revision_data
    return jsonify({'status': 'success'})


@app.route('/get_revision_data', methods=['GET'])
def get_revision_data():
    revision_data = session.get('revision_data', {})
    if revision_data:
        return jsonify({'status': 'success', 'revision_data': revision_data})
    else:
        return jsonify({'status': 'error', 'message': 'No data found'})


@app.route('/config')
def config():
    return render_template('config.html')


@app.route('/bom')
def bom():
    return render_template('bom.html')


if __name__ == '__main__':
    app.run(debug=True)
