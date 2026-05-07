const { contextBridge, ipcRenderer } = require('electron');

// Expose secure API to renderer process
contextBridge.exposeInMainWorld('bissi', {
  // Profile operations
  profile: {
    isFirst: () => ipcRenderer.invoke('profile:isFirst'),
    save: (firstName, lastName) => ipcRenderer.invoke('profile:save', firstName, lastName),
    load: () => ipcRenderer.invoke('profile:load')
  },
  
  // Navigation
  nav: {
    goToChat: () => ipcRenderer.invoke('nav:goToChat')
  },
  
  // Models and backend
  models: {
    list: () => ipcRenderer.invoke('models:list')
  },
  
  ollama: {
    models: () => ipcRenderer.invoke('ollama:models')
  }
});
