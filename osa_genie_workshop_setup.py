# Databricks notebook source
# MAGIC %md
# MAGIC # NC OSA Genie Workshop: setup
# MAGIC
# MAGIC Run this notebook **once** before the workshop. It builds a synthetic purchasing card (P-card) dataset and a Genie Agent
# MAGIC called **OSA P-Card Review (Workshop)** that the business users follow along with.
# MAGIC
# MAGIC **What it creates**
# MAGIC - Schema `<catalog>.osa_pcard_review` with 6 tables, each with table and column descriptions
# MAGIC - The Genie Agent, with instructions, a few example queries and suggested questions
# MAGIC - Optional: read access on the schema and CAN RUN on the agent for a group you name
# MAGIC
# MAGIC **How to run:** fill in `catalog` (a catalog where you can create a schema), leave `warehouse_id` blank to auto-pick a SQL warehouse,
# MAGIC optionally set `share_with_group` to the business users' group, then **Run all**. It takes a few minutes on serverless.
# MAGIC Re-running is safe: same seed, same numbers, and the agent is updated in place.
# MAGIC
# MAGIC All data is synthetic and for training only. No figure is real, and nothing here is an OSA finding.

# COMMAND ----------

dbutils.widgets.text("catalog", "", "Catalog (required)")
dbutils.widgets.text("schema", "osa_pcard_review", "Schema")
dbutils.widgets.text("warehouse_id", "", "SQL warehouse ID (blank = auto)")
dbutils.widgets.text("share_with_group", "", "Group to share with (optional)")
dbutils.widgets.text("agent_title", "OSA P-Card Review (Workshop)", "Genie Agent title")

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA = dbutils.widgets.get("schema").strip() or "osa_pcard_review"
WAREHOUSE_ID = dbutils.widgets.get("warehouse_id").strip()
SHARE_GROUP = dbutils.widgets.get("share_with_group").strip()
AGENT_TITLE = dbutils.widgets.get("agent_title").strip() or "OSA P-Card Review (Workshop)"

if not CATALOG:
    raise ValueError("Set the 'catalog' widget to a catalog where you can create a schema, then Run all again.")
FQ = f"`{CATALOG}`.`{SCHEMA}`"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FQ} COMMENT 'Synthetic NC state purchasing card data for the OSA Genie workshop. Training only.'")
print(f"Catalog : {CATALOG}\nSchema  : {SCHEMA}")

# COMMAND ----------

# MAGIC %md ## 1. Generate the synthetic data

# COMMAND ----------

import random, math
from datetime import date, datetime, timedelta

rng = random.Random(20261110)
START, END = date(2024, 7, 1), date(2026, 6, 30)   # FY2025 and FY2026; data is as of June 30, 2026

def fiscal_year(d):
    return d.year + 1 if d.month >= 7 else d.year

def fiscal_quarter(d):
    return f"Q{((d.month - 7) % 12) // 3 + 1}"

def month_end(y, m):
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return nxt - timedelta(days=1)

AGENCIES = [  # fictional agencies: code, name, share of cardholders, missing-receipt rate
    ("DRB", "Department of Roads and Bridges", 0.20, 0.05),
    ("DCH", "Department of Community Health", 0.16, 0.07),
    ("DPP", "Department of Public Protection", 0.10, 0.14),
    ("DRS", "Department of Rehabilitation Services", 0.08, 0.09),
    ("DLW", "Department of Land and Water", 0.07, 0.04),
    ("DHA", "Department of Heritage and the Arts", 0.07, 0.06),
    ("DFF", "Department of Farms and Food", 0.06, 0.05),
    ("DDS", "Department of Digital Services", 0.06, 0.03),
    ("DGS", "Department of General Services", 0.05, 0.04),
    ("DTF", "Department of Taxation and Finance", 0.05, 0.03),
    ("DLE", "Department of Learning and Education", 0.05, 0.08),
    ("DED", "Department of Economic Development", 0.05, 0.06),
]
AG_CODES = [a[0] for a in AGENCIES]
AG_W = [a[2] for a in AGENCIES]
RECEIPT_MISS = {a[0]: a[3] for a in AGENCIES}

