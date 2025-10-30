import bisect
import constants
import datetime
import google.cloud.bigquery
import json
import random

def create_fake_projects(number_of_projects=constants.DEFAULT_NUMBER_OF_PROJECTS):
    letters = "abcdefghijklmnopqrstuvwxyz"
    numbers = [0,1,2,3,4,5,6,7,8,9]
    environments = ["prod", "qv", "it", "dev"]
    gcp_projects = []
    for i in range(number_of_projects):
        tla = letters[int(random.random()*len(letters))] + letters[int(random.random()*len(letters))] + letters[int(random.random()*len(letters))]
        environment = environments[int(len(environments)*i/number_of_projects)]
        
        unique_id = ''.join([str(numbers[int(random.random()*len(numbers))]) for _ in range(4)])
        project_id = f"{tla}-{environment}-{unique_id}"
        gcp_projects.append(project_id)
    return gcp_projects

def generate_z_array():
    import math
    z = -2
    delta_z = 0.001
    z_array = []
    probabilities = []
    while z < 8 + delta_z:
        z_array.append(z)
        log_probability = 0.005650782*z**5 - 0.080413829*z**4 + 0.25401729435*z**2 - 3.38568295*z - 0.434556718
        probability = 1/(1+math.exp(log_probability))
        probabilities.append(probability)
        z += delta_z
    return {"probabilities": probabilities, "z_array": z_array}

def generate_new_z(z_data):
    return z_data['z_array'][min(bisect.bisect_left(z_data["probabilities"], random.random()), len(z_data['probabilities'])-1)]

def generate_gcp_probabilities(gcp_services=constants.GCP_SERVICES):
    sum_p = 0
    gcp_probabilities = []
    for i in range(len(gcp_services)):
        sum_p += 0.810071/(i* 3.7029 + 3.7030)
        gcp_probabilities.append(sum_p)
    return [p/sum_p * len(gcp_services)/ (1+len(gcp_services)) for p in gcp_probabilities]

def generate_project_probabilities(number_of_projects=constants.DEFAULT_NUMBER_OF_PROJECTS):
    sum_p = 0
    project_probabilities = []
    for i in range(number_of_projects):
        sum_p += 1/(i* 4.6379 + 13.851)
        project_probabilities.append(sum_p)
    return [p/sum_p * number_of_projects/ (1+number_of_projects) for p in project_probabilities]

def get_random_item_from_distribution(items, cdf_distribution):
    probability = random.random()
    index = min(bisect.bisect_left(cdf_distribution, probability), len(items)-1)
    return {"item": items[index], "probability": cdf_distribution[min(len(items)-1, index+1)]-cdf_distribution[index]}

def generate_fake_billing_data(number_of_projects=NUMBER_OF_PROJECTS):
    fake_billing_data = []
    gcp_projects = create_fake_projects(number_of_projects)
    gcp_project_cdf = generate_project_probabilities(number_of_projects=len(gcp_projects))
    gcp_service_cdf = generate_gcp_probabilities()
    
    day = datetime.date(2025, 1, 1)
    z_data = generate_z_array()
    for day_increment in range(365):
        z = generate_new_z(z_data)
        gcp_daily_cost = max(0, 19.8*day_increment + 62189 + z*17194.0821)
        current_gcp_daily_cost = 0
        while current_gcp_daily_cost < gcp_daily_cost:
            gcp_project_prob = get_random_item_from_distribution(gcp_projects, gcp_project_cdf)
            gcp_service_prob = get_random_item_from_distribution(GCP_SERVICES, gcp_service_cdf)
            
            overall_prob = gcp_project_prob["probability"]*gcp_service_prob["probability"]
            gcp_cost_for_item = gcp_daily_cost * overall_prob
            current_gcp_daily_cost += gcp_cost_for_item
            project_id = gcp_project_prob['item']
            parts= project_id.split("-")
            tla = parts[0]
            environment = parts[1]
            gcp_service = gcp_service_prob["item"]
            invoice_month = day.strftime("%Y%m")
            hour = int(random.random()*23)
            usage_start_time = datetime.datetime(day.year, day.month, day.day, hour, 0, 0)
            usage_end_time = datetime.datetime(day.year, day.month, day.day, hour+1, 0, 0)
            row = {"tla": tla, "project_id": project_id, "environment": environment, "service_description": gcp_service, "invoice_month": invoice_month, "usage_start_time": usage_start_time, "usage_end_time": usage_end_time, "cost": gcp_cost_for_item}
            fake_billing_data.append(row)
        day = day + datetime.timedelta(days=1)
    return fake_billing_data

def upload_to_bq(data, project_id, dataset_name, table_name):
  import pandas as pd
  client_bq = google.cloud.bigquery.Client()
  table_id = f"{PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}"
  job = client_bq.load_table_from_dataframe(pd.DataFrame(data), table_id)
  job.result()
