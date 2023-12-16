#!/usr/bin/env python
# coding: utf-8

# Copyright Jana Schaich Borg/Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)

# # MySQL Exercise 10: Useful Logical Operators
# 
# There are a few more logical operators we haven't covered yet that you might find useful when designing your queries.  Expressions that use logical operators return a result of "true" or "false", depending on whether the conditions you specify are met.  The "true" or "false" results are usually used to determine which, if any, subsequent parts of your query will be run.  We will discuss the IF operator, the CASE operator, and the order of operations within logical expressions in this lesson.
# 
# **Begin by loading the sql library and database, and making the Dognition database your default database:**

# In[2]:


get_ipython().run_line_magic('load_ext', 'sql')
get_ipython().run_line_magic('sql', 'mysql://studentuser:studentpw@localhost/dognitiondb')
get_ipython().run_line_magic('sql', 'USE dognitiondb')


# ## 1. IF expressions
# 
# IF expressions are used to return one of two results based on whether inputs to the expressions meet the conditions you specify.  They are frequently used in SELECT statements as a compact way to rename values in a column.  The basic syntax is as follows:
# 
# ```
# IF([your conditions],[value outputted if conditions are met],[value outputted if conditions are NOT met])
# ```
# 
# So we could write:
# 
# ```sql
# SELECT created_at, IF(created_at<'2014-06-01','early_user','late_user') AS user_type
# FROM users
# ```  
# to output one column that provided the time stamp of when a user account was created, and a second column called user_type that used that time stamp to determine whether the user was an early or late user. User_type could then be used in a GROUP BY statement to segment summary calculations (in database systems that support the use of aliases in GROUP BY statements). 
#    
# For example, since we know there are duplicate user_guids in the user table, we could combine a subquery with an IF statement to retrieve a list of unique user_guids with their classification as either an early or late user (based on when their first user entry was created): 
# 
# ```sql
# SELECT cleaned_users.user_guid as UserID,
#        IF(cleaned_users.first_account<'2014-06-01','early_user','late_user') AS user_type
# FROM (SELECT user_guid, MIN(created_at) AS first_account 
#       FROM users
#       GROUP BY user_guid) AS cleaned_users
# ```
#   
# We could then use a GROUP BY statement to count the number of unique early or late users:
# 
# ```sql 
# SELECT IF(cleaned_users.first_account<'2014-06-01','early_user','late_user') AS user_type,
#        COUNT(cleaned_users.first_account)
# FROM (SELECT user_guid, MIN(created_at) AS first_account 
#       FROM users
#       GROUP BY user_guid) AS cleaned_users
# GROUP BY user_type
# ```
# 
# **Try it yourself:**

# In[5]:


get_ipython().run_cell_magic('sql', '', "SELECT IF(cleaned_users.first_account<'2014-06-01','early_user','late_user') AS user_type,\n       COUNT(cleaned_users.first_account)\nFROM (SELECT user_guid, MIN(created_at) AS first_account \n      FROM users\n      GROUP BY user_guid) AS cleaned_users\nGROUP BY user_type")


# **Question 1: Write a query that will output distinct user_guids and their associated country of residence from the users table, excluding any user_guids or countries that have NULL values.  You should get 16,261 rows in your result.**

# In[6]:


get_ipython().run_cell_magic('sql', '', 'SELECT DISTINCT user_guid, country\nFROM users\nWHERE country IS NOT NULL;')


# **Question 2: Use an IF expression and the query you wrote in Question 1 as a subquery to determine the number of unique user_guids who reside in the United States (abbreviated "US") and outside of the US.**

# In[7]:


get_ipython().run_cell_magic('sql', '', "SELECT IF(cleaned_users.country='US','In US','Outside US') AS user_location,\ncount(cleaned_users.user_guid) AS num_guids\nFROM (SELECT DISTINCT user_guid, country\nFROM users\nWHERE user_guid IS NOT NULL AND country IS NOT NULL) AS cleaned_users\nGROUP BY user_location;")


