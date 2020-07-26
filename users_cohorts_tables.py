# MAKE COHORT TABLE
# a dataframe that shows total monthly revenue for each customer:
# identify which users are active by looking at their revenue per month
members_user_purchase = memberships.groupby(['MBSystemID','SaleYearMonth'])['SDPaymentAmt'].sum().reset_index()
members_user_purchase

# convert previous table to retention matrix with crosstab
# it shows which customers are active on each month (1 stands for active)
members_retention = pd.crosstab(members_user_purchase['MBSystemID'], members_user_purchase['SaleYearMonth']).reset_index()
members_retention

#create an array of dictionary which keeps Retained (from previous month) & Total User count for each month
months = members_retention.columns
retention_array = []
for i in range(len(months)-1):
    retention_data = {}
    selected_month = months[i+1]
    prev_month = months[i]
    retention_data['SaleYearMonth'] = selected_month
    retention_data['TotalUserCount'] = members_retention[selected_month].sum()
    retention_data['RetainedUserCount'] = members_retention[(members_retention[selected_month]>0) & (members_retention[prev_month]>0)][selected_month].sum()
    retention_array.append(retention_data)

#convert the array to dataframe and calculate Retention Rate
cohorts = pd.DataFrame(retention_array)
cohorts['RetentionRate'] = cohorts['RetainedUserCount'] / cohorts['TotalUserCount']
cohorts


# CREATE A DF OF JUST USERS AND SOME OF THEIR INFO

# 1. Initiate users table with member data
# group members by IDs and each members' max monthly seniority value
users = members.groupby('MBSystemID')['seniority'].max().to_frame().reset_index()
# add yearly seniority
users['seniority_years'] = users['seniority'] / 12
# add total amount a member spent
users = users.join(members.groupby('MBSystemID')['SDPaymentAmt'].sum(), on='MBSystemID')
users.rename(columns={'SDPaymentAmt': 'total_worth'}, inplace=True)
# add churn binary
users['purchased_february'] = np.where(users['MBSystemID'].isin(current_members_list), 1, 0)
# add cohort
user_cohort_dict = dict(zip(members['MBSystemID'], members['cohort']))
users['cohort'] = users['MBSystemID'].map(user_cohort_dict)
# checks
print("\n", "1. Created users table.",
      "\n", " * Total amount of members in users table:",len(users['MBSystemID'].unique()),
      "\n", " * User table shape:", users.shape, 
      "\n", " * Total members in each churn group in user table:", 
      "\n", users.groupby('purchased_february')['MBSystemID'].nunique())

# 2. Grab VISIT data
# gives a df per user and amount visited during each of their active year-months 
visits_grouped = member_visits.groupby(['MBSystemID', 'VisitYearMonth'])['BarcodeID'].count().to_frame().reset_index()
# divide users total amount ever visited by amount of their active months
average_monthly_visits_peruser = visits_grouped.groupby('MBSystemID')['BarcodeID'].sum() / visits_grouped.groupby('MBSystemID')['VisitYearMonth'].count()
average_monthly_visits_peruser = average_monthly_visits_peruser.to_frame().reset_index()
average_monthly_visits_peruser.rename(columns={0: 'avg_monthly_visits'}, inplace=True)
# add a rounded avg_monthly_visits col
average_monthly_visits_peruser['avg_monthly_visits_rounded'] = average_monthly_visits_peruser['avg_monthly_visits'].round(0).astype(int)
average_monthly_visits_peruser.sort_values('avg_monthly_visits', ascending=False)[:30]
# count total visits
users=users.merge(member_visits.groupby('MBSystemID')['VisitYearMonth'].count(), left_on='MBSystemID', right_index=True).rename(columns={'VisitYearMonth':'total_checkins'})
# add location 
user_locations = member_visits.groupby(['MBSystemID', 'VisitLocation']).size().to_frame().reset_index().groupby('MBSystemID').max().reset_index()[['MBSystemID','VisitLocation']]
user_location_dict = dict(zip(user_locations['MBSystemID'], user_locations['VisitLocation']))
users['location'] = users['MBSystemID'].map(user_location_dict)
print("\n", "2. Calculated average monthly and total visits per user.",
      "\n", " * Total number of members in average_monthly_visits_peruser table:",len(average_monthly_visits_peruser['MBSystemID'].unique()))

# 3. Add the average visit stat to users and member_visits
# add avg monthly visits to users table 
users=users.merge(average_monthly_visits_peruser[['MBSystemID', 'avg_monthly_visits', 'avg_monthly_visits_rounded']], on='MBSystemID')
# add avg monthly visits to member_visits table
member_visits=member_visits.merge(average_monthly_visits_peruser[['MBSystemID', 'avg_monthly_visits', 'avg_monthly_visits_rounded']], on='MBSystemID')
print("\n", "3. Added average mohtly visits to users and to member_visits table",
      "\n", " * Total number of members in users table:", len(users['MBSystemID'].unique()),
      "\n", " * Users table shape:", users.shape,
      "\n", " * Total number of members in member_visits table:", len(member_visits['MBSystemID'].unique()),
      "\n", " * Member_visits table shape:", member_visits.shape, "\n")

# 4. Write DataFrame to CSV
users.to_csv('data/users.csv', index=False)
member_visits.to_csv('data/member_visits.csv', index=False)
print("\n", "4. Saved users and member_visits to csv.")

# member_visits.head()
# users.head()
