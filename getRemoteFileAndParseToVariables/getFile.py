import json

httpConnection = {
   'url': "http://www.example.com"
}

HTTP_SUCCESS = [200, 201, 202, 203, 204, 205, 206, 207, 208]

httpRequest = HttpRequest(httpConnection)
response = httpRequest.get("/xlr-inputs.json", contentType='application/json')
if response.getStatus() not in HTTP_SUCCESS:
    print(" ERROR %s" % response.getStatus())

data = json.loads(response.getResponse())
releaseVariables['jsonString'] = data

for rec in data:
    print("Project Name : %s" % rec['projectName'])
    releaseVariables['projectName'] = rec['projectName']
    releaseVariables['buildDefinitionName'] = rec['buildDefinitionName']
    releaseVariables['releaseDefinitionName'] = rec['releaseDefinitionName']
    releaseVariables['azBoards']['taskNumber'] = rec['azBoards']['taskNumber']
    releaseVariables['azBoards']['pbiNumber'] = rec['azBoards']['pbiNumber']