MCCS = [  # mcc, description, group, blocked, typical amount, merchants
    ("5943", "Office and School Supply Stores", "Office supplies", False, 85, ["OfficePlus Supply", "Paper and Pen Co", "Triangle Office Supply"]),
    ("5111", "Stationery and Office Supplies", "Office supplies", False, 120, ["Capital Stationers", "Carolina Business Forms"]),
    ("5942", "Book Stores", "Office supplies", False, 60, ["Online Marketplace", "Campus Bookstore"]),
    ("5200", "Home Supply Warehouse Stores", "Facilities and maintenance", False, 180, ["Builders Warehouse", "HomePro Supply"]),
    ("5251", "Hardware Stores", "Facilities and maintenance", False, 75, ["Main Street Hardware", "Farm and Feed Supply"]),
    ("5085", "Industrial Supplies", "Facilities and maintenance", False, 340, ["Piedmont Industrial", "Fastener Depot", "MRO Supply Co"]),
    ("5541", "Service Stations", "Fuel and vehicles", False, 55, ["QuickFuel", "Highway Gas", "Corner Mart Fuel"]),
    ("7523", "Parking Lots and Garages", "Fuel and vehicles", False, 18, ["City Center Parking", "Garage Park"]),
    ("7011", "Hotels and Lodging", "Travel", False, 210, ["Capitol Suites Hotel", "Coastal Inn", "Mountain View Lodge"]),
    ("4511", "Airlines", "Travel", False, 380, ["Southern Air", "Atlantic Airways"]),
    ("4121", "Taxi and Rideshare", "Travel", False, 32, ["RideNow", "City Cab"]),
    ("5812", "Restaurants", "Meals", False, 45, ["Local Restaurant", "Catering Works", "Bread and Bowl Cafe"]),
    ("4816", "Computer Network Services", "Technology", False, 160, ["CloudMeet", "SoftSuite Online", "DesignApps"]),
    ("5734", "Computer Software Stores", "Technology", False, 420, ["GovTech Software", "Enterprise License Co"]),
    ("5047", "Medical and Dental Supplies", "Medical supplies", False, 260, ["MedSupply Direct", "Clinic Supply Co"]),
    ("8299", "Schools and Educational Services", "Training", False, 450, ["Public Service Training Institute", "Online Learning Co"]),
    ("7399", "Business Services", "Business services", False, 230, ["Print and Ship Center", "Records Storage Co"]),
    ("5999", "Miscellaneous Retail", "Other retail", False, 70, ["SuperMart", "Value Club", "General Store"]),
    ("5813", "Bars and Taverns", "Blocked", True, 65, ["Downtown Taproom", "Corner Pub"]),
    ("5921", "Package Stores, Beer, Wine and Liquor", "Blocked", True, 80, ["Package Store", "Wine and Spirits Outlet"]),
    ("7995", "Betting and Casino Gambling", "Blocked", True, 150, ["Riverboat Casino", "Online Gaming Co"]),
    ("5993", "Cigar Stores and Tobacco", "Blocked", True, 40, ["Corner Smoke Shop"]),
    ("6011", "ATM Cash Withdrawal", "Blocked", True, 200, ["ATM Withdrawal"]),
    ("5094", "Jewelry and Precious Metals", "Blocked", True, 420, ["Main Street Jewelers", "Gold and Gem"]),
    ("7997", "Clubs and Country Clubs", "Blocked", True, 300, ["Lakeside Country Club"]),
]
ALLOWED = [m for m in MCCS if not m[3]]
BLOCKED = [m for m in MCCS if m[3]]
ALLOWED_W = [9, 3, 3, 6, 4, 4, 8, 2, 4, 1, 2, 4, 3, 2, 2, 1, 2, 4]
# FY2026 mix shifts toward technology, travel, training and medical supplies, so category growth questions have a story
GROWTH = {"4816": 1.5, "5734": 1.6, "7011": 1.3, "4511": 1.4, "8299": 1.5, "5047": 1.4, "5943": 0.85, "5111": 0.85}
ALLOWED_W_FY26 = [w * GROWTH.get(m[0], 1.0) for m, w in zip(ALLOWED, ALLOWED_W)]

FIRST = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara",
         "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Daniel", "Lisa", "Matthew", "Nancy",
         "Anthony", "Betty", "Mark", "Sandra", "Donald", "Ashley", "Steven", "Kimberly", "Andrew", "Emily", "Kenneth", "Donna",
         "Joshua", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "Timothy", "Melissa", "Jason", "Deborah", "Jeffrey", "Laura"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Moore", "Taylor", "Thomas",
        "Jackson", "White", "Harris", "Martin", "Thompson", "Lee", "Walker", "Hall", "Allen", "Young", "King", "Wright", "Scott",
        "Green", "Baker", "Adams", "Nelson", "Hill", "Campbell", "Mitchell", "Roberts", "Carter", "Phillips", "Evans", "Turner",
        "Parker", "Collins", "Edwards", "Stewart", "Morris", "Murphy", "Cook", "Rogers", "Morgan", "Cooper", "Peterson"]
