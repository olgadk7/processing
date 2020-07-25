def build_retention_matrix(df):
    grouping = df.groupby(['cohort', 'seniority'])
    # Count the number of unique values per customer ID
    cohort_data = grouping['MBSystemID'].apply(pd.Series.nunique).reset_index()
    # Create a pivot
    cohort_counts = cohort_data.pivot(index='cohort', columns='seniority', values='MBSystemID')
    # Select the first column and store it to cohort_sizes
    cohort_sizes = cohort_counts.iloc[:,0]
    # Divide the cohort count by cohort sizes along the rows
    retention_matrix = cohort_counts.divide(cohort_sizes, axis=0)
    return retention_matrix

def calc_avg_value_percohort(df, cohort, seniority, value):
    # Create a groupby object and pass the monthly cohort and cohort index as a list
    grouping = df.groupby([cohort, seniority])
    # Calculate the average of the payment amount
    cohort_data = grouping[value].mean()
    # Reset the index of cohort_data
    cohort_data = cohort_data.reset_index()
    # Create a pivot
    average_price_table = cohort_data.pivot(index=cohort, columns=seniority, values=value)
    # print(average_price.round(1))
    return average_price_table

def calc_total_value_percohort(df, cohort, seniority, value):
    # Create a groupby object and pass the monthly cohort and cohort index as a list
    grouping = df.groupby([cohort, seniority])
    # Calculate the average of the payment amount
    cohort_data = grouping[value].sum()
    # Reset the index of cohort_data
    cohort_data = cohort_data.reset_index()
    # Create a pivot
    average_price_table = cohort_data.pivot(index=cohort, columns=seniority, values=value)
    # print(average_price.round(1))
    return average_price_table

def get_churn_retention_rates(retention_matrix):
    # Calculate the mean retention rate
    retention_rate = retention_matrix.iloc[:,1:].mean().mean()
    # Calculate churn
    churn = 1 - retention_matrix
    # Calculate the mean churn rate
    churn_rate = churn.iloc[:,1:].mean().mean()
    return retention_rate, churn_rate
#     # Print rounded retention and churn rates
#     print('Retention rate: {:.2f}; Churn rate: {:.2f}'.format(retention_rate, churn_rate))

def get_basic_clv(df, lifespan_months):
    # Calculate monthly spend per customer
    monthly_revenue = df.groupby(['MBSystemID','SaleYearMonth'])['SDPaymentAmt'].sum()
    # Calculate average monthly spend
    monthly_revenue = np.mean(monthly_revenue)
#     # Define lifespan to 36 months
#     lifespan_months = 36
    # Calculate basic CLV
    clv_basic = monthly_revenue * lifespan_months
    # Print the basic CLV value
    print('Average basic CLV for a lifespan of {} months is {:.1f} USD'.format(lifespan_months, clv_basic))


def get_granular_clv(df, lifespan_months):
    # Calculate average revenue per invoice
    revenue_per_purchase = df.groupby(['SaleID'])['SDPaymentAmt'].mean().mean()
    # Calculate average number of unique invoices per customer per month
    frequency_per_month = df.groupby(['MBSystemID','SaleYearMonth'])['SaleID'].nunique().mean()
#     # Define lifespan to 36 months
#     lifespan_months = 36
    # Calculate granular CLV
    clv_granular = revenue_per_purchase * frequency_per_month * lifespan_months
    # Print granular CLV value
    print('Average granular CLV for a lifespan of {} months is {:.1f} USD'.format(lifespan_months, clv_granular))

def get_traditional_clv(df, retention_matrix):
    # Calculate monthly spend per customer
    monthly_revenue = df.groupby(['MBSystemID','SaleYearMonth'])['SDPaymentAmt'].sum().mean()
    # Calculate average monthly retention rate
    retention_rate = retention_matrix.iloc[:,1:].mean().mean()
    # Calculate average monthly churn rate
    churn_rate = 1 - retention_rate
    # Calculate traditional CLV
    # R to C ratio gives us a multiplier that acts as a proxy to the expected length of a customer lifespan with a company. Assumes that churn is final though!
    clv_traditional = monthly_revenue * (retention_rate / churn_rate)
    # Print traditional CLV and the retention rate values
    print('Average traditional CLV is ${:.1f} at {:.1f}% retention_rate'.format(clv_traditional, retention_rate*100),
          '\n(Monthly average revenue is ${:.1f})'.format(monthly_revenue))

    # enter level: 'MBSystemID' or 'cohort'
def get_ltv(df, retention_matrix, level):
    # Calculate monthly spend per COHORT
    monthly_revenue = df.groupby([level,'SaleYearMonth'])['SDPaymentAmt'].sum().mean()
    # Calculate average monthly retention rate
    retention_rate = retention_matrix.iloc[:,1:].mean().mean()
    # Calculate average monthly churn rate
    churn_rate = 1 - retention_rate
    # Calculate traditional CLV
    # R to C ratio gives us a multiplier that acts as a proxy to the expected length of a customer lifespan with a company. Assumes that churn is final though!
    clv_traditional = monthly_revenue * (retention_rate / churn_rate)
    # Print traditional CLV and the retention rate values
    print('Average LTV per {} is ${:.1f} at {:.1f}% retention_rate'.format(level, clv_traditional, retention_rate*100),
          '\n(Monthly average revenue is ${:.1f})'.format(monthly_revenue))

# write a function re: what revenue would have been if retention was different
def simulate_revenue_different_retention(df, retention_matrix, retention_rate_change, level):
    monthly_revenue = df.groupby([level,'SaleYearMonth'])['SDPaymentAmt'].sum().mean()
#     print("monthly_revenue",monthly_revenue)
    retention_rate = retention_matrix.iloc[:,1:].mean().mean()
#     print("retention_rate", retention_rate)
    increase_retention = (retention_rate_change/100) * retention_rate
#     print("increase is", increase)
    simulated_retention_rate = retention_rate + increase_retention
#     print("increase is", round(increase, 2), "simulated_retention_rate is", round(simulated_retention_rate, 2))
    churn_rate = 1 - retention_rate
    simulated_churn_rate = 1 - simulated_retention_rate
#     print("simulated_churn_rate",simulated_churn_rate)
    clv_traditional = monthly_revenue * (retention_rate / churn_rate)
    simulated_clv_traditional = monthly_revenue * ((simulated_retention_rate / simulated_churn_rate))

    increase_clv = simulated_clv_traditional - clv_traditional
    pct_change_clv = increase_clv / clv_traditional * 100


    print('If retention rate was {}% higher (on the {} level), then average CLV is ${:.1f}.'.format(retention_rate_change, level, simulated_clv_traditional),
         '\n({:.1f}% more than at current retention rate)'.format(pct_change_clv))
