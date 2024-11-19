import os

import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify

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
                matched_files = component['_meta']['links'][4]['href'].replace('matched-files', '')
                # print(matched_files)
                component_overview.append({
                    'componentName': component_name,
                    'componentVersionName': component.get('componentVersionName', 'No name found'),
                    'componentDescription': get_component_details(component.get('component')),
                    'componentVersion': get_component_version_details(matched_files)
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
    vulnerabilities = 'vulnerabilities?limit=100&offset=0'
    bearer_token = session.get('bearerToken')
    if not bearer_token:
        flash("You need to authenticate first.")
        return redirect(url_for('home'))
    url = f"{param}{vulnerabilities}"
    headers = {
        "Authorization": f"Bearer {bearer_token}"

    }
    vulnerabilities = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        component_version_details = response.json()
        if component_version_details.get('totalCount', 0) > 0:
            for component_version_details in component_version_details.get('items', []):
                if component_version_details.get('remediationStatus', 'No severity found') in ['NEW']:
                    vulnerabilities.append({
                        'vulnerabilityUpdatedDate': component_version_details.get('lastModified', 'No date found'),
                        'vulnerabilityName': component_version_details.get('id', 'No name found'),
                        'description': component_version_details.get('summary', 'No description found'),
                        'baseScore': component_version_details.get('cvss3', {}).get('baseScore', '0'),
                        'impactSubscore': component_version_details.get('cvss3', {}).get('impactSubscore', '0'),
                        'exploitabilitySubscore': component_version_details.get('cvss3', {}).get(
                            'exploitabilitySubscore', '0'),
                        'severity': component_version_details.get('cvss3', {}).get('severity', 'LOW')
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
                'Content': section.get_text(strip=False)
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

        title_sheet(tab1_content, workbook, writer)
        component_overview_sheet(component_overview, workbook, writer)

        analysis_sheet(component_overview, workbook, writer)

        revision_history_sheet(workbook, writer)

        terminology_sheet(workbook, writer)

        references_sheet(workbook, writer)
        # workbook.close()


def references_sheet(workbook, writer):
    # References
    reference_data = session.get('referenceData', [])
    reference_data_list = []
    for data in reference_data:
        reference_data_list.append({
            'Reference Number': data.get('referenceNumber', ''),
            'Document Title': data.get('documentTitle', ''),
            'Document ID': data.get('documentId', '')
        })

    references_df = pd.DataFrame(reference_data_list)
    references_df.to_excel(writer, sheet_name='References', startrow=1, index=False)
    worksheet = writer.sheets['References']
    header_format = workbook.add_format({'text_wrap': True, 'bold': True, 'align': 'left', 'valign': 'vcenter'})
    worksheet.write('A1', 'References',
                    workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'font_size': 14}))
    for col_num, col in enumerate(references_df.columns):
        worksheet.write(1, col_num, col, header_format)
        worksheet.set_column(col_num, col_num, 26, workbook.add_format({'text_wrap': True}))

    worksheet_formater(worksheet)


def terminology_sheet(workbook, writer):
    # Terminology & Abbreviations
    data_list = session.get('terminology_data', [])
    data_terminology_list = []
    for data in data_list:
        data_terminology_list.append({
            'Terminology & Abbreviations': data.get('terminology', ''),
            'Description/Definition': data.get('description', '')
        })

    abbreviations_df = pd.DataFrame(data_terminology_list)
    abbreviations_df.to_excel(writer, sheet_name='Terminology & Abbreviations', startrow=1, index=False)
    worksheet = writer.sheets['Terminology & Abbreviations']
    worksheet.write('A1', 'Terminology & Abbreviations',
                    workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'font_size': 14}))
    header_format = workbook.add_format({'text_wrap': True, 'bold': True, 'align': 'left', 'valign': 'vcenter'})

    for col_num, col in enumerate(abbreviations_df.columns):
        worksheet.write(1, col_num, col, header_format)
        if col == 'Terminology & Abbreviations':
            worksheet.set_column(col_num, col_num, 30, workbook.add_format({'text_wrap': True}))
        else:
            worksheet.set_column(col_num, col_num, 50, workbook.add_format({'text_wrap': True}))
    worksheet_formater(worksheet)


