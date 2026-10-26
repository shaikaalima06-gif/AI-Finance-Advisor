
"use strict";

// FinWise AI - Frontend dashboard
// Data is stored locally in this browser for now.

const STORAGE_KEY = "finwise_transactions_v1";

const $ = (id) => document.getElementById(id);

const money = (value) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(value);

function loadTransactions() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    const data = saved ? JSON.parse(saved) : [];
    return Array.isArray(data) ? data.filter(isValidTransaction) : [];
  } catch (error) {
    console.warn("Could not load saved transactions.", error);
    return [];
  }
}

function isValidTransaction(item) {
  return item &&
    typeof item.id === "string" &&
    ["income", "expense"].includes(item.type) &&
    typeof item.description === "string" &&
    Number.isFinite(item.amount) &&
    item.amount > 0 &&
    typeof item.category === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(item.date);
}

let transactions = loadTransactions();

function saveTransactions() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(transactions));
  } catch (error) {
    console.error("Could not save transactions.", error);
    showMessage("Could not save data in this browser.", true);
  }
}

function showMessage(message, isError = false) {
  const element = $("formMessage");
  element.textContent = message;
  element.style.color = isError ? "#d94152" : "#078e68";
}

function getTotals(items = transactions) {
  const income = items
    .filter((item) => item.type === "income")
    .reduce((sum, item) => sum + item.amount, 0);

  const expenses = items
    .filter((item) => item.type === "expense")
    .reduce((sum, item) => sum + item.amount, 0);

  const savings = income - expenses;
  const savingsRate = income > 0 ? (savings / income) * 100 : 0;

  return { income, expenses, savings, savingsRate };
}

function renderSummary() {
  const totals = getTotals();

  $("incomeDisplay").textContent = money(totals.income);
  $("expenseDisplay").textContent = money(totals.expenses);
  $("savingsDisplay").textContent = money(totals.savings);
  $("rateDisplay").textContent =
    `${Math.round(totals.savingsRate * 10) / 10}%`;

  $("savingsDisplay").style.color =
    totals.savings < 0 ? "#ed5361" : "#172238";

  $("rateDisplay").style.color =
    totals.savingsRate < 0 ? "#ed5361" : "#172238";
}

