import requests

def query_splunk_dashboards(splunk_api_token, splunk_end_point):

    url = splunk_end_point + "/v2/dashboardgroup"

    auth = "Bearer " + splunk_api_token
    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    response = requests.request("GET", url, headers=headers, data={})

    print(response.text)