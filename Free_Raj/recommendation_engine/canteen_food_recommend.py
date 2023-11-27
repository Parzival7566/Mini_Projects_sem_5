import pandas as pd
import numpy as np
from recommendation_engine.rating_table_dynamic import export_data_to_table

rating_table = export_data_to_table()
 
#rating_table = pd.read_csv("data (2).csv")
rating_table

rec_pt = rating_table.pivot_table(index = 'Item Name',columns = 'User ID',values = 'Number of Times Ordered')
rec_pt
rec_pt.fillna(0,inplace = True)
rec_pt

from sklearn.metrics.pairwise import cosine_similarity
cosine_similarity(rec_pt)
similarity_scores = cosine_similarity(rec_pt)
list(enumerate(similarity_scores[0])) 
sorted(list(enumerate(similarity_scores[0])) , key = lambda x:x[1] , reverse = True)

def recommend(food_item_name):
    index = np.where(rec_pt.index == food_item_name)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:4]
    recommendations_list = [rec_pt.index[i[0]] for i in similar_items]
    return recommendations_list