function renderTransactions() {
  const query = $("searchInput").value.trim().toLowerCase();

  const filtered = [...transactions]
    .filter((item) =>
      `${item.description} ${item.category} ${item.type}`
        .toLowerCase()
        .includes(query)
    )
    .sort((a, b) =>
      b.date.localeCompare(a.date) || b.id.localeCompare(a.id)
    );

  const list = $("transactionList");

  if (filtered.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <span>◎</span>
        <strong>${query ? "No matching transactions" : "No transactions yet"}</strong>
        <p>${query ? "Try another search term." : "Add your first income or expense to get started."}</p>
      </div>`;
    return;
  }

  list.innerHTML = filtered.map((item) => {
    const isIncome = item.type === "income";
    const symbol = isIncome ? "+" : "−";
    const sign = isIncome ? "+" : "−";

    return `
      <div class="transaction-row">
        <div class="transaction-symbol"
          aria-hidden="true">${escapeHTML(item.category.slice(0, 1))}</div>
        <div class="transaction-name">
          ${escapeHTML(item.description)}
          <div class="transaction-meta">${formatDate(item.date)}</div>
        </div>
        <span class="category-pill">${escapeHTML(item.category)}</span>
        <span class="transaction-amount ${isIncome ? "amount-income" : "amount-expense"}">
          ${sign} ${money(item.amount)}
        </span>
        <button class="delete-transaction"
          type="button"
          data-delete="${escapeHTML(item.id)}"
          aria-label="Delete ${escapeHTML(item.description)}"
          title="Delete transaction">×</button>
      </div>`;
  }).join("");
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character]);
}

function formatDate(dateString) {
  const date = new Date(`${dateString}T12:00:00`);
  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric"
  });
}

function renderBarChart() {
  const chart = $("barChart");

  if (transactions.length === 0) {
    chart.innerHTML =
      '<div class="chart-empty">Add transactions to see your chart.</div>';
    return;
  }

  // Display the most recent six calendar months.
  const now = new Date();
  const months = [];

  for (let offset = 5; offset >= 0; offset--) {
    const date = new Date(now.getFullYear(), now.getMonth() - offset, 1);

    months.push({
      year: date.getFullYear(),
      month: date.getMonth(),
      label: date.toLocaleDateString("en-IN", { month: "short" }),
      income: 0,
      expenses: 0
    });
  }

  transactions.forEach((item) => {
    const date = new Date(`${item.date}T12:00:00`);
    const month = months.find((entry) =>
      entry.year === date.getFullYear() &&
      entry.month === date.getMonth()
    );

    if (!month) return;

    if (item.type === "income") month.income += item.amount;
    else month.expenses += item.amount;
  });

  const maxValue = Math.max(
    1,
    ...months.flatMap((month) => [month.income, month.expenses])
  );

  chart.innerHTML = months.map((month) => {
    const incomeHeight = month.income / maxValue * 100;
    const expenseHeight = month.expenses / maxValue * 100;

    return `
      <div class="chart-month" title="${month.label}: Income ${money(month.income)}, expenses ${money(month.expenses)}">
        <div class="bar-pair">
          <div class="bar income-bar"
            style="height:${incomeHeight}%"
            title="Income: ${money(month.income)}"></div>
          <div class="bar expense-bar"
            style="height:${expenseHeight}%"
            title="Expenses: ${money(month.expenses)}"></div>
        </div>
        <span>${month.label}</span>
      </div>`;
  }).join("");
}

function renderBudgetChart() {
  const totals = getTotals();
  const expenseItems = transactions.filter(
    (item) => item.type === "expense"
  );

  const categoryTotals = {};

  expenseItems.forEach((item) => {
    categoryTotals[item.category] =
      (categoryTotals[item.category] || 0) + item.amount;
  });

  const categories = Object.entries(categoryTotals)
    .sort((a, b) => b[1] - a[1]);

  // The ring represents category shares of recorded expenses.
  const colors = [
    "#0cbd8c", "#4299e9", "#9662ed",
    "#f5a623", "#ed5361", "#19b9c5",
    "#6f8199", "#e77bb8"
  ];

  const totalExpenses = totals.expenses;
  const ring = $("donutChart");
  const centerPercent = $("budgetPercent");
  const legend = $("budgetLegend");

  // No separate spending limit has been set yet.
  // Show 100% when there are expenses, 0% when there are none.
  centerPercent.textContent = totalExpenses > 0 ? "100%" : "0%";
  ring.style.background = totalExpenses > 0
    ? `conic-gradient(${colors[0]} 0% 100%)`
    : "conic-gradient(#e9edf4 0% 100%)";

  if (categories.length === 0) {
    legend.innerHTML =
      '<p class="muted">Add expenses to see categories.</p>';
    return;
  }

  let cumulative = 0;
  const stops = categories.map(([category, amount], index) => {
    const start = cumulative;
    cumulative += amount / totalExpenses * 100;
    return `${colors[index % colors.length]} ${start}% ${cumulative}%`;
  });

  ring.style.background = `conic-gradient(${stops.join(", ")})`;

  legend.innerHTML = categories.slice(0, 5).map(
    ([category, amount], index) => {
      const percent = amount / totalExpenses * 100;

      return `
        <div class="budget-item">
          <i style="background:${colors[index % colors.length]}"></i>
          <div>
            <span>${escapeHTML(category)} (${Math.round(percent)}%)</span>
            <strong>${money(amount)}</strong>
          </div>
        </div>`;
    }
  ).join("");
}

const tips = [
  "Try the 50/30/20 rule as a starting point: 50% for needs, 30% for wants and 20% for savings. Adjust it to fit your real expenses.",
  "Build an emergency fund gradually. Even small, regular contributions can help you prepare for unexpected expenses.",
  "Review your subscriptions and recurring expenses each month. Cancel services you no longer use.",
  "Set a specific savings goal and a target date. A clear goal makes it easier to track progress.",
  "Record expenses regularly so you can identify spending patterns and make informed decisions."
];

let tipIndex = 0;

function updateTip() {
  const totals = getTotals();
  const tipElement = $("aiTip");

  if (transactions.length === 0) {
    tipElement.textContent =
      "Start by recording your income and expenses. Once you have some data, FinWise can show you useful insights.";
  } else if (totals.savings < 0) {
    tipElement.textContent =
      `Your recorded expenses exceed your income by ${money(Math.abs(totals.savings))}. Review your spending and prioritize essential costs.`;
  } else if (totals.savingsRate >= 20) {
    tipElement.textContent =
      `Your current savings rate is ${totals.savingsRate.toFixed(1)}%. Great progress! Keep tracking your spending and working toward your goals.`;
  } else {
    tipElement.textContent = tips[tipIndex % tips.length];
  }
}

function renderDashboard() {
  renderSummary();
  renderTransactions();
  renderBarChart();
  renderBudgetChart();
  updateTip();
}

$("financeForm").addEventListener("submit", (event) => {
  event.preventDefault();

  const form = event.currentTarget;
  const formData = new FormData(form);
  const description = String(formData.get("description") || "").trim();
  const amount = Number(formData.get("amount"));
  const date = String(formData.get("date") || "");

  if (!description || !Number.isFinite(amount) || amount <= 0) {
    showMessage("Enter a description and a valid amount.", true);
    return;
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    showMessage("Please select a valid date.", true);
    return;
  }

  const transaction = {
    id: crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type: String(formData.get("type")),
    description,
    amount,
    category: String(formData.get("category")),
    date
  };

  if (!isValidTransaction(transaction)) {
    showMessage("Please check your transaction details.", true);
    return;
  }

  transactions.push(transaction);
  saveTransactions();
  form.reset();
  $("date").value = getToday();
  showMessage("Transaction added successfully!");
  renderDashboard();
});

$("transactionList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-delete]");
  if (!button) return;

  const id = button.dataset.delete;
  transactions = transactions.filter((item) => item.id !== id);

  saveTransactions();
  showMessage("Transaction deleted.");
  renderDashboard();
});

$("searchInput").addEventListener("input", renderTransactions);

$("clearSearchButton").addEventListener("click", () => {
  $("searchInput").value = "";
  renderTransactions();
});

function getToday() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

$("date").value = getToday();

$("todayLabel").textContent = new Date().toLocaleDateString("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric"
});

$("tipButton").addEventListener("click", () => {
  $("advisor").scrollIntoView({ behavior: "smooth" });
  updateTip();
});

$("newTipButton").addEventListener("click", () => {
  tipIndex++;
  $("aiTip").textContent = tips[tipIndex % tips.length];
});

$("menuButton").addEventListener("click", () => {
  document.querySelector(".sidebar").classList.toggle("open");
});

document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    document.querySelectorAll(".nav-link").forEach((item) =>
      item.classList.remove("active")
    );
    link.classList.add("active");
    document.querySelector(".sidebar").classList.remove("open");
  });
});

// First render
renderDashboard();

/* ==========================================
    EXTRA FEATURES: BUDGETS, GOALS, CSV, AI API
   ========================================== */

const BUDGET_KEY = "finwise_monthly_budget_v1";
const GOALS_KEY = "finwise_savings_goals_v1";

// Replace this URL with the actual endpoint provided by your backend team.
const AI_ADVISOR_API_URL = "http://127.0.0.1:5000/api/advisor";

function readLocalNumber(key) {
  try {
    const value = Number(localStorage.getItem(key));
    return Number.isFinite(value) && value > 0 ? value : 0;
  } catch {
    return 0;
  }
}

function readGoals() {
  try {
    const data = JSON.parse(localStorage.getItem(GOALS_KEY) || "[]");
    return Array.isArray(data) ? data.filter((goal) =>
      goal &&
      typeof goal.id === "string" &&
      typeof goal.name === "string" &&
      Number.isFinite(goal.target) &&
      goal.target > 0 &&
      Number.isFinite(goal.saved) &&
      goal.saved >= 0
    ) : [];
  } catch {
    return [];
  }
}

let monthlyBudget = readLocalNumber(BUDGET_KEY);
let savingsGoals = readGoals();

function currentMonthExpenses() {
  const today = getToday();
  const monthPrefix = today.slice(0, 7);

  return transactions
    .filter((item) =>
      item.type === "expense" && item.date.startsWith(monthPrefix)
    )
    .reduce((sum, item) => sum + item.amount, 0);
}

function renderBudgetPlanner() {
  const spent = currentMonthExpenses();
  const usage = monthlyBudget > 0 ? spent / monthlyBudget * 100 : 0;
  const remaining = monthlyBudget - spent;

  $("budgetUsageText").textContent =
    monthlyBudget > 0 ? `${usage.toFixed(1)}%` : "—";

  $("budgetSpentText").textContent = `Spent: ${money(spent)}`;
  $("budgetRemainingText").textContent = monthlyBudget > 0
    ? `${remaining < 0 ? "Over by: " : "Remaining: "}${money(Math.abs(remaining))}`
    : "Limit: not set";

  $("budgetUsageBar").style.width =
    `${Math.min(usage, 100)}%`;

  $("budgetUsageBar").classList.toggle(
    "over-budget",
    monthlyBudget > 0 && spent > monthlyBudget
  );

  $("budgetStatus").textContent = monthlyBudget <= 0
    ? "Set a monthly limit to track your spending."
    : spent > monthlyBudget
      ? "You have exceeded your monthly spending limit. Review your expenses."
      : usage >= 80
        ? "You are approaching your monthly budget limit."
        : "Your spending is within your monthly budget.";
}

function renderSavingsGoals() {
  const list = $("goalsList");

  if (savingsGoals.length === 0) {
    list.innerHTML =
      '<p class="muted">No savings goals yet. Create one above!</p>';
    return;
  }

  list.innerHTML = savingsGoals.map((goal) => {
    const percent = goal.target > 0
      ? goal.saved / goal.target * 100
      : 0;
    const cappedPercent = Math.min(percent, 100);
    const remaining = Math.max(0, goal.target - goal.saved);

    return `
      <div class="goal-card">
        <div class="goal-card-heading">
          <div>
            <strong>${escapeHTML(goal.name)}</strong><br>
            <small>${money(goal.saved)} saved of ${money(goal.target)}</small>
          </div>
          <button class="goal-delete" type="button"
            data-delete-goal="${escapeHTML(goal.id)}">
            Delete
          </button>
        </div>
        <div class="progress-track">
          <div class="progress-fill"
            style="width:${cappedPercent}%"></div>
        </div>
        <div class="goal-card-footer">
          <span>${Math.round(percent)}% complete</span>
          <span>${remaining > 0 ? `${money(remaining)} to go` : "Goal reached!"}</span>
        </div>
      </div>`;
  }).join("");
}

$("budgetForm").addEventListener("submit", (event) => {
  event.preventDefault();

  const value = Number($("monthlyBudget").value);

  if (!Number.isFinite(value) || value <= 0) {
    $("budgetMessage").textContent =
      "Enter a budget amount greater than zero.";
    return;
  }

  monthlyBudget = value;

  try {
    localStorage.setItem(BUDGET_KEY, String(monthlyBudget));
    $("budgetMessage").textContent = "Monthly budget saved.";
  } catch {
    $("budgetMessage").textContent =
      "Could not save the budget in this browser.";
  }

  renderBudgetPlanner();
});

$("monthlyBudget").value = monthlyBudget || "";

$("goalForm").addEventListener("submit", (event) => {
  event.preventDefault();

  const name = $("goalName").value.trim();
  const target = Number($("goalTarget").value);
  const saved = Number($("goalSaved").value);

  if (
    !name ||
    !Number.isFinite(target) || target <= 0 ||
    !Number.isFinite(saved) || saved < 0
  ) {
    $("goalMessage").textContent =
      "Enter a goal name, a positive target, and valid savings.";
    return;
  }

  savingsGoals.push({
    id: crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    name,
    target,
    saved
  });

  try {
    localStorage.setItem(GOALS_KEY, JSON.stringify(savingsGoals));
    $("goalMessage").textContent = "Savings goal created!";
  } catch {
    savingsGoals.pop();
    $("goalMessage").textContent =
      "Could not save your goal in this browser.";
    return;
  }

  $("goalForm").reset();
  $("goalSaved").value = "0";
  renderSavingsGoals();
});

$("goalsList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-delete-goal]");
  if (!button) return;

  savingsGoals = savingsGoals.filter(
    (goal) => goal.id !== button.dataset.deleteGoal
  );

  try {
    localStorage.setItem(GOALS_KEY, JSON.stringify(savingsGoals));
  } catch {
    $("goalMessage").textContent =
      "Could not update saved goals.";
  }

  renderSavingsGoals();
});

function downloadCSV() {
  if (transactions.length === 0) {
    showMessage("Add a transaction before exporting a report.", true);
    return;
  }

  const headings = [
    "Date", "Type", "Description", "Category", "Amount (INR)"
  ];

  // Quote and escape fields so commas and quotes in descriptions
  // do not break the CSV file.
  const csvCell = (value) =>
    `"${String(value).replace(/"/g, '""')}"`;

  const rows = transactions
    .slice()
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((item) => [
      item.date,
      item.type,
      item.description,
      item.category,
      item.amount.toFixed(2)
    ]);

  const csv = [headings, ...rows]
    .map((row) => row.map(csvCell).join(","))
    .join("\r\n");

  const blob = new Blob(["\uFEFF" + csv], {
    type: "text/csv;charset=utf-8;"
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `finwise-transactions-${getToday()}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);

  showMessage("CSV report downloaded.");
}

$("downloadReportButton").addEventListener("click", downloadCSV);

$("askAiButton").addEventListener("click", async () => {
  const question = $("aiQuestion").value.trim();

  if (!question) {
    $("aiStatus").textContent = "Enter a question for your advisor.";
    return;
  }

  const totals = getTotals();

  $("askAiButton").disabled = true;
  $("aiStatus").textContent = "Contacting your financial advisor...";

  try {
    const response = await fetch(AI_ADVISOR_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        currency: "INR",
        financial_summary: {
          total_income: totals.income,
          total_expenses: totals.expenses,
          total_savings: totals.savings,
          savings_rate: totals.savingsRate
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Advisor API returned HTTP ${response.status}`);
    }

    const data = await response.json();

    // Change these response fields if your backend uses another schema.
    const answer = data.answer || data.response || data.advice;

    if (typeof answer !== "string" || !answer.trim()) {
      throw new Error("The advisor response did not contain an answer.");
    }

    // Use textContent so the response is displayed as text, not HTML.
    $("aiTip").textContent = answer;
    $("aiStatus").textContent = "Advisor response received.";
  } catch (error) {
    console.error("Financial advisor connection error:", error);
    $("aiStatus").textContent =
      "Could not connect to the advisor. Check the backend URL, server, and API format.";
  } finally {
    $("askAiButton").disabled = false;
  }
});

