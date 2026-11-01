const mongoose = require('mongoose');
const createTenantModelProxy = require("../utils/tenantModel");

const notificationSchema = new mongoose.Schema({
  title: String,
  message: String,
  date: { type: Date, default: Date.now },
  employeeId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "Employee",
    default: null // null indicates broadcast/all-company notification; otherwise targeted to specific employee
  }
});

module.exports = createTenantModelProxy('Notification', notificationSchema);


