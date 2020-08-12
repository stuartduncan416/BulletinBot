import pandas as pd
import pyttsx3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time
from ibm_watson import TextToSpeechV1
from ibm_watson import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import configparser
import io
import sys
import getopt

tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 1), min_df=0, stop_words='english')

def readArticles(csvFile):

    articlesDf = pd.read_csv(csvFile)
    articlesDf = articlesDf.fillna("")

    # convert the date string into a pandas datetime
    articlesDf['pubdate'] = pd.to_datetime(articlesDf['pubdate'])

    # create a field for lede
    articlesDf['lede'] = articlesDf.apply(firstPara, axis = 1)

    #created a field for the combined data that we will perform tfidf on
    articlesDf['tfidfText'] = articlesDf[['section1', 'section2', 'section3', 'title', 'lede']]. apply(lambda x: ' '.join(x), axis=1)

    return(articlesDf)


def firstPara(row):

    # split the body text into paragraphs and return the first paragraph

    artricleParas = row["body"].splitlines()
    if(len(artricleParas) > 0):
        return(artricleParas[0])
    else:
        return("")

def tdifArticles(articlesDf):

    tfidf_matrix = tf.fit_transform(articlesDf['tfidfText'].values.astype('U'))
    return(tfidf_matrix)

def tdifUser(userArticles, articlesMatrix):

    allUserTdifCombined = [userArticles['tfidfText'].str.cat(sep=' ')]
    user_tfidf = tf.transform(allUserTdifCombined)
    cos_similarity_tfidf = map(lambda x: cosine_similarity(user_tfidf, x),articlesMatrix)
    return(list(cos_similarity_tfidf))

def outputRecommendations(output, articlesCorpus):

    top = sorted(range(len(output)), key=lambda i: output[i], reverse=True)[:100]
    listScores = [output[i][0][0] for i in top]
    resultsDf = getRecomendations(top,articlesCorpus,listScores)

    print("=====================================")

    print("Top 10 recommended articles for user")

    for index, row in resultsDf.iterrows():
        print("{}. {}  Score : {}".format(index + 1, row["title"], row["score"]))
        if(index == 9):
            break

    print("=====================================")

    return(resultsDf)

def getRecomendations(top, articles, scores):
    recommendation = pd.DataFrame(columns = ['id', 'title', 'body',  'score'])
    count = 0

    for i in top:

        recommendation.at[count, 'id'] = articles['id'][i]
        recommendation.at[count, 'title'] = articles['title'][i]
        recommendation.at[count, 'body'] = articles['body'][i]
        recommendation.at[count, 'score'] =  scores[count]
        count += 1

    return recommendation

def makeScript(results,method, numberOfItems=5):

    scripts = []

    # add SSML tags if synthesizing with watson

    if(method == "watson"):
        scripts.append("<speak version='1.0' xmlns='https://www.w3.org/2001/10/synthesis' xml:lang='en-US'>")

    for index, row in results.iterrows():

        if(index == int(numberOfItems)):
            break

        articleParas = row["body"].splitlines()
        articleParas = list(filter(None, articleParas))

        if(len(articleParas) > 0):

            if(len(articleParas[0]) > 30) :

                # check to see if the first para is somewhat short, if it is
                # add the second paragraph to the script aswell

                if(len(articleParas[0]) < 200) :
                    newword = articleParas[0] + " "  + articleParas[1]
                    scripts.append(newword)
                else:
                    scripts.append(articleParas[0])

        if(method == "watson"):
            scripts.append("<break time='1s'/>")

    if(method == "watson"):
        scripts.append("</speak>")

    return(scripts)


def makeMP3(scripts, method, apiKey=None, serviceUrl=None, watsonFilename=None, pyttsx3Filename=None):

    if(method == "pyttsx3"):

        engine = pyttsx3.init()
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate-50)
        finalScript = " ".join(scripts)

        print("\nFinal script :\n {}".format(finalScript))

        engine.save_to_file(scripts,pyttsx3Filename)
        engine.runAndWait()

        print("\nNews bulletin created with filename {}".format(pyttsx3Filename))

    elif(method == "watson"):

        authenticator = IAMAuthenticator(apiKey)

        text_to_speech = TextToSpeechV1(
            authenticator=authenticator
        )

        text_to_speech.set_service_url(serviceUrl)

        finalScript = " ".join(scripts)

        print("\nFinal script :\n {}".format(finalScript))

        try:

            with open(watsonFilename, 'wb') as audio_file:

                audio_file.write(
                        text_to_speech.synthesize(
                            finalScript,
                            voice='en-US_AllisonV3Voice',
                            accept='audio/mp3'
                        ).get_result().content)

        except ApiException as ex:
            print("Method failed with status code " + str(ex.code) + ": " + ex.message)


        print("\nNews bulletin created with filename {}".format(watsonFilename))


def getIni(filename):

    config = configparser.ConfigParser()
    config.read(filename)
    return(config)


if __name__ == "__main__":

    # read the configuartion file
    configSettings = getIni("settings.ini")

    articleCorpusCSV = configSettings["csvfiles"]["articleCorpusCSV"]
    userArticleCorpusCSV = configSettings["csvfiles"]["userArticleCorpusCSV"]
    watsonAPIKey = configSettings["watson"]["apiKey"]
    watsonServiceURL = configSettings["watson"]["serviceUrl"]
    watsonFilename = configSettings["filenames"]["watsonFile"]
    pyttsx3Filename = configSettings["filenames"]["pyttsx3File"]
    numberOfItems = configSettings["settings"]["numberOfItems"]

    userArticlesCorpus = readArticles(userArticleCorpusCSV)
    articlesCorpus = readArticles(articleCorpusCSV)

    # read the command line options
    argumentList = sys.argv[1:]
    options = "w"
    longOptions = ["Watson"]

    try :

        arguments, values = getopt.getopt(argumentList, options, longOptions)

        for currentArgument, currentValue in arguments:

            if currentArgument in ("-w", "--Watson"):
                method = "watson"

        if(len(arguments) == 0):
            method = "pyttsx3"

    except getopt.error as err:
        print (str(err))

    # perform TFIDF on the article corpus
    articlesMatrixContext = tdifArticles(articlesCorpus)

    # perform TFIDF on the combined User Corpus and find similarities with
    # article corpus
    output=tdifUser(userArticlesCorpus, articlesMatrixContext)

    # determine the topic recommended articles
    results = outputRecommendations(output, articlesCorpus)

    # make the news bulletin scripsts
    scripts = makeScript(results, method, numberOfItems)

    # make the mp3 with the script
    makeMP3(scripts, method, watsonAPIKey, watsonServiceURL, watsonFilename, pyttsx3Filename)
