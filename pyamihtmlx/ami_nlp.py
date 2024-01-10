import collections
import logging
import string
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
from sklearn import manifold
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from test.resources import Resources

logger = logging.getLogger(__file__)

# anchor
A_TEXT = "a_text"
A_ID = "a_id"
# target
T_TEXT = "t_text"
T_ID = "t_id"

# nltk
N_ENGLISH = 'english'
N_PUNKT = 'punkt'


class AmiNLP:

    def __init__(self):
        self.stemmer = nltk.stem.porter.PorterStemmer()
        self.remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
        self.vectorizer = TfidfVectorizer(tokenizer=self.normalize, stop_words=N_ENGLISH)

        nltk.download(N_PUNKT)  # if necessary...

    def stem_tokens(self, tokens):
        return [self.stemmer.stem(item) for item in tokens]

    '''remove punctuation, lowercase, stem'''

    def normalize(self, text):
        return self.stem_tokens(nltk.word_tokenize(text.lower().translate(self.remove_punctuation_map)))

    def cosine_sim(self, text1, text2):
        try:
            tfidf = self.vectorizer.fit_transform([text1, text2])
        except Exception as e:
            logger.error(f"cannot parse {text1} \n.......\n{text2}")
            return None
        return ((tfidf * tfidf.T).A)[0, 1]

    def find_similarities(self, texts, maxt=10000, min_sim=0.25):
        """
        find simiarities in list of text objects
        :param list of texts
        """
        texts = [str(t) for t in texts[:maxt] if t]
        print(f"texts:\n{texts}")
        for i, t0 in enumerate(texts[:maxt]):
            for ii, t1 in enumerate(texts[i + 1: maxt]):
                j = i + ii + 1
                sim = self.cosine_sim(t0, t1)
                if sim > min_sim:
                    sim = {round(sim, 3)}
                    print(f"\n{i}=>{j}  s={sim}\n{t0}\n{t1}")

    def find_text_similarities(self, csv_path, maxt=10000, min_sim=0.25, omit_dict=None):

        print(f"============{csv_path}=============")

        self.read_csv_remove_duplicates_and_unwanted_values(csv_path, omit_dict)

        a_text = self.data.get(A_TEXT)
        a_id = self.data.get(A_ID)
        simmat = self.find_similarities(a_text, maxt=maxt, min_sim=min_sim)

    def read_csv_remove_duplicates_and_unwanted_values(self, csv_path, omit_dict=None, duplicates=None):
        # turn all data into strings
        self.data = pd.read_csv(str(csv_path), dtype=str, keep_default_na=False)

        if duplicates:
            self.data.drop_duplicates(inplace=True, subset=duplicates)
        # make copy of data with rows NOT containing certain values
        if omit_dict:
            for colname in omit_dict.keys():
                self.data = self.data[~self.data[colname].str.contains(omit_dict.get(colname))]

    def calculate_distance_matrices(self, texts, omit_dict=None, n_clusters=2, random_state=42):
        if len(texts) == 0:
            logger.warning(f"No texts")
            print(f"NO TEXTS")
            return
        # n_clusters cannot be greater than number of data points
        n_clusters = min(n_clusters, len(texts))
        print(f"n_clust {n_clusters}")

        distance_matrix, similarity_matrix = self.create_distance_and_similarity_matrices(texts)
        self.calculate_and_display_agglom_clustering(distance_matrix, texts, ncases=50, n_clusters=n_clusters)

        # kmeans cannot use distance matric whatever GPT says
        # self.calculate_kmeans_and_display_cgpt_junk(distance_matrix, n_clusters, random_state, texts)

    def calculate_and_display_agglom_clustering(self, distance_matrix, texts, ncases=99999, n_clusters=10, distance_threshold=None):
        # Perform clustering using nearest neighbors

        n_clusters = min(n_clusters, len(distance_matrix))
        nn_cluster = AgglomerativeClustering(n_clusters=n_clusters, affinity='precomputed', linkage='average',
                                             distance_threshold=distance_threshold)
        nn_labels = nn_cluster.fit_predict(distance_matrix)
        print("Nearest Neighbors clustering {ncases}:")
        clusters = defaultdict(list)
        for i, text in enumerate(texts[:ncases]):
            idx = nn_labels[i]
            # print(f"Text: {text}\tCluster: {idx}")
            clusters[str(idx)].append(text)
        for cluster in clusters.items():
            print(f"{cluster[0]}: {len(cluster[1])}")
            if (l := len(cluster[1])) > 1:
                print(f"{l}: ")
                for text in cluster[1]:
                    print(f"   > {text}")

        AmiNLP.plot_points_labels(distance_matrix, nn_labels)


    def calculate_kmeans_and_display_cgpt_junk(self, distance_matrix, n_clusters, random_state, texts):
        # Perform clustering using k-means
        kmeans_cluster = KMeans(n_clusters=n_clusters, random_state=random_state)
        kmeans_labels = kmeans_cluster.fit_predict(distance_matrix)
        print("\nK-means clustering:")
        for i, text in enumerate(texts[:50]):
            print(f"Text: {text}\tCluster: {kmeans_labels[i]}")
        print(f"kml {kmeans_labels}")
        # filter rows of original data
        filtered_label0 = self.data[kmeans_labels == 7]
        print(f"filt {filtered_label0}")
        # plotting the results
        plt.scatter(filtered_label0[:, 0], filtered_label0[:, 1])
        plt.show()

    def create_distance_and_similarity_matrices(self, texts):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        distance_matrix = 1 - similarity_matrix
        return distance_matrix, similarity_matrix

    @classmethod
    def plot_points_labels(cls, dists, labels, marker="o", show_plot=False):
        """
        plots points and labels
        :param show_plot:
        """
        adist = np.array(dists)
        amax = np.amax(adist)
        adist /= amax
        mds = manifold.MDS(n_components=2, dissimilarity="precomputed", random_state=7)
        results = mds.fit(adist)
        coords = results.embedding_
        plt.subplots_adjust(bottom=0.1)
        plt.scatter(
            coords[:, 0], coords[:, 1], marker=marker
        )
        for label, x, y in zip(labels, coords[:, 0], coords[:, 1]):
            plt.annotate(
                label,
                xy=(x, y), xytext=(-20, 20),
                textcoords='offset points', ha='right', va='bottom',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        if show_plot:
            plt.show()
        else:
            print(f"No plot, use show_plot=True")

class WordTrieNode:
    def __init__(self):
        self.children = collections.defaultdict(WordTrieNode)
        self.is_end = False

class WordTrie:
    """needs extending to phrases
    """
    def __init__(self):
        """
        Initialize your data structure here.
        """
        self.root = WordTrieNode()

    def insert(self, word: str) -> None:
        current = self.root
        for letter in word:
            current = current.children[letter]
        current.is_end = True

    def search(self, word: str) -> bool:
        """
        Returns if the word is in the trie.
        need to extend to phrases
        """
        current = self.root
        for letter in word:
            current = current.children.get(letter)
            if current is None:
                return False
        return current.is_end

    def startsWith(self, prefix: str) -> bool:
        """
        :param prefix:
        :return: any word in the trie starting with the given prefix.
        """
        current = self.root

        for letter in prefix:
            current = current.children.get(letter)
            if not current:
                return False

        return True