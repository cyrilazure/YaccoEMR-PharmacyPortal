# Ghana Bank Codes for Paystack Integration

## Purpose
When hospitals configure their bank accounts in Yacco EMR, they can enable automatic Paystack settlement. Paystack uses bank codes to identify which bank to send money to.

## How It Works

1. **Hospital IT Admin adds bank account:**
   - Bank Name: GCB Bank
   - Account Number: 1234567890
   - **Bank Code: 040** (Paystack code for GCB)
   - Enable Paystack Settlement: ✅

2. **Yacco EMR creates Paystack Subaccount:**
   - Automatically registers hospital's bank account with Paystack
   - Gets subaccount code (e.g., ACCT_abc123xyz)

3. **Patient pays invoice via Paystack:**
   - Payment page includes subaccount parameter
   - Money goes DIRECTLY to hospital's bank account
   - Hospital receives funds in 1-2 business days
   - No manual transfer needed

## Ghana Bank Codes (Paystack)

| Bank Code | Bank Name | Common Branches |
|-----------|-----------|----------------|
| 040 | GCB Bank (Ghana Commercial Bank) | Nationwide |
| 050 | Ecobank Ghana | Nationwide |
| 030 | Stanbic Bank Ghana | Accra, Kumasi, Tema |
| 070 | Fidelity Bank Ghana | Nationwide |
| 080 | Guaranty Trust Bank (GTBank) | Major cities |
| 090 | Barclays Bank (Absa Bank Ghana) | Nationwide |
| 061 | Standard Chartered Bank | Accra, Kumasi |
| 011 | Agricultural Development Bank (ADB) | Nationwide |
| 012 | Zenith Bank Ghana | Major cities |
| 013 | Cal Bank | Accra, Tema, Kumasi |
| 014 | Access Bank Ghana | Nationwide |
| 015 | First Atlantic Bank | Accra, Kumasi |
| 016 | United Bank for Africa (UBA) | Major cities |
| 017 | First National Bank (FNB Ghana) | Accra, Kumasi |
| 018 | Prudential Bank | Nationwide |
| 019 | National Investment Bank (NIB) | Nationwide |
| 020 | Universal Merchant Bank (UMB) | Nationwide |
| 021 | Republic Bank Ghana | Accra, Tema |
| 022 | Société Générale Ghana | Accra |
| 023 | ARB Apex Bank | Rural/Community Banks |
| 024 | Omni Bank (BSIC) | Accra, Kumasi |

## Settlement Flow

### Without Subaccount (Old Way)
```
Patient → Paystack → Yacco Central Account → Manual Transfer → Hospital Bank
Time: 3-7 days | Manual work required
```

### With Subaccount (New Way - What We Built)
```
Patient → Paystack → Hospital Bank Account (Direct)
Time: 1-2 days | Automatic settlement ✅
```

## Commission Model (Optional)

Yacco can earn commission by setting `transaction_charge` percentage:

```python
"subaccount": "ACCT_hospital123",
"transaction_charge": 2.5  # Yacco takes 2.5%, hospital gets 97.5%
```

Currently set to: **0%** (hospital gets 100% of payment)

## Benefits

✅ Hospitals receive payments directly in their own bank accounts
✅ No manual transfer work for Yacco
✅ Faster settlement (1-2 days vs 3-7 days)
✅ Each hospital maintains financial independence
✅ Transparent payment tracking
✅ Hospitals see funds in their actual bank statement

## Setup Requirements

For hospital to receive Paystack payments:
1. Hospital must have a Ghana bank account
2. IT Admin enters bank code when adding account
3. Paystack subaccount auto-created on save
4. All future Paystack payments settle directly to hospital

## Testing

Test Bank Codes (Paystack Sandbox):
- Use code: **044** for test bank
- Account number: Any 10 digits
- Currency: GHS

## References

- Paystack Subaccounts API: https://paystack.com/docs/payments/multi-split-payments#subaccounts
- Ghana Bank Codes: https://paystack.com/docs/payouts/supported-banks/#ghana
