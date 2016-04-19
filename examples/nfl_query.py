from tablequery.query import TableQuery
table = TableQuery(filename='nfl_1978.csv', header=True)
print('results')
print(table.query(lambda row: len(set([row.home_team, row.visiting_team]) & set(['49ers', 'Buccaneers', 'Broncos', 'Bengals', 'Chargers', 'Falcons', 'Packers'])) == 2))
