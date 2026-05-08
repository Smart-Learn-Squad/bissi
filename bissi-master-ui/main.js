const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const os = require('os');

// Keep a global reference of the window object
let mainWindow;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    frame: true,
    transparent: false,
    show: false,
    titleBarStyle: 'default'
  });

  // Check if profile exists and route accordingly
  checkProfileAndRoute();

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

async function checkProfileAndRoute() {
  try {
    const profilePath = path.join(os.homedir(), '.bissi', 'profile.json');
    await fs.access(profilePath);
    // Profile exists, load chat
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'chat.html'));
  } catch (error) {
    // Profile doesn't exist, load onboarding
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'onboarding.html'));
  }
}

// IPC handlers for profile operations
ipcMain.handle('profile:save', async (event, firstName, lastName) => {
  try {
    const bissiDir = path.join(os.homedir(), '.bissi');
    await fs.mkdir(bissiDir, { recursive: true });
    
    const profile = {
      first_name: firstName,
      last_name: lastName,
      created_at: new Date().toISOString(),
      language: 'fr'
    };
    
    const profilePath = path.join(bissiDir, 'profile.json');
    await fs.writeFile(profilePath, JSON.stringify(profile, null, 2));
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('profile:load', async () => {
  try {
    const profilePath = path.join(os.homedir(), '.bissi', 'profile.json');
    const data = await fs.readFile(profilePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return null;
  }
});

ipcMain.handle('profile:isFirst', async () => {
  try {
    const profilePath = path.join(os.homedir(), '.bissi', 'profile.json');
    await fs.access(profilePath);
    return false;
  } catch (error) {
    return true;
  }
});

// Navigation handler
ipcMain.handle('nav:goToChat', () => {
  if (mainWindow) {
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'chat.html'));
  }
});

// Model handlers
ipcMain.handle('models:list', async () => {
  try {
    const response = await fetch('http://localhost:8765/tools');
    if (!response.ok) throw new Error('Backend not available');
    
    const healthResponse = await fetch('http://localhost:8765/health');
    const healthData = healthResponse.ok ? await healthResponse.json() : null;
    
    return {
      available: true,
      activeModel: healthData?.model || null
    };
  } catch (error) {
    return {
      available: false,
      error: error.message
    };
  }
});

ipcMain.handle('ollama:models', async () => {
  try {
    const response = await fetch('http://localhost:11434/api/tags');
    if (!response.ok) throw new Error('Ollama not available');
    
    const data = await response.json();
    return {
      available: true,
      models: data.models || []
    };
  } catch (error) {
    return {
      available: false,
      error: error.message
    };
  }
});

// File chooser dialog
ipcMain.handle('file:choose', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Documents', extensions: ['docx', 'xlsx', 'pdf', 'py', 'txt', 'csv', 'json', 'md'] },
      { name: 'Tous les fichiers', extensions: ['*'] }
    ]
  });
  if (result.canceled || !result.filePaths.length) return null;
  return result.filePaths[0];
});

// File system handlers for canvas
const fsSync = require('fs');

ipcMain.handle('file:read', async (event, filePath) => {
  try {
    return fsSync.readFileSync(filePath, 'utf8');
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('file:readBuffer', async (event, filePath) => {
  try {
    const buffer = fsSync.readFileSync(filePath);
    return { data: Array.from(new Uint8Array(buffer)) };
  } catch (error) {
    return { error: error.message };
  }
});

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
