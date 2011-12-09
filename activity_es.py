import activity


class WikipediaActivityES(activity.WikipediaActivity):

    def __init__(self, handle):
        self.WIKIDB = 'es_new/eswiki-20111112-pages-articles.xml'
        self.HOME_PAGE = '/static/index_es.html'
        self.HTTP_PORT = '8000'
        activity.WikipediaActivity.__init__(self, handle)
