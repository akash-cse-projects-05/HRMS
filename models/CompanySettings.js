const mongoose = require('mongoose');
const createTenantModelProxy = require('../utils/tenantModel');

const companySettingsSchema = new mongoose.Schema({
  // Company Profile & Branding
  companyName: {
    type: String,
    default: 'HRMS Company'
  },
  tagline: {
    type: String,
    default: ''
  },
  contactEmail: {
    type: String,
    default: ''
  },
  contactPhone: {
    type: String,
    default: ''
  },
  website: {
    type: String,
    default: ''
  },
  logoUrl: {
    type: String,
    default: '' // Can be data URI base64 or static file path
  },

  // Registered Office Address
  address: {
    type: String,
    default: ''
  },
  city: {
    type: String,
    default: ''
  },
  state: {
    type: String,
    default: ''
  },
  pincode: {
    type: String,
    default: ''
  },
  country: {
    type: String,
    default: 'India'
  },

  // Statutory & Tax IDs
  cin: {
    type: String,
    default: ''
  },
  panNumber: {
    type: String,
    default: ''
  },
  gstNumber: {
    type: String,
    default: ''
  },

  // Geofenced Office Location (for attendance)
  officeLat: {
    type: Number,
    default: 19.0597397
  },
  officeLng: {
    type: Number,
    default: 73.1189947
  },
  officeRadius: {
    type: Number,
    default: 200 // meters
  },
  officeLocationName: {
    type: String,
    default: 'Headquarters'
  },
  geofenceEnforced: {
    type: Boolean,
    default: false
  },

  // Payroll & Payslip Configuration Defaults
  currencySymbol: {
    type: String,
    default: '₹'
  },
  pfPercentage: {
    type: Number,
    default: 0 // e.g. 12%
  },
  ptAmount: {
    type: Number,
    default: 0 // e.g. 200
  },
  tdsDefaultPercent: {
    type: Number,
    default: 0
  },
  payslipNote: {
    type: String,
    default: 'This is a computer generated salary statement and does not require a physical signature.'
  },
  signatoryName: {
    type: String,
    default: 'Authorized Signatory'
  },
  signatoryDesignation: {
    type: String,
    default: 'HR Operations'
  },

  updatedAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = createTenantModelProxy('CompanySettings', companySettingsSchema);