# Single IF expressions can only result in one of two specified outputs, but multiple IF expressions can be nested to result in more than two possible outputs.  <mark>When you nest IF expressions, it is important to encase each IF expression--as well as the entire IF expression put together--in parentheses.</mark>
#     
# For example, if you examine the entries contained in the non-US countries category, you will see that many users are associated with a country called "N/A." "N/A" is an abbreviation for "Not Applicable"; it is not a real country name.  We should separate these entries from the "Outside of the US" category we made earlier.  We could use a nested query to say whenever "country" does not equal "US", use the results of a second IF expression to determine whether the outputed value should be "Not Applicable" or "Outside US."  The IF expression would look like this:
# 
# ```sql
# IF(cleaned_users.country='US','In US', IF(cleaned_users.country='N/A','Not Applicable','Outside US'))
# ```
# 
# Since the second IF expression is in the position within the IF expression where you specify "value outputted if conditions are not met," its two possible outputs will only be considered if cleaned_users.country='US' is evaluated as false.
# 
# The full query to output the number of unique users in each of the three groups would be:
# 
# ```sql 
# SELECT IF(cleaned_users.country='US','In US', 
#           IF(cleaned_users.country='N/A','Not Applicable','Outside US')) AS US_user, 
#       count(cleaned_users.user_guid)   
# FROM (SELECT DISTINCT user_guid, country 
#       FROM users
#       WHERE country IS NOT NULL) AS cleaned_users
# GROUP BY US_user
# ```
# 
# **Try it yourself. You should get 5,642 unique user_guids in the "Not Applicable" category, and 1,263 users in the "Outside US" category.**

# In[8]:


get_ipython().run_cell_magic('sql', '', "SELECT IF(cleaned_users.country='US','In US', \n          IF(cleaned_users.country='N/A','Not Applicable','Outside US')) AS US_user, \n      count(cleaned_users.user_guid)   \nFROM (SELECT DISTINCT user_guid, country \n      FROM users\n      WHERE country IS NOT NULL) AS cleaned_users\nGROUP BY US_user")


# <mark>The IF function is not supported by all database platforms, and some spell the function as IIF rather than IF, so be sure to double-check how the function works in the platform you are using.</mark>
# 
# If nested IF expressions seem confusing or hard to read, don't worry, there is a better function available for situations when you want to use conditional logic to output more than two groups.  That function is called CASE.
# 
#    
# ## 2. CASE expressions
# 
# The main purpose of CASE expressions is to return a singular value based on one or more conditional tests.  You can think of CASE expressions as an efficient way to write a set of IF and ELSEIF statements.  There are two viable syntaxes for CASE expressions.  If you need to manipulate values in a current column of your data, you would use this syntax:
# 
# <img src="https://duke.box.com/shared/static/bvyvscvvg9d1rjnov340gqyu85mhch9i.jpg" width=600 alt="CASE_Expression" />
# 
# Using this syntax, our nested IF statement from above could be written as:
# 
# ```sql
# SELECT CASE WHEN cleaned_users.country="US" THEN "In US"
#             WHEN cleaned_users.country="N/A" THEN "Not Applicable"
#             ELSE "Outside US"
#             END AS US_user, 
#       count(cleaned_users.user_guid)   
# FROM (SELECT DISTINCT user_guid, country 
#       FROM users
#       WHERE country IS NOT NULL) AS cleaned_users
# GROUP BY US_user
# ```
# 
# **Go ahead and try it:**

# In[11]:


get_ipython().run_cell_magic('sql', '', 'SELECT CASE WHEN cleaned_users.country="US" THEN "In US"\n            WHEN cleaned_users.country="N/A" THEN "Not Applicable"\n            ELSE "Outside US"\n            END AS US_user, \n      count(cleaned_users.user_guid)   \nFROM (SELECT DISTINCT user_guid, country \n      FROM users\n      WHERE country IS NOT NULL) AS cleaned_users\nGROUP BY US_user')


