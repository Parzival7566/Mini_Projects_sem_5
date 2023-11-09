#!/usr/bin/env python
# coding: utf-8

# # Recommendation Using  collaborative filtering
# 

# In[ ]:


import pandas as pd
import numpy as np
final_ratings = pd.read_pickle('pivot_table.pkl')
final_ratings
df = pd.read_pickle('dataframe.pkl')


# In[ ]:


pt = final_ratings.pivot_table(index = 'Name',columns = 'AuthorId',values = 'Rating')
#pt1 = final_ratings.pivot_table(index = 'Name',columns = 'AuthorId',values = 'Rating')
#specific no of reviews given my user selected and specific no of reviews for a food_item selected
pt.index
pt.head(100)


# In[ ]:


pt.fillna(0,inplace = True)
#Nan values are handled
pt


# In[ ]:





# In[ ]:


name_list = []

# Iterate through the 'Name' column in the DataFrame
for name in df['Name']:
    name_list.append(name)
print(len(name_list))
name_list


# In[ ]:


#pt = pt.rename_axis(name_list)
pt.index = name_list
pt


# In[ ]:


from sklearn.metrics.pairwise import cosine_similarity
cosine_similarity(pt)
#Calculates euclidian distance of each point from each other point in terms of probablity and gives a 2d matrix
cosine_similarity(pt).shape


# In[ ]:


similarity_scores = cosine_similarity(pt)
similarity_scores


# In[ ]:


similarity_scores[0] 
#gives the similarity of 1st food item with all foods
#gives food item index number and similarity score
list(enumerate(similarity_scores[0])) 
#sort with respect to similarity scores
sorted(list(enumerate(similarity_scores[0])) , key = lambda x:x[1] , reverse = True)
#most similar at top


# In[ ]:


#make function called recommend and then suggest 6 similar foods as recommendations
def recommend(food_item_name):
    #fetch index at which the food item is stored
    index = np.where(pt.index ==  food_item_name)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])) , key = lambda x:x[1] , reverse = True)[1:10]
    #distances = similarity_scores[index]
    for i in  similar_items :
            print(pt.index[i[0]])
            


# In[ ]:


food_list = df['Name']
food_list.tolist()


# In[1]:


print("What did you have recently?")
foodstuff = input()
print()
print("Here's what we would also recommend for you to try:")
print()
recommend(foodstuff)


# In[ ]:


'''from pymongo import MongoClient

# Function to check item presence and make a recommendation
def recommend(item):
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database"]
    orders_collection = db["orders"]

    # Check if the item is present in "food_list" (replace with your actual food list)
    food_list = ["item1", "item2", "item3"]

    if item in food_list:
        # Check if the item is present in the "orders" collection
        if orders_collection.count_documents({"item": item}) > 0:
            recommendation = f"We recommend trying {item} today!"
        else:
            recommendation = f"{item} is available but hasn't been ordered yet. Give it a try!"
    else:
        recommendation = f"Sorry, we don't have {item} on our menu today."

    return recommendation

# Example usage
item_to_check = "item1"
result = recommend(item_to_check)
print(result)
'''

