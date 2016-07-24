from tablequery import TableQuery
table = TableQuery(filename='nfl_1978.csv', header=True)
print('results')
teams = ['49ers', 'Buccaneers', 'Broncos', 'Bengals', 'Chargers', 'Falcons', 'Packers']
# this searches for any row where both the home
# and visiting teams are in the teams list
print(table.query(lambda row: len(set([row.home_team, row.visiting_team]) & set(teams)) == 2).data[0])
