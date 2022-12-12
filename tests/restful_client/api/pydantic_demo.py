from datetime import date, datetime
from typing import List, Union

from pydantic import BaseModel, UUID4, conlist

from pydantic_factories import ModelFactory


class Person(BaseModel):
    def __init__(self, length):
        super().__init__()
        self.len = length
    id: UUID4
    name: str
    hobbies: List[str]
    age: Union[float, int]
    birthday: Union[datetime, date]


class PersonFactory(ModelFactory):
    __model__ = Person

result = PersonFactory.build()
print(result)
