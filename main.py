from bs4 import BeautifulSoup as BS
import requests as r
import requests_cache
import json
import subprocess

requests_cache.install_cache('pypi_cache', expire_after=60*60*24)

# Do searches via the PyPI website [more relevant searches and filters!]
def search(query, order='relevance', classifiers=[], page=1):
    """Search for PyPI packages via pypi.org.
    Parameters:
        query (str): Your query to the search engine
        order (str): Orders the first page of search results.
            'relevance' (default): Sorts by relevance.
            'last_updated': Sorts by last date updated.
            'trending': Sorts by trending.
        classifiers (list): Any apppicable classifiers. [https://pypi.org/classifiers/]
        page (int): Search results page number.classifiers
    Returns:
        results (list): Returns list of search results.
    """

    params = {'q': query, 'c': classifiers, 'page': page} # Declare parameters and add the queries and classifiers

    # Append params dict depending on args
    if order == 'relevance':
        params['o'] = ''
    elif order == 'last_updated':
        params['o'] = '-created'
    elif order == 'trending':
        params['o'] = '-zscore'

    # Make the request and parse for the data we need.
    response = r.get(f'https://pypi.org/search/', params=params)
    results = [item.string for item in BS(response.text, 'html.parser').find_all(class_='package-snippet__name')]
    if results == []:
        print('Cannot be found. Try another search!')
    else:
        return results

def project(package_name, version=None):
    if version == None:
        return r.get(f'https://pypi.python.org/pypi/{package_name}/json').json()
    else:
        return r.get(f'https://pypi.python.org/pypi/{package_name}/{version}/json').json()

def pypistats(package_name):
    response = r.get(f'https://pypistats.org/api/packages/{package_name.lower()}/recent')
    if response.status_code == 404:
        return 0
    else:
        return response.json()['data']['last_month']

def installed_packages(filters=None):

    def argparse(filters):
        filter_list = []

        if filters == None:
            return filter_list

        if 'outdated' in filters:
            filter_list.append('--outdated')
        elif 'uptodate' in filters:
            filter_list.append('--uptodate')
        
        if 'editable' in filters:
            filter_list.append('--editable')
        elif 'exclude-editable' in filters:
            filter_list.append('--exclude-editable')
        elif 'include-editable' in filters:
            filter_list.append('--include-editable')
        
        if 'local' in filters:
            filter_list.append('--local')
        if 'user' in filters:
            filter_list.append('--user')
        if 'pre' in filters:
            filter_list.append('--pre')
        
        if 'not_required' in filters:
            filter_list.append('--not-required')
        return filter_list
    

    installs = json.loads(subprocess.run(['pip', 'list', '--format', 'json'] + argparse(filters), stdout=subprocess.PIPE).stdout.decode('UTF-8'))
    return [(item['name'], item['version']) for item in installs]

def display_prep(results):
    packages = []
    for result in results:
        if type(result) == tuple:
            try:
                packages.append(project(result[0], result[1]))
            except json.decoder.JSONDecodeError:
                heyo = project(result[0])
                heyo['info']['version'] = f'{result[0]} - This version isn\'t available on PyPI showing info for latest version.'
                packages.append(heyo)
        else:
            packages.append(project(result))
    packages_dict_list = []
    for package in packages:
        new_package = {}
        new_package['name'] = (package['info']['name'])
        new_package['version'] = (package['info']['version'])
        new_package['summary'] = (package['info']['summary'])
        new_package['author'] = (package['info']['author'])
        new_package['downloads'] = (pypistats(package['info']['name']))
        packages_dict_list.append(new_package)
    return packages_dict_list

def display(prep_list, filter=None):
    if filter == 'installs':
        prep_list = sorted(prep_list, key = lambda i: i['downloads'])
    if filter == 'name':
        prep_list = sorted(prep_list, key = lambda i: i['name'].lower()) 

    for item in prep_list:
        print(item['name'])
        print(item['version'])
        print(item['summary'])
        print(item['author'])
        print(item['downloads'])
        print('========================================')