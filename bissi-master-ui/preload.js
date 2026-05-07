const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('bissi', {
  profile: {
    isFirst: () => ipcRenderer.invoke('profile:isFirst'),
    save: (firstName, lastName) => ipcRenderer.invoke('profile:save', firstName, lastName),
    load: () => ipcRenderer.invoke('profile:load')
  },
  nav: {
    goToChat: () => ipcRenderer.invoke('nav:goToChat')
  },
  models: {
    list: () => ipcRenderer.invoke('models:list')
  },
  ollama: {
    models: () => ipcRenderer.invoke('ollama:models')
  },
  file: {
    read: (filePath) => ipcRenderer.invoke('file:read', filePath),
    readBuffer: (filePath) => ipcRenderer.invoke('file:readBuffer', filePath)
  }
});
