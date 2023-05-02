# region imports
from AlgorithmImports import *
# natural language tool kit
from nltk.sentiment import SentimentIntensityAnalyzer
# endregion

class TwitterAlgorithm(QCAlgorithm):

    def Initialize(self):
        # set the date to Kaggle's available Richard Branson tweet data
        self.SetStartDate(2012, 11, 1)
        self.SetEndDate(2017, 1, 1)
        self.SetCash(100000)

        # add data to use, set to minute data because
        # tweets can come on anytime of the day and we do
        # have timestamp on the tweets data 
        self.spce = self.AddEquity("SPCE", Resolution.Minute).Symbol

        # add custom data and name. The resolution here determines how often new tweet data is polled
        self.branson = self.AddData(Tweet, "BRANSONTWTS", Resolution.Minute).Symbol

        # schedule event for exiting the trade
        self.Schedule.On(self.DateRules.EveryDay(self.spce),
                        self.TimeRules.BeforeMarketClose(self.spce, 15),
                        self.ExitPositions)

    def OnData(self, data: Slice):
        if self.branson in data:
            score = data[self.branson].Value
            content = data[self.branson].Tweet

            # if compound score is higher than 0.5 buy
            if score > 0.5:
                self.SetHoldings(self.spce, 1)
            # if compound score is lower than -0.5 buy
            elif score < -0.5:
                self.SetHoldings(self.spce, -1)

            # log any score above 0.5 for both short and long
            if abs(score) > 0.5:
                self.Log(f"Score {score}, Tweet {content}")

    def ExitPositions(self):
        self.Liquidate()

class Tweet(PythonData):

    # create instance of SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()

    def GetSource(self, config, date, isLiveMode):
        # use dl=1 parameter on the end. dl=1 stands for download from url and dl=0 is to view in the browser 
        source = "<csv file share location of preprocessed data>"
        # return SubscriptionDataSource object
        # keep in mind for live you should use a stream of rest feed.
        return SubscriptionDataSource(source = source, transportMedium = SubscriptionTransportMedium.RemoteFile)

    # receives remote file by line by line basis
    def Reader(self, config, line, date, isLiveMode):
        # check if we have valid data to process
        # check if line is not empty string
        # check if first character is a digit
        if not (line.strip() and line[0].isdigit()):
            return None

        # split csv by comma
        data = line.split(',')
        # data is now a list with two elements
        tweet = Tweet()
        
        # try catch some unexpected errors might occur
        # because of using custom data
        try:
            # config parameter from Reader method
            tweet.Symbol = config.Symbol
            # format datetime and save to Time
            tweet.Time = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") + timedelta(minutes = 1)
            # save tweet to content
            content = data[1].lower()

            # perform sentiment analysis
            if "spce" in content or "virgin galactic" or "galactic" in content:
                # returns a dictionary with string keys and float values
                tweet.Value = self.sia.polarity_scores(content)["compound"]
            else:
                # assign zero to score it as a neutral tweet
                tweet.Value = 0

            # to make the content also accessible in the data bar
            # create new property for tweet object and assign content to this property
            tweet["Tweet"] = str(content)
        
        except ValueError:
            return None

        return tweet