# Since our query does not require manipulation of any of the values in the country column, though, we could also take advantage of this syntax, which is slightly more compact:
# 
# <img src="https://duke.box.com/shared/static/z9fezozm55wj5pz6slxscouxrcpq7bpz.jpg" width=600 alt="CASE_Value" />
# 
# Our query written in this syntax would look like this:
# 
# ```sql
# SELECT CASE cleaned_users.country
#             WHEN "US" THEN "In US"
#             WHEN "N/A" THEN "Not Applicable"
#             ELSE "Outside US"
#             END AS US_user, 
#       count(cleaned_users.user_guid)   
# FROM (SELECT DISTINCT user_guid, country 
#       FROM users
#       WHERE country IS NOT NULL) AS cleaned_users
# GROUP BY US_user
# ```
# 
# **Try this query as well:**
# 

# In[12]:


get_ipython().run_cell_magic('sql', '', 'SELECT CASE cleaned_users.country\n            WHEN "US" THEN "In US"\n            WHEN "N/A" THEN "Not Applicable"\n            ELSE "Outside US"\n            END AS US_user, \n      count(cleaned_users.user_guid)   \nFROM (SELECT DISTINCT user_guid, country \n      FROM users\n      WHERE country IS NOT NULL) AS cleaned_users\nGROUP BY US_user')


# There are a couple of things to know about CASE expressions:
#    
# + Make sure to include the word END at the end of the expression
# + CASE expressions do not require parentheses
# + ELSE expressions are optional
# + If an ELSE expression is omitted, NULL values will be outputted for all rows that do not meet any of the conditions stated explicitly in the expression
# + CASE expressions can be used anywhere in a SQL statement, including in GROUP BY, HAVING, and ORDER BY clauses or the SELECT column list.
# 
# You will find that CASE statements are useful in many contexts. For example, they can be used to rename or revise values in a column.
# 
# **Question 3: Write a query using a CASE statement that outputs 3 columns: dog_guid, dog_fixed, and a third column that reads "neutered" every time there is a 1 in the "dog_fixed" column of dogs, "not neutered" every time there is a value of 0 in the "dog_fixed" column of dogs, and "NULL" every time there is a value of anything else in the "dog_fixed" column.  Limit your results for troubleshooting purposes.**
# 

# In[15]:


get_ipython().run_cell_magic('sql', '', 'SELECT dog_guid,dog_fixed,\nCASE dog_fixed\nWHEN "1" THEN "neutered"\nWHEN "0" THEN "not neutered"\nEND AS neutered\nFROM dogs\nLIMIT 200;')


# You can also use CASE statements to standardize or combine several values into one.  
# 
# **Question 4: We learned that NULL values should be treated the same as "0" values in the exclude columns of the dogs and users tables.  Write a query using a CASE statement that outputs 3 columns: dog_guid, exclude, and a third column that reads "exclude" every time there is a 1 in the "exclude" column of dogs and "keep" every time there is any other value in the exclude column. Limit your results for troubleshooting purposes.**
# 
# 

# In[16]:


get_ipython().run_cell_magic('sql', '', 'SELECT dog_guid, exclude,\nCASE exclude\nWHEN "1" THEN "exclude"\nELSE "keep"\nEND AS exclude_cleaned\nFROM dogs\nLIMIT 200;')


# **Question 5: Re-write your query from Question 4 using an IF statement instead of a CASE statement.**

# In[18]:


get_ipython().run_cell_magic('sql', '', 'SELECT dog_guid, exclude, IF(exclude="1","exclude","keep") AS exclude_cleaned\nFROM dogs\nLIMIT 200;')