TITLES = ["Administrative Specialist", "Program Manager", "Maintenance Technician", "Field Supervisor", "Office Manager",
          "IT Specialist", "Engineer", "Social Worker", "Procurement Specialist", "Facility Manager", "Research Analyst"]

# ---- cardholders ----
cardholders = []
N_CARDS = 1800
for i in range(1, N_CARDS + 1):
    ag = rng.choices(AG_CODES, AG_W)[0]
    spl = rng.choices([1000, 2500, 5000, 10000], [3, 5, 3, 1])[0]
    issued = START - timedelta(days=rng.randint(30, 2500))
    cardholders.append(dict(card_id=f"C{i:05d}", agency_code=ag, cardholder_name=f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                            job_title=rng.choice(TITLES), single_purchase_limit=float(spl), monthly_limit=float(spl * rng.choice([3, 5])),
                            issued_date=issued, employee_status="Active", termination_date=None, card_status="Active", card_closed_date=None,
                            approver_name=f"{rng.choice(FIRST)} {rng.choice(LAST)}"))
idx = list(range(N_CARDS)); rng.shuffle(idx)
terminated_closed = idx[:70]          # left the state, card closed properly
terminated_open = idx[70:115]         # left the state, card never closed (planted)
dormant = set(idx[115:340])           # no activity after March 2026 (planted)
night_owls = set(idx[340:355])        # unusual share of off-hours purchases (planted)
for k in terminated_closed + terminated_open:
    c = cardholders[k]
    td = START + timedelta(days=rng.randint(200, 640))
    c.update(employee_status="Terminated", termination_date=td)
    if k in terminated_closed:
        c.update(card_status="Closed", card_closed_date=td + timedelta(days=rng.randint(0, 10)))
keep_spending = set(terminated_open[:30])   # 30 of the open cards keep being used after termination

# ---- transactions ----
tx = []
def add_tx(c, d, mcc, amount, hour=None):
    if hour is None:
        hour = rng.choices([rng.randint(7, 17), rng.randint(18, 21), rng.choice([22, 23, 0, 1, 2, 3, 4])], [93, 6, 1])[0]
    ts = datetime(d.year, d.month, d.day, hour, rng.randint(0, 59), rng.randint(0, 59))
    miss = RECEIPT_MISS[c["agency_code"]] * (0.8 if fiscal_year(d) == 2026 and c["agency_code"] in ("DRB", "DDS", "DLW") else 1.0)
    miss *= 1.25 if fiscal_year(d) == 2026 and c["agency_code"] in ("DPP", "DLE") else 1.0
    tx.append(dict(card_id=c["card_id"], agency_code=c["agency_code"], transaction_ts=ts, transaction_date=d,
                   fiscal_year=fiscal_year(d), fiscal_quarter=fiscal_quarter(d), merchant_name=rng.choice(mcc[5]), mcc=mcc[0],
                   amount=round(amount, 2), receipt_attached=rng.random() > miss))

def rand_amount(mcc, cap):
    a = math.exp(rng.gauss(math.log(mcc[4]), 0.75))
    return max(3.0, min(a, cap * 0.95))

def random_day(y, m, weekend_ok=False):
    last = month_end(y, m).day
    for _ in range(20):
        d = date(y, m, rng.randint(1, last))
        if d.weekday() < 5 or weekend_ok:
            return d
    return d

months = [(y, m) for y in (2024, 2025, 2026) for m in range(1, 13) if START <= date(y, m, 1) <= END]
for k, c in enumerate(cardholders):
    rate = rng.uniform(1.5, 7.5)
    for (y, m) in months:
        ms = date(y, m, 1)
        if c["card_closed_date"] and ms > c["card_closed_date"]:
            break
        if k in dormant and ms >= date(2026, 4, 1):
            break
        r = rate
        if c["termination_date"] and ms > c["termination_date"]:
            if k not in keep_spending:
                break
            r = rate * 0.5
        n = sum(1 for _ in range(int(r * 2)) if rng.random() < 0.5)
        fy26 = ms >= date(2025, 7, 1)
        n = int(n * (1.18 if fy26 else 1.0))
        for _ in range(n):
            mcc = rng.choices(ALLOWED, ALLOWED_W_FY26 if fy26 else ALLOWED_W)[0]
            weekend = rng.random() < (0.30 if k in night_owls else 0.02)
            d = random_day(y, m, weekend_ok=weekend)
            hour = rng.choice([22, 23, 0, 1, 2, 3, 4]) if (k in night_owls and rng.random() < 0.25) else None
            if c["termination_date"] and d > c["termination_date"] and k not in keep_spending:
                continue
            add_tx(c, d, mcc, rand_amount(mcc, c["single_purchase_limit"]), hour)

