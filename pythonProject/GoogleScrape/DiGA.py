import os
import requests as re
import json
import datetime
import pandas as pd

def DiGA():

    os.makedirs("./data/DiGA/", exist_ok=True)

    with open("token.txt", "r") as f:
        token = f.read()

    endpoints = ["https://diga.bfarm.de/api/fhir/v2.0/CatalogEntry?_profile=https://fhir.bfarm.de/StructureDefinition/HealthAppCatalogEntry&_count=9999",
                 "https://diga.bfarm.de/api/fhir/v2.0/DeviceDefinition?_profile=https://fhir.bfarm.de/StructureDefinition/HealthApp&_count=9999",
                 "https://diga.bfarm.de/api/fhir/v2.0/DeviceDefinition?_profile=https://fhir.bfarm.de/StructureDefinition/HealthAppModule&_count=9999",
                 # "https://diga-api.bfarm.de/fhir/v2.0/DeviceDefinition?_profile=https://fhir.bfarm.de/StructureDefinition/HealthAppEffect",
                 "https://diga.bfarm.de/api/fhir/v2.0/ChargeItemDefinition?_profile=https://fhir.bfarm.de/StructureDefinition/HealthAppPrescriptionUnit&_count=9999",
                 "https://diga.bfarm.de/api/fhir/v2.0/Organization?_profile=https://fhir.bfarm.de/StructureDefinition/HealthAppManufacturer&_count=9999",
                 "https://diga.bfarm.de/api/fhir/v2.0/Questionnaire?_profile=https://fhir.bfarm.de/StructureDefinition/HealthAppQuestionnaire&_count=9999",
                 "https://diga.bfarm.de/api/fhir/v2.0/QuestionnaireResponse?_profile=https://fhir.bfarm.de/StructureDefinition/HealthAppQuestionnaireResponse&_count=9999"]

    out_path = "./data/DiGA/" + str(datetime.datetime.now().date())
    os.makedirs(out_path, exist_ok=True)

    s = re.Session()
    s.headers.update({"Authorization": 'Bearer {}'.format(token)})

    out = []

    for endpoint in endpoints:
        endpoint_name = endpoint.split("/")[-1].split("&")[0]
        endpoint_path = out_path + "/" + endpoint_name
        os.makedirs(endpoint_path, exist_ok=True)

        r = s.get(endpoint).json()
        links = []

        for entry in r["entry"]:
            links.append(entry["fullUrl"])

        for link in links:
            r = s.get(link).json()
            with open(endpoint_path + "/" + r["id"] + ".json", "w") as f:
                json.dump(r, f)

            if endpoint_name == "HealthAppModule":
                temp = [r["id"], None, None]
                for spec in r["specialization"]:
                    value = spec["extension"][1]["valueUri"]
                    if "google" in value:
                        temp[1] = value
                    if "apple" in value:
                        temp[2] = value
                out.append(temp)
    out = pd.DataFrame(out, columns=["id", "google_link", "apple_link"])
    out.to_csv(out_path + "/DiGA_links.csv", index=False)


if __name__ == "__main__":
    DiGA()