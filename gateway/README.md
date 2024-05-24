This application is a Python Flask REST API that is Dockerized and run as a service in a local kubernetes cluster.

The API's responsibilities are as follows:
1. Ingest the workflow template file and create the corresponding OpenFaaS functions.
2. Execute the workflow for evaluation.
3. Faciltate the data analysis via Prometheus (WIP)