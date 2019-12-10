# Introduction to Creating and Deploying Serverless Functions on Oracle Cloud

## Prerequisites 
This tutorial covers the basics for the Fn Project, an open-source 
platform for creating serverless cloud functions. Oracle Cloud (OCI) 
chose the Fn platform for its Oracle Functions product, so that is what 
we will be deploying our Fn function to. Before beginning, I recommend 
reading these articles explaining Fn Project and Oracle Functions 
(they have inspired the contents of this tutorial).
* https://github.com/fnproject/tutorials/tree/master/python/intro
* https://www.oracle.com/webfolder/technetwork/tutorials/infographics/oci_faas_gettingstarted_quickview/functions_quickview_top/functions_quickview/index.html?source=post_page-----c1c61b68b075----------------------
* https://blogs.oracle.com/cloud-infrastructure/announcing-oracle-functions

## First Steps
* Please follow the Oracle Functions QuickStart Tutorial (Second Link in Prerequisites) for setting up your OCI tenancy.
* Make sure you have Docker installed on your local machine.
* Ensure that your OCI user has a setup API signing key. More information can be found here: https://docs.cloud.oracle.com/iaas/Content/API/Concepts/apisigningkey.htm' 
* Ensure that that you have setup an OCI Registry for storing Docker images. More information can be found here: https://www.oracle.com/webfolder/technetwork/tutorials/obe/oci/registry/index.html

## Install Fn
The local setup for this guide was done on MacOS. Run the following Homebrew command to install Fn:
```
$ brew install fn
```

## Create Function
Simply run the command below to create an initialize a simple Hello World function called 'ocifndemo'. We will be writing a Python runtime function but you have the option to work with Go, Java, or Node, as well.
```
$ fn init --runtime python ocifndemo
```

## Function structure and overview
Change directory to 'ocifndemo' and list created files 
```
$ cd ocifndemo
$ ls 
func.py func.yaml requirements.txt
```
### func.py 
This is the actual code of the function. It simply returns a JSON Hello 
World message or Hello "Name" if you pass it an input. We will modify 
this code to instead scrape weather data and return via the CLI. It is 
important to keep the handler as it is the entrypoint defined by the 
generated Fn Dockerfile. You must structure your custom logic to still 
use the handler. For our example, we define a function getWeather to do 
the actual work, but call it from our handler. The code should be changed 
from the following original code:
```
import io
import json


from fdk import response


def handler(ctx, data: io.BytesIO=None):
    name = "World"
    try:
        body = json.loads(data.getvalue())
        name = body.get("name")
    except (Exception, ValueError) as ex:
        print(str(ex))

    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(name)}),
        headers={"Content-Type": "application/json"}
    )
```
to the this updated code:
```
import io
import json

from fdk import response

import requests
from bs4 import BeautifulSoup
import pandas


def handler(ctx, data: io.BytesIO=None):
    ans = getWeather()
    return response.Response(
        ctx, response_data=json.dumps(ans),
        headers={"Content-Type": "application/json"}
    )

def getWeather():
    page = requests.get("https://weather.com/weather/hourbyhour/l/7472a7bbd3a7454aadf596f0ba7dc8b08987b1f7581fae69d8817dffffc487c2")
    content = page.content
    soup = BeautifulSoup(content, "html.parser")
    l = []
    all = soup.find("div", {"class": "locations-title hourly-page-title"}).find("h1").text

    table = soup.find_all("table", {"class": "twc-table"})

    for items in table:
        for i in range(len(items.find_all("tr")) - 1):
            d = {}
            try:
                d["desc"] = items.find_all("td", {"class": "description"})[i].text
                d["temp"] = items.find_all("td", {"class": "temp"})[i].text
            except:
                d["desc"] = "None"
                d["temp"] = "None"
            l.append(d)

    df = pandas.DataFrame(l)

    resp0nse = "It is " + df.at[0, "desc"] + ". The temperature is " + df.at[0, "temp"]

    return resp0nse
```

### func.yaml 
This generated yaml file does not need to be modified. It simply contains metadata about the function.

### requirements.txt 
This file includes the necessary libraries for the Fn function such as fdk (Function Developer Kit). Modify this file to also included our codes necessary libraries for scraping and data formatting. It should look like this:
```
fdk
requests
bs4
pandas
```

## Create and configure Context for OCI
Context is an Fn concept that determines where you're function is deployed. Run the following code to create a new Fn CLI context for OCI:
```
$ fn create context <my-context> --provider oracle
```
Select the new context for use:
```
$ fn use context <my-context>
```
Update the context with your OCI compartment ID and the Oracle Functions API URL (region may vary, in this case we used us-ashburn-1):
```
$ fn update context oracle.compartment-id <compartment-ocid>
$ fn update context api-url https://functions.us-ashburn-1.oraclecloud.com
```
Update the context with the location of the OCI Registry you wish to use:
```
$ fn update context registry <region-code>.ocir.io/<tenancy-namespace>/<ocir-repo-name>
```

## Login to your OCI Registry with Docker CLI
Note: region code may vary, we are using Ashburn region here (iad)
```
$ docker login iad.ocir.io
```
When prompted, enter your {tenancy-namespace}/{username} and your {ocir-auth-token}.
Note: If your tenancy is federated with Oracle Identity Cloud Services (IDCS), use this format:
{tenancy-namespace}/oracleidentitycloudservice/{username}

## Create Application in OCI console
### What is an Application 
Functions are grouped together in an spplication. The application is the main organizing structure for the functions.
### How to create
Login to the OCI console and on the Lefthand menu, select: Developer 
Services > Functions. Make sure to select the same region as the OCI 
Registry and select the compartment you specified earlier in the 
configured Fn context. You will then create the Application that your 
function will be deployed to.  Call it something like 'demoapp'. You will 
specify this Application when invoking the function. 

## Deploy your function
Deploying your function is the final step in setting up your function. 
Deploying creates a Docker image in the OCI Registry and makes the 
function available to the application. Run this command to deploy:
```
$ fn -v deploy --app demoapp
```
The -v flag is for -verbose. Running deploy is very similar to running
docker build command with a Dockerfile. Deploy dynamically generates a Dockerfile for your function,
builds a container, and then loads it for execution. Note: For some OCI 
users, the image will be created but the function will not because of 
tagging rules. If this occurs, you can create the function in the OCI 
console with the required tags and associate it with the image created by the deploy command.

## Invoke your function
Invoking is simply running the serverless function you created. To invoke, run this command:
```
$ fn invoke demoapp ocifndemo
```
In our case, 'demoapp' is the application and the function is 'ocidfndemo'
The final output in Terminal should look like this:
```
"It is Partly Cloudy. The temperature is 65\u00b0"
``` 








