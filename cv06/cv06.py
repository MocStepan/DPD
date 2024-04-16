from init import collection

'''
DPB - 6. cvičení - Agregační roura a Map-Reduce

V tomto cvičení si můžete vybrat, zda ho budete řešit v Mongo shellu nebo pomocí PyMongo knihovny.

Před testováním Vašich řešení si nezapomeňte zapnout Mongo v Dockeru - používáme stejná data jako v minulých cvičeních.

Pro pomoc je možné např. použít https://api.mongodb.com/python/current/examples/aggregation.html a přednášku.

Všechny výsledky limitujte na 10 záznamů. Nepoužívejte české názvy proměnných!

Struktura záznamu v db:
{
  "address": {
     "building": "1007",
     "coord": [ -73.856077, 40.848447 ],
     "street": "Morris Park Ave",
     "zipcode": "10462"
  },
  "borough": "Bronx",
  "cuisine": "Bakery",
  "grades": [
     { "date": { "$date": 1393804800000 }, "grade": "A", "score": 2 },
     { "date": { "$date": 1378857600000 }, "grade": "A", "score": 6 },
     { "date": { "$date": 1358985600000 }, "grade": "A", "score": 10 },
     { "date": { "$date": 1322006400000 }, "grade": "A", "score": 9 },
     { "date": { "$date": 1299715200000 }, "grade": "B", "score": 14 }
  ],
  "name": "Morris Park Bake Shop",
  "restaurant_id": "30075445"
}
'''


def print_delimiter(n):
    print('\n', '#' * 10, 'Úloha', n, '#' * 10, '\n')


'''
Agregační roura
Zjistěte počet restaurací pro každé PSČ (zipcode)
 a) seřaďte podle zipcode vzestupně
 b) seřaďte podle počtu restaurací sestupně
Výpis limitujte na 10 záznamů a k provedení použijte collection.aggregate(...)
'''
print_delimiter('1 a)')

data = collection.aggregate([
      {'$group': {'_id': '$address.zipcode', 'count': {'$sum': 1}}},
      {'$sort': {'_id': 1}},
      {'$limit': 10}
])
for line in data:
   print(line)


print_delimiter('1 b)')
'''
Agregační roura

Restaurace obsahují pole grades, kde jsou jednotlivá hodnocení. Vypište průměrné score pro každou hodnotu grade.
V agregaci vynechte grade pro hodnotu "Not Yet Graded" (místo A, B atd. se může vyskytovat tento řetězec).

'''
data = collection.aggregate([
    {'$unwind': '$grades'},
    {'$match': {'grades.grade': {'$ne': 'Not Yet Graded'}}},
    {'$group': {'_id': '$grades.grade', 'average_score': {'$avg': '$grades.score'}}}
])
for line in data:
   print(line)

print_delimiter('2 a)')
'''
Najdi restaruce, která má více než 3 hodnocení a jedno znich je A a zobrazte průměrné score a počet hodnocení.
'''
data = collection.aggregate([
      {'$unwind': '$grades'},
      {'$match': {'grades.grade': {'$eq': 'A'}}},
      {'$group': {'_id': '$name', 'average_score': {'$avg': '$grades.score'}, 'count': {'$sum': 1}}},
      {'$match': {'count': {'$gt': 3}}},
      {'$sort': {'average_score': -1}},
      {'$limit': 5}
])
for line in data:
   print(line)

print_delimiter('2 b)')

data = collection.aggregate([
      {'$unwind': '$grades'},
      {'$match': {'grades.grade': {'$eq': 'A'}}},
      {'$group': {'_id': {'name': '$name','cuisine': '$cuisine'},'average_score': {'$avg': '$grades.score'}, 'count': {'$sum': 1}}},
      {'$match': {'count': {'$gt': 3}}},
      {'$sort': {'average_score': -1}},
      {'$group': {'_id': '$_id.cuisine', 'restaurants': {'$first': '$_id.name'}, 'average_score': {'$first': '$average_score'}}},
      {'$limit': 5}
])
for line in data:
   print(line)

print_delimiter('2 c)')
data = collection.aggregate([
      {'$unwind': '$grades'},
      {'$match': {'grades.score': {'$gt': 10}}},
      {'$group': {'_id': {'$concat': ['$name', ' ']}, 'grades_count': {'$sum': 1}}},
      {'$match': {'grades_count': {'$gt': 2}}},
      {'$limit': 5}
])
for line in data:
    print(line)
