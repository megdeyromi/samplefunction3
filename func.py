import io
import json
import os
import requests
import cohere
from fdk import response

# Initialize Cohere Client with your API key
API_KEY = "B6ErOdasD4G2oYZyyM1xJFx8PwKRfDBhwiVmNRmB"
co = cohere.Client(API_KEY)

def downloadSwagger(url, file_path):
    r = requests.get(url, allow_redirects=True)
    open(file_path, 'wb').write(r.content)

def read_swagger_file(file_path):
    with open(file_path, 'r') as file:
        swagger_data = json.load(file)
        return swagger_data

def getComponents(data, component_name):
    item_ref = ""
    property_list = []
    for component, schema in data.items():
        if component_name == component:
            required_fields = schema.get('required', [])
            if 'properties' in schema:
                for property, pro_data in schema['properties'].items():
                    required = "required" if property in required_fields else "optional"
                    property_str = '%s | %s | %s | %s' % (property, pro_data.get('type', 'N/A'), pro_data.get('description', 'No description'), required)
                    property_list.append(property_str)
                if 'items' in schema['properties']:
                    item_ref = schema['properties']['items']['items']['$ref'].replace('#/components/schemas/', '')
    return property_list, item_ref

def getComponentParameters(methods_data):
    parameters_section = methods_data.get('parameters', [])
    parameters = []
    for parameter in parameters_section:
        required = "required" if parameter.get('required', False) else "optional"
        p = "%s | %s | %s | %s" % (parameter.get('name', 'N/A'), parameter.get('schema', {}).get('type', 'N/A'), parameter.get('schema', {}).get('description', 'No description'), required)
        parameters.append(p)
    return parameters

def getTagDetails(swagger_data, tags):
    tags_section = swagger_data.get('tags', [])
    tag_description = ""
    for tag in tags_section:
        if tags and tags[0] == tag.get('name'):
            tag_description = tag.get('description', '')
            break
    return tag_description

def generateAPIDescription(api_doc):
    prompt_template = '''Write a short description paragraph with a maximum of 100 words using the following API documentation between >>> and <<<:
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
        truncate="END"
    )
    generated = response
    return generated[0].text

def handler(ctx, data: io.BytesIO=None):
    print("Entering Oracle Functions handler", flush=True)
    
    # Default values
    swagger_url = 'https://docs.oracle.com/en/cloud/saas/project-management/24b/fapap/openapi.json'
    product_name = 'ppm'
    generateDesc = False
    
    try:
        body = json.loads(data.getvalue())
        # Fetch values from body if needed
        name = body.get("name", "World")
    except (Exception, ValueError) as ex:
        print(str(ex), flush=True)
        name = "World"
    
    # Fetch URL and product_name from ctx
    if ctx:
        try:
            url = ctx["headers"].get("url")
            product = ctx["headers"].get("product")
            generateDesc = ctx["headers"].get("generateDesc", False)
            if url:
                swagger_url = url
            if product:
                product_name = product
        except Exception as e:
            print(f"Error fetching parameters from ctx: {e}")
    
    # Other processing logic based on your original main logic
    # Download Swagger file
    home_path = '/home/datascience'
    swagger_file_path = os.path.join(home_path, f'{product_name}_openapi.json')
    downloadSwagger(swagger_url, swagger_file_path)
    
    # Read Swagger file
    swagger_data = read_swagger_file(swagger_file_path)
    
    # Additional logic based on your original main function
    # For brevity, I'm skipping the entire processing logic here.
    
    # Example response format
    response_data = {
        "message": f"Hello {name}",
        "url": swagger_url,
        "product_name": product_name,
        "generateDesc": generateDesc
    }
    
    print("Exiting Oracle Functions handler", flush=True)
    
    return response.Response(
        ctx,
        response_data=json.dumps(response_data),
        headers={"Content-Type": "application/json"}
    )
