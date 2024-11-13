// document.addEventListener('DOMContentLoaded', (event) => {
//     // Set the date we're counting down to
//     let countDownDate = new Date("Nov 31, 2024 23:59:59").getTime();
//
//     // Update the count-down every 1 second
//     let countdownFunction = setInterval(function() {
//         // Get today's date and time
//         let now = new Date().getTime();
//
//         // Find the distance between now and the count-down date
//         let distance = countDownDate - now;
//
//         // Time calculations for days, hours, minutes and seconds
//         let days = Math.floor(distance / (1000 * 60 * 60 * 24));
//         let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
//         let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
//         let seconds = Math.floor((distance % (1000 * 60)) / 1000);
//
//         // Display the result in the element with id="countdown"
//         document.getElementById("countdown").innerHTML = days + "d " + hours + "h "
//         + minutes + "m " + seconds + "s ";
//
//         // If the count-down is over, write some text
//         if (distance < 0) {
//             clearInterval(countdownFunction);
//             document.getElementById("countdown").innerHTML = "EXPIRED";
//         }
//     }, 1000);
// });

document.addEventListener('DOMContentLoaded', (event) => {
    const links = document.querySelectorAll('.nav-link');

    // Retrieve the selected link from localStorage
    const selectedLink = localStorage.getItem('selectedLink');
    if (selectedLink) {
        document.querySelector(`.nav-link[href="${selectedLink}"]`).classList.add('selected');
    } else {
        // Default to the first link if no link is selected
        links[1].classList.add('selected');
    }

    links.forEach(link => {
        link.addEventListener('click', function () {
            links.forEach(l => l.classList.remove('selected'));
            this.classList.add('selected');

            // Save the selected link to localStorage
            localStorage.setItem('selectedLink', this.getAttribute('href'));
        });
    });
});

// Function to add a new row
function addRow(tableId, cellCount) {
    const table = document.getElementById(tableId).getElementsByTagName('tbody')[0];
    const newRow = table.insertRow();

    for (let i = 0; i < cellCount; i++) {
        const cell = newRow.insertCell(i);
        cell.contentEditable = "true";
        cell.className = "editable-cell";
        cell.textContent = ""; // Start with empty cells
    }

    // Add delete button
    const actionsCell = newRow.insertCell(cellCount);
    actionsCell.innerHTML = '<button class="btn btn-danger btn-sm" onclick="deleteRow(this)">Delete</button>';
}

// Function to delete a row
function deleteRow(button) {
    const row = button.closest("tr");
    row.parentNode.removeChild(row);
}

function importExcelFile() {
    const fileInput = document.getElementById('importExcel');
    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = function (event) {
        const data = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, {type: 'array'});

        const title_page = workbook.SheetNames[0];
        const worksheet_title_page = workbook.Sheets[title_page];
        const jsonData_title_page = XLSX.utils.sheet_to_json(worksheet_title_page, {header: 1});
        console.log(jsonData_title_page);
        // Update tab1 (Title Page)
        const tab1Content = jsonData_title_page.map((row, index) => {
            if ((index === 0) || (index === 4)) {
                return `<h2>${row.join(' ')}</h2>`;
            }
            return `<p>${row.join(' ')}</p>`;
        }).join('');
        document.getElementById('tab1').innerHTML = tab1Content;


        // Assuming the first sheet is the one we want to read
        const document_revision_history = workbook.SheetNames[3];
        const worksheet_document_revision_history = workbook.Sheets[document_revision_history];
        const jsonData_document_revision_history = XLSX.utils.sheet_to_json(worksheet_document_revision_history, {header: 1});
        console.log(jsonData_document_revision_history);

        // Populate data in revision history table
        const table = document.getElementById('revisionHistoryTable').getElementsByTagName('tbody')[0];
        jsonData_document_revision_history.slice(3).forEach(rowData => {
            const newRow = table.insertRow();
            rowData.forEach((text, index) => {
                const cell = newRow.insertCell(index);
                cell.contentEditable = "true";
                cell.className = "editable-cell";
                cell.textContent = text;
            });

            // Add delete button
            const actionsCell = newRow.insertCell(rowData.length);
            actionsCell.innerHTML = '<button class="btn btn-danger btn-sm" onclick="deleteRow(this)">Delete</button>';
        });

        const abbreviation = workbook.SheetNames[4];
        const worksheet_abbreviation = workbook.Sheets[abbreviation];
        const jsonData_abbreviation = XLSX.utils.sheet_to_json(worksheet_abbreviation, {header: 1});

        // Populate data in terminology & abbreviation table
        const tableTerm = document.getElementById('terminologyAbbreviationTable').getElementsByTagName('tbody')[0];
        jsonData_abbreviation.slice(3).forEach(rowData => {
            const newRow = tableTerm.insertRow();
            rowData.forEach((text, index) => {
                const cell = newRow.insertCell(index);
                cell.contentEditable = "true";
                cell.className = "editable-cell";
                cell.textContent = text;
            });

            // Add delete button
            const actionsCell = newRow.insertCell(rowData.length);
            actionsCell.innerHTML = '<button class="btn btn-danger btn-sm" onclick="deleteRow(this)">Delete</button>';
        });


        const references = workbook.SheetNames[5];
        const worksheet_references = workbook.Sheets[references];
        const jsonData_references = XLSX.utils.sheet_to_json(worksheet_references, {header: 1});
        console.log(jsonData_references);
        // Populate data in References table
        const tableReference = document.getElementById('referencesTable').getElementsByTagName('tbody')[0];
        jsonData_references.slice(3).forEach(rowData => {
            const newRow = tableReference.insertRow();
            rowData.forEach((text, index) => {
                const cell = newRow.insertCell(index);
                cell.contentEditable = "true";
                cell.className = "editable-cell";
                cell.textContent = text;
            });

            // Add delete button
            const actionsCell = newRow.insertCell(rowData.length);
            actionsCell.innerHTML = '<button class="btn btn-danger btn-sm" onclick="deleteRow(this)">Delete</button>';
        });
    };

    reader.readAsArrayBuffer(file);
}

