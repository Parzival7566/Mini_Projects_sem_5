import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Read data from pickle files
final_ratings = pd.read_pickle('static/pivot_table.pkl')
df = pd.read_pickle('static/dataframe.pkl')

# Create pivot table
pt = final_ratings.pivot_table(index='Name', columns='AuthorId', values='Rating')
pt.fillna(0, inplace=True)  # Handle NaN values

# Rename index and calculate similarity scores
name_list = df['Name'].tolist()
pt.index = name_list
similarity_scores = cosine_similarity(pt)

# Define function to recommend similar items
def recommend(food_item_name):
    index = np.where(pt.index == food_item_name)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:10]
    recommendations_list = [pt.index[i[0]] for i in similar_items]
    return recommendations_list

food_list = df['Name'].tolist()