# Case expressions are also useful for breaking values in a column up into multiple groups that meet specific criteria or that have specific ranges of values.
# 
# **Question 6: Write a query that uses a CASE expression to output 3 columns: dog_guid, weight, and a third column that reads...     
# "very small" when a dog's weight is 1-10 pounds     
# "small" when a dog's weight is greater than 10 pounds to 30 pounds     
# "medium" when a dog's weight is greater than 30 pounds to 50 pounds     
# "large" when a dog's weight is greater than 50 pounds to 85 pounds     
# "very large" when a dog's weight is greater than 85 pounds      
# Limit your results for troubleshooting purposes.**
# 
# **Remember that when you use AND to define values between two boundaries, you need to include the variable name in all clauses that define the conditions of the values you want to extract.  In other words, you could use this combined clause in your query: 
# “WHEN weight>10 AND weight<=30 THEN "small"
# …but this combined clause would cause an error:
# “WHEN weight>10 AND <=30 THEN "small"**

# In[19]:


get_ipython().run_cell_magic('sql', 'SELECT', 'dog_guid, weight,\nCASE\nWHEN weight<=0 THEN "very small"\nWHEN weight>10 AND weight<=30 THEN "small"\nWHEN weight>30 AND weight<=50 THEN "medium"\nWHEN weight>50 AND weight<=85 THEN "large"\nWHEN weight>85 THEN "very large"\nEND AS weight_grouped\nFROM dogs\nLIMIT 200;')


# ## 3. Pay attention to the order of operations within logical expressions
# 
# As you started to see with the query you wrote in Question 6, CASE expressions often end up needing multiple AND and OR operators to accurately describe the logical conditions you want to impose on the groups in your queries.  You must pay attention to the order in which these operators are included in your logical expressions, because unless parentheses are included, the NOT operator is always evaluated before an AND operator, and an AND operator is always evaluated before the OR operator.  
# 
# <img src="https://duke.box.com/shared/static/uhrmp6vkxznn9zjgezfmxhnbfjaa8c90.jpg" width=200 alt="CASE_Value" />
# 
# When parentheses are included, the expressions within the parenthese are evaluated first.  That means this expression:
# 
# ```sql
# CASE WHEN "condition 1" OR "condition 2" AND "condition 3"...
# ```
# will lead to different results than this expression:
#    
# ```sql
# CASE WHEN "condition 3" AND "condition 1" OR "condition 2"...
# ```
#    
# or this expression:
# ```sql
# CASE WHEN ("condition 1" OR "condition 2") AND "condition 3"...
# ```
#    
# In the first case you will get rows that meet condition 2 and 3, or condition 1.  In the second case you will get rows that meet condition 1 and 3, or condition 2.  In the third case, you will get rows that meet condition 1 or 2, and condition 3.
# 
# Let's see a concrete example of how the order in which logical operators are evaluated affects query results.  
# 
# **Question 7: How many distinct dog_guids are found in group 1 using this query?**
#     
# ```sql
# SELECT COUNT(DISTINCT dog_guid), 
# CASE WHEN breed_group='Sporting' OR breed_group='Herding' AND exclude!='1' THEN "group 1"
#      ELSE "everything else"
#      END AS groups
# FROM dogs
# GROUP BY groups
# ```

# In[20]:


get_ipython().run_cell_magic('sql', '', 'SELECT COUNT(DISTINCT dog_guid), \nCASE WHEN breed_group=\'Sporting\' OR breed_group=\'Herding\' AND exclude!=\'1\' THEN "group 1"\n     ELSE "everything else"\n     END AS groups\nFROM dogs\nGROUP BY groups')


# **Question 8: How many distinct dog_guids are found in group 1 using this query?**
#     
# ```sql
# SELECT COUNT(DISTINCT dog_guid), 
# CASE WHEN exclude!='1' AND breed_group='Sporting' OR breed_group='Herding' THEN "group 1"
#      ELSE "everything else"
#      END AS group_name
# FROM dogs
# GROUP BY group_name
# ```
# 

# In[21]:


