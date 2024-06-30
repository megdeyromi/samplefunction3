#
# hello-python version 1.0.
#
# Copyright (c) 2020 Oracle, Inc.  All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#

import io
import json

from fdk import response
import io
import json
import pandas as pd
import json
import os
import sys, getopt
import pandas as pd
import cohere
import time
import requests
#API_KEY="ZXCkVLN1x6RfnMM19TBCJQ0Jki2Vq0OouTgkSGzf"
API_KEY="B6ErOdasD4G2oYZyyM1xJFx8PwKRfDBhwiVmNRmB"

co = cohere.Client(API_KEY)

from fdk import response

def downloadSwagger(url, file_path):
    r = requests.get(url, allow_redirects=True)
    open(file_path, 'wb').write(r.content)

def read_swagger_file(file_path):
    with open(file_path, 'r') as file:
        swagger_data = json.load(file)
        return swagger_data

def getComponents(data,component_name):
    item_ref=""
    property_list = []
    for component, schema in data.items():
        if component_name == component:
            required_filds = []
            if "required" in schema:
                required_filds = schema['required']
            if 'properties' in schema:
                for property, pro_data in schema.get('properties').items():
                    required = ""
                    optional = ""
                    if property in required_filds:
                        required = "required"
                    else:
                        optional = "optional"
                    if "description" in pro_data :
                        property_str = '%s | %s | %s | %s' %(property, pro_data['type'], pro_data['description'], required or optional)
                    else:
                        property_str = '%s | %s | %s' %(property, pro_data['type'], required or optional)
                    property_list.append(property_str)
                if 'items' in schema.get('properties'):
                    item_ref = schema.get('properties')['items']['items']['$ref'].replace('#/components/schemas/','')
    return property_list, item_ref

def getRequestBodyComponents(data,component_name):
    item_ref=""
    property_list = []
    for component, schema in data.items():
        if component_name == component:
            if 'content' in schema:
                for content_type, content_data in schema.get('content').items():
                    content_type = content_type
                    ref = content_data['schema']['$ref'].replace('#/components/schemas/','')
    return content_type, ref

def getComponentParameters(methods_data):
    parameters_section =  methods_data.get('parameters')
    parameters=[]
    
    for parameter in parameters_section:
        required="" 
        optional=""
        if parameter['required']:
            required = "required"
        else:
            optional = "optional"
        if 'description' in parameter.get('schema'):
            p = "%s | %s | %s | %s" % (parameter.get('name') , parameter.get('schema')['type'], parameter.get('schema')['description'], required or optional)
        else:
            p = "%s | %s | % s" % (parameter.get('name') , parameter.get('schema')['type'], required or optional)
        parameters.append(p)
    return parameters

def getComponentRequestBody(components_schemas_section,methods_data):
    content_type, item_ref=""
    requestBody_section =  methods_data.get('requestBody')
    if '$ref' in requestBody_section:
        component_name = requestBody_section['$ref'].replace('#/components/requestBodies/','')
        content_type, item_ref = getRequestBodyComponents(components_schemas_section,component_name)
    else:
        description = requestBody_section['description']
        for type, schema in requestBody_section['content'].items():
            contentType = type
            properties = schema.get['properties']
        
    return content_type, item_ref

def getTagDetails(swagger_data, tags):
    tags_section = swagger_data['tags']
    tag_description = ""
    for tag in tags_section:
        if tags:
            if tags[0] == tag['name']:
                if 'description' in tag:
                    tag_description = tag['description']
                break
    return tag_description

def generateAPIDescription(api_doc):
    prompt_template='''Write a short description paragraph with a maximum of 100 words using the following API documentation between >>> and <<<:
    >>>
    {api_doc}
    <<<
    1. The description describes the usage of this API.  
    2. Explain a bit more about the request parameters and response data.  
    3. Do not include any json object structures or HTML tags in the description.
    '''
    prompt = prompt_template.format(api_doc=api_doc)
    response = co.generate(
        prompt=prompt,
        model='command-nightly', 
        max_tokens=255,
        return_likelihoods="None",
        temperature=0,
        truncate= "END"
    )
    generated = response
    return generated[0].text

def saveProcessedInfo(info, file):
    with open(file, 'w') as file:
        json.dump(info, file)


