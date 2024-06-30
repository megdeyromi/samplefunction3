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



def handler(ctx, data: io.BytesIO=None):
    print("Entering Python Hello World handler", flush=True)
    name = "World"
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

   

       
    try:
        body = json.loads(data.getvalue())
        name = body.get("name")
    except (Exception, ValueError) as ex:
        print(str(ex), flush=True)

    print("Vale of name = ", name, flush=True)
    print("Exiting Python Hello World handler", flush=True)
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(name)}),
        headers={"Content-Type": "application/json"}
    )
