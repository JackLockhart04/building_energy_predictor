# Cleaning

### Data issues

1. Assume that all 0s for electricity are incorrect since electricity use is never 0.
2. Individual buildings with missing points for hours or days.
3. Buildings missing first few months or last few months.
4. Sites missing data points for all buildings in site at once.
5. Some outlier data that may be real but would be bad for training.
6. Some building types are useless.

### Solutions

1. Remove useless building types.
2. Remove all zeros and negatives.
3. Remove outliers. Must be done by hour because large difference between noon and midnight. Right now am ignoring time of year because fluctuations between seasons is not much.
4. Interpolate small holes in data caused by cleaning.
5. Remove buildings that have more than 10% of data missing since there are plenty of buildings in dataset.
