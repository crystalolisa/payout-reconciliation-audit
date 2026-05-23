"""
pipeline/classify.py
Payout Reconciliation Audit - Classification Pipeline
Crystal Olisa - Operations Generalist - Diagnostic & Build

Reads the three Dune query CSVs from data/ and applies the four-class
reconciliation framework to produce audit_trail.csv.

Four classification classes:
    PASS             - consistent with programmatic epoch distribution pattern
    FLAG_large_transfer  - single transfer or daily value exceeds governance threshold
    FLAG_micro_transfer  - transfer below 1 GRASS, deduplication review required
    REVIEW_wallet_type   - wallet pattern inconsistent with participant distribution

Run:
    python pipeline/classify.py

Output:
    data/audit_trail.csv
    data/pipeline_run_log.csv (appended on every run)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

DAILY_VOLUME_FILE       = os.path.join(DATA_DIR, 'grass_daily_volume.csv')
DISTRIBUTION_FILE       = os.path.join(DATA_DIR, 'grass_transfer_distribution.csv')
WALLET_CONCENTRATION_FILE = os.path.join(DATA_DIR, 'grass_wallet_concentration.csv')

OUTPUT_FILE     = os.path.join(DATA_DIR, 'audit_trail.csv')
RUN_LOG_FILE    = os.path.join(DATA_DIR, 'pipeline_run_log.csv')

# Governance thresholds — derived from audit findings
# Threshold basis documented in README Next Steps section

LARGE_TRANSFER_THRESHOLD_TOKENS = 1_000_000      # single transfer flag
DAILY_VOLUME_MULTIPLIER         = 3.0             # x rolling average = treasury event flag
ROLLING_WINDOW_DAYS             = 30
ANOMALOUS_WALLET_MAX_ACTIVE_DAYS = 30             # short window + large value = review
ANOMALOUS_WALLET_MIN_GRASS      = 10_000_000      # large value threshold for anomaly flag
INFRASTRUCTURE_TIMES_RECEIVED   = 100_000         # very high frequency = infrastructure wallet
MICRO_TRANSFER_THRESHOLD        = 1.0             # < 1 GRASS = micro-transfer


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data():
    print('Loading data...')
    daily    = pd.read_csv(DAILY_VOLUME_FILE, parse_dates=['payout_date'])
    dist     = pd.read_csv(DISTRIBUTION_FILE)
    wallets  = pd.read_csv(WALLET_CONCENTRATION_FILE,
                           parse_dates=['first_receipt', 'last_receipt'])
    print(f'  Daily volume:        {len(daily):,} rows')
    print(f'  Transfer distribution: {len(dist):,} rows')
    print(f'  Wallet concentration: {len(wallets):,} rows')
    return daily, dist, wallets


# ---------------------------------------------------------------------------
# Phase 1 - Daily volume anomaly classification
# ---------------------------------------------------------------------------

def classify_daily_volume(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Flags days where total_grass_transferred exceeds 3x the 30-day rolling average.
    These are treasury-level events requiring separate governance documentation.
    Threshold basis: Query 1 anomaly analysis - March 10 and May 7 2026 identified
    as days with value concentration 10x the daily average.
    """
    daily = daily.sort_values('payout_date').copy()
    daily['rolling_avg'] = (
        daily['total_grass_transferred']
        .rolling(window=ROLLING_WINDOW_DAYS, min_periods=5)
        .mean()
        .shift(1)
    )
    daily['volume_ratio'] = daily['total_grass_transferred'] / daily['rolling_avg']

    def classify_day(row):
        if pd.isna(row['rolling_avg']):
            return 'INSUFFICIENT_HISTORY'
        if row['volume_ratio'] >= DAILY_VOLUME_MULTIPLIER:
            return 'FLAG_treasury_event'
        return 'PASS'

    daily['day_classification'] = daily.apply(classify_day, axis=1)

    flagged = daily[daily['day_classification'] == 'FLAG_treasury_event']
    print(f'\nDaily volume classification:')
    print(f'  Total days:          {len(daily):,}')
    print(f'  Treasury event flags: {len(flagged):,}')
    if len(flagged) > 0:
        print(f'  Flagged dates:')
        for _, row in flagged.iterrows():
            print(f'    {row["payout_date"].date()} - {row["total_grass_transferred"]:,.0f} GRASS '
                  f'({row["volume_ratio"]:.1f}x rolling avg)')

    return daily


# ---------------------------------------------------------------------------
# Phase 2 - Transfer size distribution classification
# ---------------------------------------------------------------------------

