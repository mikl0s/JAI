# Donation System - High-Level Plan

## Objective
- Implement a low-friction donation system accepting both **BTC** (Bitcoin) and **ETH** (Ethereum) via **NOWPayments** and **fiat** (cards) via **Stripe**.
- Funds should remain in the payment processors until you're ready to manage withdrawals for tax purposes in Denmark.

---

## Key Components

### 1. **NOWPayments (Crypto Donations)**
- **Supports:** BTC, ETH, and 200+ cryptocurrencies.
- **No Custody Fees:** Funds can remain in NOWPayments without extra charges.
- **Withdrawals:** Manual or automatic withdrawal options to your wallet.
- **Transaction Fees:** 0.5% per transaction.
- **Setup:** Integration of NOWPayments crypto donation button/link on website.

### 2. **Stripe (Fiat Donations)**
- **Supports:** Credit cards, Apple Pay, Google Pay.
- **Funds Storage:** Donations remain in **Stripe balance** until manually withdrawn.
- **Fees:** 2.9% + $0.30 per transaction.
- **Setup:** Integration of Stripe payment gateway for credit card donations.

---

## Process Flow

1. **User Interaction:**
   - Users can choose between **crypto (BTC/ETH)** or **credit card** donations on your website.
   - Simple **donation button** or **link** for crypto, **Stripe Checkout** for fiat.

2. **Donation Flow:**
   - **Crypto Donations (BTC/ETH):**
     - User sends crypto to the provided NOWPayments wallet address.
     - NOWPayments processes the donation with a 0.5% fee.
     - Funds are held in the NOWPayments account until you decide to withdraw.
   - **Fiat Donations (Credit Card):**
     - User donates through the **Stripe Checkout** page.
     - Stripe processes the donation with the usual fees (2.9% + $0.30).
     - Funds are stored in the Stripe balance.

3. **Fund Withdrawal:**
   - Both **NOWPayments** and **Stripe** hold funds until you choose to withdraw.
   - **Stripe** funds remain in your Stripe balance, waiting for manual withdrawal.
   - **NOWPayments** allows withdrawals to your crypto wallet once you decide to access the funds.

---

## Benefits
- **Low friction for users:** Easy-to-use donation buttons for both crypto and cards.
- **Control over funds:** You can hold the funds in **Stripe** and **NOWPayments** until you're ready for tax reporting.
- **No additional fees** for holding funds in both systems.
- **Tax Planning:** Funds can be stored securely without immediate payout requirements, allowing time to consult with an accountant in Denmark.

---

## Next Steps
1. **Create NOWPayments Account** and integrate crypto donation button.
2. **Create Stripe Account** and integrate the fiat donation system.
3. **Promote donation options** on the website to users (both crypto and card options).
4. **Monitor donations and withdrawals** as they accumulate until you decide to manage them with an accountant.

---

## Considerations
- **Tax Compliance in Denmark:** Consult with an accountant to ensure tax regulations are met for both fiat and crypto donations.
- **Security:** Keep both NOWPayments and Stripe accounts secured with two-factor authentication.
