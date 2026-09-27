const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("guardianApi", {
  request: (baseUrl, endpoint, options) =>
    ipcRenderer.invoke("api-request", { baseUrl, endpoint, options })
});
