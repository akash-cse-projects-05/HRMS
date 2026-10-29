// HRMS/services/salaryEngine.js
// Statutory Indian payroll & CTC simulator engine

function calculateCTCBreakdown(annualCTC, basicPercent = 50, hraPercentOfBasic = 50) {
  const ctc = Number(annualCTC) || 0;
  const monthlyCTC = Math.round((ctc / 12) * 100) / 100;

  // Basic (e.g. 50% of Annual CTC)
  const basicAnnual = Math.round(ctc * (basicPercent / 100) * 100) / 100;
  const basicMonthly = Math.round((basicAnnual / 12) * 100) / 100;

  // HRA (e.g. 50% of Basic for Metro, 40% non-metro)
  const hraAnnual = Math.round(basicAnnual * (hraPercentOfBasic / 100) * 100) / 100;
  const hraMonthly = Math.round((hraAnnual / 12) * 100) / 100;

  // Provident Fund (12% of Basic or standard monthly cap ₹1,800)
  const pfMonthly = Math.round(Math.min(basicMonthly * 0.12, 1800) * 100) / 100;
  const pfAnnual = Math.round(pfMonthly * 12 * 100) / 100;

  // Gratuity (4.81% of Basic)
  const gratuityAnnual = Math.round(basicAnnual * 0.0481 * 100) / 100;
  const gratuityMonthly = Math.round((gratuityAnnual / 12) * 100) / 100;

  // Professional Tax (Standard ₹200/mo in India)
  const ptMonthly = 200;
  const ptAnnual = 2400;

  // Travel & Special Allowance (Balancing figure)
  const allocated = basicAnnual + hraAnnual + pfAnnual + gratuityAnnual;
  const specialAllowanceAnnual = Math.max(0, Math.round((ctc - allocated) * 100) / 100);
  const specialAllowanceMonthly = Math.round((specialAllowanceAnnual / 12) * 100) / 100;

  // Gross Pay & Net In-Hand
  const monthlyGross = Math.round((basicMonthly + hraMonthly + specialAllowanceMonthly) * 100) / 100;
  const monthlyDeductions = Math.round((pfMonthly + ptMonthly) * 100) / 100;
  const netTakeHome = Math.round((monthlyGross - monthlyDeductions) * 100) / 100;

  return {
    annualCTC: ctc,
    monthlyCTC,
    monthly: {
      basicSalary: basicMonthly,
      hra: hraMonthly,
      specialAllowance: specialAllowanceMonthly,
      grossSalary: monthlyGross,
      employeePf: pfMonthly,
      professionalTax: ptMonthly,
      totalDeductions: monthlyDeductions,
      netPay: netTakeHome
    },
    annual: {
      basicSalary: basicAnnual,
      hra: hraAnnual,
      specialAllowance: specialAllowanceAnnual,
      employerPf: pfAnnual,
      gratuity: gratuityAnnual,
      professionalTax: ptAnnual
    }
  };
}

module.exports = {
  calculateCTCBreakdown
};
