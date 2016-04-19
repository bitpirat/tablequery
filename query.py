import csv
from ast import literal_eval
from operator import itemgetter
from numbers import Number
from collections import OrderedDict

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
        zip_data = list(zip(column_names, values))
        for column_name, value in zip_data:
            setattr(self, column_name, value)
        self._column_names = column_names
        self._values = values
        self._dictionary = OrderedDict(zip_data)

    @property
    def column_names(self):
        return self._column_names

    @property
    def values(self):
        return self._values

    @property
    def dictionary(self):
        return self._dictionary
    
    def __str__(self):
        return str(self._values)

    def __getitem__(self, key):
        """ get the item at integer index key,
            or items at integer indexes in tuple key,
            or value for string column name key """
        if isinstance(key,tuple):
            data = self._values
            for n in key:
                data  = data[n]
            return data
        elif isinstance(key, str):
            return self._dictionary[key]
        return self._values[key]

    def __contains__(self, obj):
        return obj in self._values


class TableQuery:
    """
    sample query:
    get all rows where home_team is Packers:                    TableQuery(filename='nfl_1978.csv').query(home_team='Packers')
    get all rows where week is between 10 and 35                TableQuery(filename='nfl_1978.csv').query(week=lambda val: 10 <= val <= 35)

    get all rows where the home_team or                         table = TableQuery(filename='nfl_1978.csv')
        visiting_team is the home_team from                     week5 = table.query(week=5)[0][3]
        week 5's 1st game                                       (table.query(home_team=week5) + table.query(visiting_team=week5))
    """
    def __init__(self, data=None, raw_data=None, filename=None, column_names=None, header=False):
        if filename:
            with open(filename) as f:
                if header:
                    self.column_names = next(csv.reader(f))
                _data = [[eval_or_str(item) for item in line] for line in csv.reader(f)]
                if not header:
                    self.column_names = generate_column_names(len(_data[0]))
                self._data = [Row(self.column_names, row) for row in _data]
                if len(self._data) == 0:
                    raise ValueError("No data in file.")
        elif raw_data:
            _data = raw_data
            self._data = [Row(column_names, row) for row in _data]
            self.column_names = generate_column_names(column_names, len(_data[0]))
        elif data or data == []:
            self._data = data
            self.column_names = column_names
        else:
            print(data, raw_data, filename, column_names)
            raise ValueError('Invalid data.')

        self.indices = {v:k for k,v in dict(enumerate(self.column_names)).items()}

    @property
    def data(self):
        return self._data
    
    def format(self, delimiter=',', header=False):
        s = ''
        if header:
            s += delimiter.join(self.column_names) + '\n'
        return s + '\n'.join(delimiter.join(map(str, line)) for line in self._data)

    def query(self, query=None, get=None, **query_dict):
        """ query: a function, optional
            get: the indexes or indices to return of the final result, integer or tuple of integers
            query_dict: keywargs passed in, must be column names,
                        and must be a value or function that takes
                        the column value as a parameter

            How to use query:
            simple usage: obj.query(query=lambda row: 1980 < row.year < 2000 and row.home_team in ['Bears', '49ers'], get=0)
                          obj.query(winner='bob', year=lambda v: 1985 < v < 2000, get=(0,3))
                get is always optional
        """
        filtered = self._data.copy()
        if query:
            filtered = list(filter(query, filtered))
        if query_dict:
            indexed_queries = sorted([(self.indices[k], v) for k,v in query_dict.items()])
            query_indices, queries = list(zip(*indexed_queries))
            filtered = [line for line in self.data if all(call_equal(obj, comparison) \
                for (obj, comparison) in zip(tuple_wrap(itemgetter(*query_indices)(line)), queries))]

        if get == None:
            return self.__class__(data=filtered, column_names=self.column_names)
        elif isinstance(get, Number):
            return self.__class__(data=[itemgetter(get)(filtered)], column_names=self.column_names)
        else:
            # get must be tuple of indices
            return self.__class__(data=list(itemgetter(*get)(filtered)), column_names=self.column_names)

    def sort(self, *indices, keys=None, reverse=False):
        if keys:
            indices = [self.indices[key] for key in keys]
        self._data.sort(key=lambda row: itemgetter(*indices)(row.values), reverse=reverse)
        return self

    def __getitem__(self, key):
        if isinstance(key,tuple):
            data = self._data
            for n in key:
                data  = data[n]
            return data
        return self._data[key]

    def __iter__(self):
        for row in self._data:
            yield row

    def __str__(self):
        return self.format()

    def __add__(self, obj):
        return self.__class__(data=self._data + obj.data, column_names=self.column_names)

    @staticmethod
    def generate_column_names(column_names, num):
        if column_names == None:
            return ['column_{}'.format(n) for n in range(1, num + 1)]
        else:
            return column_names