# planted: purchases at blocked merchant categories
active_cards = [c for c in cardholders if c["card_status"] == "Active"]
for _ in range(190):
    c = rng.choice(active_cards); mcc = rng.choice(BLOCKED); y, m = rng.choice(months)
    add_tx(c, random_day(y, m, weekend_ok=rng.random() < 0.4), mcc, rand_amount(mcc, c["single_purchase_limit"]))

# planted: split purchases (same card, same merchant, same day, combined total over the single-purchase limit)
split_mccs = [m for m in ALLOWED if m[0] in ("5085", "5200", "5734", "5943", "5047")]
for _ in range(75):
    c = rng.choice(active_cards); mcc = rng.choice(split_mccs); y, m = rng.choice(months)
    d = random_day(y, m); merchant = rng.choice(mcc[5]); lim = c["single_purchase_limit"]
    parts = rng.choice([2, 2, 2, 3])
    for p in range(parts):
        amt = round(lim * rng.uniform(0.62, 0.97), 2)
        ts = datetime(d.year, d.month, d.day, rng.randint(9, 16), rng.randint(0, 59), rng.randint(0, 59))
        tx.append(dict(card_id=c["card_id"], agency_code=c["agency_code"], transaction_ts=ts, transaction_date=d, fiscal_year=fiscal_year(d),
                       fiscal_quarter=fiscal_quarter(d), merchant_name=merchant, mcc=mcc[0], amount=amt,
                       receipt_attached=rng.random() > RECEIPT_MISS[c["agency_code"]]))

tx.sort(key=lambda t: (t["transaction_ts"], t["card_id"]))
for i, t in enumerate(tx, 1):
    t["transaction_id"] = f"T{i:07d}"
print(f"cardholders: {len(cardholders):,}  transactions: {len(tx):,}")

# ---- monthly statements ----
by_card_month = {}
for t in tx:
    key = (t["card_id"], t["transaction_date"].year, t["transaction_date"].month)
    s = by_card_month.setdefault(key, [0.0, 0])
    s[0] += t["amount"]; s[1] += 1
card_by_id = {c["card_id"]: c for c in cardholders}
statements = []
for i, ((cid, y, m), (total, n)) in enumerate(sorted(by_card_month.items()), 1):
    c = card_by_id[cid]; sd = month_end(y, m)
    recent = sd >= date(2026, 5, 1)
    p_unrec = 0.35 if sd == date(2026, 6, 30) else 0.18 if recent else 0.04 * (1.8 if c["agency_code"] in ("DPP", "DRS") else 1)
    if rng.random() < p_unrec:
        rec, rd, days = False, None, None
    else:
        days = rng.randint(3, 28) if rng.random() < (0.80 if c["agency_code"] in ("DPP", "DRS", "DLE") else 0.90) else rng.randint(31, 90)
        rd = sd + timedelta(days=days)
        if rd > END:
            rec, rd, days = False, None, None
        else:
            rec = True
    statements.append(dict(statement_id=f"S{i:06d}", card_id=cid, agency_code=c["agency_code"], statement_month=date(y, m, 1), statement_date=sd,
                           fiscal_year=fiscal_year(sd), statement_total=round(total, 2), transaction_count=n, reconciled=rec,
                           reconciled_date=rd, days_to_reconcile=days, approver_name=c["approver_name"]))

# ---- budgets ----
spend = {}
for t in tx:
    spend[(t["agency_code"], t["fiscal_year"])] = spend.get((t["agency_code"], t["fiscal_year"]), 0) + t["amount"]
