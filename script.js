// -----------------------------
// Tabs Handling
// -----------------------------
const tabs = document.querySelectorAll(".tab-link");
const panes = document.querySelectorAll(".tab-pane");

function clearTabs() {
  tabs.forEach(t => t.classList.remove("active"));
  panes.forEach(p => p.classList.remove("active"));
}

function showTab(tabId) {
  clearTabs();
  document.querySelector(`[data-tab='${tabId}']`)?.classList.add("active");
  document.getElementById(tabId)?.classList.add("active");
  showToast(`Opened ${tabId}`, "rgba(52, 152, 219, 0.2)");
}

tabs.forEach(tab => {
  tab.addEventListener("click", () => {
    showTab(tab.dataset.tab);
    if (tab.dataset.tab === "balances") fetchBalances();
    if (tab.dataset.tab === "explorer") fetchBlockchain();
    if (tab.dataset.tab === "history") fetchTransactions();
    if (tab.dataset.tab === "pending") fetchPending();
  });
});

function showToast(message, color = "rgba(231, 76, 60, 0.2)") {
  Toastify({
    text: message,
    duration: 3000,
    gravity: "top",
    position: "right",
    backgroundColor: color,
    stopOnFocus: true
  }).showToast();
}

// -----------------------------
// Global Balances
// -----------------------------
let globalBalances = {};

// -----------------------------
// Login/Signup Functions
// -----------------------------
document.getElementById("loginForm")?.addEventListener("submit", function(e) {
  e.preventDefault();
  const username = this.username.value.trim();
  const password = this.password.value.trim();

  fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      document.getElementById("authModal").classList.add("hide");
      document.getElementById("dashboardSection").style.display = "block";
      fetchBalances();
      fetchBlockchain();
      fetchTransactions();
      showTab("send");
    } 
  })
  .catch(() => showToast("Error during login."));
});

document.getElementById("signupForm")?.addEventListener("submit", function(e) {
  e.preventDefault();
  const username = this.username.value.trim();
  const password = this.password.value.trim();

  fetch("/signup", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast("Signup Successful! Please login.", "rgba(46, 204, 113, 0.2)");
    } else {
      showToast(data.message || "Signup failed.");
    }
  })
  .catch(() => showToast("Error during signup."));
});

// -----------------------------
// Blockchain Data Fetching
// -----------------------------
async function fetchBalances() {
  try {
    const res = await fetch("/balances");
    const data = await res.json();
    globalBalances = data;
    const output = Object.entries(data).map(([user, bal]) => `<p><strong>${user}</strong>: ${bal.toFixed(2)} SIM</p>`).join("");
    document.getElementById("balanceList").innerHTML = output || "No balances yet.";
  } catch {
    showToast("Failed to load balances.");
  }
}

async function fetchBlockchain() {
  try {
    const res = await fetch("/chain");
    const data = await res.json();
    const container = document.getElementById("blockchainView");
    container.innerHTML = ""; // Clear

    data.forEach(block => {
      const card = document.createElement("div");
      card.className = "block-card";
      card.innerHTML = `
        <p><strong>Block #${block.index}</strong></p>
        <p>Hash: ${block.hash.substring(0, 10)}...</p>
        <p>Txns: ${block.transactions.length}</p>
      `;
      card.onclick = () => showBlockDetails(block);
      container.appendChild(card);
    });

  } catch {
    showToast("Failed to load blockchain.");
  }
}

function showBlockDetails(block) {
  const modal = document.getElementById("blockDetailModal");
  const contentWrapper = document.getElementById("blockDetailContent");

  const txnDetails = block.transactions.map(tx =>
    `<p>${tx.sender} → ${tx.recipient}: ${tx.amount}</p>`
  ).join("");

  contentWrapper.innerHTML = `
    <h2>Block #${block.index}</h2>
    <p><strong>Hash:</strong> ${block.hash}</p>
    <p><strong>Previous:</strong> ${block.previous_hash}</p>
    <p><strong>Nonce:</strong> ${block.nonce}</p>
    <h3>Transactions:</h3>
    ${txnDetails || "<p>No Transactions</p>"}
  `;

  modal.style.display = "flex";
}

function closeModal(e) {
  const modal = document.getElementById("blockDetailModal");
  const content = document.getElementById("modalContent");

  if (!content.contains(e.target)) {
    modal.style.display = "none";
  }
}

