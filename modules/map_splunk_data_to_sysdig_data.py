
import json


# panel type -> Visualization at panel level - Timechart, Number, Toplist, Histogram, Table, Text
import os

splunk_to_sysdig_form_panel_type_mapping_dict = {"TimeSeriesChart": "basicTimechart", "SingleValue": "basicNumber",
                                        "toplist": "basicToplist", "note": "text", "TableChart": "basicTable", "List": "List"}

splunk_to_sysdig_prom_panel_type_mapping_dict = {"TimeSeriesChart": "advancedTimechart", "SingleValue": "advancedNumber",
                                        "toplist": "advancedToplist", "note": "text", "TableChart": "advancedTable", "List": "List"}

# panel query type -> Visualization at each query level for a panel -> Line, StackedArea or StackedBar
splunk_to_sysdig_form_panel_query_type_mapping_dict = {"AreaChart": "stackedArea",  "LineChart": "lines", "ColumnChart": "stackedBar"}


# sysdig_dashboard_panel_temp_dict["panel_type"] = splunk_to_sysdig_form_panel_type_mapping_dict[chart["options"]["type"]]

# sysdig_dashboard_panel_query_temp_dict["plot_type"] = splunk_tosysdig_form_panel_query_type_mapping_dict[sysdig_dashboard_panel_query_temp_dict["plot_type"]]


def map_splunk_data_to_sysdig_data(splunk_dashboards_list):
    sysdig_dashboard_list = []
    for dashboard in splunk_dashboards_list:
        sysdig_dashboard_list = sysdig_dashboard_list + prepare_sysdig_dashoard_data(dashboard)
    return sysdig_dashboard_list

def prepare_sysdig_dashoard_data(splunk_dashboard_data):

    f = open('./templates/dashboard_template.json')
    dashboard_template = json.load(f)
    f.close()

    sysdig_dashboard_list = []

    dashboard_data = dashboard_template.copy()
    dashboard_data["dashboard"]["name"] = splunk_dashboard_data["name"]
    dashboard_data["dashboard"]["description"] = splunk_dashboard_data["description"]
    dashboard_data["dashboard"]["panels"] = prepare_sysdig_panels(splunk_dashboard_data["panels"])
    dashboard_data["dashboard"]["layout"] = prepare_sysdig_dashboard_layout(splunk_dashboard_data["layout"])

    sysdig_dashboard_list.append(dashboard_data.copy())

    reassign_panel_ids(sysdig_dashboard_list)

    return sysdig_dashboard_list

def prepare_sysdig_panels(panels):

    panel_list = []

    for panel in panels:

        panel_data = prepare_sysdig_panel(panel)

        panel_list.append(panel_data.copy())
        panel_data.clear()

    return panel_list

def form_or_promql_panel(queries):
    is_promql = False
    for query in queries:
        if query["form_or_promql"] == "promql":
            is_promql = True
            break

    return is_promql

def prepare_sysdig_panel(panel):
    is_promql = form_or_promql_panel(panel["queries"])
    if is_promql:
        return prepare_sysdig_promql_panel(panel)
    else:
        return prepare_sysdig_form_panel(panel)


def prepare_sysdig_form_panel(panel):


    panel_type = splunk_to_sysdig_form_panel_type_mapping_dict[panel["panel_type"]]

    if panel_type  == "basicTimechart":
        f = open('./templates/form/timechart_form_template.json')
        timechart_form_template = json.load(f)
        f.close()

        panel_data = timechart_form_template.copy()

    elif panel_type == "basicNumber":

        f = open('./templates/form/number_form_template.json')
        number_form_template = json.load(f)
        f.close()

        panel_data = number_form_template.copy()
    elif panel_type == "basicTable":

        f = open('./templates/form/table_form_template.json')
        table_form_template = json.load(f)
        f.close()

        panel_data = table_form_template.copy()
    else:

        f = open('./templates/form/timechart_form_template.json')
        timechart_form_template = json.load(f)
        f.close()

        panel_data = timechart_form_template.copy()

    panel_data["id"] = panel["id"]
    panel_data["type"] = panel_type
    panel_data["name"] = panel["name"]
    panel_data["description"] = panel["description"]
    panel_data["basicQueries"] = prepare_sysdig_form_query(panel["queries"])

    return panel_data


def prepare_sysdig_promql_panel(panel):
    panel_type = splunk_to_sysdig_prom_panel_type_mapping_dict[panel["panel_type"]]
    if panel_type == "advancedTimechart":
        f = open('./templates/promql/timechart_promql_template.json')
        timechart_promql_template = json.load(f)
        f.close()

        panel_data = timechart_promql_template.copy()

    elif panel_type == "advancedNumber":

        f = open('./templates/promql/number_promql_template.json')
        number_promql_template = json.load(f)
        f.close()

        panel_data = number_promql_template.copy()
    elif panel_type == "advancedTable":

        f = open('./templates/promql/table_promql_template.json')
        table_promql_template = json.load(f)
        f.close()

        panel_data = table_promql_template.copy()
    else:

        f = open('./templates/promql/timechart_promql_template.json')
        timechart_promql_template = json.load(f)
        f.close()

        panel_data = timechart_promql_template.copy()

    panel_data["id"] = panel["id"]
    panel_data["type"] = panel_type
    panel_data["name"] = panel["name"]
    panel_data["description"] = panel["description"]
    panel_data["advancedQueries"] = prepare_sysdig_promql_query(panel["queries"])

    return panel_data


