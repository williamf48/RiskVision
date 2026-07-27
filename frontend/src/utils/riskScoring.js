export const calculateRiskScore = (borrower) => {
  let score = 0;

  if (borrower.dpd > 30) score += 30;
  else if (borrower.dpd > 15) score += 15;

  if (borrower.dscr < 1) score += 25;
  else if (borrower.dscr < 1.2) score += 10;

  if (borrower.revenueTrend < -20) score += 20;
  else if (borrower.revenueTrend < -10) score += 10;

  if (borrower.cashFlow === "Negative") score += 20;

  return score;
};

export const getRiskLevel = (score) => {
  if (score >= 60) return "High Risk";
  if (score >= 30) return "Watchlist";
  return "Low Risk";
};