# -*- coding: utf-8 -*-

import copy
import json
import random
import re

import requests
import lxml.etree
import lxml.html


class config:
    API_URI = 'https://en.wikipedia.org/w/api.php?action=parse&format=json'

def scaffold_payload(payload):

    defaults = {
        'prop': 'text|images',
        'uselang': 'en'}

    payload = copy.deepcopy(payload);
    payload.update(defaults)
    return payload

def fetch(topic):
    '''fetches data about a topic'''
    payload = {'page': topic}
    payload = scaffold_payload(payload)

    response = requests.post(config.API_URI, payload)

    # TODO: add checks against response code
    data = json.loads(response.content)
    data = data['parse']['text']['*']

    selector = lxml.etree.HTML(data)

    # I'm really not sure how or why this redirect happens, but I'm guessing
    # it redirects you to another page that may have been merged with another,
    # so we basically try to fetch the data from that other page.
    try:
        redirect = selector.xpath('//*[contains(@class,"redirectMsg")]/a/text()').pop()

        # recursively search for the next suggestion
        # XXX: can this his the recursion limit? find a better alternative
        return fetch(redirect)
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
        title = re.search("/wiki\/(.*)$", next_link).groups()[0].replace("\#.*", "")

        # how I wish python implmented tail call elimination :(
        return fetch(title)

    first = selector.xpath('//p')

    # filter out those paragraphs that have a link with a title attribute
    first = filter(lambda e: e.xpath('a[@title]'), first)

    # choose a random para from the first five paragraphs
    first = random.choice(first[:5])

    links = None
    if not first:
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
            'not(contains(@href,":") and '
            'not(contains(@href,"wiktionary") and '
            'not(contains(@href,"wikimedia") and '
            'not(@class="external") and '
            'not(@class="new") and '
            'not(contains(@title,"Edit")]')

    # if we can't find a valid link, follow an old link
    if not links:
        links = selector.xpath(
            '//p/a[@title and '
            'not(contains(@href,":") and '
            'not(contains(@href,"wiktionary") and '
            'not(contains(@href,"wikimedia") and '
            'not(@class="external") and '
            'not(@class="new") and '
            'not(contains(@title,"Edit")]')

    link = random.choice(links)
    title = re.search("/wiki\/(.*)$", link)
    title = re.sub("\#.*", "", title)
    images = selector.xpath('//*[contains(@class,"thumbinner")]')

    # TODO: images

    return first

