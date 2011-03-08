import activity


class WikipediaActivityEN(activity.WikipediaActivity):

    def __init__(self, handle):
        self.WIKIDB = 'en_US_g1g1/en_US_g1g1.xml.bz2'
        self.HOME_PAGE = '/static/index_en.html'
        self.HTTP_PORT = '8001'
        activity.WikipediaActivity.__init__(self, handle)