let currentBlockIndex = 0;
let blockchainData = [];

async function fetchBlockchainData() {
  const res = await fetch("/chain");
  blockchainData = await res.json();
}

// Function to open Block Modal
function openBlockModal(index) {
  currentBlockIndex = index;
  const block = blockchainData[currentBlockIndex];
  const modal = document.getElementById('blockDetailModal');
  const contentDiv = document.getElementById('modalContent');

  let txnsHTML = block.transactions.map(tx => `<p>${tx.sender} → ${tx.recipient}: ${tx.amount}</p>`).join("");
  contentDiv.innerHTML = `
    <span class="modal-close" onclick="document.getElementById('blockDetailModal').style.display='none'">&times;</span>
    <h2>Block #${block.index}</h2>
    <p><strong>Hash:</strong> ${block.hash}</p>
    <p><strong>Previous:</strong> ${block.previous_hash}</p>
    <p><strong>Nonce:</strong> ${block.nonce}</p>
    <h3>Transactions:</h3>
    ${txnsHTML || "No Transactions"}
    <div class="modal-nav">
      <button id="prevBlockBtn" onclick="navigateBlock('prev')">← Prev</button>
      <button id="nextBlockBtn" onclick="navigateBlock('next')">Next →</button>
    </div>
  `;

  modal.style.display = 'flex';
  modal.classList.remove("slide-left", "slide-right");
}

// Navigate to Next/Prev Block
function navigateBlock(direction) {
  if (direction === 'prev' && currentBlockIndex > 0) {
    currentBlockIndex--;
    animateModal("slide-left");
  } else if (direction === 'next' && currentBlockIndex < blockchainData.length - 1) {
    currentBlockIndex++;
    animateModal("slide-right");
  } else {
    showToast("No more blocks", "rgba(231, 76, 60, 0.2)");
  }
}

function animateModal(animationClass) {
  const modalContent = document.getElementById("modalContent");
  modalContent.classList.remove("slide-left", "slide-right");
  void modalContent.offsetWidth;  // Reflow
  modalContent.classList.add(animationClass);

  const block = blockchainData[currentBlockIndex];
  showBlockDetails(block);
}

function closeModal(e) {
  if (e.target.id === 'blockDetailModal') {
    closeBlockModal();
  }
}

function closeBlockModal() {
  document.getElementById("blockDetailModal").style.display = "none";
}


const style = document.createElement("style");
style.innerHTML = `
  .slide-left {
    animation: slideLeft 0.3s forwards;
  }
  .slide-right {
    animation: slideRight 0.3s forwards;
  }
  @keyframes slideLeft {
    from { transform: translateX(50px); opacity: 0; }
    to   { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideRight {
    from { transform: translateX(-50px); opacity: 0; }
    to   { transform: translateX(0); opacity: 1; }
  }
`;
document.head.appendChild(style);

// Load Blockchain Data on Page Load
window.addEventListener("DOMContentLoaded", fetchBlockchainData);

async function fetchTransactions() {
  try {
    const res = await fetch("/transactions");
    const data = await res.json();
    const output = data.map(tx => `<p><strong>${tx.sender}</strong> → <strong>${tx.recipient}</strong>: ${tx.amount} SIM <small>(Block #${tx.block})</small></p>`).join("");
    document.getElementById("transactionList").innerHTML = output || "No transactions yet.";
  } catch {
    showToast("Failed to load transactions.");
  }
}

async function fetchPending() {
  try {
    const res = await fetch("/pending");
    const data = await res.json();
    const output = data.map(tx => `<p>${tx.sender} → ${tx.recipient}: ${tx.amount} SIM</p>`).join("");
    document.getElementById("pendingList").innerHTML = output || "No pending transactions.";
  } catch {
    showToast("Failed to load pending transactions.");
  }
}

// -----------------------------
// Wallet Operations
// -----------------------------
async function createWallet() {
  try {
    const res = await fetch("/create_wallet");
    const data = await res.json();
    
    document.getElementById("walletResult").innerHTML = `
      <p><strong>New Wallet Address:</strong> <span id="walletAddress">${data.wallet}</span></p>
      `;
    const qrDiv = document.getElementById("walletQRCode");
    qrDiv.innerHTML = ""; // Clear previous QR if exists
    QRCode.toCanvas(data.wallet, { width: 150 }, function (err, canvas) {
      if (err) console.error(err);
      qrDiv.appendChild(canvas);
    });
    fetchBalances();
    showToast(`Wallet created: ${data.wallet}`, "rgba(46, 204, 113, 0.2)");
  } catch {
    showToast("Failed to create wallet.");
  }
}