function showTab(tabId) {
    let tabs = document.querySelectorAll('.tab');
    tabs.forEach(function (tab) {
        tab.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
}

function getSelectedProject() {
    let loader = document.getElementById('loader');
    loader.style.display = 'block';

    let select = document.getElementById('projects');
    let selectedOption = select.options[select.selectedIndex];
    let selectedValue = selectedOption.value;
    let selectedName = selectedOption.getAttribute('data-name');
    console.log('Selected project ID:', selectedValue);
    fetch(`/projects/${selectedValue}`)
        .then(response => response.json())
        .then(data => {
            console.log('Project data:', data);
            // Handle the response data as needed
            populateTable(data.data);
        })
        .catch(error => {
            console.error('Error fetching project data:', error);
        })
        .finally(() => {
            loader.classList.add('fade-out');
            setTimeout(() => {
                loader.style.display = 'none';
                loader.classList.remove('fade-out');
            }, 500); // Match the duration of the fadeOut animation
        });
}

function populateTable(data) {
    let tableBody = document.querySelector('#projectDataTable tbody');
    tableBody.innerHTML = ''; // Clear existing data
    data.forEach(item => {
        let row = document.createElement('tr');
        let componentName = document.createElement('td');
        let componentVersion = document.createElement('td');
        let componentDescription = document.createElement('td');
        let supportStatus = document.createElement('td');
        let supportStatusTextArea = document.createElement('td');

        componentName.textContent = item.componentName;
        componentVersion.textContent = item.componentVersionName;
        componentDescription.textContent = item.componentDescription;
        supportStatusTextArea.textContent = 'Manual analysis done and there are no operational risks identified';

        supportStatus.appendChild(supportStatusTextArea);
        row.appendChild(componentName);
        row.appendChild(componentVersion);
        row.appendChild(componentDescription);
        row.appendChild(supportStatus);

        tableBody.appendChild(row);

        let tableBody1 = document.querySelector('#projectDataTable1 tbody');
        item.componentVersion.forEach(version => {
            let vulnerabilityUpdatedDate = document.createElement('td');
            let componentName = document.createElement('td');
            let componentVersion = document.createElement('td');
            let vulnerabilityName = document.createElement('td');
            let vulnerabilityDec = document.createElement('td');
            let baseScore = document.createElement('td');
            let exploitability = document.createElement('td');
            let impact = document.createElement('td');
            let remediationStatus = document.createElement('td');
            let remediationComment = document.createElement('textarea');
            let severityRating = document.createElement('td');
            let updatePSSD = document.createElement('td');
            let manageDefect = document.createElement('td');

            vulnerabilityUpdatedDate.textContent = version.vulnerabilityUpdatedDate.split('T')[0];
            componentName.textContent = item.componentName;
            componentVersion.textContent = item.componentVersionName;
            vulnerabilityName.textContent = version.vulnerabilityName;
            vulnerabilityDec.textContent = version.description;
            baseScore.textContent = version.baseScore;
            exploitability.textContent = version.exploitabilitySubscore;
            impact.textContent = version.impactSubscore;
            remediationStatus.value = version.remediationStatus;
            remediationComment.value = 'Please update in report';
            severityRating.textContent = version.severity;
            updatePSSD.textContent = "No";
            manageDefect.textContent = "No";
            console.log('Version', version.vulnerabilityName);

            let row = document.createElement('tr');
            row.appendChild(vulnerabilityUpdatedDate);
            row.appendChild(componentName);
            row.appendChild(componentVersion);
            row.appendChild(vulnerabilityName);
            row.appendChild(vulnerabilityDec);
            row.appendChild(baseScore);
            row.appendChild(exploitability);
            row.appendChild(impact);
            row.appendChild(remediationStatus);
            row.appendChild(remediationComment);
            row.appendChild(severityRating);
            row.appendChild(updatePSSD);
            row.appendChild(manageDefect);

            tableBody1.appendChild(row);
        });
    });
}

function generateExcelReport() {
    saveRevisionHistoryData();
    saveTerminologyData();
    saveReferenceData();
    let newData = document.getElementById('newData').value;
    let selectedProjectId = document.getElementById('projects').value;
    let tab1Content = document.getElementById('tab1').innerHTML;

    if (!selectedProjectId) {
        alert("Please select a project.");
        return;
    }

    if (!confirm("Are you sure you want to generate the Excel report?")) {
        return; // Exit the function if the user cancels
    }
    let button = document.querySelector('button[onclick="generateExcelReport()"]');
    let loader = document.getElementById('loader');

    button.classList.add('animate-click');
    button.disabled = true;
    loader.style.display = 'block';

    fetch(`/generate_excel_report/${selectedProjectId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({tab1Content: tab1Content})
    })
        .then(response => {
            if (response.ok) {
                return response.blob();
            } else {
                throw new Error('Failed to generate Excel report');
            }
        })
        .then(blob => {
            let url = window.URL.createObjectURL(blob);
            let a = document.createElement('a');
            a.href = url;
            a.download = 'Product security vulnerability analysis report.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(error => {
            console.error('Error:', error);
        })
        .finally(() => {
            setTimeout(() => {
                button.classList.remove('animate-click');
                button.disabled = false;
                loader.style.display = 'none';
            }, 300);
        });
}

function updatePlaceholder() {
    let newData = document.getElementById('newData').value;
    document.getElementById('placeholder').textContent = newData;
    document.getElementById('placeholder1').textContent = newData;
    // Send the newData value to the backend
    fetch('/update_new_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({newData: newData})
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Data updated successfully');
            } else {
                console.error('Error updating data:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

document.addEventListener('DOMContentLoaded', (event) => {
    let buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            button.classList.add('animate-click');
            setTimeout(() => {
                button.classList.remove('animate-click');
            }, 300);
        });
    });
});

function saveRevisionHistoryData() {
    const table = document.getElementById('revisionHistoryTable');
    const rows = table.querySelectorAll('tbody tr');
    const data = [];

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowData = {
            revision: cells[0].innerText,
            revisionDate: cells[1].innerText,
            author: cells[2].innerText,
            attendees: cells[3].innerText,
            reason: cells[4].innerText
        };
        data.push(rowData);
    });

    fetch('/save_revision_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({revisionData: data})
    })
    .then(response => response.json())
    .catch(error => {
        console.error('Error:', error);
    });
}

function saveTerminologyData() {
    const table = document.getElementById('terminologyAbbreviationTable');
    const rows = table.querySelectorAll('tbody tr');
    const data = [];

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowData = {
            terminology: cells[0].innerText,
            description: cells[1].innerText,
        };
        data.push(rowData);
    });

    fetch('/save_terminology_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({terminologyData: data})
    })
        .then(response => response.json())
        .catch(error => {
            console.error('Error:', error);
        });
}

function saveReferenceData() {
    const table = document.getElementById('referencesTable');
    const rows = table.querySelectorAll('tbody tr');
    const data = [];

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowData = {
            referenceNumber: cells[0].innerText,
            documentTitle: cells[1].innerText,
            documentId: cells[2].innerText,
        };
        data.push(rowData);
    });

    fetch('/save_reference_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({referenceData: data})
    })
        .then(response => response.json())
        .catch(error => {
            console.error('Error:', error);
        });
}


function saveRevisionData() {
    // const formData = new FormData(document.getElementById('configurationForm'));
    const termList = document.getElementById('revisionHistoryTable').children;
    const terms = [];
    for (let i = 0; i < termList.length; i++) {
        terms.push(termList[i].textContent);
    }
    // formData.append('terms', JSON.stringify(terms));

    fetch('/save_revision_data', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Data saved successfully');
            } else {
                alert('Failed to save data');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while saving data');
        });
}