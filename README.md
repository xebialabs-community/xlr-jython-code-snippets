# xlr-jython-code-snippets
XLR code snippets using python and jython API


### Configure reference to Certificates for access by Python Libraries in plugins
There are third party python libraries that often refer to a certificate using certifi for connecting to secured URLs. If the cert is self-signed, you might need to make it available to the python lib.
1. put the cert in a cert.pem file or append it to a cacerts.pem file
2. Store the file in a referenable location from XL Server
3. Create an environment variable inside run.sh/run.cmd referring to cert path.   
eg. ```export REQUESTS_CA_BUNDLE=$XLD_HOME/certs/cert.pem.  ```
4. Restart the server.

### Lookup all task types in XLR

```
from com.xebialabs.deployit.plugin.api.reflect import Type
from com.xebialabs.deployit.plugin.api.reflect.DescriptorRegistry import getDescriptorRegistry
taskDesc = Type.valueOf("xlrelease.Task")
registry = getDescriptorRegistry(taskDesc.getTypeSource())
print("%s\n"%registry)
descriptors = registry.getDescriptors()
tasks = [d.getType() for d in descriptors if d.isVirtual() == False and (d.isAssignableTo(Type.valueOf("xlrelease.Task")) or d.isAssignableTo(Type.valueOf("xlrelease.PythonScript")))]
print("tasks: %s\n" % tasks)
```


### Refer to passwords in xl-release-server.conf in jython
#### Setup 
In release-server.conf, provide this
```
my.password=somepassword
```