function copyWallet() {
  const walletText = document.getElementById("walletAddress")?.textContent;
  if (walletText) {
    navigator.clipboard.writeText(walletText);
    showToast("Wallet address copied", "rgba(52, 152, 219, 0.2)");
  } else {
    showToast("No wallet address to copy.");
  }
}

// -----------------------------
// Transaction Validation
// -----------------------------
document.getElementById("sendForm")?.addEventListener("submit", function (e) {
  e.preventDefault();

  const sender = this.sender.value.trim();
  const recipient = this.recipient.value.trim();
  const amount = this.amount.value.trim();

  if (!(sender in globalBalances)) {
    showToast("Sender wallet does not exist.");
    return;
  }
  if (!(recipient in globalBalances)) {
    showToast("Recipient wallet does not exist.");
    return;
  }
  if (isNaN(amount) || globalBalances[sender] < parseFloat(amount)) {
    showToast("Insufficient balance.");
    return;
  }

  fetch("/api/send", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `sender=${encodeURIComponent(sender)}&recipient=${encodeURIComponent(recipient)}&amount=${encodeURIComponent(amount)}`
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast(data.message, "rgba(46, 204, 113, 0.2)");
      fetchBalances();
      fetchPending();
    } else {
      showToast(data.message || "Transaction failed.");
    }
  })
  .catch(() => showToast("Error sending transaction."));
});


// -----------------------------
// Mining
// -----------------------------
document.querySelector("form[action='/mine']")?.addEventListener("submit", async function (e) {
  e.preventDefault();
  const miner = this.miner.value.trim();

  if (!globalBalances[miner]) {
    showToast("Miner wallet does not exist.");
    return;
  }

  try {
    const res = await fetch("/mine", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: `miner=${encodeURIComponent(miner)}`
    });
    if (res.ok) {
      fetchBalances();
      fetchBlockchain();
      fetchTransactions();
      fetchPending();
      showToast("Block mined successfully", "rgba(12, 236, 105, 0.2)");
    } else {
      showToast("Mining failed.");
    }
  } catch {
    showToast("Error mining block.");
  }
});

// -----------------------------
// Theme Switching
// -----------------------------
function toggleTheme() {
  const checkbox = document.getElementById("themeCheckbox");
  if (checkbox.checked) {
    document.body.classList.remove("light-mode");
    document.body.classList.add("dark-mode");
    localStorage.setItem("theme", "dark");
    showToast("Switched to Dark Mode", "rgba(52, 73, 94, 0.2)");
  } else {
    document.body.classList.remove("dark-mode");
    document.body.classList.add("light-mode");
    localStorage.setItem("theme", "light");
    showToast("Switched to Light Mode", "rgba(241, 196, 15, 0.2)");
  }
}

// -----------------------------
// Initial Load
// -----------------------------
window.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme") || "light";
  const checkbox = document.getElementById("themeCheckbox");

  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
    checkbox.checked = true;
  } else {
    document.body.classList.add("light-mode");
    checkbox.checked = false;
  }

  // Hide Dashboard until login
  document.getElementById("dashboardSection").style.display = "none";
});

function scrollBlocks(direction) {
  const container = document.getElementById("blockchainView");
  const scrollAmount = 250;

  if (direction === 'left') {
    container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
  } else {
    container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  }
  setTimeout(updateArrowVisibility, 300);
}

function updateArrowVisibility() {
  const container = document.getElementById("blockchainView");
  const leftArrow = document.querySelector(".left-arrow");
  const rightArrow = document.querySelector(".right-arrow");

  leftArrow.style.display = (container.scrollLeft <= 5) ? "none" : "flex";
  rightArrow.style.display = (container.scrollLeft + container.clientWidth >= container.scrollWidth - 5) ? "none" : "flex";
}

document.getElementById("blockchainView").addEventListener("scroll", updateArrowVisibility);
window.addEventListener("load", updateArrowVisibility);