over = {"DPP", "DCH", "DLE"}
budgets = []
for code, name, _, _ in AGENCIES:
    for fy in (2025, 2026):
        base = spend.get((code, fy), 0)
        factor = rng.uniform(0.88, 0.97) if (fy == 2026 and code in over) else rng.uniform(1.04, 1.25)
        budgets.append(dict(agency_code=code, fiscal_year=fy, pcard_budget=float(round(base * factor, -3))))

# COMMAND ----------

# MAGIC %md ## 2. Write the tables with descriptions Genie can read

# COMMAND ----------

from pyspark.sql import types as T

MARKER = "osa_genie_workshop"
sql_str = lambda text: text.replace("\\", "\\\\").replace("'", "\\'")

# Refuse to overwrite tables this notebook didn't create, so pointing it at a busy schema can't destroy real data.
existing_tables = {r.tableName for r in spark.sql(f"SHOW TABLES IN {FQ}").collect()}
for name in ["agencies", "agency_budgets", "cardholders", "merchant_categories", "transactions", "monthly_statements"]:
    if name in existing_tables:
        props = {r.key: r.value for r in spark.sql(f"SHOW TBLPROPERTIES {FQ}.`{name}`").collect()}
        if props.get(MARKER) != "true":
            raise ValueError(f"{CATALOG}.{SCHEMA}.{name} already exists and was not created by this notebook. Pick a different schema.")

def write(name, rows, schema, table_comment, col_comments):
    df = spark.createDataFrame(rows, schema)
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.`{name}`")
    spark.sql(f"ALTER TABLE {FQ}.`{name}` SET TBLPROPERTIES ('{MARKER}' = 'true')")
    spark.sql(f"COMMENT ON TABLE {FQ}.`{name}` IS '{sql_str(table_comment)}'")
    for col, text in col_comments.items():
        spark.sql(f"ALTER TABLE {FQ}.`{name}` ALTER COLUMN `{col}` COMMENT '{sql_str(text)}'")
    print(f"  {name}: {df.count():,} rows")

S, D, F, I, B, TS = T.StringType(), T.DateType(), T.DoubleType(), T.IntegerType(), T.BooleanType(), T.TimestampNTZType()  # local wall-clock time, no timezone shift
st = lambda *cols: T.StructType([T.StructField(n, t, True) for n, t in cols])

write("agencies", [dict(agency_code=a[0], agency_name=a[1]) for a in AGENCIES], st(("agency_code", S), ("agency_name", S)),
      "State agencies that participate in the P-card program. One row per agency.",
      {"agency_code": "Short agency code, for example DRB or DCH. Joins to every other table.",
       "agency_name": "Full agency name."})

write("agency_budgets", budgets, st(("agency_code", S), ("fiscal_year", I), ("pcard_budget", F)),
      "Annual P-card budget per agency per NC fiscal year (July 1 to June 30). One row per agency per fiscal year.",
      {"agency_code": "Agency code. Joins to agencies.agency_code.",
       "fiscal_year": "NC fiscal year, named for the year it ends. FY2026 = July 1, 2025 to June 30, 2026.",
       "pcard_budget": "Budgeted P-card spend for the agency for the fiscal year, in US dollars."})

write("cardholders", cardholders,
      st(("card_id", S), ("agency_code", S), ("cardholder_name", S), ("job_title", S), ("single_purchase_limit", F), ("monthly_limit", F),
         ("issued_date", D), ("employee_status", S), ("termination_date", D), ("card_status", S), ("card_closed_date", D), ("approver_name", S)),
      "One row per purchasing card and the employee it is issued to.",
      {"card_id": "Unique card identifier. Joins to transactions and monthly_statements.",
       "agency_code": "Agency the cardholder works for.",
       "cardholder_name": "Employee the card is issued to (synthetic name).",
       "job_title": "Cardholder job title.",
       "single_purchase_limit": "Maximum dollar amount allowed for a single purchase on this card.",
       "monthly_limit": "Maximum total dollars allowed on this card per calendar month.",
       "issued_date": "Date the card was issued.",
       "employee_status": "Active or Terminated. Terminated means the employee has left state employment.",
       "termination_date": "Date the employee left state employment. Null if still employed. Any purchase after this date is a red flag.",
       "card_status": "Active or Closed. A Terminated employee whose card is still Active is a control failure.",
       "card_closed_date": "Date the card was closed. Null if the card is still active.",
       "approver_name": "Supervisor who approves the cardholder statements."})