def prepare_sysdig_promql_query(queries):
    f = open('./templates/promql/promql_query_template.json')
    promql_query_template = json.load(f)
    f.close()

    query_list = []

    for query in queries:
        query_data = promql_query_template.copy()

        query_data["displayInfo"]["displayName"] = ""
        query_data["displayInfo"]["timeSeriesDisplayNameTemplate"] = ""
        query_data["displayInfo"]["type"] = splunk_to_sysdig_form_panel_query_type_mapping_dict[query["plot_type"]]
        query_data["query"] = query["promql"]

        query_list.append(query_data.copy())
        query_data.clear()

    return query_list

def prepare_sysdig_form_query(queries):

    f = open('./templates/form/form_query_template.json')
    form_query_template = json.load(f)
    f.close()

    query_list = []

    for query in queries:
        query_data = form_query_template.copy()

        query_data["displayInfo"]["displayName"] = ""
        query_data["displayInfo"]["timeSeriesDisplayNameTemplate"] = ""
        query_data["displayInfo"]["type"] = splunk_to_sysdig_form_panel_query_type_mapping_dict[query["plot_type"]]
        query_data["scope"]["expressions"] = prepare_sysdig_timechart_form_query_scope(query["scopes"])
        query_data["metrics"] = prepare_sysdig_form_query_metric(query["metric"], query["time_aggregation"], query["group_aggregation"])
        if "segmentations" in query:
            query_data["segmentation"]["labels"] = prepare_sysdig_form_query_seg(query["segmentations"])
        else:
            query_data["segmentation"]["labels"] = []

        query_list.append(query_data.copy())
        query_data.clear()

    return query_list

def prepare_sysdig_timechart_form_query_scope(scopes):

    f = open('./templates/form/form_query_scope_template.json')
    form_query_scope_template = json.load(f)
    f.close()

    scope_list = []
    for scope in scopes:
        scope_data = form_query_scope_template.copy()

        scope_data["operator"] = scope["operator"]
        scope_data["operand"] = scope["key_with_underscore"]
        scope_data["value"] = scope["values"]
        scope_data["descriptor"]["documentId"] = scope["key_with_underscore"]
        scope_data["descriptor"]["id"] = scope["key_with_underscore"]
        scope_data["descriptor"]["name"] = scope["key_with_underscore"]
        scope_data["descriptor"]["description"] = scope["key_with_underscore"]
        scope_data["descriptor"]["publicId"] = scope["key_with_underscore"]

        scope_list.append(scope_data.copy())
        scope_data.clear()

    return scope_list


def prepare_sysdig_form_query_metric(metric, time_agg, group_agg):

    f = open('./templates/form/form_query_metric_template.json')
    form_query_metric_template = json.load(f)
    f.close()

    metric_list = []

    metric_data = form_query_metric_template.copy()
    metric_data["id"] = metric
    # if time_agg == "":
    #     metric_data["timeAggregation"] = "avg"
    # else:
    #     metric_data["timeAggregation"] = time_agg
    # if group_agg == "":
    #     metric_data["groupAggregation"] = "avg"
    # else:
    #     metric_data["groupAggregation"] = group_agg
    metric_list.append(metric_data.copy())
    metric_data.clear()

    return metric_list


def prepare_sysdig_form_query_seg(segmentations):

    f = open('./templates/form/form_query_segment_template.json')
    form_query_seg_template = json.load(f)
    f.close()

    segment_list = []

    for segment in segmentations:
        segment_data = form_query_seg_template.copy()
        segment_data["id"] = segment["key_with_underscore"]
        segment_data["descriptor"]["documentId"] = segment["key_with_underscore"]
        segment_data["descriptor"]["id"] = segment["key_with_underscore"]
        segment_data["descriptor"]["name"] = segment["key_with_underscore"]
        segment_data["descriptor"]["description"] = segment["key_with_underscore"]
        segment_data["descriptor"]["publicId"] = segment["key_with_underscore"]

        segment_list.append(segment_data.copy())
        segment_data.clear()

    return segment_list

def reassign_panel_ids(sysdig_dashboard_list):
    id_counter = 1
    panel_ids = {}

    for panel in sysdig_dashboard_list[0]["dashboard"]["panels"]:
        panel_ids[panel["id"]] = id_counter
        panel["id"] = id_counter
        id_counter += 1

    for layout in sysdig_dashboard_list[0]["dashboard"]["layout"]:
        layout["panelId"] = panel_ids[layout["panelId"]]


def prepare_sysdig_dashboard_layout(layouts):

    f = open('./templates/dashboard_layout_template.json')
    dashboard_layout_template = json.load(f)
    f.close()

    layout_list = []

    for layout in layouts:
        layout_data = dashboard_layout_template.copy()

        layout_data["panelId"] = layout["panelId"]
        layout_data["x"] = layout["x"]
        layout_data["y"] = layout["y"]
        layout_data["w"] = layout["w"]
        layout_data["h"] = layout["h"]

        layout_list.append(layout_data.copy())

        layout_data.clear()

    return layout_list
