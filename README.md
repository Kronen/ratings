FaRatings (FilmAffinityRatings)
=========================

FaRatings is a rating finder to visualize in plain text (csv file) your movie ratings ordered from higher to lower.
Modify the script to add the path to a folder containing your movie files and it will try to guess the title from the filenames and write to a file the ratings for those movies.


Acknowlegements
--------------------------

All the data about movies is downloaded from [FilmAffinity](http://filmaffinity.com), using  [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup) to get the data.

FaRatings also uses [requests](https://github.com/kennethreitz/requests), [guessit](http://guessit.io) and [progressbar2](http://progressbar-2.readthedocs.io/).