write("merchant_categories", [dict(mcc=m[0], mcc_description=m[1], category_group=m[2], is_blocked=m[3]) for m in MCCS],
      st(("mcc", S), ("mcc_description", S), ("category_group", S), ("is_blocked", B)),
      "Merchant category codes (MCC) and whether card policy blocks them. One row per MCC.",
      {"mcc": "Four-digit merchant category code. Joins to transactions.mcc.",
       "mcc_description": "Standard description of the merchant category.",
       "category_group": "Plain-English grouping used for reporting, for example Office supplies or Travel.",
       "is_blocked": "True if card policy prohibits purchases in this category (for example bars, liquor, gambling, cash withdrawals)."})

write("transactions", tx,
      st(("transaction_id", S), ("card_id", S), ("agency_code", S), ("transaction_ts", TS), ("transaction_date", D), ("fiscal_year", I),
         ("fiscal_quarter", S), ("merchant_name", S), ("mcc", S), ("amount", F), ("receipt_attached", B)),
      "One row per P-card purchase, July 1, 2024 through June 30, 2026 (FY2025 and FY2026).",
      {"transaction_id": "Unique purchase identifier.",
       "card_id": "Card used. Joins to cardholders.card_id.",
       "agency_code": "Agency of the cardholder.",
       "transaction_ts": "Date and local time of the purchase. Use for weekend and off-hours checks.",
       "transaction_date": "Date of the purchase.",
       "fiscal_year": "NC fiscal year of the purchase, named for the year it ends. FY2026 = July 1, 2025 to June 30, 2026.",
       "fiscal_quarter": "Fiscal quarter: Q1 = Jul-Sep, Q2 = Oct-Dec, Q3 = Jan-Mar, Q4 = Apr-Jun.",
       "merchant_name": "Merchant where the purchase was made.",
       "mcc": "Merchant category code. Joins to merchant_categories.mcc.",
       "amount": "Purchase amount in US dollars.",
       "receipt_attached": "True if an itemized receipt is attached to the purchase. False means the receipt is missing."})

write("monthly_statements", statements,
      st(("statement_id", S), ("card_id", S), ("agency_code", S), ("statement_month", D), ("statement_date", D), ("fiscal_year", I),
         ("statement_total", F), ("transaction_count", I), ("reconciled", B), ("reconciled_date", D), ("days_to_reconcile", I), ("approver_name", S)),
      "One row per card per month with activity: the monthly statement and whether it has been reconciled and approved.",
      {"statement_id": "Unique statement identifier.",
       "card_id": "Card the statement belongs to.",
       "agency_code": "Agency of the cardholder.",
       "statement_month": "First day of the statement month.",
       "statement_date": "Statement closing date (last day of the month).",
       "fiscal_year": "NC fiscal year of the statement date.",
       "statement_total": "Total dollars on the statement.",
       "transaction_count": "Number of purchases on the statement.",
       "reconciled": "True if the cardholder reconciled the statement and the approver signed off.",
       "reconciled_date": "Date the statement was reconciled. Null if not yet reconciled.",
       "days_to_reconcile": "Days from statement date to reconciliation. Policy expects 30 days or fewer. Null if not reconciled.",
       "approver_name": "Supervisor who approves the statement."})

# COMMAND ----------

# MAGIC %md ## 3. Create or update the Genie Agent

# COMMAND ----------

import json, uuid
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
api = w.api_client

if not WAREHOUSE_ID:
    whs = list(w.warehouses.list())
    whs.sort(key=lambda x: (str(x.state) != "State.RUNNING", not bool(x.enable_serverless_compute)))
    if not whs:
        raise ValueError("No SQL warehouse found. Set the warehouse_id widget.")
    WAREHOUSE_ID = whs[0].id
print(f"Warehouse: {WAREHOUSE_ID}")

def lines(text):
    parts = text.strip("\n").split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]

def tid(name):  # stable ids so re-runs update in place
    return uuid.uuid5(uuid.NAMESPACE_URL, f"osa-genie-workshop/{name}").hex

t = lambda name: f"{CATALOG}.{SCHEMA}.{name}"
q = lambda name: f"`{CATALOG}`.`{SCHEMA}`.`{name}`"

