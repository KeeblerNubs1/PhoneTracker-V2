const apiUrl = document.querySelector("#api-url");
const status = document.querySelector("#status");
const devicesBody = document.querySelector("#devices");

function baseUrl() {
  const value = apiUrl.value.trim();
  if (!/^https?:\/\//.test(value)) throw new Error("API address must start with http:// or https://");
  return value.endsWith("/") ? value : `${value}/`;
}

async function request(endpoint, options) {
  return window.guardianApi.request(baseUrl(), endpoint, options);
}

function message(id, text, error = false) {
  const target = document.querySelector(id);
  target.textContent = text;
  target.classList.toggle("error", error);
}

function formatCoordinate(device) {
  return device.latitude == null || device.longitude == null ? "—" : `${Number(device.latitude).toFixed(5)}, ${Number(device.longitude).toFixed(5)}`;
}

function renderDevices(devices) {
  devicesBody.replaceChildren();
  document.querySelector("#device-count").textContent = `${devices.length} enrolled device${devices.length === 1 ? "" : "s"}`;
  if (!devices.length) {
    devicesBody.innerHTML = '<tr><td colspan="6" class="empty">No enrolled devices yet.</td></tr>';
    return;
  }
  for (const device of devices) {
    const row = document.createElement("tr");
    [device.device_id, device.name, device.platform, device.last_seen || "—", device.battery == null ? "—" : `${device.battery}%`, formatCoordinate(device)].forEach((value) => {
      const cell = document.createElement("td"); cell.textContent = value; row.append(cell);
    });
    devicesBody.append(row);
  }
}

async function refresh() {
  try { renderDevices(await request("devices")); status.textContent = "Connected"; status.classList.remove("offline"); }
  catch (error) { status.textContent = `Connection failed: ${error.message}`; status.classList.add("offline"); }
}

document.querySelector("#connect").addEventListener("click", refresh);
document.querySelector("#refresh").addEventListener("click", refresh);
document.querySelector("#enroll-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = new FormData(event.currentTarget);
  try { const result = await request("devices/enroll", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(form)) }); message("#enroll-message", `Enrolled. Save this token: ${result.token}`); event.currentTarget.reset(); await refresh(); }
  catch (error) { message("#enroll-message", error.message, true); }
});
document.querySelector("#location-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = Object.fromEntries(new FormData(event.currentTarget)); const { device_id, token, ...details } = form;
  for (const key of ["latitude", "longitude", "accuracy", "battery"]) if (details[key] !== "") details[key] = Number(details[key]); else delete details[key];
  if (details.timestamp) details.timestamp = new Date(details.timestamp).toISOString(); else delete details.timestamp;
  try { await request(`devices/${encodeURIComponent(device_id)}/location`, { method: "POST", headers: { "Content-Type": "application/json", "X-Device-Token": token }, body: JSON.stringify(details) }); message("#location-message", "Location report saved."); event.currentTarget.reset(); await refresh(); }
  catch (error) { message("#location-message", error.message, true); }
});
document.querySelector("#tower-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = Object.fromEntries(new FormData(event.currentTarget)); const { device_id, token, ...details } = form;
  for (const key of ["mobile_country_code", "mobile_network_code", "area_code", "cell_id", "signal_dbm", "latitude", "longitude", "accuracy"]) if (details[key] !== "") details[key] = Number(details[key]); else delete details[key];
  if (details.timestamp) details.timestamp = new Date(details.timestamp).toISOString(); else delete details.timestamp;
  try { await request(`devices/${encodeURIComponent(device_id)}/cell-towers`, { method: "POST", headers: { "Content-Type": "application/json", "X-Device-Token": token }, body: JSON.stringify(details) }); message("#tower-message", "Cell-tower observation saved."); event.currentTarget.reset(); await refresh(); }
  catch (error) { message("#tower-message", error.message, true); }
});