On restart of the server, this is encrypted (and will be something like
```
my.password={aes\:v0}vEWwVYoSXqKXW+1Zro5u4KwFiMfsQJ0TJBeTsmtXgv8\=
```

#### Refer to password in plugin/custom jython script (tested in XLR 9.5.2 )
```
from com.xebialabs.xlrelease.config import XlrConfig


#To retrieve the decrypted password:
myTemp = XlrConfig.getInstance().getRootConfig()
print myTemp.getString("my.password")
 
```


### Use custom python modules in XL Release
#### Sample Using git module.
1. Download the library code https://files.pythonhosted.org/packages/d2/e8/0bd80cc9e1422f5449d663479459c3c032ff7acaf6609a63324d23bde9ac/GitPython-3.0.5.tar.gz

2. untar/unzip and take out the actual module folder from it. In the above case, its the git folder.
3. Now go under `XLR_HOME/lib` folder
4. Create a new folder called `Lib` ( case sensitive )
5. Copy the git module folder under Lib. Will look like this `XLR_HOME/lib/Lib/git`
6. Find the jython standalone jar name by doing a file search `ls jython*`.  
7.  Now run this command to update the jython jar with the contents of the Lib folder 
` jar -uvf jython-standalone-2.7.1.patch2618.jar Lib`

if would give an output like this while it adds the git python module 

` adding: Lib/(in = 0) (out= 0)(stored 0%)  
adding: Lib/git/(in = 0) (out= 0)(stored 0%)   
adding: Lib/git/db.py(in = 1963) (out= 802)(deflated 59%)
adding: Lib/git/cmd.py(in = 42869) (out= 12482)(deflated 70%)
adding: Lib/git/config.py(in = 28415) (out= 8096)(deflated 71%)
adding: Lib/git/compat.py(in = 9436) (out= 3080)(deflated 67%)
adding: Lib/git/test/(in = 0) (out= 0)(stored 0%)
adding: Lib/git/test/test_stats.py(in = 971) (out= 412)(deflated 57%)`

8. Restart XLR and you should be able to use git module in jython script task.

The same can be done with XLD and then using it in plugins.

**Important**:  If you want to use a python library under a custom plugin script inside XLRelease, instead of copying to lib/Lib and bundling up,  you can bundle up the module inside the plugin jar at the root level.  If you are working under ext folder, then you may keep the module under there while using it in the custom scripts backing the custom tasks.
**Disclaimer** : Another important thing to keep in mind is that on upgrades, you will have to manually update the jython library in that version with these modules.


### Create a new Stage and add it to a new Environment
```
from com.xebialabs.xlrelease.domain.environments import EnvironmentStage, Environment
from com.xebialabs.xlrelease.api.v1.filter import EnvironmentStageFilters

# Create a new stage and create it
stage = EnvironmentStage()
stage.setTitle("MyStage")
environmentStageApi.create(stage)

# Create a new filter to find the stage we just created with its real ID

filter = EnvironmentStageFilters("MyStage")
stageList = environmentStageApi.search(filter)

if stageList:
    # Set the stage in the enviroment and create it
    envir = Environment()
    envir.setTitle("MyEnvironment")
    envir.setStage(stageList[0]._delegate)
    environmentApi.create(envir)

```


### Dynamically choose a target server for all tasks of that type in a release
```
# The variable servicenow_instance can be presented to the user as a listbox choice type during the start of release
# Then using a bootstrap jython task in the start of the release, User's selection can be dynamically applied to all service
# now tasks so they all point to the chosen server endpoing

servicenow_servers = configurationApi.searchByTypeAndTitle("servicenow.Server", releaseVariables['servicenow_instance'])
for p in release.phases:
    for t in p.tasks:
        if str(t.getTaskType()).split('.')[0] == 'servicenow':
            temp_task = taskApi.getTask(t.id)
            temp_task.pythonScript.setProperty("servicenowServer",servicenow_servers[0])
            taskApi.updateTask(temp_task.id, temp_task)
```

### Search for a release in Release Group

```
from com.xebialabs.xlrelease.domain.group import ReleaseGroup
from com.xebialabs.xlrelease.api.v1.forms import ReleaseGroupFilters
from com.xebialabs.xlrelease.api.v1.forms import ReleaseGroupOrderMode 
from com.xebialabs.xlrelease.domain.group import ReleaseGroupStatus
rgfilter = ReleaseGroupFilters()
rgfilter.withTitle(groupName)
rgfilter.statuses = [ ReleaseGroupStatus.FAILED, ReleaseGroupStatus.IN_PROGRESS, ReleaseGroupStatus.PAUSED,ReleaseGroupStatus.FAILING  ]
rg = releaseGroupApi.resource.searchGroups(rgfilter, 0, 10, ReleaseGroupOrderMode.RISK)
```


### Create a Release Group Dynamically and add the current release

```
from com.xebialabs.xlrelease.domain.group import ReleaseGroup
from com.xebialabs.xlrelease.api.v1.forms import ReleaseGroupFilters
from com.xebialabs.xlrelease.api.v1.forms import ReleaseGroupOrderMode 
from com.xebialabs.xlrelease.domain.group import ReleaseGroupStatus

from java.util import Calendar, Date
cal = Calendar.getInstance()
cal.setTime(Date())

r = ReleaseGroup()
r.title = "myReleaseGroup"
r.folderId = "Applications/FolderSamplesAndTutorials"
r.startDate = cal.getTime()
cal.add(Calendar.DAY_OF_WEEK, 7)
r.endDate = cal.getTime()
releaseGroupApi.resource.createGroup(r)

releaseGroupApi.resource.addMembersToGroup(r.id,[release.id])
```


### Messing about with attributes (or Facets as they are really known)

```
import com.xebialabs.xlrelease.api.v1.filter.ApplicationFilters as ApplicationFilters

def get_app_id_from_name(applicationName):
  """
  Given a string representing the name of an XL Release Application return the
  corresponding applicationId
  :param str applicationName - Name of the XLRelease application
  In all unhappy cases it will return an empty string -
  TODO: something better
  """
  if applicationName:
    appList = applicationApi.search(ApplicationFilters(applicationName, None))
    if appList:
      return appList[-1].id
    else:
      return ""
  else:
    return ""
    
    
# For the task in question (myTask in this example)   
if myTask.facets:
    #TODO: Loop through facets to find Deployment one!
    appId = get_app_id_from_name(component)
    if appId:
      myTask.facets[0].applicationId = appId
      myTask.facets[0].version = version
      
      
```
      
### Creating a task with Facets

![#f03c15](https://placehold.it/15/f03c15/000000?text=+) *Warning - uses currently undocumented and non-public Api (FacetsApi)*

```
import com.xebialabs.xlrelease.api.v1.filter.ApplicationFilters as ApplicationFilters
import com.xebialabs.xlrelease.api.v1.filter.EnvironmentFilters as EnvironmentFilters

def get_app_id_from_name(applicationName):
  if applicationName:
    appList = applicationApi.search(ApplicationFilters(applicationName, None))
    if appList:
      return appList[-1].id
    else:
      return ""
  else:
    return ""
    
def get_env_id_from_name(envName, stage):
  if envName:
    envList = environmentApi.search(EnvironmentFilters(envName, stage, None))
    if envList:
      return envList[-1].id
    else:
      return ""
  else:
    return ""

containerId = getCurrentTask().container.id
taskToAdd = taskApi.newTask("xlrelease.ScriptTask")
taskToAdd.title = "ScriptCreated"
taskToAdd.script = "import time \ntime.sleep(5)"
appId = get_app_id_from_name("Wish List")

if appId:
  deployFacet = facetApi.newFacet("udm.DeploymentTaskFacet")
  deployFacet.applicationId = appId
  deployFacet.version = "1.0.0"
  deployFacet.environmentId = get_env_id_from_name("DEV", "Development")
  deployFacet.targetId = taskToAdd.id
  print deployFacet.toString()
  taskfacets = list()
  taskfacets.append(deployFacet)
  taskToAdd.setFacets(taskfacets)
  
createdTask=taskApi.addTask(containerId, taskToAdd)
```

### Skip the current task (Uses OnFailureHandler (8.1+))

```
from com.xebialabs.xlrelease.domain.recover import TaskRecoverOp

task.setTaskFailureHandlerEnabled(True)
task.setTaskRecoverOp(TaskRecoverOp.SKIP_TASK)
taskApi.updateTask(task)
raise Exception("Jenkins job was not built.")
```

### Set the release title using release variables

```
#use the 'component' and 'version' release varible as title 
title = "{component}/{version}".format(**releaseVariables)
print(title)
release.title = title
releaseApi.updateRelease(release)
```

### Get previous task

```
def previousTask(task):
  index = 0
  for item in phase.tasks:
    if item.id == task.id:
      break
    index = index + 1
  return task.getPhase().tasks[index-1]
print task.title
print "previous task is: " + str(previousTask(task).title)
```

### Get Gated tasks before a task

```
def gatesBeforeTask(task):
  gatesList = []
  for item in phase.tasks:
    if str(item.getTaskType()) == "xlrelease.GateTask":
     gatesList.append(item)
    if item.id == task.id:
     break
  return gatesList

print "start gates " + str(phase.getStartGates())
for item in gatesBeforeTask(task):
  print item.title
```

### Find a task by title

```
def findTaskByTitle(title):
  list = []
  for item in phase.tasks:
    if item.title == title:
      list.append(item)
  return list
```
### Check/uncheck a gate condition via REST API

\# Sample call:  python gateupdate.py Release546450 UAT 'Gate 2' 'Gate 2 condition 1' 'true' 

```
import requests
import sys

releaseId = sys.argv[1]
phaseTitle = sys.argv[2]
gateTitle = sys.argv[3]
conditionTitle = sys.argv[4]
conditionChecked = sys.argv[5]

release = requests.get('http://admin:xlradmin@localhost:5516/releases/' + releaseId)
for phase in release.json()['phases']:
  if phase['title'] == phaseTitle:
    for task in phase['tasks']:
      if task['title'] == gateTitle:
        for condition in task['conditions']:
          if condition['title'] == conditionTitle:
            condition['checked'] = conditionChecked
            r = requests.put('http://admin:xlradmin@localhost:5516/gates/conditions/' + condition['id'], json=condition)
            print r.status_code	
```


### Fetch variables from another release

```
rvar = releaseApi.getVariables(releaseidvar)
for r in rvar: 
    print "key:%s , value:%s \n" % (r._delegate.key,r._delegate.value)
```
or

```
myRelease = getCurrentRelease()
for r in myRelease.variables: 
   print "key:%s , value:%s \n" % (r.key, r.value)

```

### Update automated task server entry

```
t = taskApi.searchTasksByTitle("buildjar","Build",release.id)[0]
jenkinslist = configurationApi.searchByTypeAndTitle("jenkins.Server",releaseVariables['jenkinsserver'])
t.pythonScript.jenkinsServer = jenkinslist[0]
taskApi.updateTask(t)
```

### Fetch URL for selected server in a automated task

```
t = taskApi.searchTasksByTitle("buildjar","Build",release.id)
jenkinsUrl = t[0].pythonScript.jenkinsServer.url
releaseVariables['jarurl'] = "%s/job/buildjar/%s/artifact/abc.jar" % (jenkinsUrl, releaseVariables['buildjarbn'])
```

### Create table/fancy markdown in a task description

```
a = [1,2,3,4,5,6]
out=  "|Heading \n |---\n"
for item in a:
    out= "{0}|{1}\n".format(out,item)
task.description = out
taskApi.updateTask(task)
```
#### Image
![images/tableintaskdescription.png](images/tableintaskdescription.png)



## Xlrelease add dynamic tags

```
release.tags.add('abc')
releaseApi.updateRelease(release)
```



## Print classpath 

```
from java.lang import ClassLoader
cl = ClassLoader.getSystemClassLoader()
paths = map(lambda url: url.getFile(), cl.getURLs())
print paths
```

## Add a folder

```
from com.xebialabs.xlrelease.domain.folder import Folder
newFolder = Folder()
newFolder.title="MyFolder"
folderApi.addFolder("Applications",newFolder)
```

## Copy a template

```
templates = folderApi.getTemplates("Applications")
# Pick the first template 
template = templates[0]
# Give it a new title
template.title = "new template"
templateApi.createTemplate(template)
```

## Generate a release pipeline dynamically with parallel group and tasks from a provided dataset

```
import json
teamProjectName = "MyProject"
buildDefinitionName = "mybuildDef"
datamap = '''[
	{
		"name": "libs",
		"entries": [
			{
				"name": "a-library",
				"skip": "false"
			},
			{
				"name": "b-library",
				"skip": "false"
			},
			{
				"name": "c-library",
				"skip": "true"
			}
		],
		"execution": "sequence"
	},
	{
		"name": "messages",
		"entries": [
			{
				"name": "a-messages",
				"skip": "false"
			},
			{
				"name": "b-messages",
				"skip": "true"
			},
			{
				"name": "c-messages",
				"skip": "false"
			}
		],
		"execution": "parallel"
	},
	{
		"name": "services",
		"entries": [
			{
				"name": "a-service",
				"skip": "false"
			},
			{
				"name": "b-service",
				"skip": "false"
			}
		],
		"execution": "parallel"
	}
]
'''
dataobj = json.loads(datamap)

for item in dataobj:
    phase = phaseApi.newPhase(item['name'])
    phase = phaseApi.addPhase(release.id, phase)
    if str(item['execution']) == "parallel":
        pgrouptask = taskApi.newTask("xlrelease.ParallelGroup")
        pgrouptask.title = "Parallel Run"
        phase = taskApi.addTask(phase.id, pgrouptask)
    for entry in item['entries']:
        task = taskApi.newTask("vsts.QueueBuild")
        task.title = entry['name']

        task.pythonScript.setProperty("teamProjectName", teamProjectName)
        task.pythonScript.setProperty("buildDefinitionName", buildDefinitionName)
        
        if entry['skip'] == "true":
            task.precondition = "True == False"
        taskApi.addTask(phase.id, task)
        
 ```

## Use a template deployment task of any type to generate multiple copies based on a map of component:versions

* Create a template with this script task
* Add a sequential/Parallel Group
* In group add your template deployment task with same name as templateTask varable below - (currently ScriptTask or any CustomScriptTask (e.g. jenkins) types
* Add precondition to your template task so it is always skipped (e.g. `result = False`)
* Add attributes if you want - component and version will be added to the Application (must exsist) and Version fields
* Remember to set run as user properties

```
import com.xebialabs.xlrelease.api.v1.filter.ApplicationFilters as ApplicationFilters

componentVersions={'Wish List':'2.0.1','Address Book':'2.1.3','Shopping Cart':'2.0.0'}
templateTask = "Deploy Me Lots"


# Get the template task - limitation here is if phases are named the same
taskToCopy = taskApi.searchTasksByTitle(templateTask, getCurrentPhase().title, getCurrentRelease().id)[-1]
#print taskToCopy.getType()

def get_app_id_from_name(applicationName):
  """
  Given a string representing the name of an XL Release Application return the
  corresponding applicationId
  :param str applicationName - Name of the XLRelease application
  In all unhappy cases it will return an empty string - 
  TODO: something better
  """
  if applicationName:
    appList = applicationApi.search(ApplicationFilters(applicationName, None))
    if appList:
      return appList[-1].id
    else:
      return ""
  else:
    return ""

def multi_replace(string, replacements, ignore_case=False):
    """
    Given a string and a dict, replaces occurrences of the dict keys found in the 
    string, with their corresponding values. The replacements will occur in "one pass", 
    i.e. there should be no clashes.
    :param str string: string to perform replacements on
    :param dict replacements: replacement dictionary {str_to_find: str_to_replace_with}
    :param bool ignore_case: whether to ignore case when looking for matches
    :rtype: str the replaced string
    """
    if ignore_case:
        replacements = dict((pair[0].lower(), pair[1]) for pair in sorted(replacements.iteritems()))
    rep_sorted = sorted(replacements, key=lambda s: (len(s), s), reverse=True)
    rep_escaped = [re.escape(replacement) for replacement in rep_sorted]
    pattern = re.compile("|".join(rep_escaped), re.I if ignore_case else 0)
    return pattern.sub(lambda match: replacements[match.group(0).lower() if ignore_case else match.group(0)], string)

# For all the entries in the component version map      
for component,version in componentVersions.iteritems():
  # Define replacements for this iteration
  replacements = {'{{component}}':component,'{{version}}':version}

  if "xlrelease.ScriptTask" in str(taskToCopy.getType()):
    taskToCopy.script = multi_replace(taskToCopy.script,replacements)

  elif "xlrelease.CustomScriptTask" in str(taskToCopy.getType()):
    for property in taskToCopy.pythonScript.getInputProperties():
      propertyName = str(property).split('.')[-1]
      propertyValue = taskToCopy.pythonScript.getProperty(propertyName)

      if type(propertyValue) is unicode:
        print "Replacing property`%s` it was [`%s`] \n" % (propertyName,propertyValue)
        taskToCopy.pythonScript.setProperty(propertyName,multi_replace(propertyValue, replacements))
  else:
    #TODO: Investigate other task types
    print "Unsupported task to copy"
    exit(1)  

  taskToCopy.title = "Deploying %s at version %s" % (component, version)
  taskToCopy.precondition = ""
  
  if taskToCopy.facets:
    #TODO: Loop through facets to find Deployment one!
    appId = get_app_id_from_name(component)
    if appId:
      taskToCopy.facets[0].applicationId = appId
      taskToCopy.facets[0].version = version
    else:
      taskToCopy.precondition="print 'No valid AppName for attributes'\nexit(1)"
  
  createdTask = taskApi.addTask(taskToCopy.container.id, taskToCopy)
  
  ```
  

## Add a Custom task (MyCustomTask.TestMapOutPut) in curent running Release and set a Key-Value (dicoPackageMap) in output property (MapOut)

```
curRelease = getCurrentRelease()
curPhase = getCurrentPhase().title
task = taskApi.newTask("MyCustomTask.TestMapOutPut")
task.title = "ScriptCreated"
task.variableMapping = {"pythonScript.MapOut" : "$""{dicoPackageMap}"}
createdTask=taskApi.addTask(getCurrentPhase().id, task)
taskApi.assignTask(createdTask.id,"Admin")

```

## Adding Date, working with Date

```
from java.util import Calendar, Date
cal = Calendar.getInstance()
cal.setTime(Date())
cal.add(Calendar.DAY_OF_WEEK, 7)
print cal.getTime()

```

## Add a Task as the last Task in phase by copying a previous Task

```
t = getTasksByTitle("t1", "New Phase")[0]
newtask = taskApi.copyTask(t.id, phase.id, len(phase.getTasks()))


```

## Scheduling a task dynamically

```
from java.util import Calendar, Date
cal = Calendar.getInstance()
cal.setTime(getCurrentTask().startDate)
cal.add(Calendar.DAY_OF_WEEK, 2)
# getting a task that is ahead of current task in the flow
t = getTasksByTitle("t1", "New Phase")[0]
t.setScheduledStartDate(cal.getTime()) 
taskApi.updateTask(t)

```

## Create a Self Scheduling Task Block - Style 1
This example makes use of a Sequential Group. You can have any number of tasks within the sequential group but the last task should be a Jython Script/Custom Task with the following Script.  The script will replicate its parent Sequential Group and then reschedule the newly cloned group for a certain datetime

```
parenttask = getCurrentTask().container
# find the sequential group child
sequentialGroupId = None
activetask = None
# Iterating on the children to find SequentialGroup ID and the last active manual task ID
for child in parenttask.getChildren():
if str(child.type).lower() == "xlrelease.SequentialGroup".lower():
    sequentialGroupId = child.id
if str(child.type).lower() == "xlrelease.Task".lower() and str(child.status).lower() == "IN_PROGRESS".lower():
    activetask = child.id

# Setting up a notification task
notfication = taskApi.newTask("xlrelease.NotificationTask")
notfication.subject = "Sending Notification at %s" % datetime.today()
notfication.addresses = Set(["a@gmail.com", "b@gmail.com"])
notfication.body = "hi Hello"
taskApi.addTask(sequentialGroupId, notfication)

# Setting up a manual task
manualtask = taskApi.newTask("xlrelease.Task")
manualtask.title = "Waiting for Activity on %s" % ( datetime.today() + timedelta(days=1) )
taskApi.addTask(sequentialGroupId, manualtask)

# assigning it to the admin user to mark it complete in the next step
taskApi.assignTask(activetask,"admin")
taskApi.completeTask(activetask,Comment())

```

## Create a Self Scheduling Task Block - Style 2 ( Better )

```
from java.util import Calendar, Date
import time

# Get the parent block for current script task
parenttask = getCurrentTask().container

# Use calendar to increment the time
cal = Calendar.getInstance()
cal.setTime(parenttask.startDate)
cal.add(Calendar.DAY_OF_WEEK, 2)

# Create a new task from that parenttask as the next task 
newtask = taskApi.copyTask(parenttask.id, phase.id, len(phase.getTasks()))

# Set the newtask to the new time and title
newtask.setScheduledStartDate(cal.getTime()) 
newtask.title = parenttask.title

# Update the new task
taskApi.updateTask(newtask)

```

## Create/Populate a List Variable using Jython
There are different interpreted types for different type of variables within the api. Usual way of knowing the right name is eg.
If variable type is **StringVariable**, then xlr type is **xlrelease.StringVariable**

Some variable types are 
* StringVariable
* ListStringVariable
* MapStringStringVariable
* PasswordStringVariable
* SetStringVariable

```
from com.xebialabs.xlrelease.api.v1.forms import Variable  
mylist = [1,2,3,4]
listvar = Variable()
listvar.value = mylist
listvar.key = "mylistvar"
listvar.type = "xlrelease.ListStringVariable"
releaseApi.createVariable(release.id,listvar )

```

## And Listboxes?
These are slightly different, the variable itself can be a **StringVariable** type but the options are provided using a provider.  This is not really documented but the following code snippet works for this use-case

```
from com.xebialabs.xlrelease.api.v1.forms import Variable  
from com.xebialabs.xlrelease.domain.variables import ListOfStringValueProviderConfiguration

mylist = ["1","2","3","4"]
listvar = Variable()
listvar.value = "1"
listvar.key = "mylistvar"
listvar.type = "xlrelease.StringVariable"


provider1 = ListOfStringValueProviderConfiguration()
provider1.id = "myvariableProvider"
provider1.values = mylist
listvar.valueProvider = provider1
releaseApi.createVariable(release.id,listvar )
```

### Update Owner of a new Release

```
c = CreateRelease()
c.setReleaseTitle('Test Release')
# Create a new release using template ID
r = templateApi.create('Releaseedf803f0dfc145189d8d38714679e075', c)
# Providing new owner
r.owner = 'tester1'
releaseApi.updateRelease(r)
```

### Update a variable in another release

```
releasetitle = "test1"
varkey = "local_ip"
releases = releaseApi.searchReleasesByTitle(releasetitle)
releaseidvar = releases[0].id
rvar = releaseApi.getVariables(releaseidvar)
vartoupdate = [ item for item in rvar if item.key == varkey ] [0]
vartoupdate.value = "newvalue"
releaseApi.updateVariable(vartoupdate)
```

### Generate a markdown table with phase/task/task status into a variable for using in email

```
out = "|Phase|Task|Status|\n|---|---|---|\n"
for ph in release.phases:
    if str(ph.status) != "PLANNED":
        for tsk in phase.tasks:
            out= "{0}|{1}|{2}|{3}\n".format(out,ph.title,tsk.title,tsk.status)
releaseVariables["emailcontent"] = out
```


### Capture a map/dict with key values and print it as a markdown table

```
out="|Ticket ID|Description|\n|---|---|\n"
for key, value in releaseVariables["issueList"].iteritems():
    out= "{0}|{1}|{2}\n".format(out,key,value)

releaseVariables["printedTable"] = out
```

### Custom task to Add a manual task just after the current running one
ie, how to find task position and add a new one just after it
```
-- synthetic.xml

<type type="dev.addManualAfter"  extends="xlrelease.PythonScript">
	<property name="scriptLocation" default="dev/addManualAfter.py" hidden="true" />
	<property name="taskColor" hidden="true" default="#009CDB"/>
</type>

-- dev/addManualAfter.py

def addManual(createTaskName):
	a = getMyPositionAndContainer(getCurrentTask(),getCurrentPhase())
	mytaskPos = a[0]
	mycontainer = a[1]
	taskFound = a[2]
	if taskFound:
		task = taskApi.newTask("xlrelease.Task")
		task.title = str(createTaskName)
		phaseApi.addTask(mycontainer.id,task,mytaskPos+1)
	else:
		raise Exception("**Exception: Task [{0}] not found in [{1}]**".format(getCurrentTask().title,getCurrentPhase().title))


def getMyPositionAndContainer(mytask,mycontainer):
	isfound = False
	i = 0
	for item in mycontainer.tasks:
		#print "[%s/%s]" %(str(item.type),item.title)
		if str(item.type) == "xlrelease.SequentialGroup":
			res = getMyPositionAndContainer(mytask,item)
			i = res[0]
			mycontainer = res[1]
			isfound = res[2]
		else:
			if item.id == mytask.id:
				isfound = True
				break
		if isfound == True:
			break
		
		i = i + 1

	return [i,mycontainer,isfound]
	
addManual("AutoCreated")
```

### Dynamically Generate Deployment Task based on json Data
```
import json
teamProjectName = "MyProject"
buildDefinitionName = "mybuildDef"
datamap = '''[
	{
		"name": "libs",
		"entries": [
			{
				"name": "a-library",
				"skip": "false"
			},
			{
				"name": "b-library",
				"skip": "false"
			},
			{
				"name": "c-library",
				"skip": "true"
			}
		],
		"execution": "sequence"
	},
	{
		"name": "messages",
		"entries": [
			{
				"name": "a-messages",
				"skip": "false"
			},
			{
				"name": "b-messages",
				"skip": "true"
			},
			{
				"name": "c-messages",
				"skip": "false"
			}
		],
		"execution": "parallel"
	},
	{
		"name": "services",
		"entries": [
			{
				"name": "a-service",
				"skip": "false"
			},
			{
				"name": "b-service",
				"skip": "false"
			}
		],
		"execution": "parallel"
	}
]
'''
dataobj = json.loads(datamap)

for item in dataobj:
    phase = phaseApi.newPhase(item['name'])
    phase = phaseApi.addPhase(release.id, phase)
    if str(item['execution']) == "parallel":
        pgrouptask = taskApi.newTask("xlrelease.ParallelGroup")
        pgrouptask.title = "Parallel Run"
        phase = taskApi.addTask(phase.id, pgrouptask)
    for entry in item['entries']:
        task = taskApi.newTask("xldeploy.Deploy")
        task.title = entry['name']

        task.pythonScript.setProperty("deploymentEnvironment", entry['name'])
        task.pythonScript.setProperty("deploymentPackage", "app-%s" % entry['name'])
        
        if entry['skip'] == "true":
            task.precondition = "True == False"
        taskApi.addTask(phase.id, task)
```

### Dynamically update the Variable Value for a Create Release Task in a release

```
for t in phase.tasks:
    if str(t.getTaskType()).split('.')[1] == 'CreateReleaseTask':
        for template_var in t.templateVariables:
            if template_var.key == 'dpackage':
                template_var.value = 'oclc'
                taskApi.updateTask(t.id, t)
```

### Get a list of links for Releases or Templates having a specific task type:
(code valid for un custom task with a "TaskType" string property)
```

from com.xebialabs.deployit.plugin.api.reflect import Type
from com.xebialabs.deployit.plugin.api.reflect.DescriptorRegistry import getDescriptorRegistry
taskDesc = Type.valueOf("xlrelease.Task")
registry = getDescriptorRegistry(taskDesc.getTypeSource())
descriptors = registry.getDescriptors()
tasks = [d.getType() for d in descriptors if d.isVirtual() == False and (d.isAssignableTo(Type.valueOf("xlrelease.Task")) or d.isAssignableTo(Type.valueOf("xlrelease.PythonScript")))]
print("tasks: %s\n" % tasks)


TaskType="XlrTasks.TaskType"


#Returns the list of planned or active releases that are visible to the current user
print "**Running or planned visible releases - Task type [%s]**"%(TaskType)
page=0
allRunningReleases=releaseApi.getReleases(page,100,1)
while len(allRunningReleases) > 0:
	for r in allRunningReleases:
		cnt=0
		for p in r.phases:
			for t in p.tasks:
				if str(t.getTaskType()) == TaskType:
					cnt=cnt+1
		if cnt>0:
			print ("%s : %s")%(r.url,cnt)
	page=page+1
	allRunningReleases=releaseApi.getReleases(page,100,1)


#Returns the list of templates that are visible to the current user.
print ""
print "**Visible templates - Task type [%s]**"%(TaskType)
page=0
allTemplates=templateApi.getTemplates("",[],page,100,1)
while len(allTemplates) > 0:
	for r in allTemplates:
		cnt=0
		for p in r.phases:
			for t in p.tasks:
				if str(t.getTaskType()) == TaskType:
					cnt=cnt+1
		if cnt>0:
			print ("%s : %s")%(r.url,cnt)
	page=page+1
	allTemplates=templateApi.getTemplates("",[],page,100,1)


```
