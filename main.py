#!/usr/bin/env python

import os
import json
import requests
from packaging.version import parse
import pprintpp


# read module path
# query module on TFE
# Check if: Current version is available[Fail if not available] Current version is latest [Warn of all modules that are using old version]

def extractModulesFromFile():

    moduleVersionDict = {}
    with open('temp.json') as f:
        data = json.load(f)

        moduleCalls = data["module_calls"]

        for x in moduleCalls:
            # moduleVersion = "{source} --> {version}".format(source = moduleReferences[x]["source"], version = moduleReferences[x]["version"])
            # print(moduleVersion)
            moduleVersionDict[moduleCalls[x]["source"]] = moduleCalls[x]["version"]

        return moduleVersionDict

def fetchModuleRegistryVersions(path, tfeBearerToken):
    # Note: You need the discovery URL
    # https://tfe.pixelize.ca/api/registry/v1/modules/rockhopper/lob-adls/azurerm/versions
    baseurl = "https://tfe.pixelize.ca/api/registry/v1/modules"
    versionsUrlTemplate = "{baseurl}/{organization}/{moduleName}/{provider}/versions"
    bearerToken = "Bearer " + tfeBearerToken
    headers = {'Authorization': bearerToken}
    
    # Split the path up so we can retrieve the components required to generate the discovery URL
    urlPathComponents = path.rsplit('/')
    provider = urlPathComponents[len(urlPathComponents)-1]
    moduleName = urlPathComponents[len(urlPathComponents)-2]
    org = urlPathComponents[len(urlPathComponents)-3]

    # Construct the module versions discovery URL
    versionUrl = versionsUrlTemplate.format(baseurl = baseurl, organization = org, moduleName = moduleName, provider = provider)
    # Fetch the version information

    response = requests.get(versionUrl, headers=headers)
    data = response.json()

    listOfVersions = data["modules"][0]["versions"]
    versionNumbers = []
    for versionblock in listOfVersions:
        versionNumbers.append(versionblock["version"])
    
    return versionNumbers
    

def performVersionValidation(currentVersion, listOfVersions):


    statusVersionAvailable = False
    statusVersionIsLatest = False
    # Check if referenced version is available
    if currentVersion in listOfVersions:
        versionAvailable = True

    # Convert the version number to a numeric
    latestVersion = parse("0.0.0")

    for version in listOfVersions:
        if parse(version) > latestVersion:
            latestVersion = parse(version)
    
    if parse(currentVersion) == latestVersion:
        statusVersionIsLatest = True

    return {"isVersionAvailableInRegistry": versionAvailable, "isUsingLatestVersion": statusVersionIsLatest}

def generateModuleGraph(folder):
    os.system('/clitools/terraform-config-inspect --json {folder} > temp.json'.format(folder=folder))

# Generate the module graph
graph = generateModuleGraph(os.environ.get('GITHUB_WORKSPACE'))

# Create a dictionary of the module versions
moduleReferences = extractModulesFromFile()

for x in moduleReferences:
    #  Grab the current version
    currentVersion = moduleReferences[x]

    # Grab a list of available version
    listOfVersions = fetchModuleRegistryVersions(x, "w4g1zT3IuAJmwQ.atlasv1.p23J7UXOScgLehwQHJWdg1veybUBbJ2WLiZB59gmLR0HByoOqlHcQlfb056fCq0Laik")

    # Generate a dictionary of status flags
    versionValidationStatuses = performVersionValidation(currentVersion, listOfVersions)
    
    newDict = {"currentVersion": currentVersion, "registryVersions": listOfVersions, "statusFlags": versionValidationStatuses}
    moduleReferences[x] = newDict

pprintpp.pprint(moduleReferences)






