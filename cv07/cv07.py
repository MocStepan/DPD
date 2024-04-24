from elasticsearch import Elasticsearch

INDEX_NAME = 'person'


def print_delimiter(n):
    print('\n', '#' * 10, 'Úloha', n, '#' * 10, '\n')


# Připojení k ES
es = Elasticsearch(
    [
        {'host': 'localhost', 'port': 9200, 'scheme': 'https'}
    ],
        basic_auth=('elastic', 'elastic'),
        verify_certs=False
    )

# Kontrola zda existuje index 'person'
# if not es.indices.exists(index=INDEX_NAME):
#     # Vytvoření indexu
#     es.indices.create(index=INDEX_NAME)

# Index není potřeba vytvářet - pokud neexistuje, tak se automaticky vytvoří při vložení prvního dokumentu

# 1. Vložte osobu se jménem John
print_delimiter(1)
person = {
    'name': 'John'
}
resp = es.index(index=INDEX_NAME, body=person)
print(resp)

# 2. Vypište vytvořenou osobu (pomocí get a parametru id)
print_delimiter(2)
resp = es.get(index=INDEX_NAME, id=resp['_id'])
print(resp)

# 3. Vypište všechny osoby (pomocí search)
print_delimiter(3)
all = es.search(index=INDEX_NAME, query={"match_all": {}})
print(all)

# 4. Přejmenujte vytvořenou osobu na 'Jane'
print_delimiter(4)
person = {
    'name': 'Jane'
}
resp = es.index(index=INDEX_NAME, id=resp['_id'], body=person)
print(resp)

# 5. Smažte vytvořenou osobu
print_delimiter(5)
resp = es.delete(index=INDEX_NAME, id=resp['_id'])
print(resp)

# 6. Smažte vytvořený index
print_delimiter(6)
resp = es.indices.delete(index=INDEX_NAME)
print(resp)
