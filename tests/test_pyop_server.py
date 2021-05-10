import unittest

from main import PyOPSever
import mvc.models.inputModels as md
from server.misc import isSequenceType



test_cases = [
    # format of input : (data,model,types,argsCount)
    {
        'data':{
            'a':3,'b':4,
        },
        'model':md.sumInputModel,
        'types':None,
        'argsCount':0,
        'output_as_list':[3,4,None,None],
    },
    {
        'data':{
            'a':3,'b':4,'c':'5'
        },
        'model':md.sumInputModel,
        'types':None,
        'argsCount':0,
        'output_as_list':[3,4,5,None],
    },
    {
        'data':{
            'a':'3','b':'4','c':'5'
        },
        'model':('a','b','c'),
        'types':{'a':int,'b':int},
        'argsCount':2,
        'output_as_list':[3,4],
    },
    {
        'data':"""{
            "a":"3","b":"4","c":5"
        }""",
        'model':('a','b','c'),
        'types':{'a':int,'b':int},
        'argsCount':2,
        'output_as_list':[3,4],
    },
    {
        'data':"""{
            "a":"3","b":"4","c":5"
        }""",
        'model':md.sumInputModel,
        'types':None,
        'argsCount':0,
        'output_as_list':[3,4,5,None],
    },
    {
        'data': "a=3&b='4'",
        'model':('a','b','c'),
        'types':{'a':int,'b':int},
        'argsCount':2,
        'output_as_list':[3,4],
    },
    {
        'data':"a=3&b='4'&c=5&e=9",
        'model':md.sumInputModel,
        'types':None,
        'argsCount':0,
        'output_as_list':[3,4,5,None],
    },
]

class Test_REQUEST_DATA_TO_OBJECT(unittest.TestCase):
    def test_json_to_class_parse(self):
        for test in test_cases:
            #test.get('class variables').get('mode',None)
            data = test.get('data',None)
            model = test.get('model',None)
            args_count = test.get('argsCount',None)
            input_params = ['PSEUSO_SELF',data,model,test.get('types',None),args_count]
            processed_data = PyOPSever.ParseRequestDataInToObject(*input_params)
            #desired = []

            desired_type = None
            if(type(model) == type):
                desired_type = model
            else:
                desired_type = type(model)
            # self.assertAlmostEqual(desired_type,type(processed_data),"Type Equality Check Failed")
            type_test = (isSequenceType(desired_type) and isSequenceType(type(processed_data)) or (desired_type is type(processed_data)))
            if(type_test == False):
                print("Failed")
            self.assertEqual(type_test,True,"Type Equality Check Failed")
            actual = []
            if(isSequenceType(desired_type)):
                actual = processed_data
            else:
                for prop,value in getattr(model,'__dict__').items():
                    if(not prop.startswith('_') and not callable(prop)):
                        #desired.append(test.get('data',None).get(prop,None))
                        actual.append(getattr(processed_data,prop))
            self.assertSequenceEqual(test.get('output_as_list'),actual,"Values Equality Check Failed")
