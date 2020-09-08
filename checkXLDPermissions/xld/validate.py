import httplib
import base64
import json
import xml.etree.ElementTree as ET
from xlrelease.HttpRequest import HttpRequest

def getXLRVersion():
    http_request = HttpRequest(xlrServer,"","")
    response = http_request.get("/server/info", contentType="application/xml")
    tree = ET.fromstring(response.getResponse())
    return tree.find("version").text
def is610andAbove():
    version = getXLRVersion()
    return version == '6.1.0' or version > '6.1.0'

def fetchConfigurations():
    http_request = HttpRequest(xlrServer,"","")
    response = http_request.get("/deployit/servers", contentType="application/json")
    return json.loads(response.getResponse())
def findServerData(serverReference, data):
    subset = [ item for item in data if item["id"] == serverReference ]
    return subset
def getProperty(task, is610andAbove, oldprop, newprop=None,isPassword=False):
    if newprop == None:
        newprop = oldprop
    if is610andAbove:
        evaluatedprop = eval("task.pythonScript.getProperty('" + newprop + "')")
    else:
        evaluatedprop = eval("task." + oldprop)
    if isPassword:
        return getRealPasswordValue(evaluatedprop)
    else:
        return getRealValue(evaluatedprop)
def getRealValue(value):
      if value != None and value != "" and isinstance(value,unicode) and value.find("$") >-1 :
        return release.variableValues[str(value)]
      return value
def getRealPasswordValue(value):
      if value != None and value != "" and isinstance(value,unicode) and value.find("$") >-1 :
        return release.passwordVariableValues[str(value)]
      return value
def  hasPermission(task, is610andAbove, configs=None):
      de = getProperty(t, is610andAbove, "environment", "deploymentEnvironment")
      if de != None:
        u =  getProperty(t, is610andAbove, "username")
        p =  getProperty(t, is610andAbove, "password", isPassword=True)
        dp = getProperty(t, is610andAbove, "deploymentPackage")
        if is610andAbove:
          s = getProperty(t, is610andAbove, "server")
          if u == None or u == "": 
            u = s.username
          if p == None  or p == "":
            p = s.password
          url = s.url
        else:
          s = findServerData(getProperty(t, is610andAbove, "server"), configs)[0]
          if u == None or u == "": 
            u = s["username"]
          if p == None  or p == "":
            p = s["password"]
            p ="admin"
          url = s["url"]
        http_request = HttpRequest({"url":url, "username":str(u),"password":str(p)},"","")
        response = http_request.get("/deployit/security/check/deploy%23initial/Environments/"+ de, contentType="application/xml")
        if response.status == 200:
          res_text = response.getResponse()
          if res_text.find("false") > -1:
            return False
          else:
            return True
        else:
          return False    
      else :
        return False

finalState = True
is610andAbove = is610andAbove()
configs = None
print "Phase Name|XL Deploy Task Title| Environment | Creds can Deploy (Y/N)"
print "---|---|---|---"
if not is610andAbove:
  configs = fetchConfigurations()
for p in release.phases:
  for t in p.tasks:
    if str(t.taskType) == "xlrelease.DeployitTask" or str(t.taskType) == "xldeploy.Deploy":
      status = hasPermission(t, is610andAbove, configs)
      print "%s|%s|%s|%s" % (p.title,t.title ,getProperty(t, is610andAbove, "environment", "deploymentEnvironment"), status)
      finalState = finalState and status
if finalState == False:
  raise ValueError("Some Credentials need to be corrected")