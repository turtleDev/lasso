# -*- coding: utf-8 -*-

'''

    ahoy! welcome to lasso!

    usage:
        >>> import lasso
        >>> for chunk in lasso.fetch('tomato'):
        ...     print chunk

    that's pretty much it.

    happy hunting!

    NOTE:
        The order in which the results come in seem to be
        random and sometimes even irrelevent. I would
        recommend that you use some form or relevance
        evaluation to optimize selection of follow up topics
'''

import copy
import json
import random
import re
import urllib

import requests
import lxml.etree
import lxml.html
from kitchen.text.converters import to_unicode


__all__ = ['fetch']


class config:
    API_URI = 'https://en.wikipedia.org/w/api.php?action=parse&format=json'


def fetch(topic, chunks=5):
    '''fetches data about a topic'''

    count = 0
    topic = urllib.unquote(topic)
    payload = {
        'page': topic,
        'prop': 'text|images',
        'uselang': 'en'}

    while count < chunks:

        response = requests.post(config.API_URI, payload)

        # TODO: add checks against response code
        data = json.loads(response.content)
        data = data['parse']['text']['*']

        selector = lxml.etree.HTML(data)

        # I'm really not sure how or why this redirect happens, but I'm guessing
        # it redirects you to another page that may have been merged with another,
        # so we basically try to fetch the data from that other page.
        try:
            redirect = selector.xpath(
                '//*[contains(@class,"redirectMsg")]/a/text()').pop()

            payload['page'] = redirect
            continue
        except IndexError:
            pass

        # handle disambiguations
        disambig = selector.xpath('//*[@id="disambigbox"]')
        if disambig:
            disambig_links = selector.xpath(
                '//a[@title and '
                'not(contains(@href,":")) and '
                'not(contains(@href,"wikitionary")) and '
                'not(contains(@href,"wikimedia")) and '
                'not(@class="external") and '
                'not(@class="new")]')

            next_link = random.choice(disambig_links)

            # this _may_ throw an IndexError
            title = re.search(
                "/wiki\/(.*)$", next_link).groups()[0].replace("\#.*", "")

            # # how I wish python implmented tail call elimination :(
            # return fetch(title)
            payload['page'] = title
            continue

        first = selector.xpath('//p//a[@title]/ancestor::p')

        # # filter out those paragraphs that have a link with a title attribute
        # first = filter(lambda e: e.xpath('a[@title]'), first)

        # choose a random para from the first five paragraphs
        try:
            first = random.choice(first[:5])
        except IndexError:
            first = []

        links = None

        if len(first) == 0:
            links = selector.xpath(
                '//a[@title and '
                'not(contains(@href,":")) and '
                'not(contains(@href,"wiktionary")) and '
                'not(contains(@href,"wikimedia")) and '
                'not(@class="external") and '
                'not(@class="new") and '
                'not(contains(@title,"Edit"))]')
        else:
            # this block makes *NO* sense to me

            # convert the para to html
            first = lxml.html.tostring(first)

            try:
                blob = re.search(".*?title=.*?\.(\s|\n|$)", first).groups()[0]
            except AttributeError:
                blob = ''

            links = lxml.etree.HTML('<p>' + blob + '</p>').xpath(
                '//a[@title and '
                'not(contains(@href,":")) and '
                'not(contains(@href,"wiktionary")) and '
                'not(contains(@href,"wikimedia")) and '
                'not(@class="external") and '
                'not(@class="new") and '
                'not(contains(@title,"Edit"))]')

        # if we can't find a valid link, follow an old link
        if not links:
            links = selector.xpath(
                '//p//a[@title and '
                'not(contains(@href,":")) and '
                'not(contains(@href,"wiktionary")) and '
                'not(contains(@href,"wikimedia")) and '
                'not(@class="external") and '
                'not(@class="new") and'
                'not(contains(@title,"Edit"))]')

        link = random.choice(links)
        link = link.xpath('@href').pop()
        title = re.search("/wiki\/(.*)$", link).groups()[0]
        title = re.sub("\#.*", "", title)
        images = selector.xpath('//*[contains(@class,"thumbinner")]')

        # TODO: images

        if isinstance(first, lxml.etree._Element):
            result = lxml.html.tostring(first)
        else:
            result = first

        if isinstance(result, list) is False:

            # get rid of refs
            result = re.sub("<sup.*?>.*?</sup>", "", result)

            # extract the text
            result = re.sub('<\/?[^<>]*>', '', result)

            result = to_unicode(result)

            yield {
                'title': payload['page'],
                'data': result}

            count += 1

        title = urllib.unquote(title)
        payload['page'] = title
