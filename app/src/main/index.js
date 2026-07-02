import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { spawn } from 'child_process'
import { existsSync } from 'fs'
import { writeFile } from 'fs/promises'
import readline from 'readline'

let pythonProcess = null
let mainWindow = null

function getAgentDir() {
  return app.isPackaged
    ? join(process.resourcesPath, 'agent')
    : join(__dirname, '../../../agent')
}

function spawnPython() {
  const agentDir = getAgentDir()
  const venvPython = join(agentDir, '.venv/bin/python')
  const pythonBin = existsSync(venvPython) ? venvPython : 'python3'

  pythonProcess = spawn(pythonBin, [join(agentDir, 'main.py')], {
    cwd: agentDir,
  })

  const rl = readline.createInterface({ input: pythonProcess.stdout })
  rl.on('line', (line) => {
    try {
      const event = JSON.parse(line)
      mainWindow?.webContents.send('agent:event', event)
    } catch {
      // ignore non-JSON lines (e.g. LangChain debug output)
    }
  })

  pythonProcess.stderr.on('data', (data) => {
    console.error('[python]', data.toString().trim())
  })

  pythonProcess.on('exit', (code) => {
    console.log('[python] exited with code', code)
    pythonProcess = null
  })
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
    },
  })

  if (!app.isPackaged) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  createWindow()
  spawnPython()
})

ipcMain.on('agent:query', (_, request) => {
  if (!pythonProcess) {
    mainWindow?.webContents.send('agent:event', {
      type: 'error',
      message: 'Python process is not running',
    })
    return
  }
  pythonProcess.stdin.write(JSON.stringify(request) + '\n')
})

ipcMain.handle('report:export-pdf', async (_, defaultName) => {
  if (!mainWindow) return { ok: false, error: 'No window' }

  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
    title: 'Save report as PDF',
    defaultPath: defaultName || 'research-report.pdf',
    filters: [{ name: 'PDF', extensions: ['pdf'] }],
  })
  if (canceled || !filePath) return { ok: false, canceled: true }

  try {
    const pdf = await mainWindow.webContents.printToPDF({
      printBackground: true,
      pageSize: 'A4',
      margins: { marginType: 'custom', top: 0.6, bottom: 0.6, left: 0.6, right: 0.6 },
    })
    await writeFile(filePath, pdf)
    return { ok: true, path: filePath }
  } catch (e) {
    return { ok: false, error: String(e) }
  }
})

app.on('window-all-closed', () => {
  pythonProcess?.kill()
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
