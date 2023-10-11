import re
import logging
from urllib.parse import urljoin
from collections import defaultdict

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, PEP_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def pep(session) -> list[str]:
    response = get_response(session, PEP_URL)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    section = find_tag(soup, 'section', {'id': 'numerical-index'})
    tag_t_body = find_tag(section, 'tbody')
    tags_tr = tag_t_body.find_all('tr')
    results = [('Статус', 'Количество')]
    status_dict = defaultdict(int)
    for tag_tr in tqdm(tags_tr):
        tag_abbr = find_tag(tag_tr, 'abbr').text
        status = tag_abbr[1:]
        tag_a = find_tag(tag_tr, 'a', {'class': 'pep reference internal'})
        url = urljoin(PEP_URL, tag_a['href'])
        response = get_response(session, url)
        if response is None:
            continue
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, features='lxml')
        tag_dl = find_tag(soup, 'dl', {'class': 'rfc2822 field-list simple'})
        pep_status = tag_dl.find(
            string='Status'
        ).parent.find_next_sibling('dd').string
        status_dict[pep_status] += 1
        expected_status = EXPECTED_STATUS.get(status)
        if pep_status not in expected_status:
            message = (f'Несовпадающие статусы:\n{url}\n'
                       f'Статус в карточку:{pep_status}\n'
                       f'Ожидаемые статуса: {expected_status}')
            logging.warning(message)
    results.append(
        (*status_dict.items(), ('Total', sum(status_dict.values())))
    )
    return results


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup,
                        'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div,
                           'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = session.get(version_link)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        results.append((version_link, h1.text, dl.text.replace('\n', '')))
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup,
                       'div',
                       attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    for a_tag in a_tags:
        link = a_tag['href']
        re_match = re.match(pattern, a_tag.text)
        if re_match:
            version, status = re_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    download_dir = BASE_DIR / 'downloads'
    response = get_response(session, downloads_url)
    if response is None:
        return
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(table_tag, 'a',
                          {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_tag = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_tag)
    filename = archive_url.split('/')[-1]
    download_dir.mkdir(exist_ok=True)
    archive_path = download_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