get_ipython().run_cell_magic('sql', '', 'SELECT COUNT(DISTINCT dog_guid), \nCASE WHEN exclude!=\'1\' AND breed_group=\'Sporting\' OR breed_group=\'Herding\' THEN "group 1"\n     ELSE "everything else"\n     END AS group_name\nFROM dogs\nGROUP BY group_name')


# **Question 9: How many distinct dog_guids are found in group 1 using this query?**
# 
# ```sql
# SELECT COUNT(DISTINCT dog_guid), 
# CASE WHEN exclude!='1' AND (breed_group='Sporting' OR breed_group='Herding') THEN "group 1"
#      ELSE "everything else"
#      END AS group_name
# FROM dogs
# GROUP BY group_name
# ```

# In[22]:


get_ipython().run_cell_magic('sql', '', 'SELECT COUNT(DISTINCT dog_guid), \nCASE WHEN exclude!=\'1\' AND (breed_group=\'Sporting\' OR breed_group=\'Herding\') THEN "group 1"\n     ELSE "everything else"\n     END AS group_name\nFROM dogs\nGROUP BY group_name')


# <mark> **So make sure you always pay attention to the order in which your logical operators are listed in your expressions, and whenever possible, include parentheses to ensure that the expressions are evaluated in the way you intend!**</mark>
# 
# ## Let's practice some more IF and CASE statements
# 
# <img src="https://duke.box.com/shared/static/p2eucjdttai08eeo7davbpfgqi3zrew0.jpg" width=600 alt="SELECT FROM WHERE" />
# 
# **Question 10: For each dog_guid, output its dog_guid, breed_type, number of completed tests, and use an IF statement to include an extra column that reads "Pure_Breed" whenever breed_type equals 'Pure Breed" and "Not_Pure_Breed" whenever breed_type equals anything else. LIMIT your output to 50 rows for troubleshooting.  HINT: you will need to use a join to complete this query.**

# In[24]:


get_ipython().run_cell_magic('sql', '', "SELECT d.dog_guid AS dogID,d.breed_type AS breed_type,count(c.created_at) AS\nnumtests,\nIF(d.breed_type='Pure Breed','pure_breed', 'not_pure_breed') AS pure_breed\nFROM dogs d, complete_tests c\nWHERE d.dog_guid=c.dog_guid\nGROUP BY dogID, breed_type, pure_breed\nLIMIT 50;")


# **Question 11: Write a query that uses a CASE statement to report the number of unique user_guids associated with customers who live in the United States and who are in the following groups of states:**
# 
# **Group 1: New York (abbreviated "NY") or New Jersey (abbreviated "NJ")    
# Group 2: North Carolina (abbreviated "NC") or South Carolina (abbreviated "SC")    
# Group 3: California (abbreviated "CA")    
# Group 4: All other states with non-null values**
# 
# **You should find 898 unique user_guids in Group1.**
# 
# 

# In[26]:


get_ipython().run_cell_magic('sql', '', 'SELECT COUNT(DISTINCT user_guid),\nCASE\nWHEN (state="NY" OR state="NJ") THEN "Group 1 NY/NJ"\nWHEN (state="NC" OR state="SC") THEN "Group 2 NC/SC"\nWHEN state="CA" THEN "Group 3 CA"\nELSE "Group 4 Other"\nEND AS state_group\nFROM users\nWHERE country="US" AND state IS NOT NULL\nGROUP BY state_group;')


# **Question 12: Write a query that allows you to determine how many unique dog_guids are associated with dogs who are DNA tested and have either stargazer or socialite personality dimensions.  Your answer should be 70.**

# In[28]:


get_ipython().run_cell_magic('sql', '', "SELECT COUNT(DISTINCT dog_guid)\nFROM dogs\nWHERE dna_tested=1 AND (dimension='stargazer' OR dimension='socialite');")


# **Feel free to practice any other queries you like here!**

# In[ ]:




