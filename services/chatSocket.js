// HRMS/services/chatSocket.js
// Presence and live chat event distributor (with SSE & HTTP Polling support)

const activeUsers = new Map(); // employeeId -> { lastSeen: Date, status: "AVAILABLE" | "FIELD" | "LEAVE" | "OFF_DUTY" }

function updateUserPresence(employeeId, status = "AVAILABLE") {
  if (!employeeId) return;
  activeUsers.set(String(employeeId), {
    lastSeen: new Date(),
    status
  });
}

function getUserPresence(employeeId) {
  const user = activeUsers.get(String(employeeId));
  if (!user) return { status: "OFF_DUTY", online: false };

  // If lastSeen was within last 5 minutes, consider online
  const isOnline = (new Date() - new Date(user.lastSeen)) < (5 * 60 * 1000);
  return {
    status: isOnline ? user.status : "OFF_DUTY",
    online: isOnline,
    lastSeen: user.lastSeen
  };
}

function getAllOnlineUsers() {
  const now = new Date();
  const onlineList = [];
  for (const [empId, data] of activeUsers.entries()) {
    if ((now - new Date(data.lastSeen)) < (5 * 60 * 1000)) {
      onlineList.push({ employeeId: empId, ...data });
    }
  }
  return onlineList;
}

module.exports = {
  updateUserPresence,
  getUserPresence,
  getAllOnlineUsers
};