def main(argv):
    swagger_url =  'https://docs.oracle.com/en/cloud/saas/project-management/24b/fapap/openapi.json'
    product_name = 'ppm'
    generateDesc =  False
    print("debug 1")
    try:
        opts, args = getopt.getopt(argv,"hu:p:g:",["url=","product=", "generateDesc="])
        print("debug 2")
    except getopt.GetoptError:
      print ('swagger_file_processor.py -u <swagger URL, e.g.: "https://docs.oracle.com/en/cloud/saas/human-resources/23b/farws/openapi.json"> -p <fusion product e.g. hcm>')
      sys.exit(2)
    for opt, arg in opts:
      if opt == '-h':
         print ('swagger_file_processor.py -u <swagger URL, e.g.: "https://docs.oracle.com/en/cloud/saas/human-resources/23b/farws/openapi.json"> -p <fusion product e.g. hcm> -g True')
         sys.exit()
      elif opt in ("-u", "--url"):
         swagger_url = arg
      elif opt in ("-p", "--product"):
         product_name = arg
      elif opt in ("-g", "--generateDesc"):
         generateDesc = eval(arg)

    api_string = '''API documentation:
Description | {description}

Endpoint | {url}
{action} {path}

Query parameters table: 
{query_parameters}

Response schema (JSON object):
{response}

Each object in the "items" key has the following schema:
{items}
'''

    api_string_no_items = '''API documentation:
Description | {description}

Endpoint | {url}
{action} {path}

Query parameters table: 
{query_parameters}

Response schema (JSON object):
{response}
'''

    api_string_not_json = '''API documentation:
Description | {description}

Endpoint | {url}
{action} {path}

Query parameters table: 
{query_parameters}

Response schema:
{response}
'''
    home_path='.'
    print('Home Path : ',home_path)
    swagger_file_path = home_path + '/' + product_name + '_openapi.json'
    api_doc_path_filename = home_path + '/' + product_name + '_api_doc.txt'
    api_summaray = []
    api_info={}
    processed_log_path_filename = home_path + '/' + product_name + '_processed_log.json'
    processed_log={"Path":[]}
    print("debug 3")
    if not os.path.exists(swagger_file_path):
        downloadSwagger(swagger_url,swagger_file_path)
    try:
        if os.path.exists(api_doc_path_filename):
            f1 = open(api_doc_path_filename, 'a')
            print("debug 4")
        else:
            f1 = open(api_doc_path_filename,'w')
            print("debug 5")
        if os.path.exists(processed_log_path_filename):
            processed_log_file =  open(processed_log_path_filename,"r")
            processed_log = json.loads(processed_log_file.read())
            processed_log_file.close()
            print("debug 6")
        swagger_data = read_swagger_file(swagger_file_path)
        if 'info' in swagger_data:
            info_section = swagger_data['info']
            api_info['Title'] = info_section.get('title', 'N/A')
            api_info['Version'] = info_section.get('version', 'N/A')
            print("debug 7")
        if 'paths' in swagger_data:
            paths_section = swagger_data['paths']
            components_schemas_section = swagger_data['components']['schemas']
            components_requestBodies_section = swagger_data['components']['requestBodies']
            api_info['Total_Paths'] = len(paths_section)
            processed_path = []
            print("debug 8")
            for path, methods in paths_section.items():
                if path in processed_log["Path"]:
                    processed_path.append(path)
                    continue
                    
                for method, method_data in methods.items():
                    if method in ["get"] :    # Only handle get at this moment
                        item_schama=[]
                        schama=[]
                        non_json_response_schema=""
                        tag_description = getTagDetails(swagger_data, method_data.get('tags'))
                        description = method_data.get('description')
                        if not description:
                            description = method_data.get('summary')
                        description = description + '.  ' + tag_description
                        if 'parameters' in method_data:
                            parameters = getComponentParameters(method_data)
                        if method_data.get('responses')['default']['content']:
                            responses_content_section =  method_data.get('responses')['default']['content']
                            for content_type, schema in responses_content_section.items():
                                if content_type in ['application/json']:
                                    if schema.get('schema')['$ref']:
                                        schema_ref = schema.get('schema')['$ref']
                                        component_name = schema_ref.replace('#/components/schemas/','')
                                        schama, item_ref = getComponents(components_schemas_section, component_name )
                                        item_schama, item_ref = getComponents(components_schemas_section, item_ref )
                                    else:
                                        if schema.get('schema')['type']:
                                            schema_type = schema.get('schema')['type']
                                elif content_type in ['text/html','application/octet-stream','text/calendar','image/png','text/css']:
                                    if schema.get('schema')['type']:
                                        schema_type = schema.get('schema')['type']
                                        non_json_response_schema = content_type + ' | '  + schema_type
                                        schama.append(non_json_response_schema)
                                else:
                                    print("Content Type:", content_type, " in path: ", path, " not supported")
                        if item_schama:
                            output1 = api_string.format(url='{url}', path=path, action=method, description=description, query_parameters='\n'.join(parameters),response='\n'.join(schama), items='\n'.join(item_schama))
                            if generateDesc:
                                updated_desc = generateAPIDescription (output1)
                                output1 = api_string.format(url='{url}', path=path, action=method, description=updated_desc, query_parameters='\n'.join(parameters),response='\n'.join(schama), items='\n'.join(item_schama))
                        elif non_json_response_schema:
                            output1 = api_string_not_json.format(url='{url}', path=path, action=method, description=description, query_parameters='\n'.join(parameters),response='\n'.join(schama), items='\n'.join(item_schama))
                            if generateDesc:
                                updated_desc = generateAPIDescription (output1)
                                output1 = api_string_not_json.format(url='{url}', path=path, action=method, description=updated_desc, query_parameters='\n'.join(parameters),response='\n'.join(schama), items='\n'.join(item_schama))
                        else:
                            output1 = api_string_no_items.format(url='{url}', path=path, action=method, description=description, query_parameters='\n'.join(parameters),response='\n'.join(schama))
                            if generateDesc:
                                updated_desc = generateAPIDescription (output1)
                                output1 = api_string_no_items.format(url='{url}', path=path, action=method, description=updated_desc, query_parameters='\n'.join(parameters),response='\n'.join(schama))
                        f1.write(output1)
                        if generateDesc:
                            time.sleep(10)
                processed_path.append(path)
                api_info.update({"Total_Processed" : len(processed_path)})
                api_info.update( {"Path": processed_path})
                saveProcessedInfo(api_info, processed_log_path_filename)
    except FileNotFoundError:
        print("Error: File not found. Please provide the correct file path.")
    except json.JSONDecodeError:
        print("Error: Unable to parse the JSON file. Please check if it's a valid Swagger JSON.")
    except Exception as e:
        print("An error occurred:", str(e))
    finally:
        f1.close


def handler(ctx, data: io.BytesIO=None):
    print("Entering Python Hello World handler", flush=True)
    name = "World"
       
    try:
        body = json.loads(data.getvalue())
        name = body.get("name")
    except (Exception, ValueError) as ex:
        print(str(ex), flush=True)

    print("Vale of name = ", name, flush=True)
    print("Exiting Python Hello World handler", flush=True)
    #main(sys.argv[1:])
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(name)}),
        headers={"Content-Type": "application/json"}
    )
