import yaml
import requests


def process_template(filepath):
    with open(filepath, 'r') as file:
        template = yaml.safe_load(file)
        print(template)
    
    print(type(template))
    print(template['functions'][0])
    function_name = template['functions'][0]['name']
    workflow_logic = template['workflow_logic']

    print("hello")
    response = requests.get("http://10.152.183.241:8080/function/" + function_name)
    print(response.text)
    # return 'you have hit the gateway lol and hello response is : ' + response.text


    match workflow_logic:
        case "pipeline":
            print("pipeline")
        case "cron":
            print("cron")
        case "one-to_many":
            print("one-to-many")
        case "many-to-one":
            print("many-to-one")
        case "branching":
            print("branching")
        case _:
            print("error")