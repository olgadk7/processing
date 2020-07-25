import pandas as pd
import numpy as np
import datetime as dt
import seaborn as sns
import matplotlib.pyplot as plt
# pd.set_option('display.max_rows', None)
pd.options.display.float_format = '{:20,.2f}'.format
pd.set_option('display.max_columns', None)
import warnings
# warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter('ignore')
print(" 1 Imported libraries.")

# define months subtractor
def month_diff(a, b):
    return (12 * (a.dt.year - b.dt.year) + (a.dt.month - b.dt.month))+1
# define year subtractor
def year_diff(a, b):
    return (a.dt.year - b.dt.year)+1

def add_cohort_seniority(df):
    # calculate the cohort (acquisition month) for each user
    df['cohort'] = df[['MBSystemID','SaleDate']].groupby('MBSystemID').transform('min')
    df['cohort'] = df['cohort'].dt.to_period('M')
    # calculate seniority in months
    # find user's signup date, a minimum date in members df
    df['signup_date'] = df.groupby('MBSystemID')['SaleDate'].transform('min')
    # assign to each transaction the seniority month
    df['seniority'] = month_diff(members['SaleDate'], members['signup_date'])
    return df

# Import relevant tables
sales = pd.read_csv("data/ClientSales1.csv", parse_dates=["SaleDate"])
sales.drop(['LastName', 'FirstName'], axis=1, inplace=True)
# autopay = pd.read_csv("data/ClientAutopayContracts1.csv", parse_dates=["ContractStartDate", "ContractEndDate"])
# autopay.drop(['PayingClient', 'ReceivingClient'], axis=1, inplace=True)
# sales = sales. loc
print("\n","2 Imported {0}sales.".format(sales.shape[0]))

member_category_type = ['Monthly Autopay Memberships','Monthly Non-Autopay Memberships', 'Annual Memberships']
members = sales[sales['CategoryName'].isin(member_category_type)]
members = members.loc[members['SaleDate'] < '2020-03-01']
# categorize description into less categories
members['Description_2'] = np.where(members['Description'].str.contains('Monthly Auto-Pay'), 'Monthly Auto-Pay',
                           np.where(members['Description'].str.contains('Discount'), 'Discount',
                           np.where(members['Description'].str.contains('Savior Series'), 'Savior Series',
                           np.where(members['Description'].str.contains('Special'), 'Special', 'Misc'))))
# # how much money do different Description_2 within members bring
# members.groupby('Description_2')['SDPaymentAmt'].sum().sort_values(ascending=False)
# # shows Description_2 - Description combinations and their sums, in alphabetical order
# members.groupby(['Description_2', 'Description'])['SDPaymentAmt'].sum()
print("\n","3 Created members table by subsetting sales table by CategoryName.")
print("  * Total members now:", len(members['MBSystemID'].unique()))

# grab the "free"-type members from autopay table
autopay = pd.read_csv("data/ClientAutopayContracts1.csv", parse_dates=["ContractStartDate", "ContractEndDate"])
free_types_list = autopay[autopay['ContractName'].str.contains("Free")]['ReceivingClientId'].unique()
members = members[~members['MBSystemID'].isin(free_types_list)]
print("\n","4 Imported autopay table and got rid of {0} free types from members.".format(len(free_types_list)))
print("  * Total members now:", len(members['MBSystemID'].unique()))

#subset by members who purchased in Feb'20
current_members_list = members['MBSystemID'].loc[(members['SaleDate'].dt.year==2020) & (members['SaleDate'].dt.month == 2)].unique()
current_members = members[members['MBSystemID'].isin(current_members_list)]
print("  * Total current / retained members / those who purchased a membership in February:",
      len(current_members['MBSystemID'].unique()))

# subset by members who didn't purchase in Feb'20
dropped_members = members[~members['MBSystemID'].isin(current_members_list)]
print("  * Total past / churned members / those who DIDN'T purchase a membership in February:",
      len(dropped_members['MBSystemID'].unique()))
# print(current_members.groupby('MBSystemID')['SaleDate'].agg(['min', 'max']).min())
print("  * Historical retained to churned rate:",
      round(len(current_members['MBSystemID'].unique()) / len(dropped_members['MBSystemID'].unique()), 2))

