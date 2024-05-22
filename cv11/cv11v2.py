from cassandra.cluster import Cluster
import time
import csv

'''
DPB - 11. cvičení Cassandra

Use case: Discord server - reálně používáno pro zprávy, zde pouze zjednodušená varianta.

Instalace python driveru: pip install cassandra-driver

V tomto cvičení se budou následující úlohy řešit s využitím DataStax driveru pro Cassandru.
Dokumentaci lze nalézt zde: https://docs.datastax.com/en/developer/python-driver/3.25/getting_started/

Optimální řešení (nepovinné) - pokud něco v db vytváříme, tak první kontrolujeme, zda to již neexistuje.

Pro uživatele PyCharmu:

Pokud chcete zvýraznění syntaxe, tak po napsání prvního dotazu se Vám u něj objeví žlutá žárovka, ta umožňuje vybrat 
jazyk pro tento projekt -> vyberte Apache Cassandra a poté Vám nabídne instalaci rozšíření pro tento typ db.
Zvýraznění občas nefunguje pro příkaz CREATE KEYSPACE.

Také je možné do PyCharmu připojit databázi -> v pravé svislé liště najděte Database a připojte si lokální Cassandru.
Řešení cvičení chceme s využitím DataStax driveru, ale s integrovaným nástrojem pro databázi si můžete pomoct sestavit
příslušně příkazy.

Pokud se Vám nedaří připojit se ke Cassandře v Dockeru, zkuste smazat kontejner a znovu spustit:

docker run --name dpb_cassandra -p 127.0.0.1:9042:9042 -p 127.0.0.1:9160:9160 -d cassandra:latest

'''


def print_delimiter(n):
    print('\n', '#' * 10, 'Úloha', n, '#' * 10, '\n')


def print_result(result):
    for row in result:
        print(row)


cluster = Cluster()  # automaticky se připojí k localhostu na port 9042
session = cluster.connect()

"""
1. Vytvořte keyspace 'dc' a přepněte se do něj (SimpleStrategy, replication_factor 1)
"""
print_delimiter(1)
session.execute("""
CREATE KEYSPACE IF NOT EXISTS ds WITH REPLICATION = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
    };
""")
session.set_keyspace('ds')


"""
2. V csv souboru message_db jsou poskytnuta data pro cvičení. V prvním řádku naleznete názvy sloupců.
   Vytvořte tabulku messages - zvolte vhodné datové typy (time bude timestamp)
   Primárním klíčem bude room_id a time
   Data chceme mít seřazené podle času, abychom mohli rychle získat poslední zprávy

   Jako id v této úloze zvolíme i time - zdůvodněte, proč by se v praxi time jako id neměl používat.

   Pokud potřebujeme použít čas, tak se v praxi používá typ timeuuid nebo speciální identifikátor, tzv. Snowflake ID
   (https://en.wikipedia.org/wiki/Snowflake_ID). Není potřeba řešit v tomto cvičení.
"""
print_delimiter(2)
session.execute("""
CREATE TABLE IF NOT EXISTS  messages (
    room_id int,
    speaker_id int,
    time timestamp,
    message text,
    PRIMARY KEY (room_id, time)
) WITH CLUSTERING ORDER BY (time DESC);
""")


"""
3. Do tabulky messages importujte message_db.csv
   COPY není možné spustit pomocí DataStax driveru ( 'copy' is a cqlsh (shell) command rather than a CQL (protocol) command)
   -> 2 možnosti:
      a) Nakopírovat csv do kontejneru a spustit COPY příkaz v cqlsh konzoli uvnitř dockeru
      b) Napsat import v Pythonu - otevření csv a INSERT dat
CSV soubor může obsahovat chybné řádky - COPY příkaz automaticky přeskočí řádky, které se nepovedlo správně parsovat
"""
print_delimiter(3)
with open('message_db.csv', 'r') as file:
    csv_reader = csv.reader(file, delimiter=';')
    next(csv_reader)
    for line in csv_reader:
        session.execute("""
        INSERT INTO messages (room_id, speaker_id, time, message) 
        VALUES (%s, %s, %s, %s);
        """, (int(line[0]), int(line[1]), line[2], line[3]))


