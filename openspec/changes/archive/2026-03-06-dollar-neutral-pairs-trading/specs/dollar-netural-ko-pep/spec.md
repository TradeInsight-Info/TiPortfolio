# Dollar Neutral Strategy Optimization: Pairs Trading (KO vs PEP)

## 1. Context & Objective
The previous implementation (`dollar_neutral_txn_kvue.ipynb`) showed a high Portfolio Beta (> 3.0), indicating significant market risk exposure.
This plan proposes a "Manual Optimization" by switching assets to a highly correlated pair to achieve a true Market Neutral state (Beta ≈ 0).

## 2. Strategy Logic
*   **Base Strategy**: Dollar Neutral (Long/Short).
*   **Engine**: Use `ScheduleBasedEngine` (same as the previous example).
*   **Rebalance**: Mid-of-month (`month_mid`).

## 3. Asset Selection (The Optimization)
Instead of TXN (Semiconductor) vs KVUE (Consumer Health), we will use:
*   **Long Asset**: `KO` (Coca-Cola Inc.)
*   **Short Asset**: `PEP` (PepsiCo Inc.)
*   **Cash Asset**: `BIL`
*   **Rationale**: Both are in the same industry (Cola Drinks) with extremely high correlation. Longing one and shorting the other should cancel out market volatility.

## 4. Implementation Steps
1.  Create a new notebook: `dollar_neutral_ko_pep.ipynb`.
2.  Reference the existing `dollar_neutral_txn_kvue.ipynb` as the code template.
3.  Update the `LONG` and `SHORT` variables to "KO" and "PEP".
4.  Keep the `RATIO` logic or reset it to 1.0 (50/50) for the initial test.
5.  Generate the comparison plots (especially Portfolio Beta).