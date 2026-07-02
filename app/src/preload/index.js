import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('agent', {
  query: (request) => ipcRenderer.send('agent:query', request),
  onEvent: (callback) => ipcRenderer.on('agent:event', (_, event) => callback(event)),
  offEvent: (callback) => ipcRenderer.removeListener('agent:event', callback),
  exportPdf: (defaultName) => ipcRenderer.invoke('report:export-pdf', defaultName),
})
