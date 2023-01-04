import sys
import modules.query_spunk_dashboard_data
import modules.map_splunk_data_to_sysdig_data
import modules.create_sysdig_dashboards
import modules.query_splunk_dashboards

splunk_dashboard_data = {} # dictionary containing all the panels for a given dashboard for Splunk. It is not yet formatted as Sysdig needs.
sysdig_dashboard_list = [] # list containing all the dashboards and panels in Sysdig format. Using templates and populating data.

sysdig_end_point = "https://us2.app.sysdig.com"
splunk_end_point = "https://app.us1.signalfx.com"

def dashboard_migration():

    # parse input arguments
    sysdig_api_token, splunk_dashboard_file = parse_args()

    # query splunk dashboards using splunk REST API
    #modules.query_splunk_dashboards.query_splunk_dashboards(splunk_end_point, splunk_api_token)

    # parse splunk dashboard data
    splunk_dashboards_list = modules.query_spunk_dashboard_data.query_splunk_dashboard_data(splunk_dashboard_file)

    # map splunk data to sysdig data
    sysdig_dashboards_list = modules.map_splunk_data_to_sysdig_data.map_splunk_data_to_sysdig_data(splunk_dashboards_list)

    # create sysdig dashboards
    modules.create_sysdig_dashboards.create_sysdig_dashboard_json(sysdig_dashboards_list, sysdig_end_point, sysdig_api_token)

    print("done")


def parse_args():
    if len(sys.argv) != 3:
        print(('usage: %s <Sysdig Monitor API Token> <Splunk Dashboard Location>' % sys.argv[0]))
        sys.exit(1)

    api_token = sys.argv[1]
    splunk_dashboard_file = sys.argv[2]

    return api_token, splunk_dashboard_file



if __name__ == '__main__':
    dashboard_migration()
