#!/usr/bin/env python3

import os
import json
import requests
from packaging.version import parse
import pprintpp

statusVersionIsLatest = True
statusVersionAvailable = False

checkForLatest = os.environ.get('INPUT_check-for-latest')
checkForAvailable = os.environ.get('INPUT_check-for-available')

pprintpp.pprint("Check for latest: ")
pprintpp.pprint(checkForLatest)

pprintpp.pprint("Check for available: ")
pprintpp.pprint(checkForAvailable)

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

    # Track the global status here
    global statusVersionIsLatest
    global statusVersionAvailable

    # Check if referenced version is available
    if currentVersion in listOfVersions:
        statusVersionAvailable = True

    # Convert the version number to a numeric
    latestVersion = parse("0.0.0")

    if checkForLatest:

        # Find the latest version
        for version in listOfVersions:
            if parse(version) > latestVersion:
                latestVersion = parse(version)
    
        # Check if we're referencing the latest version
        if parse(currentVersion) != latestVersion:
            statusVersionIsLatest = False

    return {"isVersionAvailableInRegistry": statusVersionAvailable, "isUsingLatestVersion": statusVersionIsLatest}

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

# Throw error if we're checking for availability and the module version isn't available
if checkForAvailable and statusVersionAvailable is False:
    exit(1)

# Throw error if we're checking for latest and the module version isn't the latest version
if checkForLatest and statusVersionIsLatest is False:
    exit(1)






