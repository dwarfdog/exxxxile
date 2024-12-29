#!/usr/bin/env python3
# /nexus/utils/news.py

from xml.dom import minidom
from django.db import connection

def parse_news():
    """
    Récupère et analyse les actualités stockées dans la base de données.

    Returns:
        list: Une liste d'éléments d'actualités, chaque élément étant un dictionnaire contenant les champs pertinents.
    """
    news_list = []

    with connection.cursor() as cursor:
        cursor.execute('SELECT id, xml FROM news')
        for news_id, xml_content in cursor.fetchall():
            try:
                xmldoc = minidom.parseString(xml_content)
                readbitlist = xmldoc.getElementsByTagName('item')

                for item in readbitlist:
                    parsed_item = {
                        'title': item.getElementsByTagName('title')[0].childNodes[0].data,
                        'description': item.getElementsByTagName('description')[0].childNodes[0].data,
                        'author': item.getElementsByTagName('author')[0].childNodes[0].data,
                        'pubDate': item.getElementsByTagName('pubDate')[0].childNodes[0].data,
                    }
                    news_list.append(parsed_item)

            except Exception as e:
                # Gestion d'erreur en cas de problème avec le parsing XML
                continue

    return news_list

