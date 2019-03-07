from rest_framework.views import APIView
from rest_framework.response import Response
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

import bs4
import requests

class PageDataView(APIView):
    def get(self, request):
        return Response(request.session.items())

    def post(self, request):
        url = self.request.data['url']
        if url in request.session.keys():
            return Response(request.session[url])
        self.process_url(url)
        request.session[url] = request.data
        return Response(request.data)

    def process_url(self, url):
        try:
            page_data = urllib_request.urlopen(url)
        except HTTPError as e:
            self.request.data['error message'] = e.msg
            self.request.data['status code'] = e.code
            return
        soup = bs4.BeautifulSoup(page_data.read())
        title = self.get_title(soup)
        external_links, internal_links, inaccessible_links = self.get_links_info(soup)
        doctype = self.get_doctype(soup)
        headings_data = self.get_headings_info(soup)
        self.request.data['headings'] = headings_data
        self.request.data['title'] = title
        self.request.data['external_links'] = len(external_links)
        self.request.data['internal_links'] = len(internal_links)
        self.request.data['inaccessible_links'] = inaccessible_links
        self.request.data['html_version'] = self.get_html_version_from_doctype(doctype)

    def get_title(self, soup):
        return soup.title.string

    def get_links_info(self, soup):
        links = [link.get('href') for link in soup.find_all('a')]
        external_links = [link for link in links if "//" in link] if links else []
        internal_links = [link for link in links if "//" not in link] if links else []
        inaccessible_links = 0

        for link in external_links:
            try:
                is_inaccessible = requests.get(link).status_code != 200
            except requests.exceptions.ConnectionError:
                is_inaccessible = True
            if is_inaccessible:
                inaccessible_links += 1
        return external_links, internal_links, inaccessible_links

    def get_doctype(self, soup):
        items = [item for item in soup.contents if isinstance(item, bs4.Doctype)]
        return items[0] if items else None


    def get_html_version_from_doctype(self, doctype):
        doctype_to_version = {
            'html': 'HTML 5',
            'html public "-//w3c//dtd html 4.01//en"':
                'HTML 4.01 Strict',
            'html public "-//w3c//dtd html 4.01 transitional//en"':
                'HTML 4.01 Transitional',
            'html public "-//w3c//dtd html 4.01 frameset//en"':
                'HTML 4.01 Frameset',
            'html public "-//w3c//dtd xhtml 1.0 strict//en"':
                'XHTML 1.0 Strict',
            'html public "-//w3c//dtd xhtml 1.0 transitional//en"':
                'XHTML 1.0 Transitional',
            'html public "-//w3c//dtd xhtml 1.0 frameset//en"':
                'XHTML 1.0 Frameset',
            'html public "-//w3c//dtd xhtml 1.1//en"':
                'XHTML 1.1'}
        doctype_splitted = doctype.split("\n")[0].lower()
        if doctype_splitted in doctype_to_version.keys():
            return doctype_to_version[doctype_splitted]
        else:
            return "unknown"

    def get_headings_info(self, soup):
        headings_data = {}
        for i in range(1, 7):
            headings = soup.find_all("h{0}".format(i))
            headings_data['h{0}'.format(i)] = len(headings)
        return headings_data

