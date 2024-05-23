import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import os

def jira_data(project_name):
    url = "https://blenheimchalcot.atlassian.net/rest/api/2/search"
    auth = HTTPBasicAuth("saumya.dash@blenheimchalcot.com",os.getenv("JIRA_API_KEY"))
    headers = { "Accept": "application/json"}

    # Initialize variables
    all_issues = []
    start_at = 0
    max_results = 50  # Adjust this according to your API's maximum results per request
    jql_data = f'project ="{project_name}"'
    while True:
        # Make a request to fetch issues with pagination
        response = requests.request("GET", url, headers=headers, auth=auth, params={'startAt': start_at, 'maxResults': max_results, 'jql': jql_data})
        # Check if request was successful
        
        print(response.status_code)
        if response.status_code != 200:
            print("Error: Unable to fetch issues.")
            break
        
        # Parse the JSON response
        project_data = json.loads(response.text)
        
        # Extract issues from the response
        issues = project_data.get('issues', [])
        
        # If no more issues are returned, break the loop
        if not issues:
            break
        
        # Append the retrieved issues to the list
        all_issues.extend(issues)
        
        # Increment the starting index for the next request
        start_at += max_results

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(all_issues)



    processed_issues = []
    for issue in all_issues:
        processed_issue = {
            'Issue key': issue.get('key', None),
            'Summary': issue['fields'].get('summary', None),
            'Description': issue['fields'].get('description', None),
            'Assignee': None,
            'Status': None,
            'Custom field (Story Points)': issue['fields'].get('customfield_10033', None),
            'Labels': issue['fields'].get('labels', None),
            'Components': issue['fields'].get('components', None),
            'Issue Type': None,
            'Epic Link Summary': None
            
            # Add more fields as needed
        }

        assignee_field = issue['fields'].get('assignee', None)
        if assignee_field is not None:
            processed_issue['Assignee'] = assignee_field.get('displayName', None)
        
        status_field = issue['fields'].get('status', None)
        if status_field is not None:
            processed_issue['Status'] = status_field.get('name', None)
        
        epic_linked_field = issue['fields'].get('parent', {}).get('fields', {}).get('summary', None)
        if epic_linked_field is not None:
            processed_issue['Epic Link Summary'] = epic_linked_field
        
        issuetype_field = issue['fields'].get('issuetype', None)
        if issuetype_field is not None:
            processed_issue['Issue Type'] = issuetype_field.get('name', None)

        processed_issues.append(processed_issue)

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(processed_issues)
    df= df.replace('#','',regex=True)
    
    return df
# print(jira_data("BC India - R&D"))

# Display or further process the DataFrame as neededdf.columns.to_list())