// Extend the existing dashboard refresh function.
const originalRenderDashboard = renderDashboard;

renderDashboard = function () {
  originalRenderDashboard();
  renderBudgetPlanner();
  renderSavingsGoals();
};

// Render the new sections when the page first opens.
renderBudgetPlanner();
renderSavingsGoals();



const savingsForm = document.getElementById("savingsGoalForm");

const currencyINR = (amount) =>
  amount.toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  });

function setMinimumDeadline() {
  const deadlineInput = document.getElementById("deadline");
  const today = new Date();
  const localDate = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0")
  ].join("-");

  deadlineInput.min = localDate;
}

setMinimumDeadline();

savingsForm.addEventListener("submit", function (event) {
  event.preventDefault();

  const goalName = document.getElementById("goalName").value.trim();
  const target = Number(document.getElementById("targetAmount").value);
  const saved = Number(document.getElementById("savedAmount").value);
  const deadlineValue = document.getElementById("deadline").value;

  if (
    !goalName ||
    !Number.isFinite(target) ||
    !Number.isFinite(saved) ||
    target <= 0 ||
    saved < 0 ||
    saved > target ||
    !deadlineValue
  ) {
    alert("Please enter valid goal details and amounts.");
    return;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const deadline = new Date(deadlineValue + "T00:00:00");
  const days = Math.round(
    (deadline.getTime() - today.getTime()) / 86400000
  );

  const remaining = target - saved;
  const progress = (saved / target) * 100;

  if (remaining > 0 && days <= 0) {
    alert("Choose a future deadline to calculate your savings plan.");
    return;
  }

  // If the goal is already reached, no additional saving is needed.
  const daily = remaining === 0 ? 0 : remaining / days;

  // Estimate an average month as 365.2425 / 12 days.
  const monthly = daily * (365.2425 / 12);

  document.getElementById("resultGoalName").textContent = goalName;
  document.getElementById("resultTarget").textContent =
    currencyINR(target);
  document.getElementById("resultSaved").textContent =
    currencyINR(saved);
  document.getElementById("remainingAmount").textContent =
    currencyINR(remaining);
  document.getElementById("dailySavings").textContent =
    currencyINR(daily);
  document.getElementById("monthlySavings").textContent =
    currencyINR(monthly);
  document.getElementById("daysRemaining").textContent =
    remaining === 0 ? "Goal achieved!" : `${days} days`;
  document.getElementById("goalProgress").textContent =
    `${progress.toFixed(1)}%`;

  document.getElementById("progressBar").style.width =
    `${progress}%`;

  document.getElementById("savingsPlanResult").hidden = false;
});
