import json
import re

splunk_dashboard_data = {}  # dictionary containing all the panels for a given dashboard for Splunk. It is not yet formatted as Sysdig needs.
splunk_dashboard_list = []  # list containing splunk_dashboard_data - Splunk can have mulitiple dashboards exported in a same json file as group. Will need to create multiple dashboards.
promql_filter_dict = {"notIn": "!~", "in": "=~", "equals": "=", "NotEquals": "!="}


def query_splunk_dashboard_data(splunk_dashboard_file):
    # open splunk dashboard file
    f = open(splunk_dashboard_file)

    data = json.load(f)
    f.close()

    splunk_dashboards_list = read_and_parse_splunk_dashboard_group(data)
    splunk_dashboards_list = read_and_parse_splunk_dashboard_data(splunk_dashboards_list)

    return splunk_dashboards_list


def read_and_parse_splunk_dashboard_group(data):
    # splunk has dashboard group that can contain multiple dashboards.
    # if dashboard group json is provided, need to create 1 dashboard per dashboard in the group.
    # this function creates a list of dashboards

    splunk_dashboard_data = {}
    splunk_dashboards_list = []

    if "groupExport" in data:
        for dashboard_export in data["dashboardExports"]:
            chart_ids = []
            for chart in dashboard_export["dashboard"]["charts"]:
                chart_ids.append(chart["chartId"])

            splunk_dashboard_data["dashboardExport"] = dashboard_export
            splunk_dashboard_data["chartExports"] = [d for d in data["chartExports"] if d["chart"]['id'] in chart_ids]
            splunk_dashboards_list.append(splunk_dashboard_data.copy())
    else:
        splunk_dashboards_list.append(data.copy())

    return splunk_dashboards_list


def read_and_parse_splunk_dashboard_data(splunk_dashboards_list):
    splunk_dashboards_data_temp_list = []

    for dashboard in splunk_dashboards_list:
        splunk_dashboard_data["name"] = dashboard["dashboardExport"]["dashboard"]["name"]
        splunk_dashboard_data["description"] = dashboard["dashboardExport"]["dashboard"]["description"]
        splunk_dashboard_data["panels"] = parse_dashboards_panels(dashboard["chartExports"])
        splunk_dashboard_data["layout"] = parse_dashboard_layouts(dashboard["dashboardExport"]["dashboard"]["charts"])

        splunk_dashboards_data_temp_list.append(splunk_dashboard_data.copy())
        splunk_dashboard_data.clear()

    return splunk_dashboards_data_temp_list


def parse_dashboards_panels(charts):
    splunk_dashboard_panels_list = parse_dashboard_charts(charts)
    splunk_dashboard_panels_list = prepare_sysdig_query(splunk_dashboard_panels_list)

    return splunk_dashboard_panels_list


def parse_dashboard_charts(charts):
    splunk_dashboard_panels_list = []

    for chart in charts:
        chart = chart["chart"]

        splunk_dashboard_panel_temp_dict = {}
        splunk_dashboard_panel_query_temp_dict = {}
        splunk_dashboard_panel_queries_temp_list = []

        splunk_dashboard_panel_temp_dict["id"] = chart["id"]
        splunk_dashboard_panel_temp_dict["name"] = chart["name"]
        splunk_dashboard_panel_temp_dict["description"] = chart["description"]
        # splunk_dashboard_panel_temp_dict["panel_type"] = splunk_to_sysdig_form_panel_type_mapping_dict[chart["options"]["type"]]
        splunk_dashboard_panel_temp_dict["panel_type"] = chart["options"]["type"]

        if "axes" in chart["options"]:
            splunk_dashboard_panel_temp_dict["axes"] = chart["options"]["axes"]

        # there is a defaul plot type at chart level. use that if available.
        if "defaultPlotType" in chart["options"]:
            default_plot_type = chart["options"]["defaultPlotType"]
        else:
            splunk_dashboard_panel_temp_dict["plot_type"] = ""

        # other options available at query level...
        for query in chart["options"]["publishLabelOptions"]:
            splunk_dashboard_panel_query_temp_dict["display_name"] = query["displayName"]
            splunk_dashboard_panel_query_temp_dict["label"] = query["label"]
            if "plotType" not in query or query["plotType"] is None:
                splunk_dashboard_panel_query_temp_dict["plot_type"] = default_plot_type
            else:
                splunk_dashboard_panel_query_temp_dict["plot_type"] = query["plotType"]

            # splunk_dashboard_panel_query_temp_dict["plot_type"] = splunk_tosysdig_form_panel_query_type_mapping_dict[splunk_dashboard_panel_query_temp_dict["plot_type"]]
            splunk_dashboard_panel_query_temp_dict["plot_type"] = splunk_dashboard_panel_query_temp_dict["plot_type"]

            for splunk_query in chart["programText"].split("\n"):
                if str(splunk_query).startswith(query["label"]):
                    splunk_dashboard_panel_query_temp_dict["splunk_query"] = splunk_query
                    break
            splunk_dashboard_panel_queries_temp_list.append(splunk_dashboard_panel_query_temp_dict.copy())
            splunk_dashboard_panel_query_temp_dict.clear()

        splunk_dashboard_panel_temp_dict["queries"] = splunk_dashboard_panel_queries_temp_list.copy()
        splunk_dashboard_panels_list.append(splunk_dashboard_panel_temp_dict.copy())

        splunk_dashboard_panel_temp_dict.clear()

    return splunk_dashboard_panels_list


