# Distributed Reward Network: Payout Reconciliation Audit
### When 51% of transfers move less than 0.1% of total value, one reconciliation process isn't enough
**Crystal Olisa - Operations Generalist - Diagnostic & Build**
**[Live Dashboard](https://dune.com/olisa/distributed-reward-network-payout-reconciliation) - [LinkedIn](https://linkedin.com/in/crystalolisa)**

On-chain execution is automated. The financial operations layer sitting around it - classification, reconciliation, governance documentation - is almost never built until something breaks. This project queries publicly available Solana transfer data from a live distributed reward network to show what that layer looks like: three analytical queries, a four-class reconciliation framework, and a set of diagnostic outputs structured for governance review. It demonstrates financial operations methodology applied to on-chain treasury operations - not accounting work, and not blockchain engineering.


## The Business Problem

Distributed reward networks - DePIN protocols, bandwidth markets, compute networks - pay large numbers of participants across multiple jurisdictions in token-denominated rewards. The transaction execution layer is on-chain and automated. But in early-stage networks, the validation layer is rarely formalised. No one is checking whether the right wallets received the right amounts, whether any wallets are ineligible under jurisdiction rules, or whether large treasury movements are being documented separately from participant payouts. What typically exists is execution without a structured audit trail - transfers run, but the classification logic, eligibility checks, and governance documentation that make them defensible are built after a problem surfaces, not before.

The cost of not having this layer is not just operational - it is governance exposure. A network paying millions of participants across 100+ countries without a formalised reconciliation trail, structured wallet classification, and pre-execution anomaly detection has no defensible record when something goes wrong. The audit happens after the dispute, not before the payment run.


## Why This Data Source

This project uses on-chain transfer data from the GRASS token - the reward token distributed by a live bandwidth-sharing network on Solana. GRASS was selected as the data source for three reasons.

**Scale and activity.** The network has distributed rewards to millions of participants since token launch in October 2024, generating a high-volume transfer record that reflects the real operational conditions a reconciliation framework needs to handle - large epoch distribution events, micro-transactions, infrastructure wallet movements, and treasury-level transfers all present in the same ledger.

**Public availability.** All transfer data is publicly queryable on-chain via Dune Analytics. No proprietary or private data was required. This makes the methodology fully reproducible and independently verifiable.

**Operational complexity.** The network pays participants across 100+ countries in a token with real market value, with jurisdiction-based eligibility rules and epoch-based distribution mechanics. This is structurally representative of the class of distributed reward systems this framework is designed for - not a simplified example, but a live operational context.

No private or internal data from the network was used. All analysis is based on publicly available on-chain records.


## Glossary

**Blockchain / on-chain**
A blockchain is a public, append-only ledger. "On-chain" means the record exists on that ledger - it is publicly visible, permanent, and cannot be altered. Every token transfer in this project is on-chain, meaning it can be independently verified by anyone.

**Solana**
The blockchain network this project queries. Solana processes transactions at high speed and low cost, which makes it a common choice for networks that need to distribute rewards to large numbers of participants frequently.

**Token / SPL token**
A token is a digital asset issued on a blockchain. SPL (Solana Program Library) tokens are the standard token type on Solana - the equivalent of ERC-20 tokens on Ethereum. GRASS is an SPL token.

**GRASS token**
The reward token distributed by a bandwidth-sharing network to participants who contribute their unused internet connection. 1 GRASS = one unit of the network's reward token. At the time of analysis, 1 GRASS ≈ $0.07-$0.09 USD (market price fluctuates). Token amounts in this project are expressed in GRASS units unless otherwise stated.

**Token decimals**
GRASS has 9 decimal places, meaning 1 GRASS is stored on-chain as 1,000,000,000 (1 × 10⁹) in raw integer form. All queries in this project divide raw amounts by 1e9 to convert to human-readable GRASS units.

**Wallet address**
A unique identifier on the blockchain - the equivalent of a bank account number. Every participant in a distributed reward network has a wallet address that receives token transfers.

**Epoch**
A fixed time period after which rewards are calculated and distributed. Networks typically calculate how much each participant earned during the epoch, then execute a batch of transfers to all eligible wallets at the end of it. Epoch boundaries are visible in the transfer data as days with unusually high transfer counts.

**Dune Analytics**
A public blockchain data platform that allows SQL queries to be run directly against on-chain data. Used in this project to query the `tokens_solana.transfers` table, which contains every SPL token transfer on Solana. Free tier available; some query performance limits apply.

**Infrastructure wallet**
A wallet controlled by the network team, foundation, or an exchange - not a participant. Infrastructure wallets typically show very high transfer frequency, very large total value received, or both. They are operationally distinct from participant wallets and must be classified and excluded before any participant payout report is calculated.

**Treasury wallet**
A specific type of infrastructure wallet that holds and distributes tokens on behalf of the network. Treasury transfers are typically large, infrequent, and require separate governance documentation. In this project, days where treasury-level transfers occur are classified separately from participant distribution runs.

**DePIN (Decentralised Physical Infrastructure Network)**
A category of blockchain-based networks that coordinate and reward real-world resource contributions - bandwidth, compute, storage, energy - using token incentives. The operational challenge they share is managing high-volume, cross-border, token-denominated payments to large numbers of participants.

**Reconciliation**
The process of verifying that what was supposed to happen (the expected payout, calculated off-chain) matches what actually happened (the on-chain transfer record). In traditional finance this is a standard month-close process. In early-stage distributed reward networks it is rarely formalised before something goes wrong.


## The 3 Findings

**1. Volume and value are concentrated in opposite ends of the distribution - and require completely different operational responses.**
51% of all transfers (over 8.7 million transactions) are under 10 GRASS, but represent less than 0.1% of total value transferred. The 10K+ GRASS bucket - just 0.27% of all transfers - moved 3.58 billion GRASS, the majority of total network value. A reconciliation framework that treats all transfers equally applies the wrong logic to both ends: micro-transfers require deduplication and classification; large transfers require governance sign-off. The operational cost of conflating them is misallocated review effort and undetected treasury exposure.

**2. Two anomaly days account for treasury-level movements that cannot be reconciled against participant payout patterns without separate classification.**
March 10, 2026 saw 259 million GRASS transferred - approximately 10x the daily average - with a single transfer of 46.6 million GRASS. May 7, 2026 saw 42 million GRASS transferred, with a single transfer of 16.6 million GRASS. On both days, transfer counts were within the normal range (20,170 and 12,365 respectively), meaning the anomaly is entirely in value concentration, not volume. These are consistent with treasury-level events rather than participant distribution runs - though without access to internal records, the exact nature of these transfers cannot be confirmed from on-chain data alone. Without a classification layer that separates them before reporting, they inflate payout totals, distort average transfer metrics, and produce a misleading financial picture for any governance review.

**3. Wallet behaviour reveals three operationally distinct categories that must be classified before any reconciliation report is calculated.**
The top wallet received 661,726 transfers across 503 active days - 1,315 per day on average - and 225 million GRASS total. This is almost certainly infrastructure rather than a participant wallet. A cluster of approximately 10 wallets each show 77,000-78,000 receipts with consistent amounts and identical start dates - programmatic epoch distribution, the expected pattern. Several wallets received 13-36 million GRASS in 11-119 transfers across short active windows, with timing correlating directly to the anomaly days in Finding 2. Aggregating all three categories into a single payout report without classification produces totals that cannot be audited, verified, or defended.


## What This Means For Operations

| Finding | Operational implication |
|---|---|
| 51% of transfers by count move less than 0.1% of total value | Two different review processes are required: automated deduplication for micro-transfers, governance sign-off for large transfers. A single process misallocates review effort and leaves the highest-value transfers without adequate oversight. |
| Two anomaly days account for 10x normal treasury movement | A classification layer is needed to separate treasury events from participant payouts before any reporting runs. Without it, financial reports overstate participant payout totals and obscure treasury exposure. |
| Three operationally distinct wallet categories exist in the same ledger | Wallet classification must run as a prerequisite step before any reconciliation report is calculated. Aggregating infrastructure wallets, epoch distribution wallets, and anomalous large-value wallets into a single report produces totals that cannot be audited, verified, or defended. |


## Methodology

| Step | What happened |
|---|---|
| Query 1 - Daily transfer volume | Queried `tokens_solana.transfers` filtered to the GRASS token mint from October 2024 to present. Grouped by day to establish the baseline distribution cadence and identify anomaly days. Revealed two days with value concentration 10x the daily average - flagged for separate governance treatment before any aggregate reporting runs. |
| Query 2 - Transfer size distribution | Classified all transfers into six value buckets from < 1 GRASS to 10K+ GRASS. Identified that the distribution of transaction count and the distribution of value are almost perfectly inverted - the bottom two buckets account for 51% of transactions and under 0.1% of value. This determined the two-track reconciliation logic: deduplication for micro-transfers, governance sign-off for large transfers. |
| Query 3 - Wallet concentration analysis | Queried top 50 recipient wallets by total GRASS received from January 2025, filtered to wallets with more than 10 receipts. Identified three operationally distinct wallet categories - infrastructure, programmatic epoch, and anomalous large-value - each requiring different classification before reconciliation totals are calculated. Narrowed to 2025 onwards to stay within free-tier query limits while preserving the concentration pattern. |
| Classification framework | Applied a four-class framework (PASS, FLAG_large_transfer, FLAG_micro_transfer, REVIEW_wallet_type) based on the patterns identified across all three queries. Framework runs before the payment batch executes, not after. |

The full analysis runs across the notebook with each section documenting what the data is showing and what it decides next.


## Results

| Metric | Value |
|---|---|
| Total transfers analysed (Query 2 scope) | 17,144,643 |
| Transfers under 10 GRASS (% of count) | 8,712,486 (50.8%) |
| Value moved by transfers under 10 GRASS | 20,811,559 GRASS (< 0.1% of total) |
| Transfers 10K+ GRASS (% of count) | 45,695 (0.27%) |
| Value moved by transfers 10K+ GRASS | 3,587,335,978 GRASS (majority of total) |
| Anomaly day - March 10 2026 | 259,695,783 GRASS transferred (10x daily average) |
| Anomaly day - May 7 2026 | 42,308,798 GRASS transferred |
| Largest single transfer observed | 46,620,000 GRASS (March 10 2026) |
| Top wallet total received | 225,522,665 GRASS across 661,726 transfers |
| Programmatic epoch wallet cluster | ~10 wallets, 77,000-78,000 receipts each, from January 1 2025 (~10 wallets receiving consistent amounts on a regular cadence - this is what the expected distribution pattern looks like) |


## Recommendations

These are framed as diagnostic outputs. A real engagement would validate each against the company's actual operational context before any build begins.

1. **Implement wallet classification as a prerequisite step before any reconciliation report runs.** The data shows three structurally distinct wallet categories that produce meaningless totals when aggregated. The classification logic is straightforward - transfer frequency, value concentration, and first receipt date are sufficient to distinguish infrastructure wallets, epoch distribution wallets, and anomalous large-value wallets. Measure success by whether governance reports can be produced with infrastructure and treasury wallets separated from participant payout totals.

2. **Build a treasury event documentation layer for transfers exceeding a defined governance threshold.** The March 10 and May 7 anomaly days are not visible as distinct event types in the current transfer record - they appear as high-value days alongside normal distribution runs. A governance threshold (for example, any single transfer exceeding 1 million tokens, or any day where total value exceeds 3x the 30-day rolling average) should trigger a separate documentation workflow: who authorised it, what it was for, and what the audit trail is. Measure success by whether any transfer above threshold has a corresponding governance record before it executes.

3. **Establish a two-track reconciliation process that separates micro-transfer classification from large-transfer governance review.** Over 8.7 million transfers are under 10 GRASS. Routing these through the same review process as large transfers wastes review capacity on low-financial-risk noise. Micro-transfers should be batched, deduplicated, and classified automatically. Large transfers should require manual sign-off. The current data provides the threshold logic - the operational build is a process design question, not a data question.


## The Audit-to-Monitor Framework

This project is Phase 1 of a two-phase operational model.

**Phase 1 - Audit (this project):** Establish what normal looks like. Classify the transfer types. Quantify the anomaly pattern. Define the thresholds that make a monitoring layer trustworthy. The audit answers: what is the operational gap, how material is it, and what does closing it require?

**Phase 2 - Monitor (operational extension):** Schedule the queries on a defined cadence. Set threshold-based alerts - daily value exceeds 3x rolling average, single transfer exceeds 1M tokens, new anomalous wallet pattern detected. Build the system that watches without manual intervention. The monitor operationalises the audit findings into infrastructure that runs after the engagement ends.

You cannot build a trustworthy monitor without first running the audit. The thresholds that make alerts meaningful come from knowing what normal looks like - and that requires the diagnostic phase first.

The monitor is also the answer to a common failure mode: governance processes that don't hold because they depend on people remembering to run them. A scheduled pipeline doesn't forget. It runs on the cadence you set, flags what crosses the threshold you defined, and stops requiring anyone to remember to check. The operational improvement persists because it's built into the system, not held in someone's head.


## Next Steps

### Layer 1 - Extend the audit with off-chain data

The natural extension of this analysis is connecting the on-chain transfer record to two off-chain data sources that sit adjacent to it.

First, a jurisdiction eligibility layer. User registration data (country, KYC status) joined to wallet address would add a compliance check to the reconciliation framework, surfacing whether any transfers reached ineligible wallets before the next epoch runs.

Second, an expected-vs-actual reconciliation layer. Joining the epoch reward calculation (produced off-chain from contribution data) to the actual on-chain transfer amounts would surface discrepancies between what was calculated and what was sent. Both extensions are documented in the project spec. The on-chain data is the foundation; these layers are what make it operationally complete.

### Layer 2 - Operationalise as a live monitoring system

The framework built here is a retrospective audit - it establishes the baseline pattern and identifies anomalies in historical data. That is the prerequisite, not the final output.

The production version of this work is a scheduled monitoring system: the same queries run automatically on a defined cadence, with threshold-based alerts triggering review workflows when anomalies are detected.

The audit established the thresholds that make the monitor defensible:

| Alert condition | Threshold basis | Operational response |
|---|---|---|
| Daily transfer value > 3x 30-day rolling average | Derived from Query 1 anomaly analysis | Treasury event review - governance documentation required before next epoch runs |
| Single transfer > 1M GRASS | Derived from Query 2 large transfer bucket | Flag for manual sign-off before processing |
| New wallet in top 50 recipients with < 30 active days | Derived from Query 3 wallet classification | REVIEW_wallet_type - classify before including in payout report |

You cannot set meaningful alert thresholds without first knowing what normal looks like. The audit answers that question. The monitor operationalises the answer.

Dune's scheduling and alerts features support this directly - queries run on a defined schedule, alerts fire when thresholds are breached. The monitor runs without manual intervention. It flags what needs attention and lets the routine run cleanly.

**The two-phase model:**
- Phase 1 - Audit: diagnose the historical pattern, establish the baseline, define defensible thresholds
- Phase 2 - Monitor: schedule the queries, set threshold-based alerts, build the system that watches without you

The audit is the design phase. The monitor is the operational infrastructure.


## How to Read This Project

**Non-technical reader:** The three findings, the What This Means For Operations table, and the results table above cover the analytical conclusions without requiring any technical background. The glossary explains any unfamiliar terms.

**Technical reader:** Open `notebooks/reconciliation_audit.ipynb` - all cells run with outputs saved. The pipeline classification logic is in `pipeline/classify.py`.

**GitHub:** github.com/crystalolisa/payout-reconciliation-audit

**Data source:** Dune Analytics - publicly available on-chain data. Dashboard: [Distributed Reward Network - Payout Reconciliation Audit](https://dune.com/olisa/distributed-reward-network-payout-reconciliation)


## What Comes Next

This project asks: did the right transfers happen to the right wallets?

The next project moves up one layer - from transaction validation to payment product operations. Using on-chain data from a live stablecoin payments network, it asks: how is a consumer payment product actually being used across corridors and geographies, and where does operational friction surface in the spend pattern?

**Project 3 - Stablecoin Payment Operations Audit**
github.com/crystalolisa/stablecoin-payment-o *(in progress)*

## Tools

`Dune Analytics` `Python` `Pandas` `NumPy` `Matplotlib` `Jupyter` `Solana`


*Operational insight, built on data.*
[LinkedIn](https://linkedin.com/in/crystalolisa)