members = add_cohort_seniority(members)
# members['seniority'] = str(members['seniority'])
# tag 1 if current member = purchased in Februry and 0 if not:
members['purchased_february'] = np.where(members['MBSystemID'].isin(current_members_list), 1, 0)
members['SaleYearMonth'] = members['SaleDate'].apply(lambda x: x.strftime('%Y-%m'))
print("\n","5 Added cohort_seniority and purchased_february to members.")
print("  * {0} people purchased membership in February.".format(members.groupby('purchased_february')['MBSystemID'].nunique()[1]),
      "Importing visits..")
members.to_csv('data/members.csv', index=False)

# # subset those who joined three years ago
# members_3year = members.loc[(members['cohort'] > '2017-01') & (members['SaleYearMonth'] < '2020-03'),:]
members_3year = members.loc[members['cohort'] > '2017-01',:]
members_3year.to_csv('data/members_3year.csv', index=False)


visits = pd.read_csv("data/VisitData1.csv", parse_dates=['VisitDate','VisitStartTime','VisitEndTime'])
visits.drop(['LastName', 'FirstName'], axis=1, inplace=True)
print("\n","6 Imported {0} visits.".format(visits.shape[0]))

member_visits = visits[visits['MBSystemID'].isin(members['MBSystemID'].unique())]
member_visits = member_visits[~member_visits['MBSystemID'].isin(free_types_list)]

print("\n","7 Created member_visits table by subsetting visits by members only.")

print("  * Total members in member_visits:",
      len(member_visits['MBSystemID'].unique()))
print("  * Total member visits in member_visits",
     member_visits.shape[0])

member_visits['signup_date'] = member_visits.groupby('MBSystemID')['VisitDate'].transform('min')

member_visits.set_index('MBSystemID', inplace=True)
member_visits['cohort'] = member_visits.groupby('MBSystemID')['VisitDate'].min().apply(lambda x: x.strftime('%Y-%m'))
member_visits['cohort_year'] = member_visits.groupby('MBSystemID')['VisitDate'].min().apply(lambda x: x.strftime('%Y'))
member_visits.reset_index(inplace=True)

member_visits['seniority'] = month_diff(member_visits['VisitDate'], member_visits['signup_date'])
member_visits['seniority_years'] = year_diff(member_visits['VisitDate'], member_visits['signup_date'])
member_visits['VisitYearMonth'] = member_visits['VisitDate'].apply(lambda x: x.strftime('%Y-%m'))

user_status_dict = dict(zip(members['MBSystemID'], members['purchased_february']))
member_visits['purchased_february'] = member_visits['MBSystemID'].map(user_status_dict)
member_visits.to_csv('data/member_visits.csv', index=False)

print("\n","8 Added cohort, seniority and purchased_february to member_visits table.")
print("  * {0} people in member_visits purchased membership in february.".format(member_visits.groupby('purchased_february')['MBSystemID'].nunique()[1]))


# PER CLUB subsetting
members_bellingham_3year = members_3year.loc[members['LocationName']=='Bellingham']
members_oceanside_3year = members_3year.loc[members['LocationName']=='Oceanside']
members_carlsbad_3year = members_3year.loc[members['LocationName']=='Carlsbad']
members_murrieta_3year = members_3year.loc[members['LocationName']=='Murrieta']
members_bellingham_3year.to_csv('data/members_bellingham_3year.csv', index=False)
members_oceanside_3year.to_csv('data/members_oceanside_3year.csv', index=False)
members_carlsbad_3year.to_csv('data/members_carlsbad_3year.csv', index=False)
members_murrieta_3year.to_csv('data/members_murrieta_3year.csv', index=False)

members_bellingham = members.loc[members['LocationName']=='Bellingham']
members_oceanside = members.loc[members['LocationName']=='Oceanside']
members_carlsbad = members.loc[members['LocationName']=='Carlsbad']
members_murrieta = members.loc[members['LocationName']=='Murrieta']
members_bellingham.to_csv('data/members_bellingham.csv', index=False)
members_oceanside.to_csv('data/members_oceanside.csv', index=False)
members_carlsbad.to_csv('data/members_carlsbad.csv', index=False)
members_murrieta.to_csv('data/members_murrieta.csv', index=False)

print("\n", "Aaaand done.")
