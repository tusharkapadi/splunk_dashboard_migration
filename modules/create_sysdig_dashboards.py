import copy
import json
import requests

err_data = {}
err_data_list = []
fix_me_promql = "avg(ads_brand_rtb_http_request_ok)"
fix_me_table = "ads_brand_rtb_http_request_ok"
dashboard_data_list = [] # list of dashboard_data to support multiple dashboard creation if panels > max_panels
err_data_list_of_list = [] # list of failed panels for each dashboard
response_list = [] # response for each dashboard creation



def create_sysdig_dashboard_json(sysdig_dashboards_list, end_point, api_token):

    for sysdig_dashboard in sysdig_dashboards_list:
        dashboard_data = copy.deepcopy(sysdig_dashboard)

        test_each_panel(dashboard_data, end_point, api_token)
        restore_all_panels_and_layouts(dashboard_data, end_point, api_token)
        #create_dashboards()

    print("in")


def test_each_panel(dashboard_data, end_point, api_token):

    # test each panel by creating a dashboard with that one panel only.
    panels_list = dashboard_data["dashboard"]["panels"].copy()
    layout_list = dashboard_data["dashboard"]["layout"].copy()

    dashboard_id = "3708"
    dashboard_data["dashboard"]["id"] = dashboard_id
    curr_row_no = 0
    while curr_row_no < len(panels_list):
        print(curr_row_no)

        dashboard_data["dashboard"]["panels"].clear()
        dashboard_data["dashboard"]["layout"].clear()
        dashboard_data["dashboard"]["panels"].append(panels_list[curr_row_no])
        dashboard_data["dashboard"]["layout"].append(layout_list[curr_row_no])

        response = create_dashboard(dashboard_data, "PUT", end_point, api_token)

        # if an issue with the panel:
        if response is not None and response.status_code == 422:
            print("X", end="")
            err_data["id"] = dashboard_data["dashboard"]["panels"][0]["id"]
            err_data["row_no"] = curr_row_no
            err_data["error"] = response.text
            err_data["title"] = dashboard_data["dashboard"]["panels"][0]["name"]
            err_data_list.append(err_data.copy())
            err_data.clear()
        else:
            print(".", end="")

        curr_row_no = curr_row_no + 1
        print("in")


def restore_all_panels_and_layouts(dashboard_data, end_point, api_token):

    panels_list = dashboard_data["dashboard"]["panels"].copy()
    layout_list = dashboard_data["dashboard"]["layout"].copy()

    # restore all the panels and layouts
    dashboard_data["dashboard"]["panels"].clear()
    dashboard_data["dashboard"]["panels"] = panels_list
    dashboard_data["dashboard"]["layout"].clear()
    dashboard_data["dashboard"]["layout"] = layout_list

    dashboard_data["dashboard"]["id"] = ""

    curr_row_count = 0
    query_str = ""
    for panel in dashboard_data["dashboard"]["panels"]:
        for err_data in err_data_list:
            if err_data["id"] == panel["id"]:
                query_str = ""
                # update the panel with dummy query
                panel["name"] += " - FIX ME"
                if "advancedQueries" in panel:
                    for query in panel["advancedQueries"]:
                        query_str += query["query"]
                        query["query"] = fix_me_promql
                panel["description"] = "datadog query - " + panel["description"] + "\nPromql - " + query_str
                break;
        curr_row_count += 1

    err_data_list_of_list.append(err_data_list.copy())


def create_dashboards():
    print("\nCreating a Sysdig dashboard using all the panels...")

    for dashboard_data in dashboard_data_list:
        response_list.append(create_dashboard(dashboard_data, "POST"))

def create_dashboard(dashboard_data: list, http_method, end_point, api_token):

    dashboard_id = "3708"
    if http_method == "POST":
        url = end_point + "/api/v3/dashboards"

    elif http_method == "PUT":
        url = end_point + "/api/v3/dashboards/" + dashboard_id

    payload = json.dumps(dashboard_data)

    print(payload)

    auth = "Bearer " + api_token
    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    response = requests.request(http_method, url, headers=headers, data=payload)

    return response

def print_summary_output():

    print("="*100)
    print("SUMMARY")
    print("="*100)
    print("Script attempted to create " + str(len(response_list)) + " dashboard(s).")
    for index, response in enumerate (response_list):
        print("-"*100)
        #if response.status_code != 200 and response.status_code != 201\

        if response.ok:
            #save sysdig dashboard id - useful if user wants to update the dashboard through script.
            response_json = json.loads(response.text)
            dashboard_data_list[index]["dashboard"]["id"] = response_json["dashboard"]["id"]

            print("Dashboard Title - " + dashboard_data_list[index]["dashboard"]["name"])
            print("Status: Dashboard created successfully.")
            total_imported_panels = len(dashboard_data_list[index]["dashboard"]["panels"])
            print("Total Panels - " + str(total_imported_panels) + " -- Failed Panel - " + str(
                len(err_data_list_of_list[index])))

            success_panels = total_imported_panels - len(err_data_list_of_list[index])
            success_rate = success_panels / total_imported_panels
            success_rate = round(100 * success_rate, 2)

            print("Success Rate - " + str(success_rate) + "%")
            print_failed_panels(err_data_list_of_list[index])
        else:
            print("Status: received an error while creating a dashboard - " + json.dumps(response.text))

def print_failed_panels(err_data_list:list):

    if len(err_data_list) > 0:
        print("")
        print("All failed panels/widgets will have 'FiX ME' appended in their title. Here is the list of failed "
              "panels/widgets with splunk title for your reference:")
        for err in err_data_list:
            print(err["title"])