def prepare_sysdig_query(splunk_dashboard_panels_list):
    sysdig_dashboard_widgets_temp_dict = {}
    test_list = []
    for chart in splunk_dashboard_panels_list:
        for query in chart["queries"]:

            splunk_query = query["splunk_query"]
            # find data block
            data = ""
            regex = r"data\((.*?)\)\."
            matches = re.finditer(regex, splunk_query, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    data = "(" + match.group(groupNum) + ")."

            subst = ""
            non_data_block = re.sub(regex, subst, splunk_query, 0, re.MULTILINE)
            print(non_data_block)

            # find rollup block
            rollup = ""
            regex = r"rollup=\'(.*?)\'"
            matches = re.finditer(regex, data, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    rollup = match.group(groupNum)

            subst = ""
            data = re.sub(regex, subst, data, 0, re.MULTILINE)

            # find filter block
            filter = ""
            regex = r"filter=(.*?)\)\."
            matches = re.finditer(regex, data, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    filter = match.group(groupNum)

            subst = ""
            metric = re.sub(regex, subst, data, 0, re.MULTILINE)

            # parse filter block
            filter_not_list = []
            filter_list = []

            # parse filter block - get not filter conditions as a list
            regex = r"not filter(.*?)\)"
            matches = re.finditer(regex, filter, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    filter1 = match.group(groupNum)
                    filter_not_list.append(filter1)

            subst = ""
            filter = re.sub(regex, subst, filter, 0, re.MULTILINE)

            # parse filter block - get filter conditions as a list
            regex = r"filter(.*?)\)"
            matches = re.finditer(regex, filter, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                for groupNum in range(0, len(match.groups())):
                    groupNum = groupNum + 1
                    filter1 = match.group(groupNum)
                    filter_list.append(filter1)

            subst = ""
            remaining_data_block = re.sub(regex, subst, filter, 0, re.MULTILINE)
            print(remaining_data_block)

            # find sum block
            sum = ""
            regex = r"sum\((.*?)\)\."
            matches = re.finditer(regex, splunk_query, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                sum = match.group()
                # for groupNum in range(0, len(match.groups())):
                #     groupNum = groupNum + 1
                #     sum = match.group(groupNum)

            # find count block
            count = ""
            regex = r"count\((.*?)\)\."
            matches = re.finditer(regex, splunk_query, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                count = match.group()
                # for groupNum in range(0, len(match.groups())):
                #     groupNum = groupNum + 1
                #     count = match.group(groupNum)

            # adding more dictionaries to the existing list item
            query["metric"] = clean_data(metric)
            query["scopes"] = prepare_sysdig_scope(filter_list, "filter") + prepare_sysdig_scope(filter_not_list,
                                                                                                 "not_filter")
            query["time_aggregation"] = clean_data(rollup)
            query["group_aggregation"] = clean_data(sum)
            if "by" in query["group_aggregation"]:
                query["segmentations"] = prepare_sysdig_segmentation(query["group_aggregation"])
                query["group_aggregation"] = query["group_aggregation"].split("=")[0].replace("by", "")

            filter_str = ""
            for scope in query["scopes"]:
                filter_str = filter_str + scope["filter_str"] + ","
            if filter_str != "": filter_str = "{" + filter_str[0:len(filter_str) - 1] + "}"
            query["count"] = clean_data(count)

            seg_str = ""
            if "segmentations" in query:
                for seg in query["segmentations"]:
                    seg_str = seg_str + seg["key_with_underscore"] + ","

                if seg_str != "": seg_str = " by (" + seg_str[0:len(seg_str) -1] + ")"

            if query["group_aggregation"] == "": query["group_aggregation"] = "avg"
            if query["group_aggregation"] == "": query["group_aggregation"] = "avg"

            # metric name will be empty if there is a mathematical function.
            # (A+B).publish.... apply regex to get (A+B)
            # then create a promql query
            if query["metric"] == "":
                regex = r"= (.*?).publish"
                matches = re.finditer(regex, query["splunk_query"], re.MULTILINE)
                for matchNum, match in enumerate(matches, start=1):
                    for groupNum in range(0, len(match.groups())):
                        groupNum = groupNum + 1
                        function = match.group(groupNum)
                query["promql"] = function
                query["form_or_promql"] = "promql"
            else:
                query["promql"] = query["group_aggregation"] + "(" + query["group_aggregation"] + "(" + query[
                "metric"] + filter_str + ")" + seg_str + ")"
                query["form_or_promql"] = "form"

    return splunk_dashboard_panels_list


def clean_data(input_str: str):
    output_str = input_str.replace("'", "")
    output_str = output_str.replace("(", "")
    output_str = output_str.replace(").", "")
    output_str = output_str.replace(")", "")
    output_str = output_str.replace("[", "")
    output_str = output_str.replace("]", "")

    # Note: uncommented following 2 lines to make metric work... need to test for other fields to verify there is no negative impact on other fields.
    output_str = output_str.replace(", ", "")
    output_str = output_str.replace(".", "_")

    return output_str


def prepare_sysdig_scope(input_list: list, filter_no_filter):
    # this function takes filter list, cleans it up and creates another list with required scope values like "label name", "label values", "operator", etc
    output_dict = {}
    output_list = []
    for input_str in input_list:

        output_str = input_str.replace("'", "")
        output_str = output_str.replace("(", "")
        output_str = output_str.replace(")", "")

        output_split = output_str.split(", ")
        if len(output_split) > 2:  # if there are multiple values, use in or use is
            if filter_no_filter == "not_filter":  # if not condition, use not
                output_dict["operator"] = "notIn"
            else:
                output_dict["operator"] = "in"
        else:
            if filter_no_filter == "not_filter":
                output_dict["operator"] = "notEquals"
            else:
                output_dict["operator"] = "equals"

        output_dict["key_with_dot"] = output_split[0]
        output_dict["key_with_underscore"] = output_split[0].replace(".", "_")
        output_dict["values"] = output_split[1:]
        output_dict["filter_str"] = output_dict["key_with_underscore"] + promql_filter_dict[
            output_dict["operator"]] + ','.join(f'"{x}"' for x in output_dict["values"])
        output_list.append(output_dict.copy())
        output_dict.clear()

    return output_list


def prepare_sysdig_segmentation(input_str: str):
    # this function takes filter list, cleans it up and creates another list with required segmentation values like "label name"
    output_dict = {}
    output_list = []

    input_list = input_str.split("=")[1].split(",")

    for input_str in input_list:
        output_dict["key_with_dot"] = input_str
        output_dict["key_with_underscore"] = input_str.replace(".", "_")
        output_list.append(output_dict.copy())
        output_dict.clear()

    return output_list


def parse_dashboard_layouts(dash_export):
    sysdig_dashboard_layouts_list = []

    for layout in dash_export:
        layout_dict = {"panelId": layout["chartId"], "x": layout["column"], "y": layout["row"], "w": layout["width"],
                       "h": layout["height"]}

        sysdig_dashboard_layouts_list.append(layout_dict.copy())
        layout_dict.clear()

    return sysdig_dashboard_layouts_list

# moved it to map_splunk_data_to_sysdig_data.py
# def prepare_sysdig_dashoard_data():
#     f = open('dashboard_template.json')
#     dashboard_template = json.load(f)
#     f.close()
#
#     global sysdig_dashboard_list
#
#     dashboard_data = dashboard_template.copy()
#     dashboard_data["dashboard"]["name"] = splunk_dashboard_data["name"]
#     dashboard_data["dashboard"]["panels"] = prepare_sysdig_panels(splunk_dashboard_data["panels"])
#     dashboard_data["dashboard"]["layout"] = prepare_sysdig_dashboard_layout(splunk_dashboard_data["layout"])
#
#     sysdig_dashboard_list.append(dashboard_data.copy())
#
#     reassign_panel_ids()

# moved it to map_splunk_data_to_sysdig_data.py
# def prepare_sysdig_panels(panels):
#
#     panel_list = []
#
#     for panel in panels:
#
#         panel_data = panel_with_segments.prepare_sysdig_panel(panel)
#         # if panel["panel_type"] == "basicTimechart":
#         #     panel_data = panel_with_segments.prepare_sysdig_panel(panel)
#         # elif panel["panel_type"] == "basicNumber":
#         #     panel_data = panel_with_segments.prepare_sysdig_panel(panel)
#         # elif panel["panel_type"] == "basicTable":
#         #     panel_data = panel_with_segments.prepare_sysdig_panel(panel)
#         # elif panel["panel_type"] == "basicToplist":
#         #     panel_data = panel_with_segments.prepare_sysdig_panel(panel)
#
#         panel_list.append(panel_data.copy())
#         panel_data.clear()
#
#     return panel_list


# moved to map_splunk_data_to_sysdig_data.py
# def prepare_sysdig_dashboard_layout(layouts):
#
#     f = open('dashboard_layout_template.json')
#     dashboard_layout_template = json.load(f)
#     f.close()
#
#     layout_list = []
#
#     for layout in layouts:
#         layout_data = dashboard_layout_template.copy()
#
#         layout_data["panelId"] = layout["panelId"]
#         layout_data["x"] = layout["x"]
#         layout_data["y"] = layout["y"]
#         layout_data["w"] = layout["w"]
#         layout_data["h"] = layout["h"]
#
#         layout_list.append(layout_data.copy())
#
#         layout_data.clear()
#
#     return layout_list
