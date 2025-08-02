CryptoSim - Blockchain Simulator
CryptoSim is a simulated blockchain environment where users can create wallets, send transactions, mine blocks, and explore the blockchain visually. This project is built using Flask (Python) for the backend and HTML/CSS/JavaScript for the frontend.

Features
-> User Authentication (Login/Signup)
-> Wallet Generation with QR Code
-> Send Transactions between Wallets
-> Transaction Validation (Balance Checks, Existence)
-> Mining Blocks with Proof-of-Work
-> Blockchain Explorer with Block Details
-> Transaction History & Pending Transactions
-> Light/Dark Theme Switcher

Tech Stack
-----------------------------------------------------------------------------
| Frontend            	      |   Backend	         |  Others                |
|-----------------------------|--------------------|------------------------|
| HTML, CSS, JavaScript       |  Python (Flask)	   |  Local JSON Storage    |
| Toastify.js (Notifications) |  UUID (Wallet IDs) |  QRCode.js (QR Codes)  |
-----------------------------------------------------------------------------

Folder Structure

CryptoSim/
├── blockchain_data.json
├── static/
│   ├── style.css
│   ├── script.js
├── templates/
│   └── index.html
├── users.json
├── app.py
├── README.md

Learning Outcomes
-> Understanding Blockchain Fundamentals (Transactions, Mining, Chain Validation)
-> Backend development using Flask (Routing, Sessions, APIs)
-> Frontend integration with RESTful APIs
-> Implementing QR code-based wallet systems
-> Using Local JSON as persistent storage for learning projects
-> UI/UX improvements (Glassmorphism, Theme Toggling)

Future Enhancements
-> JWT-based Authentication System
-> Persistent Database (SQLite/PostgreSQL)
-> Wallet Private/Public Key Management (Cryptographic Signing)
-> Peer-to-Peer Node Networking
-> Real-time WebSocket Updates (Pending Transactions, Mining)
-> Token/NFT simulation
-> Admin Dashboard with Analytics

How to Run Locally
1. Clone the Repository:
git clone https://github.com/your-username/cryptosim.git
cd cryptosim

2. Install Dependencies:
pip install flask werkzeug

3. Run the Application:
python app.py

4. Open in Browser:
http://localhost:5000