def classify_transfer_distribution(dist: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the two-track classification logic derived from the distribution finding:
    - Micro-transfers (< 1 GRASS): FLAG_micro_transfer - deduplication review
    - Large transfers (10K+ GRASS): FLAG_large_transfer - governance sign-off
    - Mid-range: PASS - standard epoch distribution pattern

    Finding basis: 51% of transfers by count move less than 0.1% of total value.
    One reconciliation process cannot handle both ends of this distribution.
    """
    def classify_bucket(row):
        bucket = row['transfer_bucket']
        if '< 1' in str(bucket) or '1.' in str(bucket):
            return 'FLAG_micro_transfer'
        if '10K+' in str(bucket) or '6.' in str(bucket):
            return 'FLAG_large_transfer'
        return 'PASS'

    dist = dist.copy()
    dist['bucket_classification'] = dist.apply(classify_bucket, axis=1)

    print(f'\nTransfer distribution classification:')
    for _, row in dist.iterrows():
        print(f'  {row["transfer_bucket"]:20s} - {row["bucket_classification"]:25s} '
              f'({row["pct_of_transfers"]:.2f}% of transfers, '
              f'{row["total_grass"]:,.0f} GRASS)')

    return dist


# ---------------------------------------------------------------------------
# Phase 3 - Wallet classification
# ---------------------------------------------------------------------------

def classify_wallets(wallets: pd.DataFrame) -> pd.DataFrame:
    """
    Distinguishes three operationally distinct wallet categories identified in Query 3:

    Category A - Programmatic epoch wallets (PASS):
        ~77,000-78,000 receipts, consistent amounts, January 1 2025 start date.
        This is the expected distribution pattern.

    Category B - Infrastructure wallets (REVIEW_wallet_type):
        Very high times_received (>100,000) or very large total with short active window.
        Almost certainly exchange hot wallets or treasury aggregators.
        Must be excluded from participant payout reports.

    Category C - Anomalous large-value wallets (REVIEW_wallet_type):
        High total GRASS received in very few transfers across a short active window.
        Correlates with treasury event days identified in Phase 1.
        Requires separate governance documentation.

    Threshold basis: Query 3 wallet concentration analysis.
    """
    wallets = wallets.copy()

    def classify_wallet(row):
        # Infrastructure: very high transfer frequency
        if row['times_received'] >= INFRASTRUCTURE_TIMES_RECEIVED:
            return 'REVIEW_wallet_type_infrastructure'

        # Anomalous: large value, short active window
        if (row['total_grass_received'] >= ANOMALOUS_WALLET_MIN_GRASS and
                row['active_days'] <= ANOMALOUS_WALLET_MAX_ACTIVE_DAYS):
            return 'REVIEW_wallet_type_anomalous'

        # Programmatic epoch pattern: ~77k receipts, long history
        if (70_000 <= row['times_received'] <= 85_000 and
                row['active_days'] >= 400):
            return 'PASS_epoch_distribution'

        return 'PASS'

    wallets['wallet_classification'] = wallets.apply(classify_wallet, axis=1)

    print(f'\nWallet classification:')
    summary = wallets['wallet_classification'].value_counts()
    for classification, count in summary.items():
        total_grass = wallets[wallets['wallet_classification'] == classification]['total_grass_received'].sum()
        print(f'  {classification:45s} {count:3d} wallets  {total_grass:>20,.0f} GRASS')

    return wallets


# ---------------------------------------------------------------------------
# Phase 4 - Build audit trail
# ---------------------------------------------------------------------------

def build_audit_trail(daily: pd.DataFrame,
                      dist: pd.DataFrame,
                      wallets: pd.DataFrame) -> pd.DataFrame:
    """
    Combines classifications from all three phases into a single audit trail.
    The audit trail records the classification decision, the basis for it,
    and the timestamp — structured for governance review.
    """
    audit_rows = []
    run_timestamp = datetime.utcnow().isoformat()

    # Daily volume flags
    flagged_days = daily[daily['day_classification'] == 'FLAG_treasury_event']
    for _, row in flagged_days.iterrows():
        audit_rows.append({
            'record_type':        'daily_volume',
            'identifier':         str(row['payout_date'].date()),
            'classification':     row['day_classification'],
            'basis':              f'Daily value {row["volume_ratio"]:.1f}x 30-day rolling average '
                                  f'(threshold: {DAILY_VOLUME_MULTIPLIER}x). '
                                  f'Total: {row["total_grass_transferred"]:,.0f} GRASS.',
            'operational_action': 'Hold for governance sign-off. '
                                  'Document: who authorised, what it was for, audit trail.',
            'audit_timestamp':    run_timestamp,
        })

    # Distribution flags
    flagged_buckets = dist[dist['bucket_classification'] != 'PASS']
    for _, row in flagged_buckets.iterrows():
        audit_rows.append({
            'record_type':        'transfer_bucket',
            'identifier':         row['transfer_bucket'],
            'classification':     row['bucket_classification'],
            'basis':              f'{row["transfer_count"]:,} transfers ({row["pct_of_transfers"]:.2f}% of total). '
                                  f'Total value: {row["total_grass"]:,.0f} GRASS.',
            'operational_action': ('Batch and deduplicate before financial reporting runs.'
                                   if 'micro' in row['bucket_classification']
                                   else 'Route to manual governance sign-off before processing.'),
            'audit_timestamp':    run_timestamp,
        })

    # Wallet flags
    flagged_wallets = wallets[wallets['wallet_classification'].str.startswith('REVIEW')]
    for _, row in flagged_wallets.iterrows():
        audit_rows.append({
            'record_type':        'wallet',
            'identifier':         row['wallet_address'],
            'classification':     row['wallet_classification'],
            'basis':              f'{row["times_received"]:,} receipts over {row["active_days"]} active days. '
                                  f'Total received: {row["total_grass_received"]:,.0f} GRASS.',
            'operational_action': ('Classify and exclude from participant payout report before totals are calculated.'
                                   if 'infrastructure' in row['wallet_classification']
                                   else 'Cross-reference against treasury event days. '
                                        'Require governance documentation before including in any report.'),
            'audit_timestamp':    run_timestamp,
        })

    audit_trail = pd.DataFrame(audit_rows)
    audit_trail.to_csv(OUTPUT_FILE, index=False)
    print(f'\nAudit trail exported: {OUTPUT_FILE}')
    print(f'  Total flagged records: {len(audit_trail):,}')

    return audit_trail


# ---------------------------------------------------------------------------
# Run log
# ---------------------------------------------------------------------------

def append_run_log(audit_trail: pd.DataFrame,
                   daily: pd.DataFrame,
                   wallets: pd.DataFrame):
    run_timestamp = datetime.utcnow().isoformat()
    log_row = pd.DataFrame([{
        'run_timestamp':            run_timestamp,
        'daily_volume_rows':        len(daily),
        'treasury_event_flags':     len(daily[daily['day_classification'] == 'FLAG_treasury_event']),
        'wallet_rows':              len(wallets),
        'wallet_review_flags':      len(wallets[wallets['wallet_classification'].str.startswith('REVIEW')]),
        'total_audit_flags':        len(audit_trail),
    }])

    if os.path.exists(RUN_LOG_FILE):
        existing = pd.read_csv(RUN_LOG_FILE)
        log = pd.concat([existing, log_row], ignore_index=True)
    else:
        log = log_row

    log.to_csv(RUN_LOG_FILE, index=False)
    print(f'Run log updated: {RUN_LOG_FILE}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('=' * 60)
    print('PAYOUT RECONCILIATION AUDIT - CLASSIFICATION PIPELINE')
    print('=' * 60)
    print(f'Run timestamp: {datetime.utcnow().isoformat()}')

    daily, dist, wallets = load_data()
    daily   = classify_daily_volume(daily)
    dist    = classify_transfer_distribution(dist)
    wallets = classify_wallets(wallets)
    audit_trail = build_audit_trail(daily, dist, wallets)
    append_run_log(audit_trail, daily, wallets)

    print('\n' + '=' * 60)
    print('OPS SUMMARY - PAYOUT RECONCILIATION AUDIT')
    print('=' * 60)
    print(f'Daily volume rows analysed:    {len(daily):,}')
    print(f'Treasury event flags:          '
          f'{len(daily[daily["day_classification"] == "FLAG_treasury_event"]):,}')
    print(f'Wallet records analysed:       {len(wallets):,}')
    print(f'Wallet review flags:           '
          f'{len(wallets[wallets["wallet_classification"].str.startswith("REVIEW")]):,}')
    print(f'Total audit trail records:     {len(audit_trail):,}')
    print()
    print('PRIMARY FINDING:')
    print('  51% of transfers by count move less than 0.1% of total value.')
    print('  Two ends of the distribution require completely different')
    print('  operational responses - micro-transfers need deduplication,')
    print('  large transfers need governance sign-off before execution.')
    print()
    print(f'Source: {OUTPUT_FILE}')
    print('=' * 60)


if __name__ == '__main__':
    main()
