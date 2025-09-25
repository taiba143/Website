// server.js

// Import necessary libraries
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const axios = require('axios'); // Use axios to make API requests
require('dotenv').config(); // Loads variables from your .env file

const app = express();
const PORT = process.env.PORT || 3000;

// --- Middleware ---
// These lines set up your server to correctly handle web traffic and data.
app.use(bodyParser.json()); // To parse incoming JSON data from the form
app.use(cors()); // To allow your frontend (index.html) to communicate with this server

// --- Configuration ---
// It securely loads your secret API key from the .env file.
const apiKey = process.env.FACTOR_API_KEY;

// This check ensures the server doesn't start without the API key.
if (!apiKey) {
    console.error("2Factor.in API key is not set. Please add FACTOR_API_KEY to your .env file.");
    process.exit(1); // Exit the process if the key is missing
}

// --- In-Memory Storage ---
// A simple object to temporarily store prospect data. For a real-world application,
// you would use a database like MongoDB or PostgreSQL for permanent storage.
const prospectStore = {}; // Example: { '9876543210': { name: 'Test', status: 'Pending', ... } }

// --- API Endpoints ---

/**
 * @route POST /send-otp
 * @description This is the first step. It receives the form data, checks if the prospect
 * is qualified by income, and only sends an OTP if they are.
 */
app.post('/send-otp', async (req, res) => {
    const { name, email, phone, monthly_revenue } = req.body;

    // --- 1. Data Validation ---
    if (!name || !email || !phone || !monthly_revenue) {
        return res.status(400).json({ success: false, message: 'All fields are required.' });
    }
    if (!/^[6-9]\d{9}$/.test(phone)) {
        return res.status(400).json({ success: false, message: 'Please enter a valid 10-digit Indian mobile number.' });
    }

    // --- 2. Qualification Logic ---
    if (monthly_revenue === 'lt25k') {
        // If income is less than 25k, they are a "BadLead".
        console.log(`Disqualified Lead (low income): ${phone}`);
        prospectStore[phone] = { ...req.body, status: 'BadLead' }; // Store and tag as BadLead
        // Tell the frontend they are not qualified. The frontend will then show the "Sorry" page.
        return res.status(200).json({ success: true, qualified: false, message: 'Prospect does not meet income requirements.' });
    }

    // --- 3. OTP Sending for Qualified Leads ---
    // If the code reaches here, it means the prospect's income is >= 25k.
    const url = `https://2factor.in/API/V1/${apiKey}/SMS/${phone}/AUTOGEN/OTP_Template`;

    try {
        const response = await axios.get(url);
        
        if (response.data.Status === 'Success') {
            const sessionId = response.data.Details;
            // Store all prospect data and the OTP session ID from 2Factor.
            prospectStore[phone] = { ...req.body, sessionId, status: 'Pending' };
            console.log(`Qualified prospect. OTP Sent to ${phone}. Session ID: ${sessionId}`);
            // Tell the frontend they are qualified. The frontend will then show the OTP entry form.
            res.json({ success: true, qualified: true, message: 'OTP sent successfully.' });
        } else {
            // Handle any errors from the 2Factor.in API.
            console.error('2Factor API Error:', response.data.Details);
            res.status(500).json({ success: false, message: response.data.Details });
        }
    } catch (error) {
        console.error('Error sending OTP:', error.message);
        res.status(500).json({ success: false, message: 'Failed to send OTP due to a server error.' });
    }
});


/**
 * @route POST /verify-otp
 * @description This is the second step. It verifies the OTP entered by the user.
 * If correct, the prospect becomes a "Lead". If incorrect, a "BadLead".
 */
app.post('/verify-otp', async (req, res) => {
    const { phone, otp } = req.body;
    
    const prospect = prospectStore[phone];

    // Check if we have a pending OTP session for this phone number.
    if (!prospect || !prospect.sessionId) {
        return res.status(400).json({ success: false, message: 'OTP session not found. Please start over.' });
    }
    
    const url = `https://2factor.in/API/V1/${apiKey}/SMS/VERIFY/${prospect.sessionId}/${otp}`;

    try {
        const response = await axios.get(url);

        if (response.data.Status === 'Success') {
            // OTP is correct! Update the prospect's status to "Lead".
            prospect.status = 'Lead';
            console.log(`Verification SUCCESS for ${phone}. Tagged as: Lead`);
            // In a real app, you would now save this prospect to your main database.
            // Tell the frontend it was successful. The frontend will show the "Success" page.
            res.json({ success: true, message: 'OTP verified successfully.' });
        } else {
            // OTP is incorrect. Update status to "BadLead".
            prospect.status = 'BadLead';
            console.log(`Verification FAILED for ${phone}. Tagged as: BadLead`);
            // Tell the frontend the OTP was invalid.
            res.status(400).json({ success: false, message: 'Invalid OTP. Please try again.' });
        }
    } catch (error) {
        console.error('Error verifying OTP:', error.message);
        res.status(500).json({ success: false, message: 'Failed to verify OTP due to a server error.' });
    }
});


// --- Start Server ---
// This command starts the server and makes it listen for requests.
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    console.log('Ensure you have a .env file with your FACTOR_API_KEY set.');
});

