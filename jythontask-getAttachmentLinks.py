attachmentList = "Attachment List\n"
for ph in release.phases:
  for tsk in ph.tasks:
    for atch in tsk.attachments:
      if atch.getFile().name  != "script_output.log":
        attachmentList += "%s : http://localhost:5516/export/attachments/%s-%s \n" % (atch.getFile().name, release.name, atch.name)

releaseVariables['attachmentList'] = attachmentList