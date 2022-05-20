#! /usr/bin/python

import sys,json

castsPath = "../datasets/tmdb/casts.json"

def write_movie_info(raw_movies):
    for raw_movie in raw_movies:
        movie = dict()
        casts = list()
        movie["movie_id"] = str(raw_movie["id"])
        movie["title"] = raw_movie["title"]
        movie["plot_id"] = raw_movie["id"]
        
        for raw_cast in raw_movie["cast"]:
            try:
              cast = dict()
              cast["cast_id"] = raw_cast["cast_id"]
              cast["character"] = raw_cast["character"]
              cast["cast_info_id"] = raw_cast["id"]
              casts.append(cast)
            except:
              print("Warning: cast info missing!")
        movie["casts"] = casts
        movie["thumbnail_ids"] = [raw_movie["poster_path"]]
        movie["photo_ids"] = []
        movie["video_ids"] = []
        movie["avg_rating"] = raw_movie["vote_average"]
        movie["num_rating"] = raw_movie["vote_count"]

        #plot["plot_id"] = raw_movie["id"]
        #plot["plot"] = raw_movie["overview"]

        print (raw_movie["id"])

movie_filename = "/home/ubuntu/DeathStarBenchMirror/mediaMicroservices/datasets/tmdb/movies.json"
with open(movie_filename, 'r') as movie_file:
    raw_movies = json.load(movie_file)
    write_movie_info(raw_movies)
