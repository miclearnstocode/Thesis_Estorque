from sklearn.cluster import AgglomerativeClustering
from sklearn.datasets import make_blobs
from sklearn.metrics import silhouette_score
from joblib import Parallel, delayed
import numpy as np

def perform_clustering(n_clusters, X):
    clustering = AgglomerativeClustering(n_clusters=n_clusters)
    clustering.fit(X)
    score = silhouette_score(X, clustering.labels_)
    return n_clusters, score

# Generate sample data
X, _ = make_blobs(n_samples=1000, centers=5, random_state=42)

# Define range of clusters to try
n_clusters_range = range(2, 11)

# Parallel computation of clustering for different numbers of clusters
results = Parallel(n_jobs=-1)(
    delayed(perform_clustering)(n_clusters, X) 
    for n_clusters in n_clusters_range
)

# Extract results
n_clusters_list, scores = zip(*results)

# Find the best number of clusters
best_n_clusters = n_clusters_list[np.argmax(scores)]
best_score = max(scores)

print(f"Best number of clusters: {best_n_clusters}")
print(f"Best silhouette score: {best_score}")

# Perform final clustering with the best number of clusters
final_clustering = AgglomerativeClustering(n_clusters=best_n_clusters)
final_clustering.fit(X)

print(f"Final clustering labels: {final_clustering.labels_}")