INSTRUCTIONS = f"""
This agent covers synthetic North Carolina state purchasing card (P-card) activity for FY2025 and FY2026. It is used to train auditors at the NC Office of the State Auditor. All data is synthetic.

Definitions:
- Fiscal year (FY) is the NC fiscal year, July 1 to June 30, named for the year it ends. FY2026 = July 1, 2025 to June 30, 2026. Use the fiscal_year columns.
- The data is as of June 30, 2026. "Today", "current" and "last N days" are relative to 2026-06-30, not the real current date.
- Split purchase: two or more transactions on the same card, at the same merchant, on the same day, where each is at or under the card's single_purchase_limit but the combined total is over it.
- Purchase after termination: a transaction on a card where cardholders.termination_date is not null and transactions.transaction_date > termination_date.
- Blocked merchant category: merchant_categories.is_blocked = TRUE.
- Off-hours: a transaction on a Saturday or Sunday, or with a time from 10 PM to before 5 AM (hour of transaction_ts >= 22 or < 5).
- Missing receipt: transactions.receipt_attached = FALSE. Receipt rate or missing-receipt rate is a share of transactions.
- Late reconciliation: monthly_statements.days_to_reconcile > 30. Unreconciled: reconciled = FALSE. Age of an unreconciled statement = days from statement_date to 2026-06-30.
- Inactive or dormant card: card_status = 'Active' with no transactions in the 90 days ending 2026-06-30.
- Red flags for a cardholder: count of split purchase groups, purchases after termination, blocked category purchases, off-hours purchases and missing receipts.

Rules:
- Show agency_name with agency_code when grouping by agency.
- Show dollar amounts rounded to cents and percentages to one decimal place.
- When listing transactions, include transaction_date, cardholder_name, agency_code, merchant_name and amount.
"""

EXAMPLES = [
    ("Find possible split purchases: same cardholder, same merchant, same day, where the combined total is over the card's single-purchase limit.", f"""
SELECT c.card_id, c.cardholder_name, c.agency_code, t.merchant_name, t.transaction_date,
       COUNT(*) AS purchases, ROUND(SUM(t.amount), 2) AS combined_total, c.single_purchase_limit
FROM {q('transactions')} t
JOIN {q('cardholders')} c ON t.card_id = c.card_id
GROUP BY c.card_id, c.cardholder_name, c.agency_code, t.merchant_name, t.transaction_date, c.single_purchase_limit
HAVING COUNT(*) >= 2 AND MAX(t.amount) <= c.single_purchase_limit AND SUM(t.amount) > c.single_purchase_limit
ORDER BY combined_total DESC"""),
    ("Which transactions were made on a card after the cardholder's termination date?", f"""
SELECT t.transaction_id, t.transaction_date, c.cardholder_name, c.agency_code, c.termination_date, c.card_status,
       t.merchant_name, t.amount
FROM {q('transactions')} t
JOIN {q('cardholders')} c ON t.card_id = c.card_id
WHERE c.termination_date IS NOT NULL AND t.transaction_date > c.termination_date
ORDER BY t.transaction_date"""),
    ("What share of monthly statements were reconciled within 30 days of the statement date, by agency?", f"""
SELECT s.agency_code, a.agency_name, COUNT(*) AS statements,
       ROUND(100 * AVG(CASE WHEN s.reconciled AND s.days_to_reconcile <= 30 THEN 1 ELSE 0 END), 1) AS pct_reconciled_within_30_days
FROM {q('monthly_statements')} s
JOIN {q('agencies')} a ON s.agency_code = a.agency_code
GROUP BY s.agency_code, a.agency_name
ORDER BY pct_reconciled_within_30_days"""),
]

SAMPLE_QUESTIONS = [
    "What was total P-card spend by agency in FY2026?",
    "Which agencies have the highest rate of transactions missing a receipt in FY2026?",
    "Which transactions were made on a card after the cardholder's termination date?",
    "Show monthly P-card spend for FY2026 as a line chart.",
    "Compare each agency's FY2026 P-card spend with its annual P-card budget.",
]

space = {
    "version": 2,
    "config": {"sample_questions": sorted([{"id": tid("sq/" + s), "question": [s]} for s in SAMPLE_QUESTIONS], key=lambda x: x["id"])},
    "data_sources": {"tables": sorted([{"identifier": t(n)} for n in
                     ["agencies", "agency_budgets", "cardholders", "merchant_categories", "monthly_statements", "transactions"]],
                     key=lambda x: x["identifier"])},
    "instructions": {
        "text_instructions": [{"id": tid("instructions"), "content": lines(INSTRUCTIONS)}],
        "example_question_sqls": sorted([{"id": tid("ex/" + qq), "question": [qq], "sql": lines(sql)} for qq, sql in EXAMPLES],
                                        key=lambda x: x["id"]),
    },
}
DESCRIPTION = ("Synthetic NC state purchasing card (P-card) activity for FY2025 and FY2026, for the OSA Genie workshop. "
               "Ask about spend, receipts, reconciliations, budgets, split purchases, terminated cardholders and blocked merchants. Training data only.")

