import csv
from ast import literal_eval
from operator import itemgetter
from numbers import Number

def eval_or_str(s):
    try:
        return literal_eval(s)
    except (ValueError, SyntaxError):
        return s

def call_equal(obj, comparator):
    if callable(comparator):
        return comparator(obj)
    return obj == comparator

def tuple_wrap(obj):
    if not isinstance(obj, tuple):
        return (obj,)
    return obj


class Row:
    def __init__(self, column_names, values):
        for column_name, value in zip(column_names, values):
            setattr(self, column_name, value)

class TableQuery:
    """
    sample query:
    get all rows where home_team is Packers:                    TableQuery(filename='nfl_1978.csv').query(home_team='Packers')
    get all rows where week is between 10 and 35                TableQuery(filename='nfl_1978.csv').query(week=lambda val: 10 <= val <= 35)

    get all rows where the home_team or                         table = TableQuery(filename='nfl_1978.csv')
        visiting_team is the home_team from                     week5 = table.query(week=5)[0][3]
        week 5's 1st game                                       (table.query(home_team=week5) + table.query(visiting_team=week5))
    """
    def __init__(self, data=None, filename=None, column_names=None, header=False):
        if filename:
            with open(filename) as f:
                if header:
                    self.column_names = next(csv.reader(f))
                self._data = [[eval_or_str(item) for item in line] for line in csv.reader(f)]
                if not header:
                    self.column_names = ['column_{}'.format(n) for n in range(1, len(self._data[0]) + 1)]
                if len(self._data) == 0:
                    raise ValueError("No data in file.")
        else:
            #assert isinstance(data, list)
            self._data = data

            if column_names == None:
                print('bullshit')
                self.column_names = ['column_{}'.format(n) for n in range(1, len(self._data[0]) + 1)]
            else:
                self.column_names = column_names

        self.indices = {v:k for k,v in dict(enumerate(self.column_names)).items()}

    @property
    def data(self):
        return self._data

    def format(self, delimiter=',', header=False):
        s = ''
        if header:
            s += delimiter.join(self.column_names) + '\n'
        return s + '\n'.join(delimiter.join(map(str, line)) for line in self.data)

    def query(self, query=None, get=None, _or=None, **query_dict):
        """ How to use query:
            simple usage: obj.query(query={'winner': 'bob', 'year': lambda v: 1985 < v < 2000}, get=0)
                          obj.query(winner='bob', year=lambda v: 1985 < v < 2000, get=(0,3))
                get is always optional

            Other usage is unhandled and may or may not work as expected.  You have been warned.
        """
        # returns rows where query dictionary of "column_num": "value" is true
        # value can also be a function, for filtering, i.e.
        # "column_2": lambda val: 3 <= val <= 8
        if query == None:
            query = query_dict
        
        filterable = self.data.copy()
        indexed_queries = sorted([(self.column_names.index(k), v) for k,v in query.items()])
        if query:
            query_indices, queries = list(zip(*indexed_queries))
            filtered = [line for line in self.data if all(call_equal(obj, comparison) \
                for (obj, comparison) in zip(tuple_wrap(itemgetter(*query_indices)(line)), queries))]
        else:
            query_indices, queries = ([],[])
            filtered = filterable
        #filtered = filter(lambda line: all(map(call_equal, itemgetter(*query_indices)(line), queries)), self.data)
        if _or:
            new_filtered = []
            for line in filtered:
                for k,v in _or.items():
                    indices = sorted([self.indices[key] for key in k])
                    if v in itemgetter(*indices)(line):
                        new_filtered.append(line)
                        break

            filtered = new_filtered

        if get == None:
            return self.__class__(data=filtered, column_names=self.column_names)
        elif isinstance(get, Number):
            return self.__class__(data=[itemgetter(get)(filtered)], column_names=self.column_names)
        else:
            # get must be tuple of indices
            return self.__class__(data=list(itemgetter(*get)(filtered)), column_names=self.column_names)

    '''
    # realized reflective queries would be hard, might as well just use the language
    # itself to do more advanced querying.  the reflective query given as an example
    # in the first line of the below docstring is possible, see the below __main__
    # with csvquery.query(winner=csvquery.query(etc.))
    def query_series(self, query_series):
        """ if performing reflective queries, i.e. "get all rows where the winner is the winner from 1933"
            in a csv file of mlb years and winners in the format "year,winner", then do this:
            complex usage: obj.query(query_series=[query_dict_1, where_column_1, query_dict_2, where_column_2, etc.])
            warning: this will create a nested result that is more nested with each iteration, unless you pass a get=0 parameter
        """
        if query_series:
            return self.__class__(data=filtered, column_names=self.column_names).query(where=query_series[1], query_series=query_series[2:], **query_series[0])
        if query_series:
            self.__class__(data=[getted], column_names=self.column_names).query(where=query_series[1], query_series=query_series[2:], **query_series[0])
        if query_series:
            return self.__class__(data=getted, column_names=self.column_names).query(where=query_series[1], query_series=query_series[2:], **query_series[0])
    '''

    def sort(self, *indices, keys=None, reverse=False):
        if keys:
            indices = [self.column_names.index(key) for key in keys]
        self._data.sort(key=itemgetter(*indices), reverse=reverse)
        return self

    def __getitem__(self, key):
        if isinstance(key,tuple):
            data = self._data
            for n in key:
                data  = data[n]
            return data
        return self._data[key]

    def __iter__(self):
        for line in self._data:
            yield line

    def __str__(self):
        return self.format()

    def __add__(self, obj):
        return self.__class__(data=self._data + obj.data, column_names=self.column_names)



if __name__ == '__main__':
    csvquery = TableQuery(filename='nfl_1978.csv', header=True)
    print()
    print((csvquery.query(home_team='Packers') + csvquery.query(visiting_team="Packers")).sort(keys=['week']))
    
    table = TableQuery(filename='nfl_1978.csv', header=True)
    week5 = table.query(week=5)[0][3]
    print('\nweek 5 first game\'s home team', week5)
    print('Games with home team Bears where visiting team was same team as the home team in the first game of week 5:')
    print((table.query(home_team=week5) + table.query(visiting_team=week5)).sort(keys=['week']).query(home_team='Giants'))

    # _or keywarg allows for filtering based on at least one value in a row is equal to the _or's dict value for any column in the key tuple
    print(table.query(_or={('visiting_team', 'home_team'):week5}).sort(keys=['week']).query(home_team='Giants'))
