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
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(name)}),
        headers={"Content-Type": "application/json"}
    )