"""
4. Kontrola importu - vypište 1 zprávu
"""
print_delimiter(4)
result = session.execute("""
SELECT * FROM messages LIMIT 1;
""")
print_result(result)


"""
5. Vypište posledních 5 zpráv v místnosti 1 odeslaných uživatelem 2
    Nápověda 1: Sekundární index (viz přednáška) 
    Nápověda 2: Data jsou řazena již při vkládání
"""
print_delimiter(5)
session.execute("CREATE INDEX IF NOT EXISTS speaker_index ON messages (speaker_id);")
result = session.execute("""
SELECT * FROM messages 
WHERE room_id = 1 AND speaker_index = 2 
LIMIT 5;
""")
print_result(result)

"""
6. Vypište počet zpráv odeslaných uživatelem 2 v místnosti 1
"""
print_delimiter(6)
result = session.execute("""
SELECT COUNT(*) FROM messages 
WHERE speaker_id = 2 AND room_id = 1;
""")
print_result(result)

"""
7. Vypište počet zpráv v každé místnosti
"""
print_delimiter(7)
result = session.execute("""
SELECT room_id, COUNT(*) FROM messages
GROUP BY room_id;
""")
print_result(result)

"""
8. Vypište id všech místností (3 hodnoty)
"""
print_delimiter(8)
result = session.execute("""
SELECT DISTINCT room_id FROM messages;
""")
print_result(result)

"""
Bonusové úlohy:

1. Pro textovou analýzu chcete poskytovat anonymizovaná textová data. Vytvořte Materialized View pro tabulku messages,
který bude obsahovat pouze čas, room_id a zprávu.

Vypište jeden výsledek z vytvořeného view

Před začátkem řešení je potřeba jít do souboru cassandra.yaml uvnitř docker kontejneru a nastavit enable_materialized_views=true

docker exec -it dpb_cassandra bash
sed -i -r 's/enable_materialized_views: false/enable_materialized_views: true/' /etc/cassandra/cassandra.yaml

Poté restartovat kontejner
"""
print_delimiter('Bonus 1')
session.execute("""
CREATE MATERIALIZED VIEW messages_anonymized AS
    SELECT room_id, time, message
    FROM messages
    WHERE room_id IS NOT NULL AND time IS NOT NULL AND message IS NOT NULL
    PRIMARY KEY (room_id, time) WITH CLUSTERING ORDER BY (time DESC);
""")


"""
2. Chceme vytvořit funkci (UDF), která při výběru dat vrátí navíc příznak, zda vybraný text obsahuje nevhodný výraz.

Vyberte jeden výraz (nemusí být nevhodný:), vytvořte a otestujte Vaši funkci.

Potřeba nastavit enable_user_defined_functions=true v cassandra.yaml

sed -i -r 's/enable_user_defined_functions: false/enable_user_defined_functions: true/' /etc/cassandra/cassandra.yaml
"""
print_delimiter('Bonus 2')
session.execute("""
CREATE OR REPLACE FUNCTION contains_inappropriate(text text)
    CALLED ON NULL INPUT
    RETURNS boolean
    LANGUAGE java
    AS '
    return text.contains("inappropriate");
    ';
""")
result = session.execute("""
SELECT contains_inappropriate('This is inappropriate text');
""")
print_result(result)


"""
3. Zjistěte čas odeslání nejnovější a nejstarší zprávy.

4. Zjistěte délku nejkratší a nejdelší zprávy na serveru.	

5. Pro každého uživatele zjistěte průměrnou délku zprávy.		

V celém cvičení by nemělo být použito ALLOW FILTERING.
"""

session.execute("DROP FUNCTION IF EXISTS contains_inappropriate;")
session.execute("DROP MATERIALIZED VIEW IF EXISTS messages_anonymized;")
session.execute("TRUNCATE TABLE IF EXISTS messages")
session.execute("DROP TABLE IF EXISTS messages;")
session.execute("DROP KEYSPACE IF EXISTS ds;")
cluster.shutdown()

