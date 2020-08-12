# BulletinBot V 0.1

A simple prototype of an automated and personalized audio based news bulletin.

The automated news bulletin system’s personalization approach centres around a pair of article corpora that represent (1) an archive of news items and (2) a selection of articles that a hypothetical user has previously read. In the case of our corpora the news articles have been scraped from the website of the CBC, and each article record features information about the article’s publication date, title, full body text, and up to three sections the articles have been added to, an example being: news, Canada, Toronto. Each corpus is stored as a comma-separated text file, which is included in this repository.

By comparing the corpus of articles that a user has previously read to the larger corpus of all news articles, a list of recommended articles from the news archive are selected. Our personalization approach uses a rather basic but common technique used in information retrieval studies of employing term-frequency-inverse document frequency (TF-IDF) measures alongside cosine similarity calculations, to determine the similarity between our user’s perceived interests—as represented in the user interest corpus—to the larger archive of articles.

We have simplified the article comparisons, by performing the TF-IDF calculation on a custom string created for each article that combines the article’s three possible sections, with its title and the article’s first one or two paragraphs, which in journalism is commonly called the lede. This approach was chosen because the sections, titles, and lede of an article most often represent the core elements of what a story is about, and would make for a stronger possible comparison. The TF-IDF and cosine similarity calculations are performed using the Scikit-learn Python machine learning library.

A simple news bulletin script is created from the top five articles that most match the user’s interests. This text-based script can then be synthesized into speech using either the pyttsx3 text-to-speech conversion Python library or IBM Watson’s paid text-to-speech service for more realistic voice reproduction. In both cases results are saved as an MP3 audio file.

All settings for this script are set in the settings.ini file.

In the settings.ini file, you can specify the file name of the article archive and user article corpora. If you intend to use IBM Watson's text-to-speech you can set the API key and service url in the settings.ini file. You can also change the name of the MP3 file that is saved with either Watson or pyttsx3 implementation. Finally, you can also set the number of news items you would like included in the news bulletin script.

To run this script using IBM Watson's text-to-speech system use the -w or -Watson command line argument, for example the script would be run as such :

python bulletinBot.py -w

or

python bulletinBot.py -Watson

Watson was chosen because it has free tier that doesn't require a credit card, although you are limited to 10,000 characters synthesis a month. Watson definitely sounds better pyttsx3.

An example of the MP3 output of both the Watson and pyttsx3 text-to-speech implementation is included in the repository.

This system has only been tested on a Windows 10 machine, pyttsx3 is supposed to work on Linux and MacOS but haven't had chance to test it yet.

This project is a work in progress. A few things I would like to add :
- support for other cloud based text-to-speech implementations
- more complex use of SSML
- a better free / open source text-to-speech implementation that employs SSML
