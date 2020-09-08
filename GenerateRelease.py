#
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS
# FOR A PARTICULAR PURPOSE. THIS CODE AND INFORMATION ARE NOT SUPPORTED BY XEBIALABS.
#

import sys, string, time
import com.xhaus.jyson.JysonCodec as json
from com.xebialabs.xlrelease.domain import Task
from com.xebialabs.deployit.plugin.api.reflect import Type
from java.text import SimpleDateFormat


def createManualTask(phaseId, taskTypeValue, title, propertyMap):
    parenttaskType = Type.valueOf(taskTypeValue)
    
    parentTask = parenttaskType.descriptor.newInstance("nonamerequired")
    parentTask.setTitle(title)
    sdf = SimpleDateFormat("yyyy-MM-dd hh:mm:ss")
    for item in propertyMap:
        if item.lower().find("date") > -1:
            if propertyMap[item] is not None and len(propertyMap[item]) != 0:
                parentTask.setProperty(item,sdf.parse(propertyMap[item])) 
        else:
            parentTask.setProperty(item,propertyMap[item]) 
    
    #parentTask.setStartDate(sdf.parse(startDate))
    taskApi.addTask(phaseId,parentTask)

def createAutomatedTask(phaseId,taskTypeValue,title,precondition, propertyMap):
    parenttaskType = Type.valueOf("xlrelease.CustomScriptTask")

    parentTask = parenttaskType.descriptor.newInstance("nonamerequired")
    parentTask.setTitle(title)
    
    childTaskType = Type.valueOf(taskTypeValue)
    childTask = childTaskType.descriptor.newInstance("nonamerequired")
    for item in propertyMap:
        childTask.setProperty(item,propertyMap[item])    
    parentTask.setPythonScript(childTask)
    parentTask.setPrecondition(precondition)
    
    taskApi.addTask(phaseId,parentTask)    


RECORD_CHECK_STATUS = 200

if servicenowServer is None:
    print "No server provided."
    sys.exit(1)

servicenowUrl = servicenowServer['url']
username = servicenowServer['username']
password = servicenowServer['password']

changeRecordTableName = servicenowServer['changeRecordTableName']
changeTaskTableName = servicenowServer['changeTaskTableName']
content = None
change_request_sysid = ""
credentials = CredentialsFallback(servicenowServer, username, password).getCredentials()

servicenowBaseTableURL = servicenowUrl + '/api/now/table/'
updateChangeTaskAPIURL = servicenowBaseTableURL + changeTaskTableName + '/'

# first finding changeRequest using changeRequest number to grab sysid
changeRequestAPIUrl = servicenowBaseTableURL + changeRecordTableName + '?number=' + changeRecordNumber
servicenowResponse = XLRequest(changeRequestAPIUrl, 'GET', content, credentials['username'], credentials['password'], 'application/json').send()


if servicenowResponse.status == RECORD_CHECK_STATUS:
    data = json.loads(servicenowResponse.read())
    change_request_sysid = data["result"][0]["sys_id"]
else:
    print "Failed to find change record in Service Now"
    servicenowResponse.errorDump()
    sys.exit(1)

# Use the service record for finding the change task list for that change record
changeTaskAPIUrl = servicenowBaseTableURL + changeTaskTableName + '?sysparm_query=change_request=' + change_request_sysid + '^ORDERBYnumber'
servicenowResponse = XLRequest(changeTaskAPIUrl, 'GET', content, credentials['username'], credentials['password'], 'application/json').send()


#Below preCond is deprecated. It is now being done through the extended step
preCond = "i = [ count for count,item in enumerate(phase.getTasks()) if task == item ]\n" + \
"task.getPythonScript().setProperty(\'body\',\'{state:3,work_notes:\\\'\' + phase.getTasks()[i[0]-1].comments[-1].getText() + \'\\\'}\')\n" + \
"taskApi.updateTask(task.id,task)\n" + \
"result = True"


if servicenowResponse.status == RECORD_CHECK_STATUS:
    data = json.loads(servicenowResponse.read())
    status = data["result"]
    
    for counter,item in enumerate(status):
    	# first look at the phase creation criteria field .. 'state' used for now
    	phaseName = str(item['state'])
    	existingPhaseList = phaseApi.searchPhasesByTitle(phaseName, release.id)
    	
        # Only adding newer Tasks to the release
        if counter+1 > int(baseCount):
        
            # Adding a phaseName
            if len(existingPhaseList) <= 0:
        		existingPhaseList.append(releaseApi.addPhase(release.id,phaseName))
            phaseId = existingPhaseList[0].id

            createAutomatedTask(phaseId,"webhook.JsonWebhook", "Start " + str(item['number']),None,{"URL":updateChangeTaskAPIURL + str(item['sys_id']), "method":"PUT", "body":"{state:1,work_notes:'Updated By XLRelease'}", "username": credentials['username'], "password":credentials['password']})
            createManualTask(phaseId,"xlrelease.Task", str(item['number']) + "-" +  str(item['short_description']), {'startDate':item['expected_start'],'endDate':item['work_end'],'description':'\''+ item['description'] + '\''})
            createAutomatedTask(phaseId,"servicenow.CompleteTaskJsonWebhook", "Complete " + str(item['number']),None,{"URL":updateChangeTaskAPIURL + str(item['sys_id']), "method":"PUT","body":"{state:3,work_notes:'Updated By XLRelease'}", "username": credentials['username'], "password":credentials['password']})

    if counter+1 > int(baseCount):
        createAutomatedTask(phaseId,"servicenow.GenerateRelease", "Update Plan From ServiceNow",None,{'baseCount':str(counter+1)})
    

else:
    print "Failed to check task in Service Now"
    servicenowResponse.errorDump()
    sys.exit(1)
