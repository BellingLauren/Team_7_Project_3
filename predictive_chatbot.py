import pandas as pd
import numpy as np
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans

class PredictiveChatbot:
    def __init__(self, model_path='chatbot_model.pkl', data_path='search_history.csv'):
        self.model_path = model_path
        self.data_path = data_path
        self.model = None
        self.vectorizer = None
        self.kmeans = None
        self.common_queries = None
        
        # Try to load existing model and data
        self._load_resources()
    
    def _load_resources(self):
        """Load the model and search history if they exist"""
        try:
            # Try to load model
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    resources = pickle.load(f)
                    self.model = resources.get('model')
                    self.vectorizer = resources.get('vectorizer')
                    self.kmeans = resources.get('kmeans')
                    self.common_queries = resources.get('common_queries')
                print(f"Loaded existing model and resources from {self.model_path}")
            
            # Try to load search history
            if os.path.exists(self.data_path):
                self.search_history = pd.read_csv(self.data_path)
                print(f"Loaded {len(self.search_history)} previous searches from {self.data_path}")
            else:
                # Initialize empty search history
                self.search_history = pd.DataFrame(columns=['query', 'destination', 'count'])
                print("No existing search history found. Starting with empty history.")
        except Exception as e:
            print(f"Error loading resources: {str(e)}")
            # Initialize empty search history
            self.search_history = pd.DataFrame(columns=['query', 'destination', 'count'])
    
    def save_resources(self):
        """Save the model and search history"""
        # Save model and related resources
        with open(self.model_path, 'wb') as f:
            resources = {
                'model': self.model,
                'vectorizer': self.vectorizer,
                'kmeans': self.kmeans,
                'common_queries': self.common_queries
            }
            pickle.dump(resources, f)
        
        # Save search history
        self.search_history.to_csv(self.data_path, index=False)
        print(f"Saved model and search history ({len(self.search_history)} queries)")
    
    def record_query(self, query, destination=None):
        # Check if this query already exists for this destination
        existing = self.search_history[
            (self.search_history['query'] == query) & 
            (self.search_history['destination'] == destination)
        ]
        
        if len(existing) > 0:
            # Update count of existing query
            idx = existing.index[0]
            self.search_history.at[idx, 'count'] += 1
        else:
            # Add new query
            new_row = pd.DataFrame({
                'query': [query],
                'destination': [destination],
                'count': [1]
            })
            self.search_history = pd.concat([self.search_history, new_row], ignore_index=True)
        
        # Save after each update
        self.save_resources()
    
    def train_model(self, min_samples=10):
        # Check if we have enough data to train
        if len(self.search_history) < min_samples:
            print(f"Not enough data to train model yet. Have {len(self.search_history)}, need {min_samples}")
            return False
        
        try:
            # Prepare the data - use queries weighted by count
            queries = []
            for _, row in self.search_history.iterrows():
                # Add each query multiple times based on its count (frequency weighting)
                for _ in range(int(row['count'])):
                    queries.append(row['query'])
            
            # Vectorize the queries
            self.vectorizer = TfidfVectorizer(
                min_df=2,
                max_df=0.7,
                ngram_range=(1, 2)
            )
            X = self.vectorizer.fit_transform(queries)
            
            # Train a nearest neighbors model
            self.model = NearestNeighbors(
                n_neighbors=5,
                algorithm='ball_tree'
            )
            self.model.fit(X)
            
            # Also train a K-means for clustering common questions
            n_clusters = min(5, len(self.search_history) // 2)
            if n_clusters > 1:
                self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                self.kmeans.fit(X)
                
                # Find the most common query in each cluster
                cluster_labels = self.kmeans.predict(X)
                unique_queries = list(set(queries))
                vectorized = self.vectorizer.transform(unique_queries)
                
                # For each cluster, find the query closest to the centroid
                self.common_queries = []
                for i in range(n_clusters):
                    # Get queries in this cluster
                    cluster_queries = [q for j, q in enumerate(unique_queries) 
                                    if self.kmeans.predict(self.vectorizer.transform([q]))[0] == i]
                    
                    if cluster_queries:
                        # Find most frequent in this cluster
                        query_counts = {q: queries.count(q) for q in cluster_queries}
                        most_common = max(query_counts.items(), key=lambda x: x[1])[0]
                        self.common_queries.append(most_common)
            
            # Save the trained model
            self.save_resources()
            print(f"Model trained successfully with {len(queries)} weighted queries")
            return True
            
        except Exception as e:
            print(f"Error training model: {str(e)}")
            return False
    
    def get_suggested_queries(self, destination=None, top_n=3):
        # If we have common queries from clustering, use those
        if self.common_queries:
            if destination:
                # Filter common queries that are relevant to this destination
                dest_queries = self.search_history[
                    self.search_history['destination'] == destination
                ]['query'].tolist()
                
                # If we have destination-specific queries, use those
                if dest_queries:
                    # Vector representation of destination queries
                    dest_vectors = self.vectorizer.transform(dest_queries)
                    common_vectors = self.vectorizer.transform(self.common_queries)
                    
                    # Find the nearest common queries to the destination queries
                    suggestions = []
                    for i, query in enumerate(self.common_queries):
                        # Check if this common query is similar to any destination query
                        for j, dest_query in enumerate(dest_queries):
                            if cosine_similarity(
                                common_vectors[i], 
                                dest_vectors[j]
                            )[0][0] > 0.3:
                                suggestions.append(query)
                                break
                    
                    # If we found suggestions, return them
                    if suggestions:
                        return suggestions[:top_n]
            
            # If no destination-specific suggestions, return top common queries
            return self.common_queries[:top_n]
        
        # If no clustering model, return the most frequent queries
        if len(self.search_history) > 0:
            top_queries = self.search_history.sort_values('count', ascending=False)
            
            # Filter by destination if provided
            if destination:
                dest_queries = top_queries[top_queries['destination'] == destination]
                if len(dest_queries) > 0:
                    return dest_queries['query'].head(top_n).tolist()
            
            # Otherwise return overall top queries
            return top_queries['query'].head(top_n).tolist()
        
        # If no data, return default questions
        return [
            "What are popular attractions in this destination?",
            "What's the best time to visit?",
            "What should I pack for my trip?"
        ]

# Helper function for cosine similarity
def cosine_similarity(a, b):
    """Calculate cosine similarity between two sparse vectors"""
    return (a * b.T).toarray()