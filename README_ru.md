# NAME

    gov-purchases-crawler

## DESCRIPTION

English version is available by [link](README_en.md)

Парсер FTP ресурса [ftp.zakupki.gov.ru](ftp://ftp.zakupki.gov.ru/fcs_regions)

Позволяет загружать и сохранять локально в БД данные по гос. закупкам. Поддерживается работа с СУБД PostgreSQL.
<!-- ... -->

## INSTALL

### Requirements

* Python 3.6 or above
* PostgreSQL

### Get source code and install

```bash
git checkout git@github.com:ruzhnikov/gov-purchases-crawler.git
cd gov-purchases-crawler
pip install -r requirements.txt
python setup.py test
python setup.py install
```

## USAGE

```bash
gov-purchases -c <config file> -f <'protocols' or 'notifications'> <OPTIONAL ARGUMENTS>
```