import constants
import google.cloud.bigquery

def create_dataset(job_config):
    project_id = job_config.get("project_id", constants.PROJECT_ID)
    dataset_id = job_config.get("dataset_id")    
    client = google.cloud.bigquery.Client()
    dataset = google.cloud.bigquery.Dataset(dataset_id)
    dataset.location = job_config.get("dataset_location", "us")
    try:
        dataset = client.create_dataset(dataset, timeout=30)
    except:
        message = f"[ERROR] Unable to create dataset: {str(err)}"
        if "Already Exists" in message:
            print(f"Dataset {dataset.dataset_id} already exists.")
            pass
        else:
            print(json.dumps({"message": message, "sevirity": "ERROR"}))

def create_table(job_config):
    project_id = job_config.get("project_id", constants.PROJECT_ID)
    dataset_id = job_config.get("dataset_id")
    table_fields = job_config.get("table_fields")
    table_name = job_config.get("table_name")
    schema = []
    table_id = f"{dataset_id}.{table_name}"
    for field in table_fields:
        schema.append(google.cloud.bigquery.SchemaField(field.get('name'), field.get('datatype'), mode=field.get('mode', 'REQUIRED')))
    client = google.cloud.bigquery.Client(project=project_id)
    try:
        table = client.create_table(google.cloud.bigquery.Table(table_id, schema=schema))
        print(f"Created table {table.table_id} in BigQuery")
    except Exception as err:
        message = f"Unable to create table {table_name}: {str(err)}"
        if "Already Exists" in message:
            print(f"Table {table_id} already exists.")
            pass
        else:
            print(message)
    return True

if __name__ == "__main__":
    bigquery_config = {
        "project_id": constants.PROJECT_ID, 
        "dataset_id": f"{constants.PROJECT_ID}.{constants.DATASET_NAME}",
        "table_name": constants.TABLE_NAME,
        "table_fields": constants.TABLE_FIELDS,
        "dataset_location": "us"
    }
    create_dataset(bigquery_config)
    create_table(bigquery_config)
