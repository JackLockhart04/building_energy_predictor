import pandas as pd
import numpy as np

NUM_BUILDINGS = 100

# 1. Read just the header to get all building names (skip 'timestamp')
full_header = pd.read_csv('data/electricity.csv', nrows=0).columns.tolist()
all_buildings = [col for col in full_header if col != 'timestamp']

# 2. Randomly select 100 buildings
# Setting a random_state ensures you get the same "random" set if you run it again
np.random.seed(42) 
random_buildings = np.random.choice(all_buildings, size=NUM_BUILDINGS, replace=False).tolist()

# 3. Load only those 100 columns + the timestamp
# We must include 'timestamp' in the usecols list
subset_cols = ['timestamp'] + random_buildings

# 4. Read the CSV (Year 1 only: 8784 rows for hourly data)
df_elec_short = pd.read_csv(
    'data/electricity.csv', 
    usecols=subset_cols,
    parse_dates=['timestamp'], 
    index_col='timestamp',
    nrows=8784
)

# 5. Save the "Diverse Sandbox"
df_elec_short.to_csv('data/electricity_short.csv', index=True)

print(f"Success! Saved {NUM_BUILDINGS} random buildings to 'data/electricity_short.csv'")
print(f"Buildings included from sites: {df_elec_short.columns.str.split('_').str[0].unique()}")