# The agent's ID is saved on the schema, so re-runs update this notebook's own agent and never touch anyone else's.
existing = (w.schemas.get(f"{CATALOG}.{SCHEMA}").properties or {}).get("genie_space_id")
if existing:
    try:
        api.do("GET", f"/api/2.0/genie/spaces/{existing}")
    except Exception:
        print(f"Saved agent {existing} no longer exists or isn't accessible. Creating a new one.")
        existing = None

body = {"title": AGENT_TITLE, "description": DESCRIPTION, "warehouse_id": WAREHOUSE_ID, "serialized_space": json.dumps(space)}
if existing:
    # Leave the title alone on update, so a rename in the UI isn't undone and names never collide.
    api.do("PATCH", f"/api/2.0/genie/spaces/{existing}", body={k: v for k, v in body.items() if k != "title"})
    SPACE_ID = existing
    print(f"Updated Genie Agent: {AGENT_TITLE}")
else:
    me = w.current_user.me().user_name
    body["parent_path"] = f"/Workspace/Users/{me}"
    SPACE_ID = api.do("POST", "/api/2.0/genie/spaces", body=body)["space_id"]
    spark.sql(f"ALTER SCHEMA {FQ} SET DBPROPERTIES ('genie_space_id' = '{SPACE_ID}')")
    print(f"Created Genie Agent: {AGENT_TITLE}")
host = w.config.host.rstrip("/")
print(f"Open it: {host}/genie/rooms/{SPACE_ID}")

# COMMAND ----------

# MAGIC %md ## 4. Optional: share with the business users

# COMMAND ----------

if SHARE_GROUP:
    for stmt in [f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO `{SHARE_GROUP}`",
                 f"GRANT USE SCHEMA, SELECT ON SCHEMA {FQ} TO `{SHARE_GROUP}`"]:
        try:
            spark.sql(stmt); print(stmt)
        except Exception as e:
            print(f"Could not run: {stmt}\n  {str(e).splitlines()[0]}\n  Ask a catalog owner to run it.")
    try:
        api.do("PATCH", f"/api/2.0/permissions/genie/{SPACE_ID}",
               body={"access_control_list": [{"group_name": SHARE_GROUP, "permission_level": "CAN_RUN"}]})
        print(f"Granted CAN RUN on the agent to {SHARE_GROUP}")
    except Exception as e:
        print(f"Could not set agent permissions automatically ({e}). Open the agent, click Share, and add {SHARE_GROUP} with Can Run.")
else:
    print("No group set. To share: grant the group USE CATALOG, USE SCHEMA and SELECT on the schema, then Share the agent with Can Run.")

# COMMAND ----------

# MAGIC %md ## 5. Self-test

# COMMAND ----------

checks = {
    "Split purchase groups": f"""SELECT COUNT(*) FROM (SELECT t.card_id FROM {q('transactions')} t JOIN {q('cardholders')} c ON t.card_id = c.card_id
        GROUP BY t.card_id, t.merchant_name, t.transaction_date, c.single_purchase_limit
        HAVING COUNT(*) >= 2 AND MAX(t.amount) <= c.single_purchase_limit AND SUM(t.amount) > c.single_purchase_limit)""",
    "Purchases after termination": f"""SELECT COUNT(*) FROM {q('transactions')} t JOIN {q('cardholders')} c ON t.card_id = c.card_id
        WHERE c.termination_date IS NOT NULL AND t.transaction_date > c.termination_date""",
    "Blocked category purchases": f"""SELECT COUNT(*) FROM {q('transactions')} t JOIN {q('merchant_categories')} m ON t.mcc = m.mcc WHERE m.is_blocked""",
    "FY2026 total spend ($)": f"SELECT ROUND(SUM(amount), 2) FROM {q('transactions')} WHERE fiscal_year = 2026",
    "Unreconciled statements": f"SELECT COUNT(*) FROM {q('monthly_statements')} WHERE NOT reconciled",
}
for label, sql in checks.items():
    value = spark.sql(sql).collect()[0][0]
    print(f"  {label}: {value:,}")
    assert value and value > 0, f"Self-test failed: {label} returned {value}"
print("\nSetup complete.")
