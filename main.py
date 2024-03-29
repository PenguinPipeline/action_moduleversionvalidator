#!/usr/bin/env python3

import os
import json
import requests
from packaging.version import parse
import pprintpp

totalModulesReferenced = 0
totalModulesUsingLatestVersion = 0
totalModulesWithDependenciesAvailable = 0


statusVersionIsLatest = True
allVersionsAvailable = True

checkForLatest = os.environ.get('INPUT_CHECK-FOR-LATEST').upper() == 'TRUE'
checkForAvailable = os.environ.get('INPUT_CHECK-FOR-AVAILABLE').upper() == 'TRUE'
tfeToken = os.environ.get('INPUT_TFE-TOKEN')



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
    global allVersionsAvailable
    global totalModulesUsingLatestVersion
    global totalModulesWithDependenciesAvailable
    global totalModulesReferenced

    totalModulesReferenced += 1


    # Convert the version number to a numeric
    latestVersion = parse("0.0.0")
    
    currentVersionObject = parse(currentVersion)

    localStatusVerison = False
    # Find the latest version
    for version in listOfVersions:
        versionObject = parse(version)

        if  versionObject > latestVersion:
            latestVersion = versionObject
        
        if currentVersionObject == versionObject:
            localStatusVerison = True
            totalModulesWithDependenciesAvailable += 1


    if localStatusVerison == False:
        allVersionsAvailable = False

    # Check if we're referencing the latest version
    if currentVersionObject != latestVersion:
        statusVersionIsLatest = False
    else:
        totalModulesUsingLatestVersion += 1

    return {"isVersionAvailableInRegistry": localStatusVerison, "isUsingLatestVersion": statusVersionIsLatest}

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
    listOfVersions = fetchModuleRegistryVersions(x, tfeToken)

    # Generate a dictionary of status flags
    versionValidationStatuses = performVersionValidation(currentVersion, listOfVersions)
    
    newDict = {"currentVersion": currentVersion, "registryVersions": listOfVersions, "statusFlags": versionValidationStatuses}
    moduleReferences[x] = newDict

pprintpp.pprint("==== Summary ====")
pprintpp.pprint("Number of modules Referenced: " + str(totalModulesReferenced))
pprintpp.pprint("Number of modules Missing Dependencies: " + str(totalModulesReferenced - totalModulesWithDependenciesAvailable))
pprintpp.pprint("Number of modules not using latest version: " + str(totalModulesReferenced - totalModulesUsingLatestVersion))

pprintpp.pprint("")
pprintpp.pprint("==== Detailed Breakdown ====")
pprintpp.pprint(moduleReferences)

# Throw error if we're checking for availability and the module version isn't available
if checkForAvailable and allVersionsAvailable is False:
    exit(1)

# Throw error if we're checking for latest and the module version isn't the latest version
if checkForLatest and statusVersionIsLatest is False:
    exit(1)