def revision_history_sheet(workbook, writer):
    # Document Revision History
    revision_data = session.get('revision_data', [])
    revision_history_list = []

    for data in revision_data:
        revision_history_list.append({
            'Revision': data.get('revision', ''),
            'Revision Date': data.get('revisionDate', ''),
            'Author': data.get('author', ''),
            'Attendees': data.get('attendees', ''),
            'Reason': data.get('reason', '')
        })

    revision_history_df = pd.DataFrame(revision_history_list)
    revision_history_df.to_excel(writer, sheet_name='Document Revision History', startrow=1, index=False)
    worksheet = writer.sheets['Document Revision History']
    worksheet.write('A1', 'Document revision history',
                    workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True, 'font_size': 16}))
    header_format = workbook.add_format({'text_wrap': True, 'bold': True, 'align': 'left', 'valign': 'vcenter'})

    for col_num, col in enumerate(revision_history_df.columns):
        worksheet.write(1, col_num, col, header_format)
        if col == 'Revision':
            worksheet.set_column(col_num, col_num, 8,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        elif col == 'Revision Date':
            worksheet.set_column(col_num, col_num, 8,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        elif col == 'Author':
            worksheet.set_column(col_num, col_num, 10,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        else:
            worksheet.set_column(col_num, col_num, 26,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
    worksheet_formater(worksheet)


def analysis_sheet(component_overview, workbook, writer):
    # Analysis
    analysis_data = []

    for item in component_overview:
        for version in item['componentVersion']:
            date_ = version['vulnerabilityUpdatedDate'].split('T')[0]
            analysis_data.append({
                'Review date (YYYY-MM-DD)': date_,
                'Component name': item['componentName'],
                'Component version': item['componentVersionName'],
                'Vulnerability ID (e.g. CVE)': version['vulnerabilityName'],
                'Description': version['description'],
                'Base score': version['baseScore'],
                'Exploitability': version['exploitabilitySubscore'],
                'Impact': version['impactSubscore'],
                'Remediation comment': join_remediation_comment(item['componentName'], version['severity']),
                'Severity rating': version['severity'],
                'Update PSSD?': 'No',
                'Manage Defect requested?': 'No'
            })
    analysis_df = pd.DataFrame(analysis_data)
    analysis_df.to_excel(writer, sheet_name='Analysis', startrow=1, index=False)
    worksheet = writer.sheets['Analysis']
    worksheet.write('A1',
                    'Unless indicated otherwise the vulnerability severity rating below is assessed using the <CVSS 3.1> scoring methodology.',
                    workbook.add_format({'align': 'left', 'valign': 'top'}))

    # Apply wrap format to header names
    header_format = workbook.add_format({'text_wrap': True, 'bold': True, 'align': 'left', 'valign': 'top'})
    worksheet_formater(worksheet)
    for col_num, col in enumerate(analysis_df.columns):
        worksheet.write(1, col_num, col, header_format)
        if col == 'Remediation comment':
            worksheet.set_column(col_num, col_num, 50,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        elif col == 'Description':
            worksheet.set_column(col_num, col_num, 40,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        elif col == 'Vulnerability ID (e.g. CVE)':
            worksheet.set_column(col_num, col_num, 15,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        elif col == 'Base score' or col == 'Exploitability' or col == 'Impact':
            worksheet.set_column(col_num, col_num, 6,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        else:
            worksheet.set_column(col_num, col_num, 10,
                                 workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))


def join_remediation_comment(versionName, severity):
    releaseName = session.get('new_data', {})
    a = f"a) Technical Impact on Production environment/Client:"
    b = "\n\n\nb) Why we are not addressing now:"
    c = f"\n\n\nc) When we are addressing:\n\n"

    return a + b + c


def component_overview_sheet(component_overview, workbook, writer):
    # Component Overview
    component_overview_df = pd.DataFrame(
        [{k: v for k, v in item.items() if k != 'componentVersion'} for item in component_overview])
    component_overview_df.rename(
        columns={'componentVersionName': 'Component Version', 'componentName': 'Component Name',
                 'componentDescription': 'Component Description'}, inplace=True)

    component_overview_df['Support Status'] = "Manual analysis done and there are no operational risks identified"

    component_overview_df.to_excel(writer, sheet_name='Component Overview', index=False)
    worksheet = writer.sheets['Component Overview']
    for col_num, col in enumerate(component_overview_df.columns):
        if col == 'Component Description':
            worksheet.set_column(col_num, col_num, 36, workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        elif col == 'Component Name':
            worksheet.set_column(col_num, col_num, 16, workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
        else:
            worksheet.set_column(col_num, col_num, 16, workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'}))
    worksheet_formater(worksheet)


def title_sheet(tab1_content, workbook, writer):
    # Title Page
    title_page_data = []
    for item in tab1_content:
        title_page_data.append(item['Content'])
    title_page_df = pd.DataFrame(title_page_data, columns=['Purpose'])
    title_page_df.to_excel(writer, sheet_name='Title Page', index=False, header=False)
    worksheet = writer.sheets['Title Page']
    header_format = workbook.add_format(
        {'text_wrap': True, 'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_size': 14})
    for col_num, col in enumerate(title_page_df.columns):
        worksheet.set_column(col_num + 1, col_num, 120, workbook.add_format({'text_wrap': True}))

    # Apply bold format to the first and third rows
    worksheet.set_row(0, None, header_format)
    worksheet.set_row(4, None, header_format)
    worksheet_formater(worksheet)


def worksheet_formater(worksheet):
    worksheet.set_header('&C&20Product security vulnerability analysis report')
    worksheet.set_footer(
        '&CNote: for template information, see custom properties of this document. &RFor Internal Use Only')
    worksheet.set_paper(9)  # Set paper type. US Letter = 1, A4 = 9.
    worksheet.fit_to_pages(1, 0)
    worksheet.set_portrait()


@app.route('/save_revision_data', methods=['POST'])
def save_revision_data():
    # Clear the session before storing new data
    session.pop('revision_data', None)
    revision_data = request.json.get('revisionData', [])
    # Save the data to a session or database (for simplicity, using session here)
    session['revision_data'] = revision_data
    return jsonify({'status': 'success'})


@app.route('/save_terminology_data', methods=['POST'])
def save_terminology_data():
    # Clear the session before storing new data
    session.pop('terminology_data', None)
    terminology_data = request.json.get('terminologyData', [])
    # Save the data to a session or database (for simplicity, using session here)
    session['terminology_data'] = terminology_data
    return jsonify({'status': 'success'})


@app.route('/save_reference_data', methods=['POST'])
def save_reference_data():
    # Clear the session before storing new data
    session.pop('referenceData', None)
    referenceData = request.json.get('referenceData', [])
    # Save the data to a session or database (for simplicity, using session here)
    session['referenceData'] = referenceData
    return jsonify({'status': 'success'})


@app.route('/get_revision_data', methods=['GET'])
def get_revision_data():
    revision_data = session.get('revision_data', {})
    if revision_data:
        return jsonify({'status': 'success', 'revision_data': revision_data})
    else:
        return jsonify({'status': 'error', 'message': 'No data found'})


@app.route('/update_new_data', methods=['POST'])
def update_release_name():
    data = request.get_json()
    new_data = data.get('newData')
    if new_data:
        # Process the new_data as needed
        # For example, save it to the session or database
        session['new_data'] = new_data
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'No data provided'})


# @app.route('/config')
# def config():
#     return render_template('config.html')


@app.route('/bom')
def bom():
    return render_template('bom.html')


if __name__ == '__main__':
    app.run(debug